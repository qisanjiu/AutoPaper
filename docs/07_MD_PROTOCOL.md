# Markdown 收发规范 (MD Protocol)

> **原则**: 不仅产出要规范，**接收**上游文档时也要按规范解析，确保信息不丢失、不误解

---

## 1. 双轨规范体系

```
上游产出 ──[产出规范]──► knowledge/*.md ──[接收规范]──► 下游 Agent 理解
```

- **产出规范 (Output Protocol)**: 写文档时必须遵循的结构、章节、命名
- **接收规范 (Input Protocol)**: 读文档时必须执行的解析、验证、提取步骤

---

## 1.5 文件命名与版本管理规范 (File Naming & Versioning)

### 单文件原则
**每个 Stage、Handoff、Gate 审查有且仅有一个文件。**

| 类型 | 命名格式 | 示例 | 规则 |
|------|---------|------|------|
| Stage 主产出 | `S{NN}_{snake_case_name}.md` | `S02_literature_survey.md` | 有且仅有一个 |
| Handoff 文档 | `handoff_P{N}_P{N+1}.md` | `handoff_P1_P2.md` | 有且仅有一个 |
| Gate 聚合审查 | `reviews/G{N}_aggregate.md` | `reviews/G1_aggregate.md` | 有且仅有一个 |
| 参考文献 | `refs.bib` | `refs.bib` | 有且仅有一个 |

### 禁止行为
- ❌ **禁止创建 `_v1`, `_v2`, `_rev2`, `_v3` 等后缀的版本文件**
- ❌ **禁止为同一 Stage 创建多个不同名字的产出文件**
- ❌ 例如：`S03_research_questions_rev2.md`, `S06_methodology_design_v3.md`

### 正确做法
- ✅ 回溯时**直接覆盖**原文件内容
- ✅ 在文件内的 `## 7. 版本记录` 章节中追加变更说明
- ✅ Stage 的补充内容（如数据集核实、采样参数调研）作为**原文件的附录章节**，不创建独立文件
- ✅ 例如：S02 的数据集核实和采样参数调研应合并到 `S02_literature_survey.md` 的附录中

### 版本记录格式
```markdown
## 7. 版本记录
- v1: 2026-04-20 — 初始版本
- v2: 2026-04-21 — 修正数据集策略（OMuSense-23 排除，Twente 为主）
- v3: 2026-04-21 — 采样参数调研后放弃多数据集联合训练
```

---

## 2. 通用文档模板 (Universal Document Schema)

所有 Stage 产出文档必须遵循统一的 Schema：

```markdown
# [标题] — 一句话概括本文档的核心内容

## Metadata
- **Stage**: S{NN}
- **Agent**: {agent_name}
- **Version**: v{M} (初始 v1，每次修订 +1)
- **Created**: YYYY-MM-DD HH:MM
- **DependsOn**: [S{XX}, S{YY}, handoff_P{A}_P{B}]  # 直接前置依赖
- **Status**: final / draft / stale / revised  # 文档状态

## 1. 核心内容
（Stage 的具体产出，因 Stage 而异）

## 2. 推理过程 (Reasoning Trail)
**为什么做出这些选择？**
- 选项 A vs 选项 B → 选择 A 的理由: ...
- 关键假设: ...
- 被否定的方案: ...（记录为什么被否定，防止回溯时重复尝试）

## 3. 验证与检查
- [ ] 自查项 1: ... → 结果: pass / fail
- [ ] 自查项 2: ... → 结果: ...

## 4. 风险与限制
| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|---------|------|
| ... | 高/中/低 | ... | 开放/已缓解 |

## 5. 下游接口 (Downstream Interface)
**下游 Agent 应该知道的 3-5 件事：**
1. **关键发现**: ...（一句话）
2. **核心决策**: ...（带理由）
3. **必须使用的数据**: ...（文件路径/数值）
4. **必须遵守的约束**: ...（不能违反的条件）
5. **已知陷阱**: ...（下游容易犯的错误）

## 6. 回溯触发器与修改方向 (Backtrack Triggers & Direction)

### 6.1 回溯触发器（产出时预判）
**如果下游发现以下问题，可能需要回溯到本 Stage：**
- 触发条件 1: ... → 回溯理由: ...
- 触发条件 2: ... → 回溯理由: ...

### 6.2 回溯修改方向（触发回溯时必须产出）

> **⚠️ 通用规范：任何 Stage/Critic/Agent 触发 BACKTRACK 时，产出文档中必须包含此章节。**

当本 Stage 的产出实际触发回溯时（而非仅预判），必须提供：

```markdown
## 回溯修改方向 (Backtrack Direction)

