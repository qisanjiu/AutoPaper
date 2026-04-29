---
name: autopaper
description: |
  全自动端到端科研框架 SpiralResearch (AutoPaper)。将科研全流程分解为
  8 Phase × 37 Stage，通过多 Agent 协作与三层 Critic 机制产出投稿质量论文。
  当用户提及 AutoPaper、SpiralResearch、螺旋科研、全自动科研、自动写论文、
  自动投稿、帮我研究 XXX、运行 P3/S11、推进到 S25、创建新项目、查看项目状态、
  切换 venue，或要求创建/推进/回溯/审查研究项目时触发。
---

# 执行 SpiralResearch (AutoPaper) 全自动科研流程

## 牢记核心架构

```
8 Phases × 37 Stages

P1 Discovery       S01-S05   选题、文献、假设
P2 Design          S06-S10   方法设计、实验计划（含 subagent 检验）
P3 Execution       S11-S13   代码、实验迭代探索、结果验证
P4 Ablation        S14-S17   消融设计、代码、执行、分析
P5 Further Analysis S18-S21  进一步分析实验现象
P6 Synthesis       S22-S25   Claim-Evidence 映射、洞察提炼、贡献阐述
P7 Writing         S26-S33   论文各 section 写作
P8 Refinement      S34-S36,S37  审稿、修订、编译提交

Gate G1-G8: S05, S10, S13, S17, S21, S25, S33, S37
```

注意：共 37 个 Stage（S01-S37 连续）。

## 使用项目目录结构

框架代码根目录：`.`（即本 SKILL.md 所在目录的父目录的父目录，`AutoPaper/`）

```
{FrameworkRoot}/
├── spiral/              Python 核心模块 (PipelineState, PHASE_STAGES, ...)
├── scripts/
│   └── state_manager.py 主 CLI 工具
├── docs/
│   ├── 01_ARCHITECTURE.md
│   ├── 04_STAGES.md       Stage 详细设计
│   ├── 07_MD_PROTOCOL.md  文档规范
│   └── AGENTS/            Agent 身份定义
├── config/venue_registry.yaml
└── templates/venue/       LaTeX 模板

所有项目存放于：{FrameworkRoot}/../projects/ （即框架根目录的父目录下的 projects/ 文件夹）
└── {project-name}-{timestamp}/
    ├── S01/ ~ S37/        Stage 产出目录
    ├── state/
    │   └── pipeline_state.yaml   当前 Stage/Phase/Status
    ├── knowledge/         Stage 产出 & handoff 文档
    ├── artifacts/         论文 PDF、LaTeX 模板
    └── experiments/       代码、数据、结果
```

## 首先执行多项目管理

执行任何项目操作前，先调用 `list-projects` 确认用户指的是哪个项目。

```bash
# 所有命令均在框架根目录（包含 scripts/ 的目录）下执行
# 列出所有项目
python scripts/state_manager.py list-projects

# 设置默认项目（持久化到 ~/.spiral/current_project）
python scripts/state_manager.py use ../projects/PROJECT-NAME

# 单次命令指定项目
python scripts/state_manager.py --project /path status
```

完整 CLI 语法见 [references/commands.md](references/commands.md)。

## 按以下步骤推进 Stage

### 1. 读取当前状态

```python
from spiral.state import PipelineState
from pathlib import Path

state = PipelineState(Path(project_dir))
current_stage = state.get_current_stage()   # e.g. "S01"
current_phase = state.get_current_phase()   # e.g. "P1"
status = state.get_current_status()         # e.g. "in_progress"
```

`pipeline_state.yaml` 关键字段：
```yaml
current:
  phase: "P1"
  stage: "S01"
  status: "in_progress"   # initialized | in_progress | phase_completed | completed
phases:
  P1: {status: "pending", completed_at: null, last_stage: null}
  # ... P1-P7
project:
  name: "..."
  topic: "..."
  venue: {id: "arxiv", name: "arXiv", page_limit: null, ...}
history: []    # 已完成 Stage 记录
backtrack_log: []
```

### 2. 确定负责 Agent

```python
from spiral.project import AGENT_FOR_STAGE, PHASE_STAGES, GATE_STAGES

agent_role = AGENT_FOR_STAGE[current_stage]     # e.g. "literature"
# 快速确认当前 Stage 是否是 Gate Stage
gate_stages = set(GATE_STAGES.values())
```

