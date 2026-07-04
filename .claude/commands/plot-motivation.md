# /plot-motivation — 动机图/示例图绘制

绘制论文 Introduction 中的动机图、Case Study 图、对比示例图。

## 输入
用户提供：要展示的动机/问题/对比场景

## 动机图类型

### 1. 问题示例图（Problem Illustration）
展示现有方法的不足，突出你的方法解决的问题。
- 左右对比：Bad Case vs. Good Case
- 上下对比：Baseline Output vs. Our Output
- 用红色/绿色高亮关键差异（红叉/绿勾）

### 2. 统计动机图（Statistical Motivation）
用数据说明问题的普遍性和重要性。
- 饼图/柱状图：错误分布、类型占比
- 长尾分布图：展示数据不均衡

### 3. 概念对比图（Concept Comparison）
对比不同方法的思路差异。
- 并排流程图：Method A vs. Method B (Ours)
- 用颜色区分：灰色=旧方法，蓝色=新方法
- 关键创新点用星标或高亮框标注

### 4. Case Study 图
展示具体样例的输入-输出对比。
- 表格式：输入 | Baseline | Ours | Ground Truth
- 关键差异用颜色标注

## 设计原则

- **一图一个核心信息**：读者 3 秒内能 get 到 point
- **视觉引导**：用箭头、高亮、标注引导阅读顺序
- **对比鲜明**：好/坏、新/旧的视觉区分要足够大
- **自包含**：图 + caption 就能看懂，不依赖正文
- **颜色语义一致**：红=错误/问题，绿=正确/改进，蓝=我们的方法

## 配色方案
- 错误/问题：`#E74C3C`（红）+ 浅红背景 `#FDEDEC`
- 正确/改进：`#27AE60`（绿）+ 浅绿背景 `#EAFAF1`
- 我们的方法：`#3498DB`（蓝）+ 浅蓝背景 `#EBF5FB`
- 中性/背景：`#95A5A6`（灰）+ 浅灰背景 `#F2F3F4`
- 高亮标注：`#F39C12`（橙）

## 工作流程

1. 确认动机图类型和核心信息
2. 收集/构造展示数据或案例
3. 设计布局和视觉层次
4. 生成绘图脚本
5. 输出 PDF
6. 检查：是否 3 秒能看懂？对比是否鲜明？

## 输出
- 脚本: `figures/code/figures_motiv_{图名}.py`
- 图片: `figures/data/tmp/figures_motiv_{图名}.pdf`

$ARGUMENTS
