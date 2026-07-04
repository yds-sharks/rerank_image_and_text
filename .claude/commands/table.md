# /table — LaTeX 表格生成

根据数据生成高质量 LaTeX 表格代码。

## 输入
用户提供：数据（JSON/CSV/手动描述）、表格类型、目标位置

## 表格类型

### 1. 主结果表（Main Results）
- 粗体标注最佳结果
- 下划线标注次佳结果
- 最后一行为 "Ours" 方法

### 2. 消融实验表（Ablation Study）
- 基线行 + 各变体行
- 用 ✓/✗ 标注模块开关
- 性能变化标注 ↑/↓

### 3. 超参数表（Hyperparameter）
- 两列：Parameter | Value
- 按逻辑分组

### 4. 数据集统计表（Dataset Statistics）
- 列：Dataset | #Train | #Dev | #Test | #Classes 等

## 表格规范

### 格式要求
- 使用 `booktabs` 包（`\toprule` `\midrule` `\bottomrule`）
- 禁止使用竖线 `|`
- 数字右对齐，文字左对齐
- 小数统一精度（如全部保留 2 位）
- 百分比统一格式（89.2 而非 0.892）

### 最佳/次佳标注
```latex
\newcommand{\best}[1]{\textbf{#1}}
\newcommand{\second}[1]{\underline{#1}}
```

### 表格大小
- 单栏：`\begin{table}[t]`
- 双栏：`\begin{table*}[t]`
- 表格过宽：`\resizebox{\columnwidth}{!}{...}` 或 `\small`

## 代码模板

```latex
\begin{table}[t]
\centering
\caption{Main experimental results on XXX dataset.}
\label{tab:main_results}
\small
\begin{tabular}{lcccc}
\toprule
\textbf{Model} & \textbf{Precision} & \textbf{Recall} & \textbf{F1} & \textbf{Acc.} \\
\midrule
Baseline 1 & 85.2 & 83.1 & 84.1 & 86.3 \\
Baseline 2 & 86.7 & 84.5 & 85.6 & 87.1 \\
\midrule
\textbf{Ours} & \best{89.3} & \best{87.8} & \best{88.5} & \best{90.2} \\
\bottomrule
\end{tabular}
\end{table}
```

## 工作流程

1. 确认数据和表格类型
2. 生成 LaTeX 表格代码
3. 写入对应章节的 .tex 文件或独立文件
4. 确保 `main.tex` 能正确引用

## 输出
- 表格代码插入到指定 .tex 文件
- 终端输出表格预览

$ARGUMENTS
