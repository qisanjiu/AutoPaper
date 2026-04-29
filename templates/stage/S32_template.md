---
stage: S32
phase: P7
agent: figure
version: "1.0"
depends_on: [S26, S06, S12, S16]
status: draft
---

# S32: Figure & Table Generation

> Agent: `figure`
> Phase: P7
> 目标: 生成论文所需的所有图表，确保清晰、准确、美观、符合 venue 规范

---

## 1. 核心目标

根据 S26 (Paper Outline) 的 `plotting_plan` 和实验数据，生成论文所需的全部图表。本阶段的核心任务是：
- **数据可视化**: 将实验结果转化为直观的图表
- **架构可视化**: 将方法设计转化为清晰的架构图
- **表格生成**: 将实验结果数据格式化为 LaTeX 表格

---

## 2. 图表清单与规划

### 2.1 必须生成的图表

参考 S26 (Paper Outline) 的 `plotting_plan` 和 S12/S16 的实验结果：

| 图表 ID | 内容 | 类型 | 数据来源 | 尺寸要求 |
|---------|------|------|---------|---------|
| Fig 1 | 方法架构图 | 架构图/流程图 | S06 | 单栏宽 |
| Fig 2 | 主实验结果对比 | 柱状图/折线图 | S12 | 单栏或双栏 |
| Fig 3 | 消融实验结果 | 柱状图 | S16 | 单栏 |
| Fig 4 | 分析实验可视化 | 视内容而定 | S20 | 视内容而定 |
| Table 1 | 主实验结果表 | 数据表格 | S12 | 单栏或双栏 |
| Table 2 | 消融实验结果表 | 数据表格 | S16 | 单栏 |

### 2.2 图表设计原则

- **清晰优先**: 图表应无需阅读正文即可传达核心信息
- **一致性**: 所有图表使用统一的配色、字体、线型
- **Colorblind-friendly**: 避免仅用颜色区分（使用线型、标记、纹理）
- **高分辨率**: ≥300 DPI（位图）或矢量格式（PDF/SVG）
- **标注完整**: 坐标轴标签、单位、图例、误差条（如适用）

---

## 3. 图表生成流程

### 3.1 数据提取

从实验结果中提取图表所需数据：
- 主实验结果: `experiments/results/main_results.csv` 或 S12 产出
- 消融结果: `experiments/results/ablation_results.csv` 或 S16 产出
- 分析实验结果: S20 产出

### 3.2 使用 Python/MATLAB 生成

推荐使用 Python (`matplotlib`/`seaborn`/`plotly`)：

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 设置全局样式
sns.set_context("paper")
sns.set_style("whitegrid")

# 示例：生成主实验对比图
fig, ax = plt.subplots(figsize=(6, 4))
# ... 绘图代码 ...
plt.savefig("figures/fig2_main_results.pdf", dpi=300, bbox_inches="tight")
```

### 3.3 LaTeX 表格生成

使用 `pandas` 生成 LaTeX 表格：

```python
import pandas as pd

df = pd.read_csv("experiments/results/main_results.csv")
latex_table = df.to_latex(
    index=False,
    float_format="%.3f",
    caption="Main experiment results",
    label="tab:main_results"
)
```

或使用 `booktabs` 风格的表格：

```latex
\begin{table}[t]
\centering
\caption{Main experiment results}
\label{tab:main_results}
\begin{tabular}{lccc}
\toprule
Method & Accuracy & Precision & Recall \\
\midrule
Baseline & 0.812 & 0.801 & 0.823 \\
Ours & \textbf{0.847} & \textbf{0.842} & \textbf{0.851} \\
\bottomrule
\end{tabular}
\end{table}
```

---

## 4. 验证与检查

- [ ] 所有图表与 S26 (Paper Outline) 的 `plotting_plan` 一致
- [ ] 数据与 S12/S16/S20 的原始数据一致（交叉验证）
- [ ] 图表清晰可读（字体大小 ≥8pt）
- [ ] Colorblind-friendly（不使用红绿对比）
- [ ] 分辨率 ≥300 DPI 或矢量格式
- [ ] 每个图表有独立的可复现生成脚本
- [ ] LaTeX 表格使用 `booktabs` 风格
- [ ] 表格数值与正文引用一致

---

## 5. 风险与限制

| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|---------|------|
| 数据与正文不一致 | 审稿人质疑可信度 | 交叉验证数值 | 开放 |
| 图表分辨率不足 | 印刷模糊 | 使用矢量格式或 ≥300 DPI | 开放 |
| 配色不符合 colorblind-friendly | 影响可读性 | 使用 Pattern/纹理辅助 | 开放 |

---

## 6. 下游接口（传递给下游的关键信息）

1. `figures/*.png` / `figures/*.pdf` → S33 (Full Draft Assembly)
2. `figures/*.py` (生成脚本) → 复现性保证
3. LaTeX 表格代码 → S33 (Full Draft Assembly)
4. 图表清单及对应数据文件路径

---

## 7. 回溯触发器

- 如果 S33 发现图表与正文描述矛盾 → 回溯到 S32 修正数据或图表
- 如果 S35 审稿人要求补充图表 → 回溯到 S32 生成新图表
- 如果 S33 编译时图表显示异常 → 检查格式和路径
