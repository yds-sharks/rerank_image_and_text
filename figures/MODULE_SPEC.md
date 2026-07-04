# figures 模块规范

## 模块职责
生成科研论文所需的所有图表，支持 matplotlib、tikz、pgfplots 等工具，输出 PDF/PNG 格式。

## 目录结构

figures/
├── MODULE_SPEC.md
├── code/                    # 绘图脚本
├── config/                  # matplotlib style / tikz 模板
├── data/
│   ├── tmp/                 # 草稿版本
│   └── persistent/          # 定稿版本
│       └── bad_cases/
├── instructions/            # 绘图规范
└── notes/

## 文件命名

所有文件以 `figures_` 为前缀：
- 绘图脚本: `figures_plot_{图名}.py`
- 输出图片: `figures_{图名}.pdf` / `figures_{图名}.png`
- tikz 源码: `figures_{图名}.tex`
- 样式配置: `figures_config_style.mplstyle`

## 数据生命周期

- tmp/ 中间产物不可擅自删除
- persistent/ 仅用户确认后移入
- bad_cases/ 记录典型错误

## 上下游关系
- 输入来源: 实验数据、design_docs 中的设计方案
- 输出去向: paper 模块（`\includegraphics` 引用）

## 关键注意事项
- 图片默认输出 PDF 矢量格式（期刊投稿质量）
- matplotlib 字体设置需兼容 LaTeX 渲染
- 配色方案统一，使用 config/ 中定义的调色板
