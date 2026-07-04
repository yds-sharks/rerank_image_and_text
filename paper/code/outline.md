# Paper Outline: MedAlign-RAG（v0.3）

> **标题（定稿）**：MedAlign-RAG: Agentic Cross-Modal Evidence Search with Answer-Utility Rewards for Multimodal Medical Question Answering
> 目标会议：AAAI 2026（正文 7 页 + 1 页 + 参考文献不限）
> 定位：**Agentic 多模态检索（agentic search）**（医学内镜 QA，EndoBench）——既解通用多模态 RAG 问题，又做医学专属优化
> 状态：**结果未出，Main Results 留空**；框架已与作者对齐并按 agentic 方向重构
> 更新：**v0.3 重大转向（pivot）**——放弃子模 rerank 主贡献（PPR/SEV/ODSC 实测无正收益）。新主贡献 = answer-utility RL 训练的 agentic 跨模态证据代理：判证据价值(图+文) → accept 生成 / reject 改写重检索。奖励 = P_G(a*|E) − P_G(a*|∅)，MCQ 无需逐条标注。删原痛点1（缺统一排序空间）；密度路由降为支撑贡献；端到端图文评测变为方法内在必需（奖励即端到端信号）。
> 历史：v0.2 曾为三大机制痛点（对齐排序 / 密度门控 / 视觉相似≠临床相同）+ 子模选择器，已作废。

---

## 〇、一句话定位

> 现有多模态医学 RAG 的证据选择是**被动、一次性、相似度驱动**的：把 relevance 当 answer-utility，池子差了无补救，医学场景更被"视觉相似≠临床相同"误导。我们把证据选择重构为 **agentic 决策过程**：一个视觉语言 agent 判断每条图/文证据价值，accept 生成或 rewrite 重检索，用 **answer-utility 奖励**（提供证据后正确答案概率的提升量，MCQ 天然可算、无需逐条标注）训练，在修正后的端到端图文评测下验证。

---

## 一、痛点问题（Pain Points）— 三大机制痛点 + 一条评测动机

### 痛点 1：图文融合阶段缺乏统一对齐排序（Cross-Modal Alignment for Reranking）★主贡献
- 现象：文本候选与图像候选活在**不同特征空间**（BGE-M3 1024d vs Qwen3-VL 4096d）。现有 rerank 要么把图像降级成 caption 做文本代理（cross-encoder / listwise-LLM），要么两路分数硬拼（fusion）——**没有一个统一的跨模态空间去联合排序一组证据**。
- 后果：跨模态鸿沟——文本抓语义、图像抓形态，二者无法在同一尺度比较；VLM 的 vision tower 信号被丢弃。
- 差异化立论（写作时必须讲清，防审稿人质疑"这不就是 CLIP 对齐"）：我们做的是**推理期、面向 RAG 证据集选择的对齐**——不训练新对齐器，直接用 VLM vision tower 做跨模态打分与集合选择，目标是"选对证据集"而非"检索召回"。
- 附带子问题（并入本痛点动机）：证据是**组合价值**而非独立相关性——图给形态、文给诊断标准，应互补；top-K 独立打分导致冗余同模态证据。

### 痛点 2：低判别文本是噪声源，非仅密度不一致（Low-Discriminability Text as Noise）→ 模态路由
- 两层立论：
  - **(a) 信息密度不一致**：同一 query 下判别信息在文本 vs 图像分布比例不同——有的文本已说全（高密度 L4），有的必须看图（高图像依赖 R3）。固定融合权重必然对一部分 query 失效。
  - **(b) 主打·低判别文本主动制造噪声**：部位/结构类泛化文本（"这是哪个部位""图中是什么结构"）不带判别性检索信号，喂进检索反而把同部位/同结构但不同病理的候选全捞进来，系统性引入同质误召回。→ 与痛点3咬合：正因这类文本会捞进同质候选，才更需下游判别式选择。
