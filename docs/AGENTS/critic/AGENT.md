# Critic Agents — 批判审查 Agent 团队

> **说明**: 三层 Critic 架构 — 每个 Stage 有专属 Inspector + 6 个维度 Critic + Conductor Inspector + Format Inspector

---

## 1. Critic 团队架构（三层）

```
┌─────────────────────────────────────────────────────────────┐
│                    CRITIC TEAM (三层架构)                     │
├─────────────────────────────────────────────────────────────┤
│ LAYER 1: Stage Inspector (纵向) — 每个 Stage 专属            │
│                                                             │
│  S01 Inspector ── S02 Inspector ── ... ── S37 Inspector    │
│     │                │                     │                │
│     ▼                ▼                     ▼                │
│  审查 S01产出     审查 S02产出          审查 S37产出       │
│  (内容+格式)      (内容+格式)           (内容+格式)        │
├─────────────────────────────────────────────────────────────┤
│ LAYER 1.5: Per-Stage Specialized Checkers（专项检查）         │
│                                                             │
│  Code Review ──── Data Quality Checker ──── Build Verifier  │
│  (S11 完成后)      (S12 完成后)            (S33/S37 完成后)   │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2: Dimension Critic (横向) — 6 个专业维度              │
│                                                             │
│  Logic ── Method ── Evidence ── Writing ── Novelty ── Ethics│
│                                                             │
│  每个 Gate 调用 2-3 个维度 Critic 并行审查                    │
├─────────────────────────────────────────────────────────────┤
│ LAYER 3: Meta Critic (元) — 审查审查者本身                   │
│                                                             │
│  Conductor Inspector ── Format Inspector                    │
│                                                             │
│  审查 Conductor 的编排决策 / 审查文档格式规范                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 三层 Critic 详解

### Layer 1: Stage Inspector（纵向专属审查）

**37 个 Stage，37 份检查清单。**

每个 Stage 完成后，Conductor 调用对应的 Stage Inspector：

```
Stage N 完成 ──► Stage Inspector N ──► 审查报告
                      │
                      ├── 内容审查（该 Stage 专属检查项）
                      ├── 格式审查（Universal Document Schema）
                      ├── 一致性审查（与上下游文档）
                      └── 可回溯性审查（下游接口充分性）