各 Stage 对应的 Agent 见 [references/stages.md](references/stages.md)。
Agent 与 Critic 的详细定义见 [references/agents.md](references/agents.md)。

### 3. 读取 Agent 定义与 Stage 检查清单

```
# Agent 身份定义
docs/AGENTS/{role}/AGENT.md

# Stage 专属检查清单（Critic 审查用）
docs/AGENTS/critic/stage/inspectors/S{NN}.md
```

### 3.5 验证全局配置（实验类和写作类 Stage 前强制）

**在创建 experiment Agent 前（S11-S12, S14-S16, S20）**：
```python
from spiral.env_config import load_env_config, check_env_config
from pathlib import Path

project_dir = Path("{project_dir}")
ok, msg = check_env_config(project_dir)
if not ok:
    # 报告用户：环境配置缺失，需要填写 {project_dir}/config/environment.yaml
    # 不得继续创建 experiment Agent
```
- 确认 `{project_dir}/config/environment.yaml` 存在且关键字段非空（项目创建时已从全局默认复制）
- 如验证失败，**向用户报告**具体缺失字段，等待用户填写后再继续

**在创建 writing Agent 前（S26-S31, S33, S36, S37）**：
- 确认 `config/author_info.yaml` 存在（S26 和 S37 必须）
- 确认 `artifacts/latex_template/` 下有 venue 模板文件（.sty / .cls / .bst）
- 如关键文件缺失，**向用户报告**，不得跳过

### 4. 准备输入文档

```python
from scripts.conductor_helper import get_input_docs
inputs = get_input_docs(Path(project_dir), current_stage)
```

**附加配置文档到 input_docs**：
- **实验类 Stage（S11-S12, S14-S16, S20）**：追加 `{project_dir}/config/environment.yaml` 路径到输入文档列表
- **写作类 Stage（S26-S31, S33, S36, S37）**：追加 `{project_dir}/config/author_info.yaml` 和 `{project_dir}/artifacts/latex_template/` 路径
- 配置文件在项目创建时从 AutoPaper 全局默认复制到项目本地，可独立修改

### 5. 创建子 Agent 并执行

#### 5.1 子 Agent Prompt 模板

通过 Agent 工具创建子 Agent 时，使用以下 prompt 结构：

```
你是 {role} Agent，负责执行 Stage {stage}：{stage_name}。

## Context Recovery（首次必做）
1. 读取 AGENT.md：ReadFile(path="{framework_root}/docs/AGENTS/{role}/AGENT.md")
2. 读取 MD 协议：ReadFile(path="{framework_root}/docs/07_MD_PROTOCOL.md")
3. 读取当前状态：ReadFile(path="{project_dir}/state/pipeline_state.yaml")

## 任务目标
{该 Stage 的核心产出目标，参考 docs/04_STAGES.md}

## 输入文档
{input_docs 列表，使用绝对路径}

## 输出要求
- 描述文档：{project_dir}/knowledge/S{NN}_{stage_name}.md
- 实际文件（如适用）：{project_dir}/experiments/src/*.py, {project_dir}/artifacts/draft.tex 等
- 必须遵循 docs/07_MD_PROTOCOL.md 的双产出协议

## 全局配置文件（按 Stage 类型附加）
### 实验类 Stage（S11-S12, S14-S16, S20）— 附加以下内容：
- **必须读取项目本地实验环境配置**：ReadFile(path="{project_dir}/config/environment.yaml")
  - 确认运行模式（local / remote_ssh / remote_slurm）
  - 确认 Python 路径、GPU 设备、时间预算
  - 如果关键字段为空或文件不存在，立即报告 Conductor，不要自行假设
- 实验代码必须在配置指定的环境中运行
- 迭代循环的终止条件以 general.iteration_time_budget 和 general.max_iterations 为准

### 写作类 Stage（S26-S31, S33, S36, S37）— 附加以下内容：
- **必须读取作者信息**：ReadFile(path="{project_dir}/config/author_info.yaml")
  - S26（大纲）阶段：确认作者列表，规划论文中的作者区块位置
  - S37（最终编译）阶段：将作者信息填入论文 .tex 文件
- **必须使用项目 Venue 模板**：{project_dir}/artifacts/latex_template/ 目录下的 .sty/.cls/.bst 文件
  - 在 .tex 文件中引用本地模板文件（不使用系统全局安装的版本）
  - 严格遵循模板的 \documentclass 和 \usepackage 设置
- **Anti-Leakage Prompt 强制应用**（见下方）

## 约束条件
- Venue: {从 pipeline_state.yaml 读取的 venue 信息}
- {页数限制、Anonymous 要求等}
- {Anti-Leakage Prompt，如果是写作类 Stage}
- {Learned Experience，如果 docs/LEARNED/ 中有相关记录}

## 完成标准
- {该 Stage 具体的验证检查清单}
- 完成后不要自行推进，等待 Conductor 验证
```

