# SpiralResearch — 全自动科研框架

> **版本**: 0.3.0  
> **执行模型**: 原生子 Agent 策略（Agent 工具）  
> **核心哲学**: 螺旋前进、三层批判驱动、经验主义内循环

---

## 使用方式

**您（用户）发号施令 → 我（Conductor）自动执行**

整个科研流程由 Conductor（即我，Root Agent）自动编排。您只需要用自然语言告诉我您的需求，我负责：

1. 创建项目目录和初始化状态
2. 读取当前 Stage 和状态
3. 用 `Agent` 工具创建对应的子 Agent
4. 将子 Agent 的产出保存到项目目录
5. 调用批判机制审查产出
6. 自动推进到下一步或回溯修复

### 自动加载 Skill

本项目内置自动加载 Skill（`.agents/skills/autopaper/`），当用户提及科研相关关键词时自动加载。即使我的上下文被压缩，skill 也能确保我立即掌握：

- 8 Phase × 37 Stage 的完整架构
- 如何创建和管理多项目
- 如何推进 Stage 和执行 Gate 审查
- Context Recovery 强制协议

**触发词**："AutoPaper"、"SpiralResearch"、"螺旋科研"、"全自动科研"、"自动写论文"、"运行 P3"、"执行 S11"、"创建新项目"、"切换 venue"，或任何要求创建/推进/回溯研究项目的指令。

### 执行模式

#### 模式 A：全自动执行（一次性跑完全程）

```
用户: 我想做一个关于"基于深度学习和毫米波雷达的呼吸检测"的研究

Conductor（我）:
→ 在 ../projects/ 创建项目
→ 初始化 pipeline_state.yaml
→ 调用 Literature Agent 执行 S01（文献调研）
→ 保存 S01_topic_analysis.md
→ 调用 Stage Inspector 审查
→ 推进到 S02
→ ...（持续自动执行全部 37 个 Stage）
```

#### 实验环境配置（Phase 3 执行前）

所有研究项目共享**同一个全局环境配置**，位于 AutoPaper 框架根目录：

```
AutoPaper/
├── config/
│   └── environment.yaml      # ← 只需填写一次，所有项目共用
```

在 Phase 3（实验执行阶段）之前，请填写 `{AutoPaper}/config/environment.yaml`：

```yaml
environment:
  mode: "remote_ssh"          # local | remote_ssh | remote_slurm
  remote_ssh:
    host: "192.168.1.100"     # 服务器 IP
    user: "your_username"     # SSH 用户名
    key_file: "~/.ssh/id_rsa" # SSH 私钥路径
    gpu_devices: "0,1"
    setup_commands:
      - "conda activate myenv"
  general:
    iteration_time_budget: 30  # 单次迭代时间预算（分钟）
    total_gpu_budget: 24       # 总 GPU 时间预算（小时）
```

Experiment Agent 在**每次**实验运行前（S13、S18 等）都会读取此全局配置。
如果关键字段为空，会先询问你填写。

> **安全提示**: `config/environment.yaml` 已加入 `.gitignore` —— 该文件可能包含密钥/密码。

#### 模式 B：分 Phase 执行（推荐用于复杂项目）

```
用户: 执行 Phase 1: Discovery（发现阶段）

Conductor（我）:
→ 检查前置条件（P1 无前置依赖）
→ 从 S01 开始，依次执行 S01→S02→S03→S04→S05
→ 通过 Gate G1 审查
→ 停止。汇报："Phase 1 已完成，S05 通过 G1。"
→ 状态设置为 phase_completed
```

```
用户: 执行 Phase 2: Design（设计阶段）

Conductor（我）:
→ 检查前置条件：P1 必须已完成
→ 若 P1 未完成："请先完成 Phase 1。"
→ 若 P1 已完成：从 S06 开始，依次执行 S06→S07→S08→S09→S10
→ 通过 Gate G2 审查
→ 停止。汇报："Phase 2 已完成。"
```

```
用户: 查看 Phase 进度

Conductor（我）:
→ 显示进度表：
  ✅ P1: completed | last=S05 | 2024-01-15 09:30
  ⏳ P2: in_progress | last=S07
  ⬜ P3: pending
  ⬜ P4: pending
  ⬜ P5: pending
  ⬜ P6: pending
  ⬜ P7: pending
  ⬜ P8: pending
```

```
用户: 继续下一步 / 推进到实验阶段 / 回退到 S11 修改代码

Conductor（我）:
→ 读取当前状态
→ 执行您的指令
→ 更新 pipeline_state.yaml
```

