# SpiralResearch — 总体架构设计

> **版本**: v0.2-framework  
> **状态**: 设计阶段（未实现）  
> **核心理念**: 螺旋向前、多Agent协作、专业批判驱动、规范文档流转

---

## 1. 设计哲学

### 1.1 螺旋向前 (Spiral Progression)

传统工作流是线性的：Stage 1 → Stage 2 → ... → Stage N。但真实科研从来不是线性的——一个实验结果可能推翻之前的假设，写作时发现方法描述不清需要返回修改，审稿意见可能要求补充实验。

**SpiralResearch 的核心设计：工作流是螺旋向前的。**

```
        Phase 1 (Discovery)
              ↗
    Phase 7 ←   → Phase 2 (Design)
(Refinement)    ↗
        ← Phase 7 (Refinement)
              ↖
    Phase 6 ←   → Phase 3 (Execution)
   (Writing)     ↗
        ← Phase 5 (Synthesis)
              ↖
           Phase 4 (Validation)
```

每一圈螺旋都产生更高质量的结果。当下游发现上游错误时，系统不会强行推进，而是**回溯到错误源头修复后再前进**。

### 1.2 多Agent + 三层批判驱动

参考 ARIS 的对抗性交叉模型协作、PaperOrchestra 的多 Agent 管道，以及真实顶会的多审稿人制度，SpiralResearch 采用 **三层 Critic 架构**：

- **专业子 Agent**：7 个执行 Agent，每个只负责一个领域
- **三层 Critic 团队**：
  - **Layer 1 — Stage Inspector**：37 个 Stage，每个 Stage 有专属的检查清单（内容 + MD 格式）
  - **Layer 2 — Dimension Critic**：6 个专业维度 Critic（逻辑/方法/证据/写作/新颖性/伦理），在 Gate 时并行审查
  - **Layer 3 — Meta Critic**：Conductor Inspector（审查编排决策）+ Format Inspector（审查 MD 格式规范）
- **模拟审稿 Agent**：Review Agent 以顶会审稿人的视角审视工作

### 1.3 知识即文档 + 规范收发

每个 Stage 的产出必须是**规范化、可阅读、可审查**的 Markdown 文档。Agent 不通过内存传递信息，而是通过**按规范读取**文档获取上下文。

**双轨规范**：
- **产出规范**：所有文档遵循 Universal Document Schema（含 Metadata、Reasoning Trail、Downstream Interface 等）
- **接收规范**：Agent 按 9 步解析流程读取上游文档（存在性检查 → 元数据解析 → 内容提取 → 推理审查 → 验证确认 → 风险加载 → 下游接口提取 → 回溯触发器检查 → 一致性交叉验证）

---

## 2. 系统架构

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Conductor Agent (主编排者)                      │   │
│  │  - 读取 pipeline_state.yaml 了解全局状态                    │   │
│  │  - 根据当前阶段创建/调用子 Agent                            │   │
│  │  - 处理 Gate Checkpoints 和 Backward Propagation            │   │
│  │  - 聚合多 Critic 的审查结果                                 │   │
│  │  - 维护决策日志和螺旋进度                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────┐ ┌─────────────┐ ┌─────────────────────────┐
│      EXECUTION LAYER    │ │ CRITIC      │ │    REVIEW LAYER         │

│                         │ │  (x6+2)     │ │                         │
│  (专业子 Agent 团队)     │ │   TEAM      │ │   (模拟同行评审)        │
│                         │ │  (x6)       │ │                         │
│  ┌─────┐ ┌─────┐       │ │             │ │  ┌─────────────────┐   │
│  │Lit  │ │Idea │       │ │ ┌─────────┐ │ │  │ Review Agent    │   │
│  │Agent│ │Agent│       │ │ │ Logic   │ │ │  │ (NeurIPS/ICML   │   │
│  └──┬──┘ └──┬──┘       │ │ │ Method  │ │ │  │  reviewer sim)  │   │
│     │       │          │ │ │Evidence │ │ │  └─────────────────┘   │
│  ┌──┴──┐ ┌──┴──┐       │ │ │Writing  │ │ │                         │
│  │Meth-│ │Exper│       │ │ │Novelty  │ │ │                         │
│  │od   │ │iment│       │ │ │ Ethics  │ │ │                         │
│  │Agent│ │Agent│       │ │ └─────────┘ │ │                         │
│  └──┬──┘ └──┬──┘       │ │             │ │                         │
│     │       │          │ └─────────────┘ │                         │
│  ┌──┴──┐ ┌──┴──┐       │                 │                         │
│  │Analy│ │Writ-│       │                 │                         │
│  │sis  │ │ing  │       │                 │                         │
│  │Agent│ │Agent│       │                 │                         │
│  └─────┘ └─────┘       │                 │                         │
│       ┌─────┐          │                 │                         │
│       │Fig- │          │                 │                         │
│       │ure  │          │                 │                         │
│       │Agent│          │                 │                         │
│       └─────┘          │                 │                         │
└─────────────────────────┘                 └─────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      KNOWLEDGE LAYER                                │
│                                                                     │
│   knowledge/           state/              artifacts/               │
│   ├── S01_*.md         ├── pipeline_state.yaml                      │
│   ├── S02_*.md         ├── decision_log.md                          │
│   ├── handoff_*.md     ├── spiral_log.md                            │
│   ├── reviews/         └── agent_registry.yaml                      │
│   │   └── G*_*_review.md                                            │
│   └── ...                                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Conductor Agent 的核心职责

