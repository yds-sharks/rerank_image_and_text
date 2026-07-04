# /review-paper — 论文自审（模拟 Reviewer 视角）

模拟顶会 Reviewer 视角审稿，提供改进建议。

## 输入
用户提供：要审查的范围（全文 / 特定章节），目标会议/期刊（可选）

## 审查维度

### 1. Novelty & Contribution（新颖性与贡献）
- 核心创新点是否清晰？
- 与最相关工作的区别是否明确说明？
- 贡献是否 incremental？
- 给出 Novelty 评分：Strong / Moderate / Weak

### 2. Clarity & Presentation（清晰度与表达）
- 论文故事线是否连贯？
- 方法描述是否可复现？
- 符号定义是否一致？
- 图表是否自包含（图 + caption 能独立看懂）？
- 给出 Clarity 评分：Clear / Mostly Clear / Unclear

### 3. Soundness & Rigor（技术严谨性）
- 公式推导是否正确？
- 假设是否合理且明确说明？
- 实验设计是否公平（相同条件对比）？
- 结论是否有数据支撑？
- 给出 Soundness 评分：Sound / Minor Issues / Major Issues

### 4. Experiments（实验充分性）
- 数据集是否足够且有代表性？
- Baseline 是否包含最新 SOTA？
- 指标是否标准且全面？
- 是否有 ablation study？
- 是否有统计显著性分析？
- 给出 Experiments 评分：Sufficient / Partially Sufficient / Insufficient

### 5. Writing Quality（写作质量）
- 语法、拼写
- 格式规范（引用、图表编号）
- 页数限制

## 输出格式

```
## Review Summary

### Overall Score: X/10
### Recommendation: Accept / Weak Accept / Borderline / Weak Reject / Reject

### Strengths
1. ...
2. ...
3. ...

### Weaknesses
1. [Major] ...
2. [Major] ...
3. [Minor] ...

### Questions to Authors
1. ...
2. ...

### Detailed Comments
#### Section 1: Introduction
- ...

### Suggestions for Improvement
1. [Priority: High] ...
2. [Priority: Medium] ...
3. [Priority: Low] ...
```

## 工作流程

1. 读取全部 .tex 文件
2. 按 5 个维度逐一审查
3. 生成结构化审稿意见
4. 输出到终端 + `paper/data/tmp/review_report.md`

## 输出
- 审稿报告: `paper/data/tmp/review_report.md`
- 终端输出审查摘要

$ARGUMENTS
