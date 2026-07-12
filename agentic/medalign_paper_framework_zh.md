# MedAlign-RAG 设计思路（解耦版）

> 版本 v0.3（2026-07-11 重写）。本文是 agentic 部分的**权威设计思路**，取代旧版
> framework/workbench spec 中相互矛盾的表述。核心变化：agent 与 reranker 职责解耦，
> reranker 用现成 reranker 模型（弃 PPR），奖励改为 answer-utility，训练走 SFT 暖启 → GRPO。

---

## 1. 论文定位

本文的核心贡献不是新的 retriever / reranker / generator，而是：

> 在固定的多模态 RAG 前端之上，训练一个由 **answer-utility 奖励**驱动的
> **agentic 证据控制器**。它对固定 reranker 给出的少量候选做**逐条跨模态取舍
> （keep/drop）**，判断证据是否足以作答（**ACCEPT**），不足则**改写 query 重新检索
> （REWRITE）**，从而提升最终多模态问答效果。

系统中 retriever、密度路由、reranker、generator 全部**冻结**，唯一被训练的组件是这个
agent。这样避免"堆模块"的审稿风险，也让性能变化能干净地归因到 agent。

| 模块 | 作用 | 是否训练 | 角色 |
|---|---|---|---|
| 双路粗召回 | 从文本库/图像库各召回 top-20 | 否 | 固定前端 |
| 密度感知路由 | 分配文本/图像检索预算、可关噪声模态 | 否 | 固定前端（支撑贡献 C2）|
| 多模态 reranker | 把 40 候选压到小 top-k（k≈6–8） | 否 | 固定观察压缩器 |
| **agent** | **keep/drop + ACCEPT/REWRITE + 改写 query** | **是** | **核心贡献 C1** |
| generator | 基于 kept 证据答 MCQ 并提供 logprob 奖励 | 否 | 冻结评估器 |

---

## 2. 核心问题与三痛点

现有多模态 RAG 多为一次性流程 `query → retrieve → rerank → generate`，一旦初始 query
低密度、图像依赖强，或召回被"同部位不同病理"的相似证据干扰，系统没有自我恢复机制。

- **P1（主）被动一次性相似度选择**：rerank/select 只在已有候选内按相似度排序，
  (a) 分不清"相关"与"真正有用于答对"（relevance ≠ answer-utility）；
  (b) 证据池差时无补救（不能改写重检索）。
- **P2（医学专属）视觉相似 ≠ 临床相同**：内镜图像里同部位不同病理可能视觉高度相似，
  相似度系统会系统性召回"高置信但临床错误"的证据。需要"判价值"而非"判相似"。
- **P3（支撑）图文信息密度不一致**：低判别文本会主动制造噪声 → 密度路由，可关掉噪声模态。

本文关注：**当 reranked top-k 不足以支持回答时，agent 能否用 answer-utility 奖励学会
（i）否决误导证据、（ii）判断是否需要改写、（iii）改写 query 使重检索逼近真正有用的证据。**

---

## 3. 方法总览

### 3.1 链路

```text
原始 query（低信息）+ query image
      │
      ▼
密度感知路由（分配文本/图像检索预算）      ← 每轮重检索都重新路由
      │
      ▼
双路粗召回（文本 top-20 + 图像 top-20）
      │
      ▼
固定多模态 reranker → 小 top-k 证据（k≈6–8，图文混合）
      │
      ▼
agent（Qwen3.5-4B 原生多模态，读像素）
  一次结构化输出：先 keep/drop，再 action
      │
      ├─ ACCEPT → generator 基于 kept 证据答 MCQ → answer
      │
      └─ REWRITE → 新 query（+ 抑制 dropped/已见 ID）→ 回到路由/召回，最多 T 轮
```

### 3.2 agent 的动作空间（一个模型、一次输出）

agent 是**单个 VLM policy**，读入：question、options、query image（像素）、当前 top-k 每条证据
（modality、文本、图片像素或路径、reranker score）。**一次性**吐出一段结构化 JSON，
决策按 token 顺序排列——**keep/drop 在前**（先看筛完剩什么），**action 在后**：

```json
{"keep": [1,3,4], "drop": [2,5], "action": "ACCEPT"}
```

```json
{"keep": [1], "drop": [2,3,4,5], "action": "REWRITE", "rewrite_query": "..."}
```

- **不是两个模型、不是两次调用**，就是一个 policy 自回归生成这一段；动作 = 解析 JSON。
- keep/drop 是**小范围逐条否决**（对 reranker 给的 k 条，不是对 40 条重排）→ 动作空间有界、
  方差可控，且**不等于再训一个大 reranker**。
