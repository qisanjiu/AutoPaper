# Stage 详细设计

> **原则**: 37 个 Stage，每个都是原子性的，有明确的输入、输出、质量标准和负责 Agent

---

## 1. Stage 总览

```
Phase 1: Discovery (发现)
├── S01: Topic Analysis          [Literature]  → S01_topic_analysis.md
├── S02: Literature Survey       [Literature]  → S02_literature_survey.md
├── S03: Research Question       [Ideation]    → S03_research_question.md
├── S04: Hypothesis Generation   [Ideation]    → S04_hypothesis_generation.md
├── S05: Novelty & Feasibility   [Ideation]    → S05_novelty_feasibility.md
└── Gate G1 [Stage Insp S01-S05 + Logic + Novelty] ───►

Phase 2: Design (设计)
├── S06: Methodology Design      [Method]      → S06_methodology_design.md
│   └── Subagent feasibility check required
├── S07: Benchmark Selection     [Method]      → S07_benchmark_selection.md
│   └── Subagent feasibility check required (dataset info collection)
├── S08: Experiment Protocol     [Method]      → S08_experiment_protocol.md
├── S09: Baseline Selection      [Method]      → S09_baseline_selection.md
│   └── Subagent feasibility check required (must not conflict with ablation)
├── S10: Full Experiment Plan    [Method]      → S10_full_experiment_plan.md
│   └── Covers method + baselines
└── Gate G2 [Stage Insp S06-S10 + Logic + Method + Novelty] ──►

Phase 3: Execution (执行)
├── S11: Code Generation         [Experiment]  → S11_code_generation.md
│   └── Implement method + baselines
├── S12: Experiment Execution, Result Collection & Preliminary Analysis
│   └── [Experiment]  → S12_experiment_iteration.md
│   └── Inner Loop: modify → git commit → run → record → analyze
│   └── S12 不做决策，所有尝试 git commit 保存
├── S13: Experiment Result Verification
│   └── [Analysis]  → S13_result_verification.md
│   └── Phase 3 唯一决策点：KEEP / FIX→S12 / BACKTRACK→S11 / S06 / S08 / S07 / S09 / S04
└── Gate G3 [Stage Insp S11-S13 + Method + Evidence] ──►

Phase 4: Ablation (消融)
├── S14: Ablation Design         [Experiment]  → S14_ablation_design.md
│   └── Subagent review required (validate module effectiveness)
├── S15: Ablation Code Generation [Experiment] → S15_ablation_code.md
├── S16: Ablation Execution      [Experiment]  → S16_ablation_execution.md
│   └── If errors occur, backtrack to S15 or S14
├── S17: Ablation Result Analysis [Analysis]   → S17_ablation_analysis.md
└── Gate G4 [Stage Insp S14-S17 + Method + Evidence] ──►

Phase 5: Further Analysis (进一步分析)
├── S18: Other Findings          [Analysis]    → S18_other_findings.md
│   └── Discover experimental phenomena from P3+P4 results
├── S19: Analysis Experiment Design [Analysis] → S19_analysis_experiment_design.md
│   └── Subagent feasibility check required (visualization, etc.)
├── S20: Analysis Experiment Implementation [Experiment] → S20_analysis_experiment.md
├── S21: Analysis Result Collection & Analysis [Analysis] → S21_analysis_results.md
│   └── Review required; backtrack if necessary
└── Gate G5 [Stage Insp S18-S21 + Logic + Evidence + Novelty] ──►

Phase 6: Synthesis (合成)
├── S22: Claim-Evidence Map      [Analysis]    → S22_claim_evidence_map.md
├── S23: Finding Synthesis       [Analysis]    → S23_finding_synthesis.md
├── S24: Contribution Articulation [Writing]   → S24_contribution_articulation.md
├── S25: Future Work             [Ideation]    → S25_future_work.md
└── Gate G6 [Stage Insp S22-S25 + Logic + Evidence + Novelty] ──►

Phase 7: Writing (写作)
├── S26: Paper Outline           [Writing]     → S26_paper_outline.md
├── S27: Introduction & Related Work [Writing] → S27_introduction_relatedwork.md
├── S28: Methodology Section     [Writing]     → S28_methodology_section.md
├── S29: Experiments & Results   [Writing]     → S29_experiments_results.md
├── S30: Analysis & Discussion   [Writing]     → S30_analysis_discussion.md
├── S31: Abstract & Conclusion   [Writing]     → S31_abstract_conclusion.md
├── S32: Figure & Table Generation [Figure]    → S32_figure_table_generation.md
├── S33: Full Draft Assembly     [Writing]     → S33_full_draft.md
└── Gate G7 [Stage Insp S26-S33 + Logic + Writing + Evidence] ──►

Phase 8: Refinement & Compilation (精炼与编译)
├── S34: Internal Review         [Critic Team x5] → S34_internal_review.md
├── S35: Peer Review Simulation  [Review]      → S35_peer_review_simulation.md
├── S36: Revision Loop           [Writing + Review] → S36_revision_loop.md
│   └── 每轮包含：修改 → 编译检查 → Orphan Cite / Anti-Leakage / Ethics
│   └── 停止条件：评分 ≥ 7/10 且所有检查通过
├── S37: Final Compilation       [Writing]     → S37_final_compilation.md
│   └── Camera-ready 调整 → 多次编译 → paper.pdf + 提交包 zip
└── Gate G8 [Stage Insp S34-S36-S37 + Writing + Novelty + Ethics + Conductor Insp] ──►
```