```
用户: 现在研究方案确定了，把项目名改成最终论文标题

Conductor（我）:
→ 检查：Phase 2 (Design) 是否已完成？（S10 通过 Gate G2）
→ 若已完成：重命名项目 display_name，更新 state 和日志
→ 若已完成 + 用户要求重命名文件夹：物理重命名文件夹（带 Windows 文件锁定回退机制）
→ 若未完成："Phase 2 完成前不能重命名。研究方向尚未最终确定。"
```

### 多项目管理

可以同时运行多个项目，我会自动追踪当前默认项目。

```
用户: 列出所有项目

Conductor（我）:
→ 显示 ../projects/ 下所有项目表格
→ 展示：名称、当前 Stage、Phase、状态
→ 用 👈 标记当前默认项目
```

```
用户: 切换到呼吸检测项目

Conductor（我）:
→ 设置默认项目为 ../projects/呼吸检测-...
→ 后续命令自动针对该项目
```

```
用户: 查看另一个项目的状态（不切换默认）

Conductor（我）:
→ 使用 --project 参数查询指定项目，不改变默认设置
```

### 人类介入审查

你可以随时自发审查任何已完成的 Stage，无需等我提问。

```
用户: 审查一下 S05

Conductor（我）:
→ 读取项目中的 S05 产出
→ 展示完整内容供你审查
→ 等待你的反馈
```

```
用户: S05 的假设太宽泛了，限定在室内场景

Conductor（我）:
→ 记录你的意见为人类审查
→ 判定：REVISE
→ 重置状态到 S05
→ 携带你的反馈重新执行 S05
→ 完成后从 S05 继续推进
```

```
用户: 回到 S04 重新做

Conductor（我）:
→ 执行从当前 Stage 回溯到 S04
→ 在 backtrack_log 中记录原因
→ 重置状态到 S04，设为 in_progress
```

---

## 框架概述

SpiralResearch 是一个**全自动端到端科研框架**，将人类科研的完整流程——从选题、文献调研、方法设计、实验执行、论文写作到投稿——分解为 **8 个阶段（Phase）、37 个原子级步骤（Stage）**，并通过多 Agent 协作与多层批判机制确保产出质量。

### 为什么叫 "Spiral"（螺旋）？

真实科研从来不是线性的。一个实验结果可能推翻之前的假设，写作时发现方法描述不清需要返回修改，审稿意见可能要求补充实验。SpiralResearch 的核心设计是**螺旋向前**：

- 每一圈螺旋都产生更高质量的结果
- 当下游发现上游错误时，系统自动**回溯到源头修复后再前进**
- 用 git commit/reset 记录每一次尝试，失败可无损回退

### 核心设计亮点

| 设计特性 | 说明 |
|---------|------|
| **8 Phase × 37 Stage** | 科研全流程原子化分解，每步有明确输入/输出/质量标准 |
| **三层批判架构** | 37 个 Stage Inspector + 6 个 Dimension Critic + 2 个 Meta Critic |
| **双循环机制** | Inner Loop（快速迭代：实验/写作）+ Outer Loop（战略反思：回溯重定向）|
| **确定性检查器** | Orphan Cite Gate、Anti-Leakage Check、LaTeX Sanity Check |
| **上下文恢复** | 每次上下文压缩后，Agent 自动重新加载身份定义 |
| **Agent 原生** | 所有编排基于原生 Agent 工具 |

---

## 内部工具

以下脚本由 Conductor（我）在对话中调用，**用户无需手动执行**：

| 脚本 | 用途 |
|------|------|
| `scripts/state_manager.py` | 读写 `pipeline_state.yaml`、记录历史、推进/回溯 Stage |
| `scripts/conductor_helper.py` | 获取下一步的 Stage、Agent、输入文档、输出路径 |
| `utils/md_validator.py` | 验证 Stage 产出是否符合 Universal Document Schema |
| `utils/orphan_cite_gate.py` | 检查论文引用完整性 |
| `utils/anti_leakage_check.py` | 扫描预训练数据泄露风险 |
| `utils/latex_sanity.py` | LaTeX 编译检查 |

---

## 工作流详解（37 Stage）

### Phase 1: Discovery（发现）S01-S05