### 问题诊断 (Problem Diagnosis)
- **发现的问题**: ...（具体描述什么问题导致了回溯）
- **根因分析**: ...（为什么会产生这个问题？上游哪个决策/产出导致了它？）
- **影响范围**: ...（这个问题影响了哪些下游 Stage？）

### 修改方向/建议 (Modification Direction)
- **建议修改什么**: ...（方向性建议，非代码级具体方案）
- **建议如何修改**: ...（修改思路和方法，由回溯目标 Agent 制定具体方案）
- **预期效果**: ...（修改后应达到什么状态）
- **验证方式**: ...（修改后如何验证问题已解决）

### 回溯目标确认
- **回溯到 Stage**: ...
- **原因**: ...（为什么选择该 Stage 作为回溯目标）
```

**原则**：
- **回溯发起方**（分析型 Agent/Critic）负责「问题诊断 + 修改方向」
- **回溯目标方**（执行型 Agent）负责基于方向「制定具体方案 + 执行修改」
- **不越权**：分析型 Agent 不制定代码级修改方案；执行型 Agent 不忽视分析型 Agent 的诊断方向

## 7. 版本记录
```
- v1: YYYY-MM-DD — 初始版本
- v2: YYYY-MM-DD — 修正内容（简短说明变更原因）
- v3: YYYY-MM-DD — 再次修正...
```
> **版本管理规则**: 回溯时直接覆盖文件内容，在版本记录中追加新版本说明。**禁止创建 `_v1`, `_v2`, `_rev2` 等后缀的版本文件**。

## 8. 附录
- 原始数据路径: ...
- 额外参考资料: ...
```

---

## 3. 接收规范 (Input Protocol)

每个子 Agent 被创建后，**必须按以下步骤解析上游文档**：

### Step 1: 文档存在性检查
```
FOR each doc in input_docs:
    IF doc does not exist:
        REPORT to Conductor: "缺少必需输入: {doc}"
        HALT execution
```

### Step 2: 元数据解析
```
READ "## Metadata" section:
    - 确认 Stage 编号是否与当前任务匹配
    - 确认 Status 不是 "stale"（如果是，向 Conductor 报告）
    - 确认 Version（如果不是 v1，注意可能有修订历史）
    - 记录 DependsOn（用于一致性检查）
```

### Step 3: 核心内容提取
```
READ "## 1. 核心内容" section:
    - 提取所有结构化信息（表格、列表、代码块）
    - 记录所有数值、公式、结论
    - 标记不确定或模糊的部分
```

### Step 4: 推理过程审查
```
READ "## 2. 推理过程":
    - 理解上游 Agent 为什么做出这些选择
    - 检查推理是否有漏洞
    - 如果被否定的方案值得重新考虑，记录下来
```

### Step 5: 验证状态确认
```
READ "## 3. 验证与检查":
    - 确认所有自查项都通过
    - 如果有未通过的项，向 Conductor 报告
```

### Step 6: 风险意识加载
```
READ "## 4. 风险与限制":
    - 加载所有已知风险到自己的工作记忆
    - 确保自己的产出不放大这些风险
```

### Step 7: 下游接口提取
```
READ "## 5. 下游接口":
    - 提取必须使用的数据和约束
    - 提取已知陷阱（防止自己犯错）
    - 如果有不理解的部分，标记为 "需要澄清"
```

### Step 8: 回溯触发器检查
```
READ "## 6. 回溯触发器":
    - 了解什么情况下自己的产出可能导致回溯
    - 尽量避免触发这些条件
```

### Step 9: 一致性交叉验证
```
IF multiple input docs:
    CHECK: 文档间是否有矛盾？
    CHECK: 数值是否一致？
    CHECK: 结论是否互相支持？
    IF 发现矛盾:
        REPORT to Conductor with details
```