---

## 2. Gate 与 Critic 调用策略

每个 Gate 调用一组专业 Critic，并行审查，然后聚合结果。

### Gate 调用表

| Gate | Phase | 调用的 Critic | 审查重点 | 通过标准 |
|------|-------|--------------|---------|---------|
| **G1** | Discovery | Logic, Novelty | 问题清晰、逻辑连贯、想法新颖 | 问题定义明确；3+ Gap；有可行性分析 |
| **G2** | Design | Logic, Method, Novelty | 方法严谨、能验证假设、baseline公平、新颖 | 方法能回答假设；实验可验证；baseline 合理；subagent检验通过 |
| **G3** | Execution | Method, Evidence | 代码正确、结果可靠、可复现、迭代收敛 | 代码可运行；结果可复现；无重大 bug；AutoResearch决策合理 |
| **G4** | Ablation | Method, Evidence | 消融设计完整、执行正确、分析到位 | 每个核心组件有消融；结果完整；统计显著 |
| **G5** | Further Analysis | Logic, Evidence, Novelty | 分析实验有意义、现象发现深刻 | 分析有深度；能突出方法优势；与P3/P4结果一致 |
| **G6** | Synthesis | Logic, Evidence, Novelty | Claim-Evidence映射清晰、洞察深刻、贡献准确 | 所有claim有证据；无夸大；贡献清晰 |
| **G7** | Draft | Logic, Writing, Evidence | 结构合理、论证完整、数据一致、写作规范 | 符合 venue；所有 claim 有证据；图表清晰 |
| **G8** | Final | Writing, Novelty, Ethics, Conductor Inspector | 投稿质量、无伦理问题、新颖性确认、编排决策审查 | Review score ≥ 6/10；无 Critical；伦理合规 |

### Critic 审查文档产出

每个 Critic 产出独立的审查报告：

```
knowledge/reviews/
├── G1_logic_review.md
├── G1_novelty_review.md
├── G2_logic_review.md
├── G2_method_review.md
├── G2_novelty_review.md
├── ...
└── G8_ethics_review.md
```

Conductor 读取所有审查报告后聚合决策。

---

## 3. Stage 设计原则

### 3.1 原子性
每个 Stage 不可再分。如果一个任务可以拆成两个独立的子任务，它就应该是两个 Stage。

### 3.2 明确边界
每个 Stage 有明确的：
- **输入**：来自哪些上游 Stage 的产出（遵循 MD 接收规范）
- **输出**：产出的文档路径和格式（遵循 MD 产出规范）
- **质量标准**：什么样的产出算"完成"
- **负责 Agent**：哪个 Agent 执行

### 3.3 可回溯性
每个 Stage 的产出都保存在 `knowledge/` 目录中，带有时间戳版本。回溯时可以精确恢复到任意 Stage 的状态。

### 3.4 可并行性
没有依赖关系的 Stage 可以并行执行（由 Conductor 判断）。

---

## 4. 各 Stage 详细说明

### Phase 1: Discovery

#### S01: Topic Analysis
- **目标**: 定义研究主题的范围，从多个角度收集信息，绘制领域地图
- **输入**: 用户提供的 topic
- **输出**: `S01_topic_analysis.md`
- **Agent**: Literature
- **审查**: Stage Inspector S01（内容 + MD 格式）
- **质量标准**: 主题定义清晰；领域地图完整；关键词列表可用；符合 Universal Document Schema
- **预估时间**: 15-30 分钟
- **可回溯原因**: 主题定义错误、范围过宽/过窄