- 关键结论：不是"按比例配权重"，而是**某个模态多用反而有害，必须能被抑制/关掉**（more of a modality hurts，反直觉卖点）。
- 我们的刻画：模态路由（语义密度 L0-L4 + 图像依赖 R1-R3）动态分配检索预算与融合权重，φ 饱和时可把某路预算/权重压到 0，等效关掉噪声模态。**已实现，checkpoints 就绪。**

### 痛点 3：视觉相似 ≠ 临床相同（Visual-Homogeneity False Positives）★医学专属
- 现象：内镜图像高度同质——同一部位不同病理在像素层面极像。纯视觉相似度检索/排序会返回**"高置信但临床错误"**的证据，这是通用 RAG 没有的医学痛点。
- 后果：相似度 top-K 在医学图像上系统性误召回；越"相似"越危险。
- 与痛点 1 的耦合：正因为视觉相似会误导，对齐排序必须是**语义判别式**（能把正确答案从干扰项区分），而非相似度排序 → 这条把方法从"又一个 rerank"抬升为"针对医学跨模态误召回的证据选择"。

### 评测动机（非核心贡献，作 motivation + 一个对照实验）：评测盲区
- 现象：主流多模态 RAG 检索了图像，生成阶段却只把 caption 喂给模型，VLM 从未真正"看到"检索到的图。
- 用途：EndoBench 84.5% 是图像依赖 query，text-proxy 评测系统性掩盖视觉证据价值 → 作为 Figure 1 动机图 + Experiments 的一个揭示性对照（现在就能做，不依赖重排序跑通）。

---

## 二、核心洞察（Key Insight）

> 把图文融合排序的目标从 **"query-candidate 相关性最大化"** 重新定义为 **"在真实图文输入下，选出一组视觉锚定、语义可判别、图文互补的证据集"**。
> 桥梁：用 VLM 的 vision tower 直接做跨模态打分与集合选择，绕过文本代理的信息损失；用 option-aware 判别压制医学图像"视觉相似≠临床相同"的误召回。

---

## 三、创新点（Contributions）— 3 个机制贡献（对应三大痛点）

### C1：跨模态证据集对齐选择器（Cross-Modal Evidence Selection）★核心，对应痛点1+3，结果 TBD
- 统一 Qwen3-VL-Embedding-2B 编码，vision tower 做跨模态打分，把图文候选放到同一尺度联合排序。
- 选择目标为**一个统一的证据集目标函数**（由 VCMS/ODSC 两套草稿收敛而来）：
  - **视觉锚定**（对应痛点1）：直接用 vision tower 距离，不走文本代理
  - **语义判别力**（对应痛点3）：option-aware sub-query，选"能判别选项"的候选，压制"视觉相似但临床错误"的高置信误召回
  - **互补/去冗余**（组合价值）：submodular 贪心，(1-1/e) 近似保证，图文互补加分
- 交付：Main Results + 消融 + case study。**当前留空，待实现跑通。**

### C2：密度感知模态路由（Density-Aware Modality Routing）对应痛点2
- Mengzi-BERT 双分类器：语义密度 L0-L4 + 图像依赖 R1-R3，动态分配文本/图像检索预算与融合权重；φ 饱和时可关掉噪声模态（预算/权重→0）。
- 交付：路由 vs 固定权重的消融，证明按 query 密度分配预算 + 抑制噪声文本能减噪。
- **已实现（checkpoints 就绪）。**

### C3：修正的端到端图文评测协议（Corrected Multimodal Evaluation）支撑动机
- 揭示 text-proxy 评测缺陷，提出真实图像证据喂入 VLM 的端到端评测。
- 交付：对照实验（text-only vs image-text 输入）量化评测盲区偏差。
- **现在即可完成，不依赖 C1 跑通——为整篇论文提供"为什么这个问题重要"的地基。**

> 决策点（C1 方法路线）：**统一多项目标函数**（视觉锚定 + 判别 + 子模去冗余），兼顾 ODSC 理论保证与 VCMS 视觉桥梁。已按此写入，待实现验证。

---

## 四、故事线（Story Arc）

