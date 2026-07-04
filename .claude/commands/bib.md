# /bib — 参考文献管理

管理论文的参考文献库。

## 输入
用户提供：论文标题 / DOI / arXiv ID / BibTeX 条目

## 工作流程

1. 根据用户输入查找或格式化 BibTeX 条目
2. 检查 `paper/code/references.bib` 中是否已存在
3. 添加到 `references.bib`，按 cite key 字母排序
4. 检查论文 .tex 中的 `\cite{}` 引用是否都有对应条目
5. 报告未引用的条目和缺失引用的 cite key

## BibTeX 规范
- cite key 格式：`{第一作者姓}{年份}{标题首词}`，如 `vaswani2017attention`
- 必填字段：author, title, year, booktitle/journal
- 保持条目格式统一

## 输出
- 更新后的 `paper/code/references.bib`
- 引用完整性检查报告

$ARGUMENTS
