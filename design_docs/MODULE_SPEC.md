# design_docs 模块规范

## 模块职责
存放和管理之前的设计思路、技术路线、实验方案等文档，为论文撰写提供素材。

## 目录结构

design_docs/
├── MODULE_SPEC.md
├── code/
├── config/
├── data/
│   ├── tmp/                 # 临时存储（可覆盖不可擅删）
│   └── persistent/          # 长期存储（用户确认后移入）
│       └── bad_cases/       # 特殊case记录
├── instructions/            # 沉淀的处理指令文档
└── notes/                   # 报错、踩坑、关键决策记录

## 文件命名

所有文件以 `design_docs_` 为前缀：
- 中间产物: `design_docs_{序号}_{步骤}.ext`
- 最终产出: `design_docs_{语义名}.ext`

## 数据生命周期

- tmp/ 中间产物不可擅自删除
- persistent/ 仅用户确认后移入
- bad_cases/ 记录典型错误（样本ID + 问题 + 原因 + 处理方式）

## 上下游关系
- 输入来源: 用户上传的原始设计文档
- 输出去向: paper 模块（论文写作参考素材）

## 关键注意事项
- 上传的文档保持原始格式，不做自动修改
- 整理后的文档与原始文档并存，不覆盖原始版本
