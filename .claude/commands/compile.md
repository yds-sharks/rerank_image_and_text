# /compile — 编译 LaTeX 并检查错误

编译论文 LaTeX 项目，报告错误和警告。

## 工作流程

1. 进入 `paper/code/` 目录
2. 运行 `pdflatex main.tex`（两遍）
3. 运行 `bibtex main`（如有参考文献）
4. 再运行 `pdflatex main.tex`（两遍，解析交叉引用）
5. 检查 `.log` 文件中的 error / warning
6. 输出编译结果摘要

## 错误处理
- 解析 `.log` 文件，提取所有 error 和 warning
- 对常见错误给出修复建议
- 检查缺失的包、未定义的引用、图片路径错误

## 输出
- 编译后的 PDF: `paper/data/tmp/main.pdf`
- 错误报告：终端输出

$ARGUMENTS