| Stage | 名称 | Agent | 核心任务 |
|-------|------|-------|---------|
| S01 | 主题分析 | Literature | 定义研究范围，绘制领域地图 |
| S02 | 文献综述 | Literature | 系统调研文献，识别研究空白（Gap）|
| S03 | 研究问题 | Ideation | 将 Gap 转化为具体研究问题 |
| S04 | 假设生成 | Ideation | 构建可检验的假设 |
| S05 | 新颖性与可行性 | Ideation | 评估想法的新颖性和可行性 |

**Gate G1**: Logic Critic + Novelty Critic 并行审查

### Phase 2: Design（设计）S06-S10

| Stage | 名称 | Agent | 核心任务 |
|-------|------|-------|---------|
| S06 | 方法论设计 | Method | 设计严谨的研究方法 |
| S07 | Benchmark 选择 | Method | 选择数据集和评价指标 |
| S08 | 实验协议 | Method | 定义实验步骤和超参数 |
| S09 | Baseline 选择 | Method | 选择公平的对比方法 |
| S10 | 完整实验计划 | Method | 整合所有设计决策 |

**Gate G2**: Logic + Method + Novelty Critic

> 💡 **重命名提示**: Phase 2 完成后，研究方案已确定，建议将项目名改为最终论文标题。

### Phase 3: Execution（执行）S11-S13

| Stage | 名称 | Agent | 核心任务 |
|-------|------|-------|---------|
| S11 | 代码生成 | Experiment | 实现方法和 baseline |
| S12 | 实验执行、结果收集与初步分析 | Experiment | 实验迭代探索（修改→git commit→运行→记录→分析；**内嵌 AutoResearch 评估决策**）|
| S13 | 实验结果验证 | Analysis | 当迭代探索收敛、方法达到较好效果后，验证结果可靠性 |

**Gate G3**: Method + Evidence Critic

### Phase 4: Ablation（消融）S14-S17

| Stage | 名称 | Agent | 核心任务 |
|-------|------|-------|---------|
| S14 | 消融设计 | Experiment | 设计消融实验，验证各模块有效性（**需 subagent 审查**）|
| S15 | 消融代码生成 | Experiment | 实现消融实验代码 |
| S16 | 消融执行 | Experiment | 执行消融代码；若报错，回溯到 S15 或 S14 |
| S17 | 消融结果分析 | Analysis | 分析消融实验结果 |

**Gate G4**: Method + Evidence Critic

### Phase 5: Further Analysis（进一步分析）S18-S21

| Stage | 名称 | Agent | 核心任务 |
|-------|------|-------|---------|
| S18 | 其他发现 | Analysis | 根据 P3/P4 实验结果，发现突出方法优越性的实验现象 |
| S19 | 分析实验设计 | Analysis | 设计进一步分析实验（可视化、敏感性分析等）；**需 subagent 审查可行性** |
| S20 | 分析实验实现 | Experiment | 实现 S19 设计的分析实验 |
| S21 | 分析结果收集与分析 | Analysis | 收集和分析分析实验结果；**需审查，必要时回溯** |

**Gate G5**: Logic + Evidence + Novelty Critic

### Phase 6: Synthesis（合成）S22-S25

| Stage | 名称 | Agent | 核心任务 |
|-------|------|-------|---------|
| S22 | Claim-Evidence 映射 | Analysis | 根据 P3/P4/P5 实验结果，建立声明到证据的映射 |
| S23 | 发现综合 | Analysis | 提炼研究洞察（含 Outer Loop 反馈）|
| S24 | 贡献阐述 | Writing | 清晰阐述研究贡献 |
| S25 | 未来工作 | Ideation | 识别未来研究方向 |

**Gate G6**: Logic + Evidence + Novelty Critic

### Phase 7: Writing（写作）S26-S33

| Stage | 名称 | Agent | 核心任务 |
|-------|------|-------|---------|
| S26 | 论文大纲 | Writing | PaperOrchestra Step 1：产出结构化大纲；**严格按 venue LaTeX 模板要求规划 section 结构** |
| S27 | 引言与相关工作 | Writing | PaperOrchestra Step 3：基于 S02 文献综述写作 |
| S28 | 方法部分 | Writing | 撰写方法论 section |
| S29 | 实验与结果 | Writing | 撰写实验 section |
| S30 | 分析与讨论 | Writing | 撰写讨论 section |
| S31 | 摘要与结论 | Writing | 撰写 Abstract 和 Conclusion |
| S32 | 图表生成 | Figure | PaperOrchestra Step 2：Planner→Renderer→VLM Critic |
| S33 | 完整草稿整合 | Writing | PaperOrchestra Step 4：单次多模态调用生成完整草稿 |