#### S02: Literature Survey
- **目标**: 系统调研文献，识别研究空白（宏观 Gap + 细粒度 μGap），同时了解现有工作的数据集、评价指标、实验设置等实验细节
- **输入**: S01（按 MD 接收规范解析）
- **输出**: `S02_literature_survey.md` + `knowledge/refs.bib`
- **Agent**: Literature
- **质量标准**: 20+ 篇核心文献；3+ 个明确 Gap；**建立了方法论/技术方案库（含可解决 Gap 的具体方法/架构/模块）**；分类清晰；**必须从论文研究过程中发现细粒度的方法内在空白（μGap），而非仅从场景创新角度识别空白**；**记录现有工作的数据集、指标、实验细节**；**标注每篇核心论文的代码可用性（开源且有维护 / 开源但不可运行 / 未开源）和许可证，供 S09 baseline 选择时降权参考**
- **预估时间**: 30-60 分钟
- **可回溯原因**: 遗漏关键文献、Gap 识别错误、方案库不完整（无可用方法解决 Gap）
- **⚠️ 关键流程规范**: 若 S02 发生 major revision，遵循 `docs/06_FEEDBACK_LOOP.md` §4.1.1 的通用回溯规则，触发 S03-S05 回溯更新

#### S03: Research Question
- **目标**: 将 Gap 转化为具体的研究问题，找到当前工作存在的问题或未涉足的地方（细节问题或大场景问题）
- **输入**: S01, S02（解析 Gap 表格和趋势分析）
- **输出**: `S03_research_question.md`
- **Agent**: Ideation
- **质量标准**: FINER 标准；问题可分解；范围明确
- **预估时间**: 15-30 分钟

#### S04: Hypothesis Generation
- **目标**: 构建可检验的假设，建立从问题到假设的映射
- **输入**: S02, S03（解析 Gap-问题对应关系）
- **输出**: `S04_hypothesis_generation.md`
- **Agent**: Ideation
- **质量标准**: 每个假设有可测量预测；考虑零假设
- **预估时间**: 20-40 分钟
- **可回溯原因**: 假设不可证伪、与文献矛盾

#### S05: Novelty & Feasibility
- **目标**: 评估想法的新颖性和可行性
- **输入**: S03, S04（解析假设和预测）
- **输出**: `S05_novelty_feasibility.md`
- **Agent**: Ideation
- **Critic 审查**: 是（S05 完成后自动进入 G1）
- **质量标准**: 有具体文献对比；风险评估诚实
- **预估时间**: 15-30 分钟

---

### Phase 2: Design

#### S06: Methodology Design
- **目标**: 设计严谨的研究方法，设计完成后创建 subagent 检验是否可行，且需和 P1 内容对应
- **输入**: handoff_P1_P2, S03-S05（解析核心假设和约束）
- **输出**: `S06_methodology_design.md`
- **Agent**: Method
- **质量标准**: 方法能回答问题；有形式化描述；设计决策记录；**subagent 检验通过**
- **预估时间**: 30-60 分钟
- **可回溯原因**: 方法无法验证假设、方法存在理论缺陷、subagent 检验不通过

#### S07: Benchmark Selection
- **目标**: 选择合适的数据集和 benchmark，创建 subagent 检验可行性。首先需要收集数据集信息，了解输入输出，是否适配本任务和本模型。注意和 S02 关联，因为 S02 说明了现有方法的数据集
- **输入**: S06（解析方法需求和假设场景），S02（现有工作的数据集信息）
- **输出**: `S07_benchmark_selection.md`
- **Agent**: Method
- **质量标准**: 数据集领域标准；预处理清晰；许可证合规；**数据集与任务/模型适配性分析完整**；**subagent 检验通过**
- **预估时间**: 15-30 分钟

#### S08: Experiment Protocol
- **目标**: 设计详细的实验协议
- **输入**: S06, S07（解析方法组件和数据集特性）
- **输出**: `S08_experiment_protocol.md`
- **Agent**: Method
- **质量标准**: 每个实验有明确目标；超参数固定；可复现清单
- **预估时间**: 20-40 分钟

#### S09: Baseline Selection
- **目标**: 选择公平的 baseline。需要和 S02 关联，从 S02 找到相关任务进行选择。评估所选的 baseline 是否有意义，是否符合数据集和评价指标。不仅是相关工作作为 baseline，也可以是其他角度的变体，用于验证方法提出的有效性。注意不要和消融产生冲突。最后用 subagent 检查可行性。**参考 S02 的代码可用性标注：对未开源或代码不可运行的 baseline 降权，优先选择有可运行公开代码的方法。**
- **输入**: S08（解析实验设计），S02（现有工作、baseline 信息、**代码可用性标注**）
- **输出**: `S09_baseline_selection.md`
- **Agent**: Method
- **质量标准**: baseline 覆盖主要竞争方法；公平性保证；**与消融设计无冲突**；**subagent 检验通过**
- **预估时间**: 15-30 分钟