Conductor 是**唯一的主控 Agent**，它不执行具体研究工作，只做三件事：

1. **状态感知**：读取 `pipeline_state.yaml`，了解当前所处阶段、历史决策、待办事项
2. **任务派发**：根据当前阶段，创建对应的子 Agent（通过 Agent 工具），传递必要的上下文文档路径
3. **流程控制**：处理 Gate 结果（通过/驳回/回退），**聚合多 Critic 的审查意见**，记录决策到 `decision_log.md`

**Conductor 绝不**：直接写论文正文、直接跑实验、直接搜索文献。这些全部派发给子 Agent。

### 2.3 子 Agent 的生命周期

```
Conductor 创建子 Agent
        │
        ▼
子 Agent 首先读取自己的 AGENTS/{role}/AGENT.md
        │
        ▼
子 Agent 读取 docs/07_MD_PROTOCOL.md 了解收发规范
        │
        ▼
子 Agent 按接收规范解析输入文档（9步流程）
        │
        ▼
子 Agent 执行工作，产出规范化文档
        │
        ▼
子 Agent 自检产出是否符合规范
        │
        ▼
子 Agent 向 Conductor 汇报完成，提交产出文档路径
```

---

## 3. Phase-Stage-Gate 结构

### 3.1 八 Phase 三十七 Stage

科研全流程被划分为 **8 个 Phase**，共 **37 个 Stage**。每个 Stage 都是原子性的（不可再分），有明确的输入文档、输出文档和质量标准。

| Phase | 名称 | Stage 范围 | 核心目标 | Gate 调用的 Critic |
|-------|------|-----------|---------|-------------------|
| P1 | Discovery | S01-S05 | 发现值得研究的问题 | Logic + Novelty |
| P2 | Design | S06-S10 | 设计严谨的解决方案 | Logic + Method + Novelty |
| P3 | Execution | S11-S13 | 执行实验并迭代探索 | Method + Evidence |
| P4 | Ablation | S14-S17 | 验证各模块有效性 | Method + Evidence |
| P5 | Further Analysis | S18-S21 | 进一步分析实验现象 | Logic + Evidence + Novelty |
| P6 | Synthesis | S22-S25 | 提炼研究洞察与贡献 | Logic + Evidence + Novelty |
| P7 | Writing | S26-S33 | 将研究转化为论文 | Logic + Writing + Evidence |
| P8 | Refinement | S34-S37 | 通过批判循环提升质量，最终编译提交包 | Writing + Novelty + Ethics + Conductor Insp |

### 3.2 Gate 检查点

在每个 Phase 结束时设置 **Gate**，由 **Critic Team（多个专业 Critic 并行）** 进行质量审查：

```
S05 ──► Gate G1 [Logic + Novelty] ──► S06
S10 ──► Gate G2 [Logic + Method + Novelty] ──► S11
S13 ──► Gate G3 [Method + Evidence] ──► S14
S17 ──► Gate G4 [Method + Evidence] ──► S18
S21 ──► Gate G5 [Logic + Evidence + Novelty] ──► S22
S25 ──► Gate G6 [Logic + Evidence + Novelty] ──► S26
S33 ──► Gate G7 [Logic + Writing + Evidence] ──► S34
S37 ──► Gate G8 [Writing + Novelty + Ethics + Conductor Inspector]
```

Gate 不是形式主义的"下一步"按钮，而是**真正的质量关卡**。多个专业 Critic 独立审查，Conductor 聚合结果。结果可能是：