**Gate G7**: Logic + Writing + Evidence Critic

### Phase 8: Refinement（精炼）S34-S37

| Stage | 名称 | Agent | 核心任务 |
|-------|------|-------|---------|
| S34 | 内部审查 | Critic Team | 多 Critic 并行审查 |
| S35 | 审稿人模拟 | Review | 3 Reviewer Simulation（Method/Experiment/Writing 视角）|
| S36 | 修订循环 | Writing | PaperOrchestra Step 5：Accept/Revert Halt Rules（最后一轮自动执行 Orphan Cite / Anti-Leakage / LaTeX Sanity 检查）|
| S37 | 最终编译与提交包 | Writing | LaTeX 编译生成 PDF；**从 `config/author_info.yaml` 读取并添加作者信息**；准备投稿包 |

**Gate G8**: Writing + Novelty + Ethics + Conductor Inspector

---

## Conductor 的执行流程

```
用户指令
    │
    ▼
Conductor（我）读取 pipeline_state.yaml
    │
    ├── 如果是新项目 → 创建目录 + 初始化状态
    │
    ▼
确定当前 Stage（如 S01）
    │
    ▼
调用 Agent 工具创建子 Agent
    ├── 传递：AGENT.md 路径、MD Protocol、输入文档、输出要求
    │
    ▼
子 Agent 执行任务并返回产出内容
    │
    ▼
Conductor（我）保存产出到项目目录
    │
    ▼
调用 Stage Inspector / Critic Team 审查
    │
    ├── PASS → 推进到下一 Stage
    ├── REVISE → 要求子 Agent 修改
    └── BACKTRACK → 回退到上游 Stage
    │
    ▼
更新 pipeline_state.yaml
    │
    ▼
向用户汇报进展
```

---

## 框架目录结构

```
/mnt/c/AutoPaper/              # 框架代码
├── spiral/                    # Python 核心模块
│   ├── state.py               # pipeline_state.yaml 管理器
│   └── project.py             # 项目创建与布局
├── scripts/                   # CLI 工具（Conductor 内部使用）
│   ├── state_manager.py       # 读写状态、推进/回溯
│   └── conductor_helper.py    # 下一步决策辅助
├── .agents/skills/autopaper/  # 自动加载 Skill（触发词自动加载）
│   ├── SKILL.md               # Skill 定义
│   └── references/            # 命令、Stage、Agent 参考
├── .agents/                   # Agent prompt 模板
├── templates/stage/           # 37 Stage markdown 模板
├── utils/                     # 确定性检查器
│   ├── md_validator.py
│   ├── orphan_cite_gate.py
│   ├── anti_leakage_check.py
│   └── latex_sanity.py
├── config/
│   ├── venue_registry.yaml    # Venue 注册表
│   └── environment.yaml       # 全局实验环境配置
└── docs/                      # 框架设计文档（64 个文件）
```

## 项目结构（生成的研究项目）

```
../projects/
└── {project-name}-{timestamp}/
    ├── S01/ ~ S37/           # 每个 Stage 一个文件夹
    │   └── S{NN}_output.md   # Stage 产出文档
    │
    ├── state/                # 项目状态（Conductor 维护）
    │   ├── pipeline_state.yaml   # 当前 Stage、历史、回溯记录
    │   ├── decision_log.md       # Conductor 的所有决策
    │   └── spiral_log.md         # 完整的螺旋迭代历史
    │
    ├── knowledge/            # 知识文档（Stage 间传递）
    │   ├── handoff_P1_to_P2.md   # Phase 间交接文档
    │   ├── handoff_P2_to_P3.md
    │   └── reviews/              # Critic 审查报告
    │       ├── G1_logic_review.md
    │       └── ...
    │
    ├── artifacts/            # 最终产出
    │   ├── paper.pdf         # 编译后的论文
    │   └── submission-package.zip
    │
    └── experiments/          # 实验代码和数据
        ├── src/              # 源代码
        ├── configs/          # 配置文件
        ├── results/          # 原始结果
        └── results.tsv       # AutoResearch 迭代日志
```

---

## Agent 系统

SpiralResearch 包含 **17 个 Agent**（含 2 个 Meta Critic），分为三类：

### 执行 Agent（7 个）