#### S10: Full Experiment Plan
- **目标**: 整合方法和 baseline 的实验计划（执行顺序、资源预算、主实验成功/失败标准）。注意：消融实验的具体设计（组件选择、变量隔离、预期效果）在 P4 S14 完成，S10 仅做调度层面的预留
- **输入**: S06-S09（解析所有设计决策）
- **输出**: `S10_full_experiment_plan.md`
- **Agent**: Method
- **Critic 审查**: 是（G2: Logic + Method + Novelty）
- **质量标准**: 执行顺序清晰；主实验成功/失败标准明确；风险评估；覆盖 method + baselines；消融部分限于调度预留，不预设具体设计
- **预估时间**: 15-30 分钟

---

### Phase 3: Execution

#### S11: Code Generation
- **目标**: 实现方法和 baseline 的代码。**Baseline 实现必须记录来源**（官方代码精确 commit / 自行实现参考论文章节），并在 S12 中与原论文报告值做一致性验证
- **输入**: handoff_P2_P3, S06-S10, **S02**（解析方法设计、协议、文献中的方法实现细节）
- **输出**: `S11_code_generation.md`（含 Baseline 实现溯源表） + 代码文件
- **Agent**: Experiment
- **质量标准**: 代码可运行；结构清晰；有复现指南；**Baseline 实现溯源完整**
- **预估时间**: 30-90 分钟
- **可回溯原因**: 代码 bug、未正确实现设计

#### S12: Experiment Execution, Result Collection & Preliminary Analysis
- **目标**: 实验迭代探索（AutoResearch 风格实验循环），包含实验执行、结果收集和初步分析。在此处实现实验迭代探索
- **输入**: S11, S10（解析代码、执行计划）
- **输出**: `S12_experiment_iteration.md` + 原始结果 + git 分支历史 + `experiments/results.tsv`
- **Agent**: Experiment
- **质量标准**: 
  - 按协议执行；环境记录完整；日志保存
  - **迭代循环记录完整**：每个 experiment iteration 都有 git commit 和 `results.tsv` 记录
  - **所有尝试保留**：不做 `git reset`，所有实验尝试（包括失败的）都通过 git commit 保存
  - **Baseline 复现验证通过**：所有 baseline 的运行结果与原论文报告值偏差 ≤ 5%，或偏差已记录为 implementation gap 并在结果中诚实报告
  - **初步分析到位**：每次迭代后做基本的数据质量检查
- **工作模式**:
  1. 创建 `experiments/auto-{topic}-{timestamp}` 分支
  2. 运行 baseline，记录参考指标
  3. 进入迭代循环：`modify code → git commit → run iteration (budgeted full run, 5-30min) → evaluate → preliminary analysis → 记录结果`
  4. 当达到收敛条件（指标收敛/预算耗尽/方向已充分探索）时停止迭代
  5. **S12 不做最终决策**：所有实验尝试（无论效果好坏）均通过 git commit 保留，最终 KEEP/DISCARD/FIX 决策由 S13 (Analysis Agent) 做出
- **关于效果不佳**：S12 可能因预算耗尽、方向验证（负向）、或在低水平收敛而结束。即使方法效果明显不佳，S12 也应正常结束并将完整记录交给 S13。**S13 负责判断是否需要回溯以及回溯目标**
- **预估时间**: 取决于实验（单次迭代 5-30 分钟，总预算可能数小时到数天）
- **可回溯原因**: 实验失败、结果异常、不可复现、假设被否定、代码 bug

#### S13: Experiment Result Verification
- **目标**: 对 S12 收敛后的**所有**实验结果（包括失败的尝试）进行深度分析，做出最终 KEEP / FIX / BACKTRACK 决策，并产出「回溯修改方向」
- **输入**: S11, S12, S07, S09, S04（解析代码、实验结果、git 历史、`results.tsv`、基准数据集信息、baseline 选择、研究假设）
- **输出**: `S13_result_verification.md`（含回溯修改方向章节）
- **Agent**: Analysis
- **Critic 审查**: 是（G3: Method + Evidence）
- **质量标准**: 复现性确认；统计显著性；baseline 合理；结果可靠性验证；**必须给出明确决策**
- **预估时间**: 20-40 分钟

**S13 决策树（根据实验结果做出分类决策）**：

