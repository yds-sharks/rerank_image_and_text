# 论文撰写 — 科研论文写作与绘图工作台

## 行为规范
完整规范见 `/mnt/workspace/yds/claude-code-guide/CLAUDE.md`，以下为本项目必须遵守的核心条目：

### 环境约束
- 内存 <4GB 时禁止启新进程；>2GB 文件流式读取
- 文件写 NAS `/mnt/workspace/yds/`，禁止往 `/tmp/` 存大文件

### 记忆制度
- 记忆存放：`memory/` 目录（本项目内）
- `memory/intent.md`：实时更新用户当前目标
- `memory/progress.md`：进度表（做了什么/结果/问题/下一步）
- `memory/skills/`：长期经验沉淀
- 错误记忆必须删除或覆盖，不保留错误信息
- 每天 18:00 提醒用户沉淀

### 项目访问规范
禁止主动访问本项目以外的内容。需要通用 skill 时 Read `/mnt/workspace/yds/通用skill/{skill名}/skill.md`。

### 代码三件套
所有脚本必带：时间统计 + 流式落盘（os.replace） + 断点续传（--resume）

### 数据生命周期
- `data/tmp/`：临时，可覆盖不可擅删
- `data/persistent/`：用户确认后移入，不可删除
- 结果文件绝不删除，用重命名区分版本

### 任务验证
完成后必须独立命令交叉验证（wc -l + ls -lh + 抽样）

### 工作风格
先看数据再写码 -> 10条验证 -> 本地开发推集群 -> 不冗余确认

---

## 项目定位
管理科研论文撰写全流程：收集整理设计思路、生成科研绘图、撰写 Overleaf 格式 LaTeX 论文。当前重点：搭建基础框架，配置绘图和写作 skill。

## 子模块

| 模块 | 职责 |
|------|------|
| design_docs | 存放和管理之前的设计思路文档 |
| figures | 科研绘图（matplotlib/tikz/pgfplots） |
| paper | LaTeX 论文撰写（Overleaf 兼容格式） |

## 文件命名
所有文件以子模块名为前缀：`{模块}_{序号}_{步骤}.ext`

## Skill 索引

### 绘图类
| Skill | 用途 |
|-------|------|
| /plot | 通用科研绘图 |
| /plot-nature | Nature/Science/IEEE 风格绘图（SciencePlots） |
| /plot-arch | 架构图/框架图/流程图 |
| /plot-motivation | 动机图/示例图/Case Study 图 |
| /figure-guide | 绘图审美指南与质量检查 |

### 写作类
| Skill | 用途 |
|-------|------|
| /outline | 论文框架梳理与大纲设计 |
| /write-section | 撰写论文章节 |
| /polish | 论文润色与学术表达优化 |
| /review-paper | 论文自审（模拟 Reviewer 视角） |

### 工具类
| Skill | 用途 |
|-------|------|
| /table | LaTeX 表格生成 |
| /bib | 参考文献管理 |
| /compile | 编译 LaTeX 并检查错误 |
| /tex-template | 会议/期刊模板切换（ACL/NeurIPS/AAAI 等） |