| Agent | 职责 | 负责 Stage |
|-------|------|-----------|
| **Literature** | 文献调研与综述 | S01-S02 |
| **Ideation** | 想法生成与评估 | S03-S05, S23 |
| **Method** | 方法论设计 | S06-S10 |
| **Experiment** | 实验执行 | S11-S12, S14-S16, S20 |
| **Analysis** | 结果分析 | S13, S17-S19, S21-S23 |
| **Writing** | 论文写作 | S24, S26-S31, S33, S36, S37 |
| **Figure** | 图表生成 | S31 |

### 批判 Agent（8 个）

**Dimension Critics（6 个）**：在 Gate 时并行调用

| Critic | 审查维度 | 审查范围 |
|--------|---------|---------|
| **Logic** | 论证链条、因果推断 | S03-S06, S10, S22, S24-S33 |
| **Method** | 方法正确性、baseline 公平性 | S06-S11, S12, S14-S16, S19, S28 |
| **Evidence** | 统计正确性、Claim-Evidence 映射 | S12-S13, S17, S21-S22, S29 |
| **Writing** | 学术规范、Anti-Leakage、Orphan Cite | S26-S33, S36-S37 |
| **Novelty** | 遗漏相关工作、新颖性评估 | S04-S06, S24, S27, S34 |
| **Ethics** | 数据伦理、隐私、公平性 | S07-S08, S12, S18-S21, S29 |

**Meta Critics（2 个）**：

| Critic | 职责 |
|--------|------|
| **Conductor Inspector** | 审查 Conductor 编排决策、回溯逻辑 |
| **Format Inspector** | 深度 MD 格式验证、Schema 合规性 |

### Review Agent（1 个）

模拟 3 位顶会审稿人，执行 Accept/Revert Halt Rules。

---

## 关键机制

### Inner Loop（内循环）

- **S12 Experiment Loop**: AutoResearch 风格内嵌迭代循环
  ```
  modify code → git commit → run (5-30min) → 记录结果 → 初步分析
  深入分析（过拟合/数据泄露/稳定性）→ 评估决策 → KEEP / DISCARD / 回溯 S11
  ```
- **S36 Revision Loop**: PaperOrchestra 内容精炼
  ```
  Review Agent 审稿 → Writing Agent 修改 → Review Agent 重新审稿
  Accept if score ↑, Revert if score ↓, Halt after 3 rounds
  ```

### Outer Loop（外循环）

当 Analysis Agent 在 S21 发现核心假设被否定，或 Gate 审查发现根本性问题时：

```
触发 Backward Propagation → 计算最小回溯范围 → 回退到目标 Stage → 重新执行
```

### 回溯保护机制

如果同一 Stage 回溯 ≥3 次：
1. Conductor 向用户报告反复失败
2. 提供选项：人工介入 / 降低标准继续 / 跳过当前 Phase
3. 记录用户选择到 `decision_log.md`

---

## 文件规范

### Stage 产出文档命名

```
S{两位数字}_{描述}.md

示例：
- S01_topic_analysis.md
- S13_experiment_execution.md
- S32_full_draft.md
```

### Universal Document Schema（必需章节）

每个 Stage 产出必须包含：

```markdown
---
stage: S01
phase: P1
agent: literature
version: "1.0"
depends_on: []
status: draft
---

# S01: Topic Analysis

## 1. 核心内容
## 2. Reasoning Trail（推理过程）
## 3. 验证与检查
## 4. 风险与限制
## 5. 下游接口（≥3 个关键信息）
## 6. 回溯触发器（≥1 个）
```

---

## 设计文档索引

| 文档 | 内容 |
|------|------|
| `docs/01_ARCHITECTURE.md` | 总体架构：3层栈、8 Phase、37 Stage、Gate 模型 |
| `docs/02_CONDUCTOR_AGENT.md` | Conductor 编排逻辑：启动流程、主循环、Gate 处理 |
| `docs/03_SUB_AGENTS.md` | 子 Agent 团队：职责矩阵、协作模式、创建协议 |
| `docs/04_STAGES.md` | 37 个 Stage 详细设计：输入、输出、质量标准、Agent |
| `docs/05_KNOWLEDGE_FLOW.md` | 知识流转：Handoff 文档、跨 Stage 传递规则 |
| `docs/06_FEEDBACK_LOOP.md` | 反馈机制：Inner/Outer Loop、Backward Propagation |
| `docs/07_MD_PROTOCOL.md` | MD 收发规范：Universal Document Schema、9步解析 |
| `docs/AGENTS/**/AGENT.md` | 19 个 Agent 的身份定义、能力、规范、陷阱 |

---

## 许可证

MIT License
