# /plot-nature — Nature/Science/IEEE 风格科研绘图

使用 SciencePlots 库生成顶刊级别的科研图表。

## 输入
用户提供：图表类型、数据、目标期刊/会议风格

## 可用风格
- `science`: Science 期刊风格（默认）
- `nature`: Nature 风格
- `ieee`: IEEE 风格
- `science` + `no-latex`: 无 LaTeX 依赖版本
- 组合风格：`['science', 'bright']`, `['science', 'vibrant']`, `['science', 'high-vis']`

## 工作流程

1. 确认图表类型和目标风格
2. 生成 Python 脚本，使用 `plt.style.use()` 加载风格
3. 遵循以下绘图规范：
   - 单栏图宽度：3.3 inch (8.4cm)；双栏图：6.75 inch (17.1cm)
   - 字号：标签 8pt，刻度 7pt，图例 7pt
   - 线宽：0.75pt 数据线，0.5pt 辅助线
   - 颜色：使用 SciencePlots 内置 colorblind-safe 调色板
   - 边距紧凑：`plt.tight_layout()` 或 `bbox_inches='tight'`
4. 输出 PDF + PNG（300dpi 备用）
5. 用户确认后移入 persistent/

## 图表类型速查
- 折线图：训练曲线、消融实验对比
- 柱状图：模型性能对比、指标对比
- 热力图：混淆矩阵、注意力权重
- 散点图：嵌入可视化、相关性分析
- 箱线图：分布对比
- 雷达图：多维指标对比

## 代码模板

```python
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'no-latex'])  # 无 LaTeX 环境时用此行
# plt.style.use(['science', 'nature'])  # Nature 风格
# plt.style.use(['science', 'ieee'])    # IEEE 风格

fig, ax = plt.subplots(figsize=(3.3, 2.5))
# ... 绑定数据 ...
fig.savefig('output.pdf', dpi=300, bbox_inches='tight')
```

## 输出
- 脚本: `figures/code/figures_nature_{图名}.py`
- 图片: `figures/data/tmp/figures_{图名}.pdf`
- 备用: `figures/data/tmp/figures_{图名}.png`

$ARGUMENTS
