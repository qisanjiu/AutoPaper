# 37 Stages 速查表

> **编号规则**：S01-S36 连续，S37 已删除，之后直接 S37。
> **Gate 位置**：G1(S05), G2(S10), G3(S13), G4(S17), G5(S21), G6(S25), G7(S33), G8(S37)

## P1 Discovery — 发现值得研究的问题

| Stage | Agent | 核心任务 | 产出文档 |
|-------|-------|---------|---------|
| S01 | literature | 选题分析（多角度收集） | `S01_topic_analysis.md` |
| S02 | literature | 文献调研（含数据集、指标、代码可用性等实验细节）+ refs.bib | `S02_literature_survey.md` |
| S03 | ideation | 研究问题生成 | `S03_research_question.md` |
| S04 | ideation | 假设生成 | `S04_hypothesis_generation.md` |
| S05 | ideation | 新颖性可行性评估 | `S05_novelty_feasibility.md` |

## P2 Design — 设计严谨的解决方案

| Stage | Agent | 核心任务 | 产出文档 |
|-------|-------|---------|---------|
| S06 | method | 方法论设计（**subagent 检验可行性**） | `S06_methodology_design.md` |
| S07 | method | Benchmark 选择（**subagent 检验**，收集数据集信息） | `S07_benchmark_selection.md` |
| S08 | method | 实验协议设计 | `S08_experiment_protocol.md` |
| S09 | method | Baseline 选择（**subagent 检验**，不与消融冲突，参考 S02 代码可用性降权） | `S09_baseline_selection.md` |
| S10 | method | 完整实验计划（method + baselines） | `S10_full_experiment_plan.md` |

## P3 Execution — 执行实验并迭代探索

| Stage | Agent | 核心任务 | 产出文档 |
|-------|-------|---------|---------|
| S11 | experiment | 代码生成（method + baselines） | `S11_code_generation.md` + `experiments/src/` |
| S12 | experiment | 实验执行+结果收集+初步分析（**内嵌 AutoResearch 迭代循环**） | `S12_experiment_iteration.md` |
| S13 | analysis | 实验结果验证（迭代收敛后进入） | `S13_result_verification.md` |

> **S12 关键设计**: 内嵌实验迭代循环（修改→git commit→运行→记录→分析），所有尝试保留。基于深入分析（过拟合、数据泄露、训练稳定性等）做 KEEP/DISCARD/BACKTRACK 决策。若需修复代码，回溯到 S11。

## P4 Ablation — 验证各模块有效性

| Stage | Agent | 核心任务 | 产出文档 |
|-------|-------|---------|---------|
| S14 | experiment | 消融实验设计（**subagent 审查**） | `S14_ablation_design.md` |
| S15 | experiment | 消融代码生成 | `S15_ablation_code.md` |
| S16 | experiment | 消融实验执行（报错则回溯 S15/S14） | `S16_ablation_execution.md` |
| S17 | analysis | 消融结果分析 | `S17_ablation_analysis.md` |

## P5 Further Analysis — 进一步分析实验现象

| Stage | Agent | 核心任务 | 产出文档 |
|-------|-------|---------|---------|
| S18 | analysis | 其他发现（突出方法优越性，参考 S02） | `S18_other_findings.md` |
| S19 | analysis | 分析实验设计（可视化等，**subagent 审查**） | `S19_analysis_experiment_design.md` |
| S20 | experiment | 分析实验实现 | `S20_analysis_experiment.md` |
| S21 | analysis | 分析结果收集与分析（**需审查，必要时回溯**） | `S21_analysis_results.md` |

## P6 Synthesis — 提炼研究洞察与贡献

| Stage | Agent | 核心任务 | 产出文档 |
|-------|-------|---------|---------|
| S22 | analysis | Claim-Evidence 映射（基于 P3/P4/P5） | `S22_claim_evidence_map.md` |
| S23 | analysis | 发现综合 | `S23_finding_synthesis.md` |
| S24 | writing | 贡献阐述 | `S24_contribution_articulation.md` |
| S25 | ideation | 未来工作 | `S25_future_work.md` |

## P7 Writing — 将研究转化为论文

| Stage | Agent | 核心任务 | 产出文档 |
|-------|-------|---------|---------|
| S26 | writing | 论文结构定义 | `S26_paper_outline.md` |
| S27 | writing | Introduction & Related Work | `S27_intro_related_work.tex` |
| S28 | writing | Methodology | `S28_methodology.tex` |
| S29 | writing | Experiments & Results | `S29_experiments_results.tex` |
| S30 | writing | Analysis & Discussion | `S30_analysis_discussion.tex` |
| S31 | writing | Abstract & Conclusion | `S31_abstract_conclusion.tex` |
| S32 | figure | 图表生成 | `figures/*.png/pdf` |
| S33 | writing | 完整草稿整合 | `artifacts/draft.tex` + `draft.pdf` |

## P8 Refinement — 通过批判循环提升质量

| Stage | Agent | 核心任务 | 产出文档 |
|-------|-------|---------|---------|
| S34 | critic_team | 内部审查 | `S34_internal_review.md` |
| S35 | review | 审稿人模拟 (3 reviewers) | `S35_peer_review_simulation.md` |
| S36 | writing | 修订循环 (≤3 轮, Accept/Revert/Halt) | `S36_revision_loop.md` |
| S37 | writing | 最终编译 + 提交包 | `S37_final_compilation.md` + `paper.pdf` + `submission-package.zip` |

> **S36 注意**：最后一轮自动执行 Orphan Cite / Anti-Leakage / LaTeX Sanity 检查。

## 实际文件位置（双产出协议）

| Stage | 实际文件 | 描述 MD |
|-------|---------|---------|
| S02 | `knowledge/refs.bib` | `S02_literature_survey.md` |
| S11 | `experiments/src/*.py`, `configs/*.yaml` | `S11_code_generation.md` |
| S12 | `experiments/results/`, `results.tsv` (所有尝试) | `S12_experiment_iteration.md` |
| S16 | `experiments/results/ablation_*.json` | `S16_ablation_execution.md` |
| S20 | `experiments/results/analysis_*.json` | `S20_analysis_experiment.md` |
| S32 | `figures/*.png`, `figures/*.pdf` | `S32_figure_table_generation.md` |
| S33 | `artifacts/draft.tex`, `draft.pdf` | `S33_full_draft.md` |
| S36 | `drafts/iter*/paper.tex` | `S36_revision_loop.md` |
| S37 | `artifacts/paper.pdf`, `paper.tex`, `submission-package.zip` | `S37_final_compilation.md` |