- **PASS**：所有 Critic 认可，继续下一阶段
- **REVISE**：某些 Critic 发现问题，在当前 Phase 内修改后重新 Gate
- **BACKTRACK**：发现根本性问题，需要回溯到更早的 Stage/Phase 重新做
- **HALT**：无法继续，需要人工介入

### 3.3 Backward Propagation 机制

当 Critic 发现错误时，需要判断错误的根因：

```
如果 S12 (Experiment Iteration) 发现实验代码有逻辑错误或结果异常
    → 回溯到 S11 (Code Generation) 重新生成
    → 如果代码正确但假设错误，回溯到 S04 (Hypothesis Generation)

如果 S13 (Result Verification, Evidence Critic) 发现结果不可复现
    → 回溯到 S12 (Experiment Iteration) 重新执行
    → 如果仍然失败，回溯到 S11 (Code Generation)
    → 如果代码正确但假设错误，回溯到 S04 (Hypothesis Generation)

如果 S16 (Ablation Execution) 报错
    → 回溯到 S15 (Ablation Code Generation) 修复代码
    → 如果设计有问题，回溯到 S14 (Ablation Design)

如果 S21 (Analysis Results) 发现分析实验结果不支持假设
    → 回溯到 S20 (Analysis Experiment Implementation) 修复实现
    → 或回溯到 S19 (Analysis Experiment Design) 重新设计

如果 S34 (Internal Review, Logic Critic) 发现方法论描述不清
    → 回溯到 S06 (Methodology Design) 重新设计
    → 如果方法本身有问题，回溯到 S04 (Hypothesis Generation)

如果 S36 (Revision Loop, Novelty Critic) 指出遗漏关键相关工作
    → 回溯到 S02 (Literature Survey) 补充文献
    → 如果核心想法已被做，回溯到 S04 (Hypothesis Generation)

如果 S36 (Revision Loop, Ethics Critic) 发现数据隐私问题
    → 回溯到 S07 (Benchmark Selection) 更换数据集
```

**回溯不是全盘推翻。** Conductor 会记录哪些部分需要修改，保留无需修改的部分，最小化回溯成本。

---

## 4. 文档规范

### 4.1 知识文档命名规范

```
knowledge/
├── S01_topic_analysis.md           # Stage 产出
├── S02_literature_survey.md
├── S03_research_question.md
├── S04_hypothesis_generation.md
├── S05_novelty_feasibility.md
├── handoff_P1_to_P2.md             # Phase 间传递文档
├── S06_methodology_design.md
├── ...
├── handoff_P6_to_P7.md
└── reviews/
    ├── G1_logic_review.md          # Gate 审查报告
    ├── G1_novelty_review.md
    ├── G2_logic_review.md
    └── ...
```

### 4.2 传递文档 (Handoff Document) 结构

每个 Phase 结束时，产出一个 `handoff_P{X}_to_P{Y}.md`，包含：

```markdown
# Handoff: Phase X → Phase Y

## 已完成的工作摘要
（3-5 句话概括本 Phase 的核心产出）

## 关键决策记录
- 决策1：选择了方案 A 而非方案 B，原因：...
- 决策2：...

## 传递给下游的核心信息
- 关键发现：...
- 核心假设：...
- 验证状态：...

## 已知风险与限制
- 风险1：...
- 缓解措施：...

## 下游需要特别注意的事项
- 注意1：...
- 注意2：...

## 回溯历史
- 本 Phase 经历了 N 次回溯，原因：...
```

### 4.3 状态文件 (pipeline_state.yaml)

```yaml
project:
  name: "string"
  topic: "string"
  created_at: "ISO8601"
  
current:
  phase: "P1"          # 当前 Phase
  stage: "S01"         # 当前 Stage
  status: "in_progress" # in_progress | waiting_gate | waiting_review | halted | completed
  
history:
  - stage: "S01"
    agent: "literature"
    started_at: "..."
    completed_at: "..."
    output: "knowledge/S01_topic_analysis.md"
    gate_result: "pass"
    
backtrack_log:
  - from: "S16"
    to: "S11"
    reason: "结果不可复现，代码存在随机种子问题"
    timestamp: "..."
    
spiral_count:
  P1: 1    # Phase 1 经历了 1 次（无回溯）
  P2: 1
  P3: 2    # Phase 3 经历了 2 次（回溯过一次）
  
agents:
  literature:
    status: "idle"
    last_invoked: "..."
  ideation:
    status: "idle"
    last_invoked: "..."
  # ...
  
gates:
  G1:
    status: "passed"
    critics: ["logic", "novelty"]
    scores:
      logic: "8/10"
      novelty: "7/10"
    notes: "..."
```

