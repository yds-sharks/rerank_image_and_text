# /outline — 论文框架梳理与大纲设计

帮助梳理论文整体结构、故事线、章节分配和写作策略。

## 输入
用户提供：研究主题、核心贡献、已有设计文档（可选）

## 工作流程

### 阶段一：信息收集
1. 读取 `design_docs/data/persistent/` 中的设计文档
2. 确认以下关键要素：
   - 解决什么问题（Problem）
   - 为什么重要（Motivation）
   - 核心方法/创新点（Contribution）
   - 实验验证了什么（Evaluation）
   - 与已有工作的区别（Novelty）

### 阶段二：故事线设计（Story Arc）
构建论文的叙事逻辑链：

```
Problem → Why existing methods fail → Key insight → Our approach → Why it works → Experiments prove it
```

具体包括：
- **Hook**：开篇用什么场景/数据抓住读者
- **Gap**：现有方法的核心短板是什么
- **Bridge**：我们的 key insight 是什么
- **Solution**：方法概述（一句话版本）
- **Evidence**：什么实验最有说服力

### 阶段三：章节大纲
为每个章节生成：
- 核心论点（1 句话）
- 关键段落列表（每段 1 句话 topic sentence）
- 需要的图/表
- 预估页数

### 阶段四：输出

生成 `paper/code/outline.md`，包含：

```markdown
# Paper Outline: {标题}

## Story Arc
[一段话描述论文故事线]

## Abstract (0.5 page)
[3-4 个要点]

## 1. Introduction (1.5 pages)
### 段落分配
- P1: [Hook + 问题背景]
- P2: [现有方法及不足]
- P3: [Our insight + 方法概述]
- P4: [贡献总结，3 个 bullet]
### 需要的图表
- Figure 1: 动机图/概览图

## 2. Related Work (1 page)
[分成 2-3 个子方向]

## 3. Method (2-3 pages)
### 3.1 Problem Formulation
### 3.2 [核心方法模块 1]
### 3.3 [核心方法模块 2]
### 需要的图表
- Figure 2: 架构图
- 关键公式列表

## 4. Experiments (2-3 pages)
### 4.1 Setup (数据集、基线、指标)
### 4.2 Main Results
### 4.3 Ablation Study
### 4.4 Analysis / Case Study
### 需要的图表
- Table 1: Main results
- Table 2: Ablation
- Figure 3: 分析图

## 5. Conclusion (0.5 page)
```

## 页数预算
根据目标会议/期刊调整：
- ACL/EMNLP: 正文 8 页
- NeurIPS/ICML: 正文 9 页
- AAAI: 正文 7+1 页
- Nature/Science: 短文 4-5 页

## 输出
- 大纲文件: `paper/code/outline.md`
- 终端输出故事线和章节概要

$ARGUMENTS
