---
stage: S33
phase: P7
agent: writing
version: "1.0"
depends_on: [S26, S27, S28, S29, S30, S31, S32]
status: draft
---

# S33: Full Draft Assembly

> Agent: `writing`
> Phase: P7
> 目标: 整合 S26-S31 的各 section 和 S32 的图表，生成完整 LaTeX 草稿

---

## 1. 核心目标

将已完成的各 section（S27-S31）和图表（S32）整合为一份完整的、可编译的 LaTeX 论文草稿。本阶段的核心任务是：
- **整合一致性**: 确保全文术语、风格、引用一致
- **LaTeX 编译**: 生成可编译的 `.tex` 文件
- **图表插入**: 正确引用所有图表
- **引用完整性**: 通过 orphan cite gate 检查

---

## 2. 整合输入

| 输入 | 来源 | 状态要求 |
|------|------|---------|
| Paper Outline | S26 | 已完成 |
| Intro & Related Work | S27 | 已完成 |
| Methodology | S28 | 已完成 |
| Experiments & Results | S29 | 已完成 |
| Analysis & Discussion | S30 | 已完成 |
| Abstract & Conclusion | S31 | 已完成 |
| Figures & Tables | S32 | 已完成 |
| refs.bib | S02/S27 | 已更新 |

---

## 3. 整合流程

### 3.1 准备 LaTeX 源文件

使用 venue 模板：
```latex
\documentclass{article}
\usepackage{neurips_2025}  % 使用 artifacts/latex_template/ 中的 .sty
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx,booktabs}
\bibliographystyle{unsrtnat}
```

### 3.2 Section 整合

- **保留 S27-S31 的文本 verbatim**（除非明显的术语不一致）
- **插入图表**: 使用 `\ref{fig:xxx}` / `\ref{tab:xxx}` 引用，由 LaTeX 自动编号
- **统一术语**: 全文搜索核心术语（如方法名、数据集名、指标名），确认仅使用一种表述
- **统一符号**: 检查数学符号是否在全文一致（如 $\mathcal{L}$ 不会在某处变成 $L$）
- **检查过渡**: section 之间的过渡是否自然
- **风格一致性**: 检查各 section 之间是否存在风格断裂（如某 section 使用了 bullet list 而其他没有，某 section 有 contractions 而其他没有）

### 3.3 跨 Section 风格检查清单

整合完成后逐项检查：
- [ ] 核心术语 ≥2 处出现时表述完全一致（如 "LOSO-CV" vs "leave-one-subject-out cross-validation" — 首次定义后统一使用缩写）
- [ ] 数学符号全文一致（如 $\theta$ 不在某处变成 $\Theta$）
- [ ] 时态一致：Method 使用现在时，Experiments 使用过去时，Discussion 混合使用
- [ ] 无任何 section 残留 bullet list 正文（贡献声明除外）
- [ ] 无任何 section 出现博客式问句标题
- [ ] Contractions 全文清零
- [ ] 引用风格一致（全部使用 \cite{key}，无 \citep{} / \citet{} 混用）

### 3.4 编译流程

```bash
cd artifacts/

# Pass 1: 初次编译，生成 .aux
pdflatex -interaction=nonstopmode draft.tex

# Pass 2: BibTeX 处理参考文献
bibtex draft

# Pass 3-4: 解析交叉引用
pdflatex -interaction=nonstopmode draft.tex
pdflatex -interaction=nonstopmode draft.tex
```

或使用: `python3 utils/latex_sanity.py artifacts/draft.tex`

---

## 4. 自动检查

### 4.1 Orphan Cite Gate
- [ ] 每个 `\cite{KEY}` 都存在于 `refs.bib`
- [ ] 每个 `\ref{fig:xxx}` / `\ref{tab:xxx}` 都有对应的 `\label`

### 4.2 Anti-Leakage Check
- [ ] 无作者名/机构/邮箱（如 venue 要求匿名）
- [ ] 无已知论文的原文复制

### 4.3 页数检查
- [ ] 总页数 ≤ venue 限制
- [ ] 各 section 长度符合 S26 预算

### 4.4 术语一致性
- [ ] 核心术语全文一致
- [ ] 符号定义不重复且不冲突

---

## 5. 已知问题与改动记录

| 问题 | 严重程度 | 解决方案 | 状态 |
|------|---------|---------|------|
| ... | 高/中/低 | ... | 已修复/待修复 |

---

## 6. Reasoning Trail

- **整合时发现了哪些不一致？** ...
- **哪些 section 需要微调以改善连贯性？** ...
- **编译遇到了哪些问题？** ...

---

## 7. 验证与检查

### 7.1 编译硬性关卡（必须先通过，否则 Stage 不完成）

```bash
cd artifacts/
# 必须连续 4 次编译全部通过
pdflatex -interaction=nonstopmode draft.tex   # Pass 1: 生成 .aux
bibtex draft                                    # Pass 2: 处理参考文献
pdflatex -interaction=nonstopmode draft.tex   # Pass 3: 解析引用
pdflatex -interaction=nonstopmode draft.tex   # Pass 4: 稳定交叉引用
```

**判定标准**：
- [ ] 4 次编译全部 exit code = 0（无错误；warning 可接受但需记录）
- [ ] 最终 PDF 中无 `??` 占位符（表示未解析的引用）
- [ ] 如编译失败，必须修复后重新编译，**不得跳过**
- [ ] 编译通过后运行 `python utils/latex_sanity.py artifacts/draft.tex` 二次确认

### 7.2 内容与格式检查

- [ ] 使用了正确的 venue 模板文件（`artifacts/latex_template/` 下的 .sty/.cls）
- [ ] 无孤儿引用（orphan cite gate pass — `python utils/orphan_cite_gate.py`）
- [ ] 页数在 venue 限制内
- [ ] 双盲要求满足（如 venue 要求匿名）
- [ ] 所有图表正确插入并引用（`\ref` 全部解析）
- [ ] Anti-Leakage Check 通过
- [ ] 术语一致性检查通过
- [ ] **学术风格检查通过**：无 §5.6.1 禁止表达、无 contractions、无博客式标题、无 bullet list 正文

---

## 8. 风险与限制

| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|---------|------|
| LaTeX 编译错误 | 无法生成 PDF | 保留各 section 备份，分步调试 | 开放 |
| 术语不一致 | 读者困惑 | 全文搜索核心术语 | 开放 |
| 图表引用断裂 | 编译警告 | 检查所有 \ref 和 \label | 开放 |

---

## 9. 下游接口（传递给下游的关键信息）

1. `artifacts/draft.tex` + `artifacts/draft.pdf` → S34 (Internal Review)
2. 编译日志和问题清单 → S34/S35
3. 已知问题列表 → S36 (Revision Loop)

---

## 10. 回溯触发器

- 如果编译失败无法修复 → 回溯到对应 section（S27-S31）修正
- 如果页数严重超出 → 回溯到 S26 调整大纲
- 如果术语不一致严重 → 回溯到对应 section 统一