#### 5.1.1 路径传递规范（强制）

**所有传递给子 Agent 的路径必须是绝对路径。** 子 Agent 的 CWD 不可控，相对路径在不同 CWD 下会解析到错误位置。

- `{project_dir}`：始终使用 `Path(project_dir).resolve()` 后的绝对路径
- `{framework_root}`：始终使用 `Path(__file__).parent.parent.resolve()` 后的绝对路径
- 在子 Agent prompt 中的 `ReadFile(path="...")` 路径，使用上述绝对路径拼接
- 框架内的相对路径（如 `docs/AGENTS/.../AGENT.md`）必须用 `{framework_root}/docs/AGENTS/.../AGENT.md`（绝对路径形式）传递
- **禁止在子 Agent prompt 中使用 `../projects/...` 或 `config/environment.yaml` 等相对路径**

#### 5.2 子 Agent 类型与参数

| Agent Role | 执行 Stage | AGENT.md 路径 | 特殊约束 |
|-----------|-----------|---------------|---------|
| literature | S01, S02 | `docs/AGENTS/literature/AGENT.md` | 多源检索、μGap 识别 |
| ideation | S03, S04, S05, S25 | `docs/AGENTS/ideation/AGENT.md` | FINER 标准、可证伪性 |
| method | S06, S07, S08, S09, S10 | `docs/AGENTS/method/AGENT.md` | 方案库优先、变量隔离 |
| experiment | S11, S12, S14, S15, S16, S20 | `docs/AGENTS/experiment/AGENT.md` | AutoResearch 循环、**必须读项目本地 config/environment.yaml** |
| analysis | S13, S17, S18, S19, S21, S22, S23 | `docs/AGENTS/analysis/AGENT.md` | 统计检验、Claim-Evidence |
| writing | S24, S26-S31, S33, S36, S37 | `docs/AGENTS/writing/AGENT.md` | Anti-Leakage、PaperOrchestra 5-step、**必须读 author_info.yaml + 使用 artifacts/latex_template/** |
| figure | S32 | `docs/AGENTS/figure/AGENT.md` | 4-stage plotting pipeline |
| critic_team | S34 | `docs/AGENTS/critic/AGENT.md` | 5-dimension review |
| review | S35 | `docs/AGENTS/review/AGENT.md` | 3-reviewer simulation |

#### 5.3 并行 vs 串行调用

| 场景 | 策略 | 说明 |
|------|------|------|
| **Gate Critic 审查** | **并行** | G1-G8 的 Dimension Critics 相互独立，可并行调用 |
| **S26 + S32** | **并行** | Paper Outline 和 Figure Generation 可并行执行 |
| **同一 Phase 内的 Stage** | **串行** | 每个 Stage 依赖前一个 Stage 的产出 |
| **S27-S31 各 Section** | **可部分并行** | S27 Intro+Related Work 完成后，S28-S31 可独立并行写作 |
| **专项检查 (Code Review / Data Checker / Build Verifier)** | **串行于对应 Stage 后** | 在 Stage 产出完成后立即调用 |

#### 5.4 Context Window 管理

- 子 Agent 创建时只传递**必要的输入文档**，不传递完整项目上下文
- 每个子 Agent prompt 应控制在 ~2000 tokens 以内（不含输入文档）
- 输入文档总长度不宜超过子 Agent 上下文窗口的 70%
- 如输入文档过多，在 prompt 中**列出文件路径**让子 Agent 自行读取，而非内嵌全文

**Anti-Leakage Prompt（任何生成论文内容的 LLM 调用前必须附加）：**
```
Anti-Leakage Instruction:
You must not reproduce or closely paraphrase any copyrighted text,
including but not limited to: textbook explanations, Wikipedia passages,
or source code from existing implementations. Generate all explanations,
descriptions, and code from first principles or using your own words.
Cite sources using [Author, Year] format but do not copy their prose.
```

**Academic Style Prompt（写作类 Stage 的 LLM 调用前必须附加）：**
> **同步注意**：此 Prompt 与 `docs/AGENTS/writing/AGENT.md` §5.6 保持同步。完整风格参考手册见 AGENT.md §5.6。修改任一处时，必须同步更新另一处。
```
Academic Style Instruction:
You are writing for a top-tier academic venue (NeurIPS, ICML, ICLR, ACL, CVPR, etc.).
Your output must use formal academic English throughout. The following are ABSOLUTELY FORBIDDEN:
- Contractions: don't, can't, won't, isn't, it's, we're, etc. → Expand all to full forms.
- Colloquial transitions: "Let's dive into", "Now, let's talk about", "First up", "Next up" → Use formal transitions.
- Blog-style question subheadings: "Why LOSO-CV?", "What went wrong?" → Use declarative headings.
- Informal emphasis: "a lot of", "really", "very", "huge", "massive" → Use "substantial", "considerable", "significant".
- Bullet lists as paragraph substitutes → Use proper prose paragraphs with topic sentences.
- Single-sentence paragraphs (except immediately after math definitions/algorithm blocks).
Every paragraph must have a topic sentence. Every claim must use appropriate academic hedging
("suggests", "indicates", "provides evidence") rather than absolute declarations ("proves", "demonstrates conclusively").
All content must be written in LaTeX format: \\section{}, \\cite{}, \\ref{}, \\begin{table} with booktabs, etc.
Tables must use \\toprule, \\midrule, \\bottomrule. Figures must use \\label and \\ref for automatic numbering.
Use ~ to prevent line breaks before \\ref and \\cite (e.g., Figure~\\ref{fig:xxx}, Section~\\ref{sec:xxx}).
```

### 6. 验证产出

#### 6.1 自动化验证工具

根据 Stage 类型执行相应的验证：

| 验证类型 | 工具/命令 | 适用 Stage |
|---------|----------|-----------|
| LaTeX 编译 | `python utils/latex_sanity.py artifacts/draft.tex` | S33, S37 |
| Orphan Cite 检查 | `python utils/orphan_cite_gate.py artifacts/draft.tex artifacts/refs.bib` | S33, S37 |
| Anti-Leakage 检查 | `python utils/anti_leakage_check.py knowledge/S{NN}_*.md` | S26-S33, S36, S37 |
| MD 格式验证 | `python utils/md_validator.py knowledge/S{NN}_*.md` | 所有 Stage |

LaTeX 编译必须执行多次：`pdflatex → bibtex → pdflatex × 2`

#### 6.2 专项检查子 Agent

对于特定关键 Stage，创建专项检查子 Agent 进行深度验证：

| Stage | 检查子 Agent | AGENT.md | 检查重点 |
|-------|------------|----------|---------|
| S11 (代码生成) | **Code Review Agent** | `docs/AGENTS/critic/code_review/AGENT.md` | 代码正确性、可复现性、安全性 |
| S12 (实验执行) | **Data Quality Checker** | `docs/AGENTS/critic/data_checker/AGENT.md` | 数据完整性、过拟合、数据泄露、训练稳定性 |
| S15 (消融代码生成) | **Code Review Agent** | `docs/AGENTS/critic/code_review/AGENT.md` | 消融代码正确性、变量隔离、与主实验一致性 |
| S33 (草稿整合) | **Build Verifier** | `docs/AGENTS/build_verifier/AGENT.md` | LaTeX 编译、Orphan Cite、Anti-Leakage、图表完整性 |
| S37 (最终编译) | **Build Verifier** | `docs/AGENTS/build_verifier/AGENT.md` | 上述全部 + 提交包验证、匿名化检查 |

专项检查子 Agent 的创建 prompt 模板：
```
你是 {checker_role}，负责对 Stage {stage} 的产出进行专项验证。

## Context Recovery
1. 读取 AGENT.md：ReadFile(path="docs/AGENTS/{checker_path}/AGENT.md")
2. 读取 MD 协议：ReadFile(path="docs/07_MD_PROTOCOL.md")

## 检查对象
- Stage: {stage}
- 产出文件: {output_files}
- 检查时间: {timestamp}

## 检查要求
按照你的 AGENT.md 中定义的检查清单，逐项验证并输出标准格式的审查报告。
```

### 7. 标记完成并推进

```bash
python scripts/state_manager.py advance <stage> <agent> <output_file>
```

- 若 `stage` 是 Gate Stage，自动标记当前 Phase 为 completed
- 若 `stage` 是 S37（最终 Stage），自动标记项目为 completed

## 执行 Gate 审查

每个 Phase 最后一个 Stage 完成后必须执行 Gate：

1. 确认 Gate 位置：`GATE_STAGES` 映射
2. 并行调用 2-3 个 Dimension Critic（Logic/Method/Evidence/Writing/Novelty/Ethics）
3. 每个 Critic 读取 `docs/AGENTS/critic/stage/inspectors/S{NN}.md` 检查清单
4. 聚合结果为 **PASS / REVISE / BACKTRACK / HALT**
5. 决策：
   - **PASS** → 推进到下一 Phase 的第一个 Stage
   - **REVISE** → 问题局限于当前 Stage/Phase，在当前范围内修改后重新 Gate
   - **BACKTRACK** → 根因在前序 Phase，执行以下完整流程：
     1. 调用 `state_manager.py backtrack <from> <to> <reason>` 设置回溯状态
     2. **修改回溯目标 Stage**（to_stage），携带「回溯修改方向」
     3. **逐个重新执行所有下游 Stage**（to_stage+1, to_stage+2, ... 直到 Gate Stage）
        - 每个下游 Stage 必须检查：上游修改是否影响本阶段
        - 每个 Stage 完成后 advance 到下一个
     4. **重新触发受影响的 Gate 审查**（包括回溯路径上所有 Phase 的 Gate）
     5. 聚合 Gate 结果 → 决定 PASS / REVISE / 继续 BACKTRACK / HALT
     - **关键**：不是修改完目标 Stage 就跳回原位置；不是只重新跑 Gate 不跑中间 Stage。
       必须完整重走 "目标 Stage → 下游 Stage 逐个 → Gate" 的全路径。
   - **HALT** → 无法继续，向用户报告并等待指示

Critic Team 三层架构和 Dimension Critic 详细定义见 [references/agents.md](references/agents.md)。

## 回溯流程核心原则（BACKTRACK = 修改目标 → 重走全链路 → Gate）

**回溯后的执行流程是：修改回溯目标 Stage → 从目标 Stage 继续向下逐个重新执行所有下游 Stage → 重新过所有受影响的 Gate。**

```
示例：S13 发现方法架构问题，回溯到 S06

❌ 错误做法：修改 S06 → 直接跳回 S13（S07-S12 基于旧设计，会产生下游不一致）
❌ 错误做法：修改 S06 → 只重新跑 G2（S07-S13 没有根据新设计更新）
✅ 正确做法：修改 S06 → S07 → S08 → S09 → S10 → Gate G2 → S11 → S12 → S13 → Gate G3
```

**流程步骤**：
1. `state_manager.py backtrack <from> <to> <reason>` — 设置当前 Stage=to，标记下游为 stale，标记 Gate 需重审
2. 修改回溯目标 Stage（to_stage），传入「回溯修改方向」
3. 逐个重新执行下游 stale Stage（stale_stages 列表）
4. 重新触发所有标记为 `needs_re_review` 的 Gate
5. 所有 Gate 通过后，从最终位置继续推进

**原则**：任何时刻，回溯目标 Stage 之前的所有 Stage 必须基于**同一版本**。不允许 "S06 是 v2 但 S07 还是基于 S06-v1" 的状态。

## 管理 Venue

```bash
# 查看所有 venue
python scripts/state_manager.py list-venues

# 切换 venue（自动重新复制 LaTeX 模板）
python scripts/state_manager.py set-venue <venue_id>
```

Venue ID 可选值：`arxiv` (默认), `neurips`, `icml`, `iclr`, `acl`, `cvpr`, `ieee_trans`

注册表：`config/venue_registry.yaml`

## 强制执行 Context Recovery

**每次上下文被压缩后，执行任何操作前按顺序完成以下步骤：**

1. ✅ 本 Skill 已自动加载
2. 读取 Conductor Agent 定义：`ReadFile(path="docs/AGENTS/conductor/AGENT.md")`
3. 读取 MD Protocol：`ReadFile(path="docs/07_MD_PROTOCOL.md")`
4. 读取当前项目状态：`ReadFile(path="{project_dir}/state/pipeline_state.yaml")`
5. 读取决策日志：`ReadFile(path="{project_dir}/state/decision_log.md")`
6. 读取螺旋日志：`ReadFile(path="{project_dir}/state/spiral_log.md")`

每步确认成功后再执行下一步。

## 支持人类介入审查（Human-in-the-Loop Gate）

默认运行模式：**AUTO_PROCEED**，Gate 自动通过，不打扰用户。

用户可以随时自发介入，无需等待 Conductor 提问。识别以下触发模式：

| 用户说法 | 含义 | 操作 |
|---------|------|------|
| "审查 S05" / "看看 S05 的产出" | 用户想审查 S05 | 读取 S05 产出，展示给用户 |
| "S05 有问题" / "S05 需要修改" | 用户发现问题 | 记录意见 → REVISE → 重置到 S05 |
| "S05 假设不成立" | 具体修改意见 | 记录意见 → REVISE → 重置到 S05 并传入反馈 |
| "通过" / "没问题" | 用户确认通过 | 记录 PASS，继续推进 |
| "回到 S04" | 用户要求回溯 | 执行 backtrack 到 S04 |

### 介入后的处理流程

1. **记录用户意见**：保存到 `knowledge/reviews/human_S{NN}_review.md`
2. **执行 verdict**：
   - `pass` — 记录通过，继续推进
   - `revise` — 重置当前 Stage 为 `in_progress`，重新执行该 Stage（携带用户反馈）
   - `backtrack` — 回溯到指定 Stage（执行 `state_manager.py backtrack`），然后：
     a) 修改回溯目标 Stage N（携带用户反馈）
     b) 逐个重新执行 N+1, N+2, ... 直到 Gate Stage
     c) 重新触发受影响的 Gate 审查
3. **重新执行 Stage**：将用户反馈作为约束传入子 Agent
4. **继续推进**：Gate 重审通过后继续正常流程

### CLI 命令

```bash
# 提交审查意见（默认 verdict=revise）
python scripts/state_manager.py human-review S05 "假设过于宽泛，需要限定数据集"

# 指定 verdict
python scripts/state_manager.py human-review S05 "假设OK" pass
python scripts/state_manager.py human-review S05 "需要回溯修改方法" backtrack
```

用户可以在**任何时刻**（即使当前已推进到 S20）对**任何已完成的 Stage**（如 S05）提出审查意见，系统将自动回溯并重新执行。

详见 [references/human-gate.md](references/human-gate.md)。

## 经验学习机制（Learning from Mistakes）

每次 Critic 审查或用户介入发现问题后，必须从中学习，避免下次重复。

### 学习流程

1. **问题发生**：Critic / 用户发现某 Stage 存在问题
2. **根因分析**：分析问题为何发生，为何本可提前规避
3. **记录经验**：写入 `docs/LEARNED/` 对应文件
4. **下次预防**：执行同类型 Stage 前，先读取学习笔记，作为约束传递给子 Agent
5. **定期清理**：过时经验按 `clear_after` 规则清除

### 学习笔记存储

```
docs/LEARNED/
├── conductor.md           # 编排经验
├── writing.md             # 写作陷阱
├── experiment.md          # 实验常见错误
└── stage/
    ├── S05.md             # S05 特有陷阱
    └── ...
```

每个文件格式：
```markdown
---
type: learned
learned_from: "project-name"
stage: "S05"
date: "2026-04-20"
clear_after: "3 projects"   # 3个项目后 / 1个月后 / never
severity: high
---

## 问题描述
## 根因分析
## 预防措施
## 验证方法
```

### 使用学习笔记

执行 Stage 前，检查是否存在对应的学习笔记：

```python
learned_file = Path("docs/LEARNED/stage/S05.md")
if learned_file.exists():
    learned = learned_file.read_text()
    # 将 learned 内容作为约束附加到子 Agent prompt
```

**子 Agent prompt 附加约束模板**：
```
[Learned Experience — 必须遵守]
以下是从过往项目中学习到的经验教训。执行本 Stage 时必须遵守，
避免重复相同的错误：

{learned_content}

请在产出中明确说明你已遵守以上预防措施。
```

### CLI 命令

```bash
# 查看所有学习笔记
python scripts/state_manager.py list-learned

# 为当前项目生成学习报告（项目结束时调用）
python scripts/state_manager.py learn-report

# 清除过时的学习笔记
python scripts/state_manager.py clear-learned [--dry-run]
```

详见 [references/learning.md](references/learning.md)。

## 根据用户指令选择操作

| 用户指令 | 操作 |
|---------|------|
| "全自动运行 XXX" / "帮我研究 XXX" / "自动写论文关于 XXX" | `list-projects` → `use`（或 `create`）→ 顺序执行 S01 → S37 |
| "创建新项目 XXX" / "new project" | `create <topic> <display_name> [venue]`（项目自动创建在 `../projects/` 下） |
| "运行 P3" / "执行实验阶段" | **先验证**项目本地 `config/environment.yaml` → 确认 P2 已完成 → 从 S11 执行到 S13（S12 内嵌迭代探索）→ Gate G3 |
| "运行 P4" / "执行消融阶段" | **先验证**项目本地 `config/environment.yaml` → 确认 P3 已完成 → 从 S14 执行到 S17 → Gate G4 |
| "运行 P5" / "执行进一步分析" | **先验证**项目本地 `config/environment.yaml` → 确认 P4 已完成 → 从 S18 执行到 S21 → Gate G5 |
| "从 S26 开始" | 检查 S01-S25 前置状态 → 从 S26 执行 |
| "只写论文"（跳过实验） | **先确认** `config/author_info.yaml` 和 `artifacts/latex_template/` → 确认已有实验结果和 draft → 从 S26 执行到 S37 |
| "查看状态" / "项目状态" | `status` / `phase-status` / `list-projects` |
| "回溯到 S04" | `backtrack S{current} S04 "用户指定原因"` |
| "切换 venue 到 NeurIPS" | `set-venue neurips` → 验证编译和页数 |
| "继续上一个项目" | `list-projects` → `use` → 读取 state → 继续当前 Stage |
| "审查 S05" / "S05 有问题" | `human-review S05 "用户意见" [pass\|revise\|backtrack]` |

## 关键文件速查

| 需要了解 | 读取文件 | 何时读取 |
|---------|---------|---------|
| 整体架构 | `docs/01_ARCHITECTURE.md` | 首次使用或恢复上下文 |
| 37 Stages 详细设计 | `docs/04_STAGES.md` | 执行具体 Stage 前 |
| Stage 间知识流转 | `docs/05_KNOWLEDGE_FLOW.md` | 准备输入文档时 |
| 反馈与回溯机制 | `docs/06_FEEDBACK_LOOP.md` | Gate 审查前 |
| 文档规范（双产出协议） | `docs/07_MD_PROTOCOL.md` | 创建子 Agent 前 |
| Agent 职责总览 | `docs/03_SUB_AGENTS.md` | 分配 Agent 时 |
| Conductor 执行细节 | `docs/02_CONDUCTOR_AGENT.md` | 编排复杂 Stage 时 |
| Conductor Agent 定义 | `docs/AGENTS/conductor/AGENT.md` | **Context Recovery 必做** |
| Critic Team 定义 | `docs/AGENTS/critic/AGENT.md` | Gate 审查前 |
| Stage Inspector 通用定义 | `docs/AGENTS/critic/stage/AGENT.md` | Critic 审查时 |
| Code Review Agent | `docs/AGENTS/critic/code_review/AGENT.md` | S11 代码生成后 |
| Data Quality Checker | `docs/AGENTS/critic/data_checker/AGENT.md` | S12 实验执行后 |
| Build Verifier | `docs/AGENTS/build_verifier/AGENT.md` | S33/S37 编译后 |
| Venue 注册表 | `config/venue_registry.yaml` | 创建项目或切换 venue 时 |
| **实验环境配置** | `{project_dir}/config/environment.yaml`（项目本地） | **执行 S11-S20 实验类 Stage 前（必读）** |
| **作者信息** | `config/author_info.yaml` | **执行 S26（大纲）和 S37（最终编译）时（必读）** |
| CLI 命令完整参考 | `references/commands.md`（本 skill） | 需要精确 CLI 语法时 |
| 37 Stages 速查表 | `references/stages.md`（本 skill） | 快速查找 Stage 对应 Agent 时 |
| Agent 与 Critic 详细定义 | `references/agents.md`（本 skill） | 分配 Agent 或执行 Gate 时 |
| 人类介入审查机制 | `references/human-gate.md`（本 skill） | 用户主动介入审查时 |
| 经验学习机制 | `references/learning.md`（本 skill） | 记录或使用学习笔记时 |