- **P2 落点**：keep/drop 让 agent 能显式 drop 掉"视觉相似但临床错"的证据；REWRITE 通过注入
  判别性临床词 + 抑制已见 ID，把临床正确的证据从相似陷阱里"拉上来"。

### 3.3 抑制（suppression）

REWRITE 时把 dropped / 前几轮已见的证据 ID 在**召回层**排除（不是 rerank 层），使多轮检索
**单调探索新证据**、避免在同一批垃圾上打转。注意：只在召回层抑制，避免把"被 reranker 排错、
其实正确"的证据永久删掉。

---

## 4. 奖励设计（answer-utility，护城河）

唯一主奖励来自**冻结 generator 的答案效用**，不来自检索相关性命中：

```text
对某个动作 a（其产出的证据集为 E_a）：
    r(a) = P_G(a* | q, I_q, E_a) − P_G(a* | q, I_q, ∅)
```

- `a*` 为正确选项 token，`P_G` 为冻结 generator 给正确选项的概率（从 vLLM logprobs 取）。
- ACCEPT 的 `E_a` = kept 子集；REWRITE 的 `E_a` = 重检索+重排+再 keep 后的证据集。
- baseline `P_G(...|∅)` = 不给证据时的概率。

> ⚠️ 这是整个方法的护城河。一旦奖励退回"检索命中/相关性"，方法就塌成"学一个检索 query
> 改写器"，与 Search-R1 / IterRetGen / DeepRAG 撞车且丢失医学特异性。**generator 必须能出
> logprob，否则奖励与下文软标签都算不出来。**

轻量约束项（工程约束，论文里不作为主贡献）：无效 JSON、泄露答案字母、改写过长、不必要改写
（原证据已够仍 REWRITE）各扣少量分。

---

## 5. 训练框架

### 5.1 GPT Agent 预验证（Go/No-Go 闸门）

训练小模型前，先用 GPT 当 agent 跑同一批样本，比较：

```text
原始 query → 召回/rerank/kept → generator → reward_original
GPT 决策（keep/drop + ACCEPT/REWRITE）→ ... → reward_gpt
```

若 GPT 不能稳定优于 no-op，则先查数据/召回/reranker/generator，不急于训小模型。

### 5.2 两阶段训练（SFT 暖启 → GRPO）

**阶段一：cold-start SFT 暖启（保持轻）**
目标只是让模型出合法 JSON + 粗略正确的先验，**不喂太饱**（喂饱=RL 没空间=稀释主线）。
监督目标为完整 JSON（keep/drop + action 一起）：
- keep/drop 标签 = 见 §6 软标签（冻结 generator 自动生成，无需人工）。
- ACCEPT/REWRITE 及 rewrite 文本标签 = 来自 GPT rollout（§5.1）里 utility 真升的决策。

**阶段二：GRPO（主线、增益来源）**
每个 query 一个 group，组内包含多个动作各自跑完整闭环：

```text
{ ACCEPT(原始 top-k),  keep-子集,  rewrite 分支×N }
 每个动作 → (REWRITE 则重检索) → rerank → kept → generator → r(a)
```

GRPO 用组内相对优势 `A = (r − mean)/std` 推动 policy 偏向高 answer-utility 的动作。

### 5.3 为什么 SFT 不够、也不违背 agentic RL

- **SFT 不够**：软标签是代理信号（天花板受限）；SFT 只能模仿 GPT 的改写、发现不了更优改写；
  无组内反事实比较；多轮时单步模仿会累积漂移。**RL 才是真正优化 answer-utility 的地方。**
- **不违背主线**：SFT→RL 是标准做法（RLHF 的 SFT→PPO、DeepSeek-R1 的 cold-start SFT→RL）。
  headline 仍是"policy 由 answer-utility RL 优化"，SFT 写成 cold-start/rejection-sampling 暖启。
- **硬要求**：必须做 **SFT-only vs SFT+RL 消融**，用数字证明 RL 挣到了它的位置（也是卖点）。

---

## 6. keep/drop 软标签构造（自动、无需人标）

用冻结 generator 当"探针"，看每条证据把正确答案概率抬高还是压低：

1. **测基线**：只给"题目+题图+选项"（无检索证据），记正确选项概率，例 0.30。
2. **逐条测增量**：把 top-k 每条证据 e_i 单独加入再问一次，记新概率：
   - +第3条 → 0.55（增量 +0.25）→ keep
   - +第2条 → 0.20（增量 −0.10）→ drop
