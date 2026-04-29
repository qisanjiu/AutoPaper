---
stage: S26
phase: P7
agent: writing
version: "1.0"
depends_on: [S25]
status: draft
---

# S26: Paper Outline

> Agent: `writing`
> Phase: P7
> 目标: 设计论文结构、图表计划、每段核心信息，确保符合目标 venue 的格式和页数限制

---

## 1. 核心目标

将 P1-P6 的所有研究成果转化为一份详细的论文写作蓝图。本阶段的核心任务是：
- **结构设计**: 按照 venue 模板要求和**领域惯例**（参考 S02 §7 论文框架惯例）规划 section 结构
- **页数预算**: 为每个 section 分配合理的页数
- **图表规划**: 确定所有图表的内容、类型和位置
- **信息分配**: 确保每段都有明确的"核心信息"
- **风格约定**: 确定全文统一的术语表、符号表、写作风格规范（作为 S27-S31 的约束）

> **结构设计不是凭空决定的**：必须参考 S02 §7 中从最相关论文提取的 section 结构惯例。
> 如果 S02 §7 尚未填写，必须先补齐再规划大纲。

---

## 2. 读取 Venue 配置

在开始写作前，必须读取项目 state 中的 venue 信息：

```bash
# 从 pipeline_state.yaml 读取 venue
cat state/pipeline_state.yaml | grep -A 10 "venue:"
```

或查看 `artifacts/latex_template/README.md` 了解模板使用方式。

关键信息：
- **Venue ID**: 如 `neurips`, `icml`, `iclr`, `acl`, `cvpr`, `ieee_trans`
- **页数限制**: 正文最大页数（references/appendix 通常不计入）
- **格式**: 单栏/双栏、纸张大小、字体大小
- **匿名要求**: 是否双盲（submission 时不可出现作者信息）
- **Style Package**: 如 `neurips_2025`, `icml2025`, `cvpr` 等

---

## 3. 领域框架对标（基于 S02 §7）

在确定具体 section 结构之前，必须先对照 S02 §7 中提取的领域惯例，回答以下问题：

### 3.1 参考论文的结构提取
从 S02 §7.1 中选取 3-5 篇最相关论文，列出其 section 结构：

| 论文 | Venue | Section 结构 |
|------|-------|-------------|
| ... | ... | ... |

### 3.2 框架决策
基于 S02 §7.2-7.4 的领域惯例，对以下关键问题做出明确决策：

| 决策 | 领域惯例（来自 S02 §7） | 我们的选择 | 理由 |
|------|----------------------|----------|------|
| Related Work 位置 | S02 §7.2 中总结的惯例 | intro 后 / 实验后 / 融入 intro | ... |
| 是否有 Problem Formulation / Preliminaries | S02 §7.3 中的特有 section | 是/否 | ... |
| Method section 命名 | S02 §7.2 中的命名惯例 | Method / Approach / Model | ... |
| 实验设置是否独立 | S02 §7.2 中的惯例 | 独立 / 并入 Experiments | ... |
| 是否有独立 Limitations | S02 §7.2 中的惯例 | 是 / 放在 Discussion 中 | ... |

### 3.3 我们的 Section 结构

基于上述对标，确定最终 section 结构：

```
1. Introduction                    (X 页) — 含/不含 Related Work 植入
2. [Preliminaries / Background]    (X 页) — 如 S02 §7 显示领域需要
3. [Method / Approach / Model]     (X 页)
4. [Experimental Setup]            (X 页) — 如独立
5. Experiments                     (X 页)
6. Discussion / Limitations        (X 页)
7. Conclusion                      (X 页)
[Related Work]                     (X 页) — 如后置
```

> **偏离说明**：如果我们的结构与 S02 §7 的领域惯例有差异，必须在 Reasoning Trail 中说明原因。

---

## 4. 页数预算分配

根据 venue 的页数限制，为每个 section 分配页数预算：

```markdown
| Section | 预算页数 | 说明 |
|---------|---------|------|
| Abstract | 0.25 | 150-250 words |
| Introduction | 1.0-1.5 | |
| Related Work | 0.5-1.0 | |
| Methodology | 2.0-3.0 | |
| Experiments | 2.0-3.0 | |
| Analysis/Discussion | 0.5-1.0 | |
| Conclusion | 0.25 | |
| **Total** | **≤ {page_limit}** | 不超过 venue 限制 |
```

**页数超出的应对策略**：
- 如果预估超出限制，优先压缩 Related Work 和 Discussion
- Methodology 和 Experiments 是核心，尽量保留完整
- 考虑将部分细节移到 Appendix

---

## 5. 写作风格与术语约定

在开始各 section 写作前，必须确定全文统一的写作规范，确保 S27-S31 风格一致：

### 4.1 术语表（强制）
| 术语 | 统一表述 | 缩写（如有） | 备注 |
|------|---------|------------|------|
| 方法名 | e.g., RadarHRNet | - | S06 中定义 |
| 数据集名 | e.g., Schellenberger et al. (2020) dataset | - | S07 中选定 |
| 核心指标 | e.g., Mean Absolute Error | MAE | 首次出现时定义 |
| ... | ... | ... | ... |

### 4.2 符号表（如有数学符号）
| 符号 | 含义 | 首次出现位置 |
|------|------|------------|
| $x$ | ... | §3.1 |
| $\theta$ | ... | §3.3 |