---

## 4. Agent 专属接收清单

不同 Agent 对接收内容的关注点不同，以下是各 Agent 的**重点提取清单**：

### Literature Agent 接收清单
- [ ] 用户提供的 topic 是否清晰
- [ ] 是否有预设的偏好 venue / 方向
- [ ] 是否有已知的相关论文（避免重复调研）

### Ideation Agent 接收清单
- [ ] **关键提取**: Gap 列表（从 S02 的 "研究空白分析" 表格）
- [ ] **关键提取**: 领域活跃方向（从 S01 的 "趋势与机会"）
- [ ] **关键提取**: 经典 baseline 方法（从 S02 的 "文献分类表"）
- [ ] **验证**: Gap 是否真实存在（交叉检查多来源）
- [ ] **验证**: 文献覆盖是否全面

### Method Agent 接收清单
- [ ] **关键提取**: 研究问题（S03）
- [ ] **关键提取**: 假设及预测（S04）
- [ ] **关键提取**: 可行性评估（S05）
- [ ] **验证**: 方法是否能验证假设（方法→实验→假设的链条是否完整）
- [ ] **验证**: 新颖性声明是否有文献支撑

### Experiment Agent 接收清单
- [ ] **关键提取**: 方法设计（S06）
- [ ] **关键提取**: 实验协议（S08）
- [ ] **关键提取**: baseline 列表（S09）
- [ ] **验证**: 协议中的超参数是否完整
- [ ] **验证**: 随机种子和可复现性要求

### Analysis Agent 接收清单
- [ ] **关键提取**: 原始结果数据（S14 中的表格和文件路径）
- [ ] **关键提取**: 实验协议中的评估指标（S08）
- [ ] **关键提取**: 假设列表（S04）
- [ ] **验证**: 数据完整性（是否有缺失/异常）
- [ ] **验证**: 实验是否按协议执行

### Writing Agent 接收清单
- [ ] **关键提取**: Claim-Evidence 映射（S20）
- [ ] **关键提取**: 核心发现（S21）
- [ ] **关键提取**: 局限性（S22）
- [ ] **关键提取**: 贡献声明（S24）
- [ ] **验证**: 每个 claim 是否有证据支撑
- [ ] **验证**: 数值与原始结果是否一致

### Figure Agent 接收清单
- [ ] **关键提取**: 图表计划（S25）
- [ ] **关键提取**: 实验结果数据（S14, S18）
- [ ] **关键提取**: 方法架构描述（S06）
- [ ] **验证**: 数据文件是否存在且可读
- [ ] **验证**: 图表类型是否合适

### Critic Agent 接收清单（因类型而异，见下文）

---

## 5. 文档状态生命周期

```
                    ┌─────────────┐
       ┌───────────►│   DRAFT    │◄────────┐
       │            │  (初稿)    │         │
       │            └──────┬─────┘         │
       │                   │ 完成自检       │
       │                   ▼                │
  修订中 │            ┌─────────────┐       │ 发现问题
       │            │   FINAL     │       │
       │            │  (终稿)     │       │
       │            └──────┬─────┘       │
       │                   │ Gate 通过    │
       │                   ▼              │
       │            ┌─────────────┐       │
       └────────────┤   FROZEN   │───────┘
                    │ (冻结,只读) │
                    └──────┬─────┘
                           │ 回溯触发
                           ▼
                    ┌─────────────┐
                    │   STALE    │
                    │ (过期,待修) │
                    └─────────────┘
```

**状态含义**：
- **DRAFT**: 正在撰写中，可能不完整
- **FINAL**: 已完成，通过自检，等待 Gate
- **FROZEN**: Gate 通过，成为下游的权威输入（只读）
- **STALE**: 因回溯而失效，需要重新生成

---

## 6. 数值一致性协议

Agent 之间传递的数值必须遵循严格的规范：

### 6.1 数值格式

