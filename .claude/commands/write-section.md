# /write-section — 撰写论文章节

根据设计思路和用户指导撰写论文的某个章节。

## 输入
用户提供：章节名称、写作要点、参考的设计思路文档

## 工作流程

1. 读取 `design_docs/data/persistent/` 中的相关设计文档
2. 读取已有章节（如有），保持风格一致
3. 在 `paper/code/sections/` 中生成/更新对应 .tex 文件
4. 确保 `main.tex` 中有对应的 `\input` 引用
5. 检查交叉引用（\ref, \cite）是否完整

## 写作规范
- 使用学术英文，语言简洁精确
- 段落结构：topic sentence + supporting evidence + transition
- 数学公式使用 `\equation` 或 `align` 环境
- 图表引用使用 `\ref{fig:xxx}` / `\ref{tab:xxx}`
- 文献引用使用 `\cite{key}`
- 不添加多余的注释或 TODO 标记

## Overleaf 兼容性
- 使用标准 LaTeX 包（amsmath, graphicx, booktabs 等）
- 路径使用相对路径
- 编码 UTF-8

## 输出
- 章节文件: `paper/code/sections/{section_name}.tex`

$ARGUMENTS