```
S13 深度分析所有实验结果（复现性、过拟合、数据泄露、稳定性、统计显著性）
    │
    ├── 结果显著优于 baseline，无数据问题，各项检查通过
    │   → 决策: KEEP → 推进到 P4 (S14)
    │
    ├── 效果尚可但有改进空间（如超参可微调、seed 稳定性需改善）
    │   → 决策: FIX → 回溯到 S12
    │   → 产出「回溯修改方向」说明具体修复方向
    │   → Experiment Agent 在 S12 内继续迭代
    │
    ├── 效果不佳，根因在代码/实现层面（如实现 bug、超参严重错误、数据预处理逻辑错误）
    │   → 决策: BACKTRACK → 回溯到 S11
    │   → 产出「回溯修改方向」：问题诊断 + 代码修改方向
    │
    ├── 效果不佳，根因在方法设计层面（如核心架构设计不合理、损失函数选择不当）
    │   → 决策: BACKTRACK → 回溯到 S06
    │   → 产出「回溯修改方向」：方法缺陷诊断 + 重新设计方向
    │
    ├── 效果不佳，根因在实验设计层面（如超参搜索空间不合理、数据划分方式有问题）
    │   → 决策: BACKTRACK → 回溯到 S08
    │   → 产出「回溯修改方向」：实验设计问题诊断 + 修订方向
    │
    ├── 效果不佳，根因在数据/基准层面（如数据集标注质量差、类别严重不均衡、训练/测试分布漂移、基准数据集与任务不匹配）
    │   → 决策: BACKTRACK → 回溯到 S07
    │   → 产出「回溯修改方向」：数据问题诊断 + 替代数据集建议
    │
    ├── 效果不佳，根因在 baseline 选择层面（如选用了不适用于本任务的 baseline、baseline 过于陈旧导致虚假 superiority、缺少关键 baseline 导致对比不完整、baseline 实现质量问题）
    │   → 决策: BACKTRACK → 回溯到 S09
    │   → 产出「回溯修改方向」：baseline 问题诊断 + 替换/补充建议
    │
    └── 效果差，核心假设被实验结果否定（如假设的方法机制并未产生预期效果）
        → 决策: BACKTRACK → 回溯到 S04
        → 产出「回溯修改方向」：假设被否定的证据 + 新假设方向建议
```

**关键原则**：
- S13 是 Phase 3 的**唯一决策点**，S12 只记录不决策
- S13 必须基于数据质量检查（过拟合、数据泄露、训练稳定性），**不只看表面指标**
- 每个 BACKTRACK 决策必须附带「回溯修改方向」章节，让回溯目标 Agent 知道修什么
- 如果 S13 无法确定根因在哪一层，**保守回溯到更上游**（如不确定是 S11 还是 S06，回溯到 S06；不确定是 S07/S09 还是 S06，回溯到 S06）
- **可回溯原因**: 结果不可靠、统计方法错误、baseline 选择不当、数据集质量问题、方法效果不达预期、核心假设被否定

---

### Phase 4: Ablation

#### S14: Ablation Design
- **目标**: 为了验证本方法各个模块的有效性，进行消融实验设计。此处和实验方法的步骤基本相同，都需要 subagent 审查
- **输入**: S13, S06（解析验证结果和方法组件）
- **输出**: `S14_ablation_design.md`
- **Agent**: Experiment
- **质量标准**: 每个核心组件有对应消融；设计能隔离变量；**subagent 审查通过**
- **预估时间**: 15-30 分钟

#### S15: Ablation Code Generation
- **目标**: 生成消融实验的代码
- **输入**: S14, S11（解析消融设计和主实验代码）
- **输出**: `S15_ablation_code.md` + 消融代码文件
- **Agent**: Experiment
- **质量标准**: 代码可运行；与主实验一致；消融变量正确隔离；**通过 Code Review 子 Agent 审查**
- **预估时间**: 20-40 分钟
- **可回溯原因**: 代码 bug、消融实现错误

#### S16: Ablation Execution
- **目标**: 执行消融实验代码。S15 已通过 Code Review，此处若报错需回溯到 S15 代码生成或 S14 设计
- **输入**: S15（解析消融代码）
- **输出**: `S16_ablation_execution.md` + 原始结果（`experiments/results/ablation_*.json`, `experiments/results/ablation.tsv`）
- **Agent**: Experiment
- **质量标准**: 结果完整；与主实验一致；运行无报错
- **预估时间**: 取决于实验规模
- **可回溯原因**: 运行报错 → 回溯到 S15 或 S14