```markdown
| 指标 | 值 | 格式说明 |
|------|-----|---------|
| 准确率 | 0.847 ± 0.012 | mean ± std, 保留 3 位小数 |
| 运行时间 | 2.3h | 带单位 |
| p-value | 3.2e-4 | 科学计数法，保留 2 位有效数字 |
| 效应量 | d = 0.82 (large) | 报告效应量 + 解释 |
```

### 6.2 数值溯源

每个出现在文档中的数值必须可追溯：

```markdown
结果: 准确率 84.7%
来源: experiments/results/exp_1/eval.json, seed=42
计算方式: mean of 5 runs
```

### 6.3 一致性检查

下游 Agent 发现数值不一致时必须报告：

```markdown
⚠️ 一致性警告: S28 中报告准确率 84.7%，但 S14 中的原始数据为 84.2% (seed=42)。
建议: 核实哪个数值正确。
```

---

## 7. 引用规范 (Inter-Document References)

Agent 在文档中引用其他文档时必须使用规范格式：

### 7.1 文档引用
```markdown
根据 [S02 文献综述](knowledge/S02_literature_survey.md) 的 Gap-3 分析...
```

### 7.2 章节引用
```markdown
详见 S04 [H1 假设](knowledge/S04_hypothesis_generation.md#h1) 的预测...
```

### 7.3 数值引用
```markdown
如 S14 所述，主实验准确率为 `S14.main_result.accuracy`
```

### 7.4 引用验证

Conductor 在派发任务时应检查：
- 引用的文档是否存在
- 引用的章节是否存在（通过锚点检查）
- 引用的数值是否与源文档一致

---

## 8. 异常处理协议

### 8.1 发现上游文档问题

当 Agent 发现上游文档有问题时：

```
1. 记录问题详情（位置、类型、严重程度）
2. 在自己的产出中标注：
   ⚠️ 上游警告: S04 的 H1 假设缺少可测量预测。
   当前工作暂按 "准确率提升 > 2%" 假设，需回溯确认。
3. 向 Conductor 报告
4. Conductor 决定：继续（带风险标注）/ 回溯 / 暂停
```

### 8.2 信息不足

当 Agent 发现信息不足以完成任务时：

```
1. 明确列出缺少什么信息
2. 说明为什么需要这些信息
3. 说明没有这些信息时的替代方案（如果有）
4. 向 Conductor 请求补充信息或授权继续
```

### 8.3 信息冲突

当多个上游文档提供冲突信息时：

```
1. 列出冲突点
2. 分析可能的原因（哪个更可靠）
3. 选择一个版本并说明理由
4. 标注："注意：S02 和 S03 在 X 问题上存在分歧，本文采用 S02 的说法，因为..."
5. 向 Conductor 报告冲突
```

---

## 9. 大文件产出规范 (Large Artifact Protocol)

当 Stage 产出包含以下类型内容时，**必须**遵循双产出协议 (Two-Output Contract)：

### 9.1 双产出协议

```
┌─────────────────────────────────────────────────────────────┐
│  实际文件  → 保存到专用目录（figures/, experiments/src/等）   │
│  描述文档  → knowledge/S{NN}_*.md（仅含元数据、路径、短片段）  │
└─────────────────────────────────────────────────────────────┘
```

**实际文件**包括但不限于：
- 图片：`figures/*.png`, `figures/*.pdf`
- 代码：`experiments/src/*.py`, `experiments/configs/*.yaml`
- 数据：`experiments/results/*.json`, `experiments/results/*.csv`, `experiments/results.tsv`
- 实验日志：`experiments/logs/*.log`
- 模型检查点：`experiments/checkpoints/`
- LaTeX：`artifacts/*.tex`
- 参考文献（BibTeX）：`knowledge/refs.bib`, `artifacts/refs.bib`
- 编译产物：`artifacts/paper.pdf`
- 提交包：`artifacts/submission-package.zip`, `artifacts/supplementary_materials/`

**描述文档 (MD)** 应包含：
- 文件清单（路径、格式、大小/行数）
- 关键决策和设计说明
- **简短的** illustrative 代码片段（≤15 行，用于展示核心逻辑）
- 下游引用路径

### 9.2 禁止行为