---

## 5. Agent 目录结构

每个子 Agent 都有独立的目录，包含自己的身份定义：

```
AGENTS/
├── conductor/
│   └── AGENT.md          # 主控 Agent 的身份和流程规则
├── literature/
│   └── AGENT.md          # 文献调研 Agent
├── ideation/
│   └── AGENT.md          # 想法生成 Agent
├── method/
│   └── AGENT.md          # 方法论设计 Agent
├── experiment/
│   └── AGENT.md          # 实验执行 Agent
├── analysis/
│   └── AGENT.md          # 结果分析 Agent
├── writing/
│   └── AGENT.md          # 论文写作 Agent
├── figure/
│   └── AGENT.md          # 图表生成 Agent
├── critic/
│   ├── AGENT.md          # Critic 团队总览（含 Gate 调用策略）
│   ├── logic/
│   │   └── AGENT.md      # 逻辑审查 Agent
│   ├── method/
│   │   └── AGENT.md      # 方法审查 Agent
│   ├── evidence/
│   │   └── AGENT.md      # 证据审查 Agent
│   ├── writing/
│   │   └── AGENT.md      # 写作审查 Agent
│   ├── novelty/
│   │   └── AGENT.md      # 新颖性审查 Agent
│   └── ethics/
│       └── AGENT.md      # 伦理审查 Agent
└── review/
    └── AGENT.md          # 模拟审稿 Agent
```

---

## 6. MD 收发规范

所有 Agent 之间的知识流转遵循 `docs/07_MD_PROTOCOL.md` 中定义的规范：

### 产出规范 (Output Protocol)
- 遵循 **Universal Document Schema**：Metadata → 核心内容 → Reasoning Trail → 验证检查 → 风险与限制 → 下游接口 → 回溯触发器 → 附录
- 包含完整的 **Metadata**（Stage、Agent、Version、DependsOn、Status）
- **下游接口**章节：明确传递给下游的 3-5 个关键信息
- **回溯触发器**章节：预判下游可能的问题

### 接收规范 (Input Protocol)
- 9 步解析流程：存在性检查 → 元数据解析 → 内容提取 → 推理审查 → 验证确认 → 风险加载 → 下游接口提取 → 回溯触发器检查 → 一致性交叉验证
- Agent **专属提取清单**：不同 Agent 关注不同信息
- **数值一致性验证**：确保跨文档数值一致
- **异常报告机制**：发现问题时立即报告

---

## 7. 与其他工作流的差异

| 特性 | SpiralResearch | ARIS | PaperOrchestra | AutoResearchClaw | ai-research-skills |
|------|---------------|------|----------------|------------------|-------------------|
| **核心哲学** | 螺旋向前 + 三层批判 | 对抗协作 | 5-Agent 管道 | 23-Stage 管道 | 双循环架构 |
| **执行Agent** | 7 | 2+ | 5+1 | 多子系统 | 1+N skills |
| **批判机制** | **37 Stage Inspector + 6维度Critic + 2 Meta Critic** + Review | 交叉模型审查 | Content Refinement | Critic Agent | 自我审查 |
| **知识流转** | **规范MD + 收发协议** | SKILL 调用 | 文件管道 | stage-{N}/ 目录 | findings.md |
| **回溯机制** | 显式 Backward Propagation | 重新运行 skill | 无（线性） | --from-stage | Outer Loop 转向 |
| **Gate检查** | **Stage Inspector(每Stage) + 多Critic并行(Gate)** | 部分有 | 无 | Stage 5,9,20 | 无 |
| **Agent身份** | 独立 AGENT.md | SKILL.md | SKILL.md | 代码定义 | SKILL.md |
| **主控方式** | Conductor 编排 | 用户触发 skill | Orchestrator | Pipeline Runner | 双循环 |
| **MD规范** | **产出+接收双轨 + Stage Inspector格式审查** | 无 | 无 | 无 | 无 |
| **实验优化** | **AutoResearch 风格迭代循环（git+empirical critique）** | 无 | 无 | 无 | 快速迭代 |
| **写作优化** | **PaperOrchestra 5-step（single-call multimodal+accept/revert）** | 无 | 5-step pipeline | 无 | 无 |
| **双循环** | **Inner Loop + Outer Loop** | 无 | 无 | 无 | **findings.md + Outer Loop** |
| **检查器** | **Orphan Cite Gate + Anti-Leakage + LaTeX Sanity** | 无 | 3 deterministic helpers | 无 | 无 |

