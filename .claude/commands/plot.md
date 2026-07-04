# /plot — 科研绘图

根据用户描述生成科研级别的图表。

## 输入
用户提供：图表类型、数据来源、样式要求

## 工作流程

1. 确认图表类型（折线图/柱状图/热力图/架构图/流程图等）
2. 确认数据来源（手动输入 / CSV / JSON / 实验日志）
3. 在 `figures/code/` 中生成绘图脚本
4. 执行脚本，输出 PDF 到 `figures/data/tmp/`
5. 用户确认后移入 `figures/data/persistent/`

## 绘图规范
- 默认输出 PDF 矢量格式
- 字体：serif（兼容 LaTeX）
- DPI：300（栅格图时）
- 配色：使用 config/ 中的调色板，默认 colorblind-friendly
- 图例、轴标签、标题均使用英文
- 字号：标题 14pt，轴标签 12pt，刻度 10pt

## 输出
- 脚本: `figures/code/figures_plot_{图名}.py`
- 图片: `figures/data/tmp/figures_{图名}.pdf`

$ARGUMENTS