- ❌ 将完整可执行代码（>30 行）仅嵌入 MD，而不保存为实际文件
- ❌ 将图片以 base64 编码嵌入 MD
- ❌ 将完整 LaTeX 文档（>100 行）仅嵌入 MD，而不保存为 `.tex` 文件
- ❌ 将大型数据表格（>20 行）仅嵌入 MD，而不保存为 `.csv`/`.tsv` 文件

### 9.3 允许行为

- ✅ 在 MD 中嵌入简短的 illustrative 代码片段（关键逻辑展示）
- ✅ 在 MD 中用目录树说明文件结构
- ✅ 在 MD 中用表格列出所有产出文件清单（含路径、格式、大小）
- ✅ 在 MD 中引用实际文件的相对路径（如 `figures/fig1_architecture.pdf`）

### 9.4 各 Stage 的双产出要求

| Stage | 实际文件 | 描述 MD |
|-------|---------|---------|
| S02 | `knowledge/refs.bib` | `S02_literature_survey.md` |
| S11 | `experiments/src/*.py`, `experiments/configs/*.yaml`, `experiments/baselines/`, `requirements.txt` | `S11_code_generation.md` |
| S13 | `experiments/results/`, `experiments/results.tsv`, `experiments/results/eval.json`, `experiments/checkpoints/`, git 分支 | `S13_experiment_execution.md` |
| S12 | `experiments/results/summary.json`, `experiments/results/main_results.csv`, `experiments/results/*.json` | `S12_experiment_iteration.md` |
| S16 | `experiments/results/ablation_*.json`, `experiments/results/ablation.tsv`, `experiments/checkpoints/ablation_*/` | `S16_ablation_execution.md` |
| S31 | `figures/*.png`, `figures/*.pdf`, `figures/src/*.py` | `S31_figure_table_generation.md` |
| S33 | `artifacts/draft.tex`, `artifacts/refs.bib`, `artifacts/draft.pdf`, `artifacts/latex_template/*.sty` | `S33_full_draft.md` |
| S36 | `drafts/iter*/paper.tex` | `S36_revision_loop.md` |
| S37 | `artifacts/paper.pdf`, `artifacts/paper.tex`, `artifacts/refs.bib`, `artifacts/submission-package.zip` | `S37_final_compilation.md` |

> **关于 Venue 模板**：项目创建时，所选 venue 的 LaTeX 模板（`.sty`/`.cls`/`.bst`/`.tex`）自动复制到 `artifacts/latex_template/`。S33 必须使用此目录下的模板文件，严禁使用其他来源的模板。 Venue 注册表位于 `config/venue_registry.yaml`，配置保存在 `state/pipeline_state.yaml` 的 `project.venue` 字段中。
>
> **关于 LaTeX 编译**：S33 和 S37 必须执行**多次编译**（pdflatex → bibtex → pdflatex × 2），使用 `utils/latex_sanity.py` 验证编译结果和页数合规性。

---

## 10. 总结：产出-接收闭环

```
┌────────────────────────────────────────────────────────────┐
│                    产出规范 (Output)                        │
│  1. 遵循 Universal Document Schema                         │
│  2. 包含完整的 Metadata                                    │
│  3. 核心内容结构化（表格、列表、代码块）                      │
│  4. Reasoning Trail 记录决策过程                             │
│  5. 验证检查清单                                           │
│  6. 下游接口明确传递 3-5 个关键信息                          │
│  7. 回溯触发器预判下游可能的问题                             │
│  8. 数值带溯源信息                                         │
└────────────────────┬───────────────────────────────────────┘
                     │ knowledge/*.md
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    接收规范 (Input)                         │
│  1. 存在性检查 → 元数据解析 → 内容提取                       │
│  2. 推理过程审查 → 验证状态确认                              │
│  3. 风险加载 → 下游接口提取                                  │
│  4. 回溯触发器检查 → 一致性交叉验证                          │
│  5. Agent 专属提取清单                                       │
│  6. 数值一致性验证                                         │
│  7. 引用有效性检查                                         │
│  8. 异常报告机制                                           │
└────────────────────────────────────────────────────────────┘
```

---

> **下一步**: 阅读更新后的 `03_SUB_AGENTS.md` 和 `AGENTS/critic/` 下的专业 Critic Agent 定义。