3. 对 k 条各做一遍 → 得逐条 keep/drop 标签，作为阶段一 SFT 目标。

概率来源：让 generator 只输出单字母答案，从 vLLM logprobs 取该字母 token 的 logprob 转概率。
廉价版"逐条单加"忽略交互但够暖启用；更准的 leave-one-out 更贵，非必需。

---

## 7. 模型选型

| 组件 | 选型 | 说明 |
|---|---|---|
| policy（训练） | **Qwen3.5-4B（原生多模态，看像素）** | 任务规模够用；看图才能撑 P2 的视觉否决 |
| generator（冻结） | Qwen3-VL-8B-Instruct（vLLM，需开 logprobs） | 算 answer-utility 与软标签 |
| reranker（冻结） | 现成 reranker 模型（**弃 PPR**） | 40→小 top-k；见下 |
| 文本召回 | BGE-M3（1024d，~517K 段，top-20） | 冻结 |
| 图像召回 | Qwen3-VL 图像塔（4096d，~66K 图，top-20） | 冻结 |
| 密度路由 | Mengzi-BERT 双头（密度 L0–L4 + 图像依赖 R1–R3） | 冻结，checkpoint 就绪 |

> **reranker 待定项**：候选池含文本+图像，需要能对图文联合打分的多模态 reranker，
> 或明确"reranker = 一阶分数排序（NoOp）"并如实写。**不要用 embedding 双塔冒充 reranker。**
> 这是当前最欠定义的一块，实现前需拍板。

---

## 8. 数据构造（详见 data_construction_design_zh.md）

- 训练数据**不使用 benchmark 样本**；benchmark 仅用于统计分布与最终测试。
- 来源：自有向量库 image-text pair + 原始 PDF + 图注/邻近正文 + 器官/病理元信息。
- 每条为四选一 MCQ：question / options / answer / answer_text / query_image_path / source。
- **正确答案由来源元信息 + 独立 verifier 决定，不由 API 单独判定。**
- 生成与校验的 API 调用**必须传入图像像素**（否则"图像依赖"与 verifier 独立性失效）。
- pipeline：`prepare_qa_source_pool → route_qa_source_pool → generate（API，带图）→
  verify（API，带图）→ validate`。按 doc_id 切分防泄漏；lesion 类优先"同部位不同病理"hard neg；
  禁止 taxonomy 元分类题。

---

## 9. 实验设计

### 9.1 主表

| Method | keep/drop | Rewrite | Trainable | Overall |
|---|---|---|---|---|
| Closed-book generator | — | No | No | TBD |
| Retrieve + rerank top-k | No | No | No | TBD |
| + agent（no rewrite，仅 keep/drop） | Yes | No | Yes | TBD |
| Agentic baselines（Self-RAG / Search-R1 / IterRetGen 适配） | — | Yes | Yes | TBD |
| **MedAlign-RAG（full RL）** | Yes | Yes | Yes | TBD |

### 9.2 消融

- keep/drop on/off；
- rewrite + re-retrieve on/off；
- 抑制 suppression on/off；
- 奖励：answer-utility vs relevance/format（证明护城河）；
- **SFT-only vs SFT+RL（证明 RL 增益）**；
- 最大轮数 T（1 vs 2）；
- 密度路由 on/off。

### 9.3 分析指标

最终 accuracy 外：rewrite trigger rate、keep/drop 准确率（对照 §6 离线 utility 标签）、
证据 utility lift、平均轮数、模态分布、invalid JSON rate、answer leakage rate、
kept 证据中有效证据比例变化。

---

## 10. 叙事边界

**不主打**：新 retriever / reranker / generator / 器官识别 / 图文权重模块。
**主打**：固定多模态 RAG 前端上、由 answer-utility RL 训练的 agentic 跨模态证据控制器
（keep/drop + accept/rewrite）。这一定位降低"堆模块"风险，也让消融清晰。

---

## 11. 与代码现状的差距（实现待办）

- `code/reward_model.py`：当前是 evidence-hit（相关性命中），**需改为 §4 的 answer-utility**。
- `code/generator_adapter.py`：当前只回文本，**需支持取 logprob**（vLLM logprobs）。
- `code/rerank_adapter.py`：当前只有 PPR/NoOp，**需替换为现成 reranker 模型**（§7 待拍板）。
- 密度路由未接入 runtime（retrieval_adapter 有 level1/level2 钩子但未传）——**需接线**。
- 数据侧缺 `generate_qa_candidates_with_api.py`（生成 caller，须带图），verify 须对齐新流字段
  并默认带图、复用 `qa_api_prompts.py`。
