# paper 模块规范

## 模块职责
撰写 LaTeX 论文，采用 Overleaf 兼容格式，支持多章节分文件管理。

## 目录结构

paper/
├── MODULE_SPEC.md
├── code/                    # LaTeX 源文件
│   ├── main.tex             # 主文件
│   ├── sections/            # 各章节 .tex
│   ├── figures/             # 图片引用（软链接或复制自 ../figures/）
│   └── references.bib       # 参考文献
├── config/                  # 模板文件 (.cls, .sty, .bst)
├── data/
│   ├── tmp/                 # 编译产物
│   └── persistent/          # 定稿 PDF
│       └── bad_cases/
├── instructions/            # 期刊投稿要求、格式规范
└── notes/

## 文件命名

LaTeX 源文件命名：
- 主文件: `main.tex`
- 章节: `sections/{section_name}.tex`（如 `sections/introduction.tex`）
- 参考文献: `references.bib`
- 其他产出以 `paper_` 为前缀

## 数据生命周期

- tmp/ 中间产物不可擅自删除
- persistent/ 仅用户确认后移入
- bad_cases/ 记录典型错误

## 上下游关系
- 输入来源: design_docs（思路文档）、figures（图表）
- 输出去向: 最终论文 PDF

## LaTeX 项目结构（Overleaf 兼容）

```
code/
├── main.tex                 # \documentclass + \input{sections/...}
├── sections/
│   ├── abstract.tex
│   ├── introduction.tex
│   ├── related_work.tex
│   ├── method.tex
│   ├── experiments.tex
│   ├── results.tex
│   ├── conclusion.tex
│   └── appendix.tex
├── figures/                 # 论文引用的图片
├── tables/                  # 表格文件（可选）
└── references.bib
```

## 关键注意事项
- 保持 Overleaf 兼容：不使用本地特有的包或路径
- 章节分文件管理，main.tex 只做 \input 组装
- 参考文献统一用 BibTeX 管理
