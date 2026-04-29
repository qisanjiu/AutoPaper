---
stage: S37
phase: P8
agent: writing
version: "1.0"
depends_on: [S36]
status: draft
---

# S37: Final Compilation

> Agent: `writing`
> Phase: P8

## 1. 核心目标
将经过 Phase 7 精修后的论文内容，编译为**最终投稿版本的 PDF**，确保完全符合 venue 规范。

## 2. 核心内容

### 2.1 读取作者信息

在最终编译前，必须读取作者信息配置文件：

```yaml
# {AutoPaper根目录}/config/author_info.yaml
# 示例结构（实际内容从配置文件读取，请勿编造）:
authors:
  - name: "[从 config/author_info.yaml 读取]"
    affiliation: "[机构名称]"
    email: "[通讯邮箱]"
    corresponding: true
```

**注意**：
- 最终版本（camera-ready）必须添加完整的作者信息
- 使用 `config/author_info.yaml` 中的内容，**不要编造或修改**
- IEEE Trans 等模板需要按特定格式排版作者区块，参考模板示例文件

### 2.2 最终编译流程

S37 负责执行标准的**多次编译**：

```bash
cd artifacts/

# Pass 1: 初次编译，生成 .aux
pdflatex -interaction=nonstopmode paper.tex

# Pass 2: BibTeX 处理参考文献
bibtex paper

# Pass 3: 解析交叉引用
pdflatex -interaction=nonstopmode paper.tex

# Pass 4: 最终化
pdflatex -interaction=nonstopmode paper.tex
```

或使用 `latexmk`（如果可用）：
```bash
latexmk -pdf -interaction=nonstopmode paper.tex
```

### 2.3 Venue 特定的最终调整

根据 venue 要求，在最终编译前可能需要调整：

| Venue | Camera-ready 调整 |
|-------|------------------|
| NeurIPS | `\usepackage[final]{neurips_2025}` + 从 `config/author_info.yaml` 添加作者信息 |
| ICML | `\usepackage[accepted]{icml2025}` + Impact Statement + 作者信息 |
| ICLR | `\iclrfinalcopy` + 从 `config/author_info.yaml` 添加作者信息 |
| ACL | `\usepackage{acl}` (移除 `review`) + 从 `config/author_info.yaml` 添加作者信息 |
| CVPR | `\usepackage{cvpr}` (移除 `review`) + 从 `config/author_info.yaml` 添加作者信息 |
| IEEE Trans | `\documentclass[journal]{IEEEtran}` + 从 `config/author_info.yaml` 添加完整作者信息 |

### 2.4 最终检查清单

- [ ] **编译通过**：无错误，警告已审查
- [ ] **页数合规**：在 venue 限制内
- [ ] **字体正确**：所有文字为 venue 要求的字体（Times 等）
- [ ] **参考文献完整**：bibtex 已正确处理，无缺失引用
- [ ] **图表清晰**：PDF 中所有图表可读
- [ ] **作者信息**：从 `config/author_info.yaml` 正确添加，无编造或修改
- [ ] **特殊要求**：
  - NeurIPS: checklist 已包含
  - ICML: impact statement 已添加
  - ACL: limitations section 已包含

### 2.5 使用 latex_sanity.py 验证

```bash
python3 utils/latex_sanity.py artifacts/paper.tex [max_pages]
```

## 3. Reasoning Trail
（记录关键决策的推理过程）

## 4. 验证与检查
- [ ] 多次编译成功，PDF 已生成
- [ ] 页数在限制内
- [ ] 无 orphan citation
- [ ] 所有图表在 PDF 中正确显示
- [ ] 符合 venue 的 camera-ready 要求

## 5. 风险与限制
- 风险: 最终编译报错 → 缓解: 保留 S32 的 draft.tex 作为备份
- 风险: camera-ready 格式调整遗漏 → 缓解: 对照 venue README 逐项检查

## 6. 下游接口（传递给下游的关键信息）
1. `artifacts/paper.pdf` → 作为最终产出和提交包核心
2. `artifacts/paper.tex` + `artifacts/refs.bib` + `artifacts/submission-package.zip` → 最终提交包

## 7. 回溯触发器
- 如果编译失败且无法修复 → 回溯到 S33 (Draft Assembly) 修复 LaTeX 结构问题
  - 如果是 S36 引入的格式错误 → 回溯到 S36 (Revision Loop)
- 如果页数超出限制 → 回溯到 S26 (Paper Outline) 重新规划页数预算
  - **注意**: 回溯到 S26 意味着需要重新执行完整写作链 (S27-S33, S36)，
    因为修改大纲会影响所有下游 section。这是 Major Revision 级别的回溯，
    符合全链路回溯原则。
- 如果参考文献缺失/错误 → 回溯到 S33 (Draft Assembly) 修正 .bib 集成