```
Hook: 临床诊断天然图文并用；医学 RAG 却在"假装看图"
  → Gap0(动机): 评测只传文本，视觉价值被掩盖 → 修正后瓶颈转向融合排序（痛点0/C3）
  → Gap1: 图文融合缺统一对齐排序，rerank 全在文本空间（痛点1）
  → Gap2: 图文信息密度不一致，固定权重失效（痛点2）
  → Gap3: 医学图像视觉相似≠临床相同，相似度排序系统性误召回（痛点3）
  → Insight: 融合排序目标应是"视觉锚定 + 语义判别 + 图文互补的证据集"
  → Solution: 双门控路由(C2) + 跨模态证据集选择器(C1)，在修正图文评测(C3)下验证
  → Evidence: 评测盲区对照(C3) + 路由消融(C2) + 证据选择超越 top-K/cross-encoder/PPR(C1, TBD)
```

---

## 五、章节大纲（AAAI 7+1 页）

### Abstract（≤150 words，AAAI 硬约束）
- 4 点：问题(图文融合缺对齐排序 + 密度不一致 + 医学视觉误召回) / 洞察(视觉锚定+判别+互补的证据集选择) / 方法(双门控路由 + 跨模态证据集选择器 + 修正图文评测) / 结果(EndoBench 提升，TBD)

### 1. Introduction（1.5 页）
- P1: Hook — 临床图文并用 + 医学 VQA 检索增强趋势；引出"评测只传文本"的盲区（Figure 1 动机图）
- P2: 痛点1 图文融合缺统一对齐排序（rerank 全在文本空间）
- P3: 痛点2 图文信息密度不一致 + 痛点3 医学视觉相似≠临床相同
- P4: 洞察 + 方法一句话 + 3 个贡献 bullet（C1 证据选择 / C2 双门控 / C3 修正评测）
- 图表：Figure 1（动机图：text-proxy vs 真实图文输入准确率差）

### 2. Related Work（1 页）
- 2.1 Multimodal RAG（MuRAG / RA-CM3 / RAG-Anything）— gap: 无跨模态重排序、评测只用文本
- 2.2 Evidence Reranking（cross-encoder / listwise-LLM / PPR）— gap: 文本空间、优化相关性
- 2.3 Medical VQA & Benchmarks（LLaVA-Med / EndoBench）— gap: closed-book，无检索增强

### 3. Method（2.5 页）
- 3.1 Problem Formulation（图文 RAG 形式化 + 评测协议定义）
- 3.2 Dual-Path Retrieval（BGE-M3 文本 + Qwen3-VL-8B 图像）
- 3.3 Dual-Gate Routing（密度 + 图像依赖 → 预算分配）
- 3.4 Cross-Modal Evidence Selection ★（统一目标函数：视觉锚定+判别+多样性）
- 3.5 Multimodal Generation（真实图文证据喂入 VLM）
- 图表：Figure 2（系统架构图）、Figure 3（证据选择方法示意）、核心公式 4-6 条

### 4. Experiments（2.5 页）
- 4.1 Setup：EndoBench 6832 MCQ / 基线 / 指标 / 实现细节（匿名化）
- 4.2 **评测盲区实验**（C3）：text-only vs image-text 输入对照 ← 现在可做
- 4.3 Main Results（C1）：**留空表格**，占位 7 个基线
- 4.4 Ablation：门控(C2) / 目标项 / 簇数 K / 选择策略 / vision tower 规模
- 4.5 Analysis：case study + 聚类 t-SNE + 模态分布 + 错误归因
- 图表：Table 1（评测盲区）、Table 2（Main，留空）、Table 3（消融）、Figure 4（case study）

### 5. Conclusion（0.5 页）

---

## 六、插图与表格规划（大头 — 逐个定位）

> AAAI 双栏 7+1 页。图占版面且决定第一印象，按"讲清一个论点用一张图"排布。
> 跨栏用 `figure*`（浮到页顶）；单栏用 `figure`。当前 .tex 里 Fig1/Fig2 已放占位框。