### 4.3 写作风格约定
- [ ] **时态约定**: Method → 现在时；Experiments → 过去时；Discussion → 混合（发现用过去时，解释用现在时）
- [ ] **人称约定**: 统一使用 "we"（不使用 "the authors"、"this paper" 作为主语）
- [ ] **Hedging 要求**: 所有结论性陈述使用适当 hedging（"suggest", "indicate", "provide evidence"），避免 "prove", "demonstrate conclusively"
- [ ] **禁止 bullet list**: 正文中只允许在贡献声明（Introduction 末尾）使用一次 numbered list，其他位置全部使用 prose 段落
- [ ] **禁止单句段落**: 除数学定义框后的短暂过渡外，所有段落 ≥ 2 句
- [ ] **引用格式**: 统一使用 `\cite{key}`（不用 `\citep`/`\citet`），多个引用用 `\cite{key1,key2}`
- [ ] **图表引用**: 使用 `Figure~\ref{fig:xxx}` 和 `Table~\ref{tab:xxx}`（含不可断空格 `~`）

---

## 6. 图表计划 (plotting_plan)

| Figure | 内容 | 类型 | 位置 | 引用段落 | 数据来源 |
|--------|------|------|------|---------|---------|
| Fig 1 | 方法架构图 | 架构图/流程图 | Method 开头 | Intro 末段 | S06 |
| Fig 2 | 主实验结果对比 | 柱状图/折线图 | Exp 主结果 | Abstract, Intro | S12 |
| Fig 3 | 消融实验结果 | 柱状图 | Exp 消融 | Exp 消融段落 | S16 |
| Fig 4 | 分析实验可视化 | 视内容而定 | Analysis | Analysis | S20 |
| Table 1 | 主实验结果表 | 数据表格 | Exp 主结果 | Abstract, Intro | S12 |
| Table 2 | 消融实验结果表 | 数据表格 | Exp 消融 | Exp 消融段落 | S16 |

**图表设计原则**:
- Colorblind-friendly（不使用红绿对比）
- 分辨率 ≥300 DPI 或矢量格式
- 每个图表有独立的可复现生成脚本

---

## 7. Section 详细规划

### 6.1 Abstract (150-250 words)
- 一句话概括
- 问题
- 方法
- 主要结果（具体数值）
- 贡献

### 6.2 Introduction (1.0-1.5 pages)
- 段落 1: 背景 + 广泛意义
- 段落 2: 现有工作进展 + 局限性（引用 2-3 篇关键工作）
- 段落 3: 我们的方法 + 核心洞察
- 段落 4: 主要贡献（bullet list，与 S24 一致）
- 段落 5: 论文结构概述

### 6.3 Related Work (0.5-1.0 pages)
- 子主题 A: ...（对应 S02 中的文献类别 X）
- 子主题 B: ...（对应 S02 中的文献类别 Y）
- 与我们的区别

### 6.4 Methodology (2.0-3.0 pages)
- 问题定义
- 方法概述（含 Fig 1 引用）
- 核心组件 A
- 核心组件 B
- 理论分析（如有）

### 6.5 Experiments (2.0-3.0 pages)
- 实验设置
- 主结果（含 Fig 2 / Table 1 引用）
- 消融实验（含 Fig 3 / Table 2 引用）
- 分析实验

### 6.6 Analysis & Discussion (0.5-1.0 pages)
- 关键发现解释
- 局限性诚实报告

### 6.7 Conclusion (0.25 page)
- 总结核心贡献
- 简短未来方向

---

## 8. Reasoning Trail

- **为什么选择这个 section 顺序？** ...
- **为什么在这个 venue 用这样的页数分配？** ...
- **每个图表为什么选择这种类型？** ...

---

## 9. 验证与检查

- [ ] Venue 配置已正确读取并确认
- [ ] **领域框架对标已完成**（参考 S02 §7 的 3-5 篇最相关论文结构，框架决策表已填写）
- [ ] Section 结构与领域惯例的偏离已在 Reasoning Trail 中说明
- [ ] 页数预算总和 ≤ venue 限制
- [ ] 图表计划完整，每个图/表都有数据支撑
- [ ] 每段都有明确的"核心信息"
- [ ] 格式要求（单/双栏、匿名等）已确认
- [ ] Section 结构与 venue 模板完全一致
- [ ] **术语表已建立**（核心术语统一表述 + 缩写定义）
- [ ] **风格约定已确定**（时态、人称、hedging、引用格式）

---

## 10. 风险与限制

| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|---------|------|
| 内容超出页数限制 | 需要大幅删减 | 在大纲阶段严格控制预算 | 开放 |
| 图表数据不足 | 计划无法执行 | 与 S12/S16 核对数据可用性 | 开放 |

---

## 11. 下游接口（传递给下游的关键信息）

1. `plotting_plan` → S32 (Figure Agent)
2. `section_plan` + `page_budget` → S27-S31 (各 section Writing)
3. `venue_style_info` → S33 (Full Draft Assembly)
4. 每段核心信息清单 → 确保 S27-S31 写作聚焦
5. **术语表 + 符号表 + 风格约定** → S27-S31（各 section 必须遵守统一的术语和风格）
6. **领域框架决策**（来自 §3，参考 S02 §7）→ S27-S31（section 结构、命名、内容组织遵循领域惯例）

---

## 12. 回溯触发器

- 如果 S33 编译后发现页数超出限制 → 回溯到 S26 重新调整大纲和内容分配
- 如果 venue 信息有误 → 回溯并修正 venue 配置
- 如果 S32 发现图表计划与数据不匹配 → 回溯到 S26 调整 plotting_plan
