# 论文撰写

## 项目目标
管理科研论文的完整撰写流程，包括设计思路整理、科研绘图、LaTeX 论文写作。输出为 Overleaf 兼容的 LaTeX 项目。

## 子模块职责

| 模块 | 职责 | 主要产出 |
|------|------|---------|
| design_docs | 存放之前的设计思路、实验方案、技术路线文档 | 整理后的思路文档 |
| figures | 科研绘图，支持 matplotlib/tikz/pgfplots | .pdf/.png 图片文件 |
| paper | LaTeX 论文撰写，Overleaf 格式 | .tex 源文件 + 编译后 PDF |

## 数据流

```
design_docs (设计思路)
    |
    v
paper (论文撰写) <--- figures (绘图)
    |
    v
  最终 PDF
```

## 快速开始

1. 将设计思路文档放入 `design_docs/data/persistent/`
2. 使用 `/plot` skill 生成图表到 `figures/`
3. 使用 `/write-section` skill 撰写论文章节到 `paper/`
4. 使用 `/compile` skill 编译并检查
