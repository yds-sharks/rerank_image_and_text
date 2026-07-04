# /tex-template — 会议/期刊模板切换

切换论文的 LaTeX 模板以适配不同会议或期刊的投稿要求。

## 输入
用户提供：目标会议/期刊名称

## 支持的模板

### NLP/AI 会议
| 会议 | 模板包 | 页数限制 | 特殊要求 |
|------|--------|---------|---------|
| ACL/EMNLP/NAACL | `acl2024.sty` | 正文 8 页 | Limitation 章节必选 |
| AAAI | `aaai25.sty` | 正文 7+1 页 | 禁止 \vspace 调页 |
| NeurIPS | `neurips_2024.sty` | 正文 9 页 | 匿名审稿 |
| ICML | `icml2024.sty` | 正文 9 页 | 双栏 |
| ICLR | OpenReview 格式 | 无严格限制 | 匿名审稿 |
| COLING | `coling2025.sty` | 正文 8 页 | 类 ACL |
| SIGIR | `sigconf` | 正文 9 页 | ACM 格式 |

### 期刊
| 期刊 | 模板 | 特殊要求 |
|------|------|---------|
| TACL | ACL 格式 | 正文无严格页数限制 |
| JMLR | `jmlr.sty` | 单栏 |
| Nature | `nature.cls` | 极度简洁 |
| IEEE TPAMI | `ieeejournal` | 双栏 |

## 工作流程

1. 确认目标会议/期刊
2. 下载/配置对应模板文件到 `paper/config/`
3. 修改 `main.tex` 的 `\documentclass` 和包引用
4. 调整章节结构适配模板要求：
   - 添加/删除必需章节（如 Ethics Statement, Limitation）
   - 调整页数预算
   - 处理匿名化要求（删除作者信息、自引匿名化）
5. 编译检查

## 匿名化检查清单
- [ ] 作者信息替换为 Anonymous
- [ ] 自引改为 "Author (2024)" → "Anonymous (2024)"
- [ ] 删除致谢章节
- [ ] 代码/数据链接匿名化（Anonymous GitHub）
- [ ] 删除页眉页脚中的身份信息

## 输出
- 更新后的 `paper/code/main.tex`
- 模板文件: `paper/config/{template_name}/`
- 终端输出切换摘要和注意事项

$ARGUMENTS