---

## 8. 从现有工作流学习的关键优化

SpiralResearch 不是闭门造车，而是积极吸收现有成熟工作流的核心优势，将其适配到我们的 36-Stage + 3-Layer Critic 框架中。

### 8.1 AutoResearch 风格：实验的 Inner Loop（P3 Execution）

来自 `autoresearch` 的核心洞见：**实验不是一次性的，而是一个由结果自动驱动的 tight loop**。

**在 SpiralResearch 中的体现**：
- **Experiment Agent** 在 S13（Experiment Execution）中运行一个自主迭代探索循环：
  ```
  modify code → git commit → run iteration (budgeted full run, 5-30min) → evaluate metric → 记录结果
  ```
- **Analysis Agent** 在 S15（Preliminary Analysis）中执行 AutoResearch 的评估决策：
  ```
  深入分析所有实验结果 → 数据质量检查 → 可靠性评估（过拟合/泄露/稳定性）→ KEEP / DISCARD / FIX
  ```
- **跨 Stage 循环**：S13 只做实验探索（所有尝试保留），S15 做最终评估决策。如果 S15 发现需要修复的问题，触发 Backward Propagation 回溯到 S13 重新执行。
- **Git 作为时间机器**：每个实验尝试都是一个 commit，S15 的评估决策后可以通过回溯实现无损回退
- **Empirical Critique**：S13 用指标引导探索方向，S15 用深入分析做最终判断
- **迭代实验**：默认以完整配置运行，通过时间预算控制单次迭代成本。简化模型仅在有明确验证需求时使用。

这使得 P3 不再是 "跑一次实验"，而是 "在一个受控的跨阶段循环中不断探索→分析→决策→回溯修复直到收敛"。

**关键设计**：S13 不做 `git reset`，所有尝试都保留。S15 是唯一的保留/回退决策点，基于深入分析（而非仅看表面指标）做出可靠判断。

### 8.2 PaperOrchestra 风格：写作的 5-Step Pipeline（P6/P7 Writing）

来自 `paperorchestra` 的核心洞见：**论文写作是一个高度结构化的文件管道，并行化、单次调用、严格 halt rules 能显著提升效率和一致性**。

**在 SpiralResearch 中的体现**：
- **Step 1: Outline**（S25）：先产出结构化的 `outline.json` 风格大纲，后续所有工作围绕大纲展开
- **Step 2: Plotting**（S31）与 **Step 3: Lit Review**（S02/S26）**并行**：Figure Agent 和 Literature Agent 同时工作
- **Step 4: Single Multimodal Call**（S32）：Writing Agent 一次性消费大纲+图表+文献综述，生成完整论文草稿
  - 避免多次调用导致的风格断裂和逻辑矛盾
  - 图表作为多模态输入直接 "看" 到
- **Step 5: Content Refinement**（S35）：Review Agent 与 Writing Agent 迭代
  - **Accept/Revert Halt Rules**：修改后总体评分必须提升或持平且无 regressions，否则 revert
  - 每次修改前保存快照，确保 revert 真实可行
- **确定性检查器**：Writing Critic 运行 `orphan cite gate`、`anti-leakage check`、`LaTeX sanity check`
- **Anti-Leakage Prompt**：所有写作 LLM 调用前强制附加

### 8.3 ai-research-skills 风格：双循环架构

来自 `ai-research-skills` 的核心洞见：**研究需要 Inner Loop（快速执行）和 Outer Loop（元反思）的结合**。

**在 SpiralResearch 中的体现**：
- **Inner Loop**：
  - P3 Execution 的 AutoResearch 实验循环
  - P6/P7 的 PaperOrchestra 内容精炼循环
- **Outer Loop**：
  - Analysis Agent 在 P5 Synthesis 阶段综合所有 findings，写入 `spiral_log.md`
  - 如果 Outer Loop 发现研究方向有问题（例如核心假设被否定），触发跨 Phase Backward Propagation
  - Conductor 定期评估 "我们是否还在正确的轨道上？"

### 8.4 ARIS 风格：对抗性协作与引用纪律

来自 `aris` 的核心洞见：**不同模型之间的对抗能发现单模型看不到的盲点**。