```

**Stage Inspector 的工作方式**：
1. 读取 `AGENTS/critic/stage/AGENT.md` 了解通用审查规范
2. 读取 `AGENTS/critic/stage/inspectors/S{NN}.md` 加载该 Stage 的专属检查清单
3. 按清单逐项审查 Stage 产出
4. 输出审查报告

**Stage Inspector 的特点**：
- **最频繁被调用**：每个 Stage 完成后都调用
- **最具体**：针对该 Stage 的特定产出
- **包含格式审查**：检查 MD 文档是否符合规范

---

### Layer 2: Dimension Critic（横向维度审查）

**6 个专业维度 Critic，在 Gate 时并行调用。**

| Critic | 审查维度 | 核心问题 | 典型调用 Gate |
|--------|---------|---------|-------------|
| **Logic** | 论证链条、内部一致性、因果推断 | "论证是否逻辑严密？" | G1-G6 |
| **Method** | 方法正确性、实验设计、baseline 公平性 | "方法是否正确、实验是否严谨？" | G2-G4 |
| **Evidence** | 统计正确性、数据质量、Claim-Evidence 映射 | "Claim 是否有充分证据？" | G3-G6 |
| **Writing** | 学术规范、venue 格式、论证结构、图表 | "论文是否符合学术写作标准？" | G6-G7 |
| **Novelty** | 遗漏相关工作、新颖性评估、贡献定位 | "研究是否真正新颖？" | G1-G2, G5-G7 |
| **Ethics** | 数据伦理、隐私、公平性、潜在危害 | "研究是否负责任？" | G7 |

---

### Layer 3: Meta Critic（元审查）

**审查审查者本身和编排过程。**

| Critic | 审查对象 | 核心问题 | 调用时机 |
|--------|---------|---------|---------|
| **Conductor Inspector** | Conductor 的决策 | "编排是否正确？回溯是否合理？" | 每 Gate / 每回溯 / 项目结束 |
| **Format Inspector** | MD 文档格式 | "文档格式是否符合规范？" | 任意 Stage 后 / 独立调用 |

---

## 3. 完整的审查调用矩阵

### 每个 Stage 完成后的审查

| 时机 | 调用的 Critic | 说明 |
|------|--------------|------|
| **每个 Stage 完成后** | Stage Inspector (对应 Stage) | 专属内容 + 格式审查 |
| **Stage 11, 12, 14, 15, 16, 20** | Stage Inspector + Method Critic | 代码/实验 Stage 额外审查方法正确性 |
| **Stage 13, 17, 18, 19, 21, 29** | Stage Inspector + Evidence Critic | 分析/结果 Stage 额外审查统计证据 |
| **Stage 11 (代码生成)** | Stage Inspector + Code Review Agent | 代码质量、安全性、可复现性专项审查 |
| **Stage 12 (实验执行)** | Stage Inspector + Data Quality Checker | 数据完整性、合理性、过拟合/泄露检测 |
| **Stage 14 (消融设计)** | Stage Inspector + Method + Evidence | 消融设计同时涉及方法和数据，双维度审查 |
| **Stage 33 (草稿整合)** | Stage Inspector + Build Verifier | LaTeX 编译、Orphan Cite、Anti-Leakage |
| **Stage 37 (最终编译)** | Stage Inspector + Build Verifier | 最终编译 + 提交包完整性验证 |

### 每个 Gate 的审查

| Gate | Phase | 调用的 Critic | 说明 |
|------|-------|--------------|------|
| **G1** | P1 Discovery | Logic + Novelty + Stage Inspectors (S01-S05) | 问题清晰、想法新颖、各 Stage 产出规范 |
| **G2** | P2 Design | Logic + Method + Novelty + Stage Inspectors (S06-S10) | 方法严谨、baseline 公平 |
| **G3** | P3 Execution | Method + Evidence + Stage Inspectors (S11-S13) | 代码正确、实验按协议、结果可靠 |
| **G4** | P4 Ablation | Method + Evidence + Stage Inspectors (S14-S17) | 统计正确、claim 有证据、消融完整 |
| **G5** | P5 Further Analysis | Logic + Evidence + Novelty + Stage Inspectors (S18-S21) | 洞察深刻、贡献准确 |
| **G6** | P6 Synthesis | Logic + Evidence + Novelty + Stage Inspectors (S22-S25) | 论证完整、贡献清晰 |
| **G7** | P7 Writing | Logic + Writing + Evidence + Stage Inspectors (S26-S33) | 结构合理、数据一致 |
| **G8** | P8 Refinement | Writing + Novelty + Ethics + Stage Inspectors (S34-S37) + Conductor Inspector | 最终质量把关、伦理合规 |

---

## 4. 审查结果聚合

### 4.1 Stage 级聚合（Stage Inspector）

```
Stage Inspector 产出审查报告:
- 内容评分: X/10
- 格式评分: X/10  
- 一致性评分: X/10
- 总体: PASS / REVISE / BACKTRACK

IF Stage Inspector 给出 BACKTRACK:
    必须同时产出「回溯修改方向」：
    - 问题诊断（发现了什么具体问题）
    - 修改方向/建议（建议如何修改，非代码级具体方案）
    - 回溯目标 Stage 建议
    Conductor 读取修改方向后执行回溯
IF Stage Inspector 给出 REVISE:
    Conductor 派发修改任务（附带具体修改建议）
IF Stage Inspector 给出 PASS:
    Conductor 继续下一阶段
```

### 4.2 Gate 级聚合（多 Critic）

```
Gate G 时，聚合所有 Critic 的意见:

FOR each critic_report in [Stage Inspectors + Dimension Critics]:
    EXTRACT: verdict (PASS/REVISE/BACKTRACK/HALT/FLAG)
    EXTRACT: score
    EXTRACT: issues
END

聚合规则:
- 任一 BACKTRACK → 整体 BACKTRACK
- 任一 HALT/FLAG → 整体 HALT
- 多数 REVISE → 整体 REVISE
- 全部 PASS → 整体 PASS