### 页面级布局（预估）
```
p1  col1顶: Fig 1 动机图(单栏)          | 正文 Intro
p2  顶部跨栏: Fig 2 架构图(figure*)      | Related Work / Method 开头
p3  col?: Fig 3 证据选择示意(单栏或跨栏) | Method 3.4
p4-5 顶部: Tab 1(评测盲区) + Tab 2(Main,跨栏) | Experiments
p5-6 col?: Fig 4 Case study(单栏/跨栏) + Tab 3 消融 | Analysis
p6  col?: Fig 5 t-SNE(单栏,可选)         | Analysis
```

### 逐图规格

| 编号 | 位置 | 栏 | 内容与要点 | 状态 |
|------|------|----|-----------|------|
| **Fig 1** 动机图 | p1 顶部 | 单栏 | 上半：概念示意——检索到图却只喂 caption（text-proxy）vs 喂真图；下半：小柱状图，同一 rerank 在 text-only vs image-text 下准确率差（暴露盲区）。**全篇第一卖点** | 可先做（需 C3 对照数据） |
| **Fig 2** 架构图 | p2 顶部 | **跨栏** figure* | 四阶段流水线：双路召回 → 密度门控（预算分配）→ 跨模态证据选择（视觉锚定/判别/子模）→ VLM 生成。用 /plot-arch | 可先做 |
| **Fig 3** 证据选择示意 | p3 Method内 | 单栏（挤则跨栏） | 候选池在统一空间的分布；三项作用可视化：视觉锚定拉近、option 判别压制"视觉相似≠临床相同"、子模去冗余选互补集合。用 /plot-motivation | 待方法定稿（已定，可做） |
| **Fig 4** Case study | p5-6 Analysis | 单栏起（可跨栏） | 一道真实题：top-K 选出的冗余/误召回证据 vs 本方法选出的判别性证据；**必含一个视觉相似但临床错误的反例** | **待结果** |
| **Fig 5** t-SNE（可选） | p6 Analysis | 单栏 | 候选 embedding 聚类结构 + 被选中点标注，佐证多样性 | **待结果** |

### 逐表规格

| 编号 | 位置 | 栏 | 内容 | 状态 |
|------|------|----|------|------|
| **Tab 1** 评测盲区 | p4 Experiments | 单栏 | 同方法 text-only vs image-text 输入的准确率（分图像/混合 query），量化盲区偏差 | 可先做 |
| **Tab 2** Main Results | p4-5 | **跨栏** table* | 7 基线 × {图像/混合/总体}；**当前留空占位** | **留空** |
| **Tab 3** 消融 | p5 | 单栏 | 门控 on/off、目标项(rel/disc/cov)、簇数/K、选择策略(medoid/nearest/random) | 部分可做（门控行先填） |

### 制作优先级（不依赖 rerank 结果的先做）
1. **Fig 2 架构图**（纯示意，最能先定稿，且帮团队对齐管线）
2. **Fig 1 动机图** + **Tab 1**（需要跑 C3 评测盲区对照，数据量小、现在能跑）
3. **Fig 3 方法示意**（方法已定，可示意性绘制）
4. Fig 4 / Fig 5 / Tab 2 / Tab 3主体 —— 等 rerank 跑出效果再做

---

## 七、已定方向（v0.2 与作者对齐）

1. **痛点结构**：三大机制痛点——对齐排序(1) / 密度门控(2) / 视觉相似≠临床相同(3)；评测盲区降级为动机 + 对照实验。✔
2. **多模态 RAG + 医学专属双层立论**：痛点1/2 是通用多模态 RAG 问题，痛点3 是医学针对性优化。✔
3. **C1 方法路线**：统一证据集目标函数（视觉锚定 + 判别力 + 子模去冗余）。✔

## 八、仍待你拍板

1. ~~标题~~ ✔ 定为 **MedAlign-RAG**（见文件顶部）。
2. **写作顺序**：先写哪一章？建议从 **Method（3.3 门控 + 3.4 证据选择）** 或 **Introduction** 起手——门控已实现、Intro 立论已清晰，都可脱离 TBD 结果先写。