**在 SpiralResearch 中的体现**：
- **三层 Critic 本身就是对抗性的**：Stage Inspector 抓具体错误，Dimension Critic 抓专业盲区，Meta Critic 抓系统级问题
- **Review Agent 的 3-Reviewer Simulation**：Reviewer A（方法）、Reviewer B（实验）、Reviewer C（写作）从不同角度 "攻击" 论文
- **引用纪律**：所有 claim 必须有引用支撑，Orphan Cite Gate 严格把关

### 8.5 Agent 工具策略

SpiralResearch 使用原生 subagent 策略进行多 Agent 调度。

框架中所有多 Agent 调度都基于 `Agent` 工具（通过 `Agent(subagent_type=...)` 调用子 Agent）：

**调度方式**：
- Conductor 使用 `Agent` 工具创建/恢复子 Agent 实例
- 子 Agent 独立运行，完成后返回结果给 Conductor
- 复杂任务可启动多个子 Agent 并行执行（如 Gate 时多个 Critic 同时审查）
- 所有 Agent 的身份和能力定义在 `AGENTS/{role}/AGENT.md` 中

---

## 9. 实现路线图

### Phase 1: 框架设计（已完成）
- [x] 分析现有工作流
- [x] 编写架构设计文档
- [x] 编写所有 Agent 定义（含 6 个专业 Critic）
- [x] 编写 Stage 详细设计
- [x] 编写知识流转规范
- [x] 编写反馈纠错机制
- [x] 编写 MD 收发规范（产出 + 接收）

### Phase 2: 最小可运行原型
- [x] 实现 Conductor Agent 的核心编排逻辑（文档级）
- [x] 实现 3-5 个核心子 Agent（文档级）
- [x] 实现 P1-P3 的最小流程（文档级）
- [x] 实现 Gate 和 Backward Propagation（文档级）

### Phase 3: 完整流程（当前）
- [ ] 实现可运行的 Conductor Agent（代码级）
- [ ] 实现全部 17 个 Agent（代码级）
- [ ] 打通 P1-P7 的端到端自动化
- [ ] 集成 Agent 工具进行真实运行测试

### Phase 4: 优化与硬化
- [ ] 添加确定性辅助脚本（验证、检查、格式化）
- [ ] 添加更多 fallback 机制
- [ ] 性能优化与成本控制
- [ ] 文档完善

---

## 10. 命名与术语

| 术语 | 含义 |
|------|------|
| **Conductor** | 主编排 Agent，负责流程控制 |
| **Stage** | 工作流的最小原子单位，有明确的输入输出 |
| **Phase** | Stage 的逻辑分组，对应科研的一个大阶段 |
| **Gate** | Phase 之间的质量检查点，由 Critic Team 并行审查 |
| **Handoff** | Phase 之间的知识传递文档 |
| **Backward Propagation** | 发现上游错误时的回溯机制 |
| **Spiral** | 一轮完整的 Phase 1→8 执行 |
| **Critic Team** | 三层: 37 Stage Inspector + 6 Dimension Critic + 2 Meta Critic |
| **Review** | 模拟同行评审 Agent |
| **MD Protocol** | Markdown 收发规范（产出 + 接收） |
| **Inner Loop** | 快速迭代循环（如实验优化、内容精炼） |
| **Outer Loop** | 元反思循环（如研究方向调整、findings synthesis） |
| **Orphan Cite Gate** | 检查引用是否在 bib 中存在对应条目的确定性检查器 |
| **Anti-Leakage** | 防止 LLM 输出泄露训练数据或复制已知论文的机制 |
| **Single Multimodal Call** | 一次性消费文本+图像输入生成完整论文草稿的写作策略 |

---

## 11. 文档索引

| 文档 | 内容 |
|------|------|
| `01_ARCHITECTURE.md` | 总体架构设计（本文档） |
| `02_CONDUCTOR_AGENT.md` | Conductor Agent 详细设计 |
| `03_SUB_AGENTS.md` | 子 Agent 团队概览 |
| `04_STAGES.md` | 37 个 Stage 详细设计 |
| `05_KNOWLEDGE_FLOW.md` | 知识流转规范 |
| `06_FEEDBACK_LOOP.md` | 反馈与纠错机制 |
| `07_MD_PROTOCOL.md` | Markdown 收发规范（产出 + 接收） |

---

> **下一步**: 阅读 `04_STAGES.md` 了解 37 个 Stage 的详细设计，然后阅读 `06_FEEDBACK_LOOP.md` 了解 Inner/Outer Loop 的反馈机制。