#### S17: Ablation Result Analysis
- **目标**: 分析消融实验结果
- **输入**: S16, S14（解析消融结果和设计）
- **输出**: `S17_ablation_analysis.md`
- **Agent**: Analysis
- **Critic 审查**: 是（G4: Method + Evidence）
- **质量标准**: 每个消融变量有明确结论；与主实验结果一致；统计显著
- **预估时间**: 15-30 分钟

---

### Phase 5: Further Analysis

#### S18: Other Findings
- **目标**: 根据 P3 和 P4 的实验结果，进一步发现一些实验现象。该现象可以突出本文方法的优越性；或是为进一步研究提供线索。注意，此处可以和 S02 关联，参考其他工作的进一步分析是如何实现的，做了什么
- **输入**: S12, S16, S17, S02（解析主实验结果、消融结果、文献中的分析方法）
- **输出**: `S18_other_findings.md`
- **Agent**: Analysis
- **质量标准**: 现象有数据支撑；与文献中类似分析可比；有洞察力
- **预估时间**: 20-40 分钟

#### S19: Analysis Experiment Design
- **目标**: 设计进一步的分析实验（如可视化分析、敏感性分析、失败案例分析等）。此处需要 subagent 审查可行性
- **输入**: S18, S06（解析发现的现象和方法组件）
- **输出**: `S19_analysis_experiment_design.md`
- **Agent**: Analysis
- **质量标准**: 实验设计能回答分析目标；**subagent 审查通过**；与主实验不冲突
- **预估时间**: 15-30 分钟

#### S20: Analysis Experiment Implementation
- **目标**: 实现 S19 设计的分析实验
- **输入**: S19, S11（解析分析实验设计和主实验代码）
- **输出**: `S20_analysis_experiment.md` + 分析代码/结果
- **Agent**: Experiment
- **质量标准**: 实现正确；结果可复现；与主实验数据一致
- **预估时间**: 20-40 分钟
- **可回溯原因**: 实现错误、结果异常

#### S21: Analysis Result Collection & Analysis
- **目标**: 收集和分析 S20 的实验结果。需要审查，必要时回溯
- **输入**: S20, S18（解析分析实验结果和发现的现象）
- **输出**: `S21_analysis_results.md`
- **Agent**: Analysis
- **Critic 审查**: 是（G5: Logic + Evidence + Novelty）
- **质量标准**: 结果完整；分析深入；与 P3/P4 结果一致；能支撑论文 claim
- **预估时间**: 20-40 分钟
- **可回溯原因**: 结果不支持假设、分析有缺陷

---

### Phase 6: Synthesis

#### S22: Claim-Evidence Map
- **目标**: 根据 P3、P4、P5 的实验结果，建立 claim 到 evidence 的映射
- **输入**: S12, S17, S21, S04（解析主实验结果、消融结果、进一步分析结果、假设）
- **输出**: `S22_claim_evidence_map.md`
- **Agent**: Analysis
- **质量标准**: 每个 claim 有证据；弱声明已识别；证据覆盖 P3+P4+P5
- **预估时间**: 20-40 分钟

#### S23: Finding Synthesis
- **目标**: 从所有实验结果中提炼洞察（含 Outer Loop 反馈）
- **输入**: handoff_P5_P6, S22（解析 claim-evidence 映射）
- **输出**: `S23_finding_synthesis.md`
- **Agent**: Analysis
- **质量标准**: 超越数据表面；与假设对应；模式识别
- **预估时间**: 30-60 分钟

#### S24: Contribution Articulation
- **目标**: 清晰阐述研究贡献
- **输入**: S22-S23（解析发现、claim-evidence 映射）
- **输出**: `S24_contribution_articulation.md`
- **Agent**: Writing
- **质量标准**: 贡献点清晰；无夸大；有证据支撑
- **预估时间**: 20-40 分钟

#### S25: Future Work
- **目标**: 识别未来研究方向
- **输入**: S23, S24（解析局限性和贡献）
- **输出**: `S25_future_work.md`
- **Agent**: Ideation
- **Critic 审查**: 是（G6: Logic + Evidence + Novelty）
- **质量标准**: 方向具体；与当前工作关联；有价值
- **预估时间**: 15-30 分钟

---

### Phase 7: Writing

#### S26: Paper Outline
- **目标**: 设计论文结构，**严格按照 venue LaTeX 模板要求规划后续所有 section**
- **输入**: handoff_P6_P7, S24, `artifacts/latex_template/`（解析贡献声明和 venue 模板要求）
- **输出**: `S26_paper_outline.md`
- **Agent**: Writing
- **质量标准**: 
  - 符合 venue 规范；每段有核心信息；图表计划
  - **Section 结构与 venue 模板完全一致**（如 IEEE Trans 需包含特定 section）
  - **页数分配在 venue 限制内**
  - **引用格式符合 venue 要求**
