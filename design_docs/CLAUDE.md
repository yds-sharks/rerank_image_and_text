# design_docs — 设计思路文档管理

## 行为规范
完整规范见项目根目录 CLAUDE.md，以下为本模块关键约束：

- 代码三件套：时间统计 + 流式落盘 + 断点续传
- 数据：tmp/ 不可擅删，persistent/ 用户确认后移入
- 文件命名：`design_docs_` 前缀
- 任务完成后：wc -l + ls -lh + 抽样验证
- 记忆更新：进展记录到 `../memory/progress.md`

## 目录结构

design_docs/
├── CLAUDE.md
├── MODULE_SPEC.md
├── code/
├── config/
├── data/
│   ├── tmp/
│   └── persistent/
│       └── bad_cases/
├── instructions/
└── notes/

## 上下游
- 输入：用户上传的设计思路、实验方案文档
- 输出：整理后的思路文档 -> paper 模块引用
