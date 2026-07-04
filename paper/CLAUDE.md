# paper — LaTeX 论文撰写（Overleaf 格式）

## 行为规范
完整规范见项目根目录 CLAUDE.md，以下为本模块关键约束：

- 代码三件套：时间统计 + 流式落盘 + 断点续传
- 数据：tmp/ 不可擅删，persistent/ 用户确认后移入
- 文件命名：`paper_` 前缀
- 任务完成后：wc -l + ls -lh + 抽样验证
- 记忆更新：进展记录到 `../memory/progress.md`

## 目录结构

paper/
├── CLAUDE.md
├── MODULE_SPEC.md
├── code/                    # LaTeX 源文件 (.tex)
├── config/                  # 模板、cls、sty 文件
├── data/
│   ├── tmp/                 # 编译中间文件
│   └── persistent/          # 定稿 PDF
│       └── bad_cases/
├── instructions/            # 写作规范、期刊要求
└── notes/

## 上下游
- 输入：design_docs 的思路文档 + figures 的图表
- 输出：编译后的论文 PDF