- **关键要求**: 从 S26 开始，所有写作必须遵循 `artifacts/latex_template/` 中的 venue 模板格式。若使用 IEEE Trans，Related Work 的论述架构应与同 venue 文章保持一致。
- **预估时间**: 15-30 分钟

#### S27: Introduction & Related Work
- **目标**: 撰写引言和相关工作（PaperOrchestra Step 3）
- **输入**: S26, S02, S24（解析大纲、文献综述、贡献）
- **输出**: `S27_introduction_relatedwork.md`
- **Agent**: Writing
- **质量标准**: 动机清晰；相关工作对比充分；贡献陈述明确
- **特殊要求**: 所有 LLM 写作调用前必须附加 **Anti-Leakage Prompt**
- **预估时间**: 30-60 分钟

#### S28: Methodology Section
- **目标**: 撰写方法部分
- **输入**: S26, S06（解析大纲、方法设计）
- **输出**: `S28_methodology_section.md`
- **Agent**: Writing
- **质量标准**: 描述完整；有伪代码；读者可复现
- **预估时间**: 30-60 分钟

#### S29: Experiments & Results
- **目标**: 撰写实验和结果部分
- **输入**: S26, S12, S16, S17, S21（解析大纲、主实验结果、消融结果、进一步分析结果）
- **输出**: `S29_experiments_results.md`
- **Agent**: Writing
- **质量标准**: 实验设置清晰；结果报告完整；统计检验提及
- **预估时间**: 30-60 分钟

#### S30: Analysis & Discussion
- **目标**: 撰写分析和讨论
- **输入**: S26, S23, S18（解析大纲、发现综合、其他发现）
- **输出**: `S30_analysis_discussion.md`
- **Agent**: Writing
- **质量标准**: 洞察深刻；局限性诚实；讨论有深度
- **预估时间**: 20-40 分钟

#### S31: Abstract & Conclusion
- **目标**: 撰写摘要和结论
- **输入**: S26, S23, S24（解析大纲、发现、贡献）
- **输出**: `S31_abstract_conclusion.md`
- **Agent**: Writing
- **质量标准**: Abstract 150-250 词；结论不引入新内容
- **预估时间**: 15-30 分钟

#### S32: Figure & Table Generation
- **目标**: 生成所有图表（PaperOrchestra Step 2: Plotting Pipeline）
- **输入**: S26 (`plotting_plan`), S12, S06（解析图表计划、结果数据、方法描述）
- **输出**: `S32_figure_table_generation.md` + 图表文件 + 生成代码
- **Agent**: Figure
- **质量标准**: 
  - 清晰；准确；美观；colorblind-friendly
  - 经过 **VLM Critic ≥1 轮** 视觉审查
  - 每个图都有独立的可复现生成脚本
  - 分辨率 ≥300 DPI 或矢量格式
- **工作模式**: Planner → Renderer → VLM Critic（迭代 ≤3 轮）
- **预估时间**: 30-60 分钟
- **可并行**: 是（与 S27-S31 并行）

#### S33: Full Draft Assembly
- **目标**: 整合完整草稿（PaperOrchestra Step 4: Single Multimodal Call）
- **输入**: S26 (`outline`) + S27-S31（各 section，必须已完成）+ S32（图表文件，作为多模态输入）
- **输出**: `S33_full_draft.md` + `artifacts/draft.tex` + `artifacts/draft.pdf`
- **Agent**: Writing
- **Critic 审查**: 是（G7: Logic + Writing + Evidence）
- **质量标准**: 
  - 结构完整；内部一致；引用正确
  - **使用项目 venue 模板**：`artifacts/latex_template/` 中的 `.sty`/`.cls` 文件
  - **页数在 venue 限制内**：从 `state/pipeline_state.yaml` 读取 `project.venue.page_limit`
  - **优先使用单次多模态调用**生成完整 LaTeX 草稿
  - 图表已正确插入并引用
  - Anti-Leakage Prompt 已应用
  - **LaTeX 编译通过**：执行多次编译（pdflatex → bibtex → pdflatex × 2）
- **预估时间**: 30-60 分钟（单次 multimodal call + 编译）

---

### Phase 8: Refinement

#### S34: Internal Review
- **目标**: 内部质量审查（多 Critic 并行）
- **输入**: S33
- **输出**: `S34_internal_review.md`（聚合所有 Critic 意见）
- **Agent**: Critic Team (Logic, Method, Evidence, Writing, Novelty)
- **质量标准**: 各维度评分；具体问题列表
- **预估时间**: 30-60 分钟（并行）

