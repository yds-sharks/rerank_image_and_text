# /polish — 论文润色与学术表达优化

对论文章节进行语言润色、语法修正、学术表达升级。

## 输入
用户提供：要润色的章节名 或 具体段落

## 润色维度

### 1. 语法与拼写
- 主谓一致、时态统一（方法描述用现在时，实验用过去时）
- 冠词（a/an/the）修正
- 介词搭配

### 2. 学术表达升级
常见替换规则：
| 口语化 | 学术化 |
|--------|--------|
| a lot of | numerous / substantial |
| get better | improve / enhance |
| show | demonstrate / illustrate / indicate |
| use | employ / leverage / utilize |
| big | significant / substantial |
| problem | challenge / limitation |
| way | approach / methodology |
| part | component / module |
| good | effective / robust / superior |
| bad | suboptimal / inferior |

### 3. 句式优化
- 避免过长复合句（>35 词拆分）
- 避免连续短句（合并为复合句）
- 被动/主动语态平衡（方法描述可用 "we"）
- 避免口语化连接词（So → Therefore, But → However）
- 段落首句必须是 topic sentence

### 4. 逻辑连贯
- 段落间添加过渡句
- 因果关系明确标注（therefore, consequently, as a result）
- 对比关系清晰（in contrast, whereas, unlike）
- 递进关系（furthermore, moreover, additionally）

### 5. 简洁性
- 删除冗余表达（"it is worth noting that" → 直接说）
- 删除弱化语气词（"quite", "rather", "somewhat"）
- 避免重复表述同一概念

## 工作流程

1. 读取目标章节 .tex 文件
2. 逐段分析，标注问题
3. 生成润色后版本，用 `\textcolor{blue}{新内容}` 标注修改处
4. 输出修改摘要（改了什么、为什么）
5. 用户确认后更新文件

## 输出
- 润色后的 .tex 文件覆盖原文件
- 终端输出修改摘要

$ARGUMENTS
