# 当前目标

撰写 AAAI 2026 论文：**MedAlign-RAG**（医学多模态 RAG，EndoBench）。**已转向 agentic search**：
answer-utility RL 训练的 agentic 跨模态证据代理——判每条图/文证据价值，accept 生成 or rewrite 重检索；
奖励 = P_G(a*|E) − P_G(a*|∅)（MCQ 天然可算，无需逐条标注）。密度路由降为支撑贡献，端到端图文评测内在必需。

## 阶段

- [已完成] 全篇按 agentic 方向重构：main 标题 / abstract / introduction / method 3.4 / related_work / experiments 全部重写
- [已完成] Fig 2 重画为闭环 agentic 流水线（figures/data/tmp/figures_arch_medalign.png）
- [已完成] 正文全篇成稿（conclusion 补齐）；RL 训练+数据构造方案设计
- [已完成] 数据 pipeline 两脚本（清洗 design_docs_01 + 源锚定合成 design_docs_02），样本/fixture 验证通过
- [阻塞] 全量数据（/mnt/data_1 语料库、/mnt/data_10 retrieval_export 6832）本会话未挂载；HF/simula 被墙 → 需用户挂载或导出
- [下一步] 数据到位后跑全量清洗 + 接真 API 合成 5-10K（硬负例30-40%）；补查询图 I_q 回连；Overleaf 编译；Main Results 待结果

## 关键位置

- LaTeX 正文：`paper/code/sections/*.tex`（method.tex 核心：eq:policy + eq:reward）
- 大纲（v0.3 记录 pivot）：`paper/code/outline.md`
- Fig 2 脚本：`figures/code/figures_arch_medalign.py`
- 事实来源：`design_docs/data/persistent/rerank_source/pipeline_summary.md`（模型/数据规模/旧结果）

## 已确认决策（作者）
- 标题：MedAlign-RAG: Agentic Cross-Modal Evidence Search with Answer-Utility Rewards...
- Agent policy 底座：Qwen3-VL 小模型（原生看图）
- RL 算法：method 用通用 policy-gradient 表述，不锁定 GRPO/PPO