#### S35: Peer Review Simulation
- **目标**: 模拟 3 位审稿人审稿
- **输入**: S34, S33
- **输出**: `S35_peer_review_simulation.md`
- **Agent**: Review
- **质量标准**: 3 个不同视角；评分有依据；意见具体
- **预估时间**: 30-60 分钟

#### S36: Revision Loop
- **目标**: 根据审稿意见迭代修改（PaperOrchestra Step 5: Content Refinement）
- **输入**: S35, S33
- **输出**: `S36_revision_loop.md` + 修改后的 `drafts/iter*/paper.tex`
- **Agent**: Writing + Review（协作）
- **循环结构**:
  ```
  Iteration N:
    1. Writing Agent 根据评审意见修改
    2. LaTeX 编译检查 + Orphan Cite Gate + Anti-Leakage Check
    3. Review Agent 重审（独立评分，不受旧评分影响）
    4. Ethics Critic（最后一轮）
    5. Accept/Revert 决策
  ```
- **停止条件**（满足任一即 HALT）:
  - 评分 ≥ 7/10 且所有自动检查通过
  - 达到最大迭代次数（3 轮）
  - 连续两轮无提升
  - Review Agent 无新可操作 weakness
- **质量标准**: 
  - 逐条回应审稿意见；修改有针对性
  - **Accept/Revert Halt Rules**：
    - 总体评分提升 → ACCEPT 新版本
    - 总体评分持平且子维度无下降 → ACCEPT
    - 否则 → REVERT 到上一版本快照
  - 每次迭代前保存快照
- **预估时间**: 30-90 分钟

#### S37: Final Compilation
- **目标**: 编译最终论文并准备提交包（Camera-ready 版本）
- **输入**: S36（达到标准的最终版本）, `config/author_info.yaml`（作者信息）
- **输出**: `S37_final_compilation.md` + `artifacts/paper.pdf` + `artifacts/paper.tex` + `artifacts/submission-package.zip`
- **Agent**: Writing
- **质量标准**: 
  - **Camera-ready 调整**：使用正确的 style 选项（如 `\usepackage[final]{neurips_2025}`）
  - **多次编译**：pdflatex → bibtex → pdflatex × 2
  - **页数合规**：使用 `utils/latex_sanity.py` 验证
  - **作者信息从 `config/author_info.yaml` 读取并正确添加**，严禁编造或修改
  - 提交包整理：zip 包含 paper.pdf, paper.tex, refs.bib, supplementary/
- **预估时间**: 15-30 分钟

---

## 5. 关键路径与可并行任务

### 关键路径（不可并行）
```
S01 → S02 → S03 → S04 → S05 → G1 →
S06 → S07 → S08 → S09 → S10 → G2 →
S11 → S12 → S13 → G3 →
S14 → S15 → S16 → S17 → G4 →
S18 → S19 → S20 → S21 → G5 →
S22 → S23 → S24 → S25 → G6 →
S26 → {S27 ∥ S32} → S33 → G7 →
S34 → S35 → S36 → G8 →
S37
```

### 可并行任务
- **S32**（图表生成）可与 **S27**（Intro & Related Work）并行启动，后续与 S28-S31 区域并行完成
- **Gate 审查时**：多个 Critic 并行审查同一产出
- **S02** 和 **S01** 部分重叠

---

## 6. Stage 状态机

每个 Stage 有以下状态：

```
PENDING ──► ASSIGNED ──► IN_PROGRESS ──► COMPLETED
                              │
                              ▼
                         FAILED ──► RETRY
                              │
                              ▼
                         BACKTRACK_REQUESTED
```

---

## 7. 时间估算汇总

| Phase | Stage 数 | 预估时间 | 可睡觉？ |
|-------|---------|---------|---------|
| P1 Discovery | 5 | 2-4 小时 | 是（如果 AUTO_PROCEED） |
| P2 Design | 5 | 2-3 小时 | 是 |
| P3 Execution | 3 | 1-24+ 小时 | 是（实验运行时可） |
| P4 Ablation | 4 | 1-3 小时 | 是 |
| P5 Further Analysis | 4 | 1-3 小时 | 是 |
| P6 Synthesis | 4 | 2-3 小时 | 是 |
| P7 Writing | 8 | 3-6 小时 | 是 |
| P8 Refinement | 4 | 2-4 小时 | 是（最后阶段） |
| **总计** | **37** | **~15-50+ 小时** | |

---

> **下一步**: 阅读 `05_KNOWLEDGE_FLOW.md` 了解知识如何在 Stage 之间流转。