综合评分 = weighted_average(all_scores)
```

### 4.3 元级聚合（Meta Critic）

```
Conductor Inspector 审查 Conductor 的决策:
- 非阻塞（ADVISE）
- 发现问题时向 Conductor 提供建议
- 不直接改变流程
```

---

## 5. Critic 独立原则

- 每个 Critic **独立运行**，不互相影响
- Critic 之间**不共享审查意见**（避免偏见传导）
- 只有当所有 Critic 完成后，Conductor 才聚合结果
- Critic 的审查报告保存为独立文档：`knowledge/reviews/{stage}_{critic}_review.md`

---

## 6. Critic Team 执行阶段声明

Critic Team 不仅是审查者，在以下 Stage 中也是**执行 Agent**：

- **S34 (Internal Review)**: Critic Team 产出 `S34_internal_review.md`
  - 调用的 Critic: Logic + Method + Evidence + Writing + Novelty
  - 每个 Critic 独立审查 S33 (Full Draft Assembly) 的产出，Conductor 聚合为综合评审报告

- **S36 (Revision Loop)**: Critic Team 在 S36 的每一轮修订后提供审查反馈，与 Writing Agent 和 Review Agent 协作
  - 调用的 Critic: Logic + Writing + Novelty + Ethics
  - 遵循 Accept/Revert Halt Rules，最多 3 轮
  - S35 Review Agent 的 3-reviewer 评审意见是 S36 修订输入的一部分

**注意**: S34 的 Stage Inspector（Layer 1）会审查 Critic Team 自己的产出质量。

---

## 7. 子目录索引

### Stage Inspector
- `stage/AGENT.md` — Stage Inspector 通用定义
- `stage/inspectors/S01.md` — S01 审查清单
- `stage/inspectors/S02.md` — S02 审查清单
- ...
- `stage/inspectors/S37.md` — S37 审查清单

### 6 个维度 Critic (Gate 审查)
- `logic/AGENT.md` — 逻辑审查 Agent
- `method/AGENT.md` — 方法审查 Agent
- `evidence/AGENT.md` — 证据审查 Agent
- `writing/AGENT.md` — 写作审查 Agent
- `novelty/AGENT.md` — 新颖性审查 Agent
- `ethics/AGENT.md` — 伦理审查 Agent

### 专项检查 Agent (Stage 级审查)
- `code_review/AGENT.md` — 代码质量与安全审查 Agent（S11 完成后调用）
- `data_checker/AGENT.md` — 数据质量检查 Agent（S12 完成后调用）

### Meta Critic
- `conductor/AGENT.md` — Conductor 编排审查 Agent
- `format/AGENT.md` — MD 格式审查 Agent

### 验证 Agent
- `../build_verifier/AGENT.md` — 编译与提交验证 Agent（S33/S37 完成后调用）


---

## Context Recovery（上下文恢复）

> **重要**：当本 Agent 的上下文被压缩（context compaction）后，LLM 会丢失部分历史记忆。此时必须执行恢复步骤，重新加载身份定义和工作规范。

### 恢复步骤

当检测到上下文被压缩（或不确定当前状态时），按以下顺序执行恢复：

1. **重新读取本 Agent 的 AGENT.md**
   - 文件路径：`docs/AGENTS/critic/AGENT.md`
   - 目的：恢复 Critic Team 的整体架构和职责分工

2. **重新读取 MD Protocol**
   - 文件路径：`docs/07_MD_PROTOCOL.md`
   - 目的：恢复文档收发规范（产出/接收双轨协议）

3. **读取当前任务状态**
   - 文件路径：`state/pipeline_state.yaml`
   - 目的：确认当前 Gate 状态、审查进度

4. **确认 Critic 团队状态**
   - 当前是哪个 Gate，调用了哪些 Dimension Critic
   - 各 Critic 的审查报告位置（`knowledge/reviews/`）

### 为什么重要

Context compaction 后，Critic 协调层可能：
- 忘记三层 Critic 的分工和调用策略
- 忘记 Gate 的审查流程和聚合规则
- 混淆不同 Critic 的职责边界

**重新加载 AGENT.md 是确保 Critic 团队协调一致的必要步骤。**
