# figures — 科研绘图

## 行为规范
完整规范见项目根目录 CLAUDE.md，以下为本模块关键约束：

- 代码三件套：时间统计 + 流式落盘 + 断点续传
- 数据：tmp/ 不可擅删，persistent/ 用户确认后移入
- 文件命名：`figures_` 前缀
- 任务完成后：wc -l + ls -lh + 抽样验证
- 记忆更新：进展记录到 `../memory/progress.md`

## 目录结构

figures/
├── CLAUDE.md
├── MODULE_SPEC.md
├── code/                    # 绘图脚本
├── config/                  # 绘图样式配置
├── data/
│   ├── tmp/                 # 草稿图
│   └── persistent/          # 定稿图
│       └── bad_cases/
├── instructions/            # 绘图规范说明
└── notes/

## 上下游
- 输入：实验数据、design_docs 中的设计方案
- 输出：.pdf/.png 图片 -> paper 模块引用
