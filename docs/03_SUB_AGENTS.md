# 子 Agent 团队设计

> **原则**: 每个子 Agent 都是领域专家，只负责一个狭窄但深入的任务  
> **身份获取**: 被 Conductor 创建后，第一时间读取 `AGENTS/{role}/AGENT.md`  
> **工作方式**: 按 MD 接收规范解析输入 → 执行任务 → 按 MD 产出规范输出 → 向 Conductor 汇报

---

## 1. Agent 团队概览

```
                    ┌─────────────────┐
                    │   Conductor     │
                    │   (主编排者)     │
                    └────────┬────────┘
                             │ 创建 / 调用
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────┴────┐         ┌─────┴──────┐      ┌─────┴─────┐
   │Execution│         │ Critic     │      │  Review   │
   │ Agents  │         │ Team (x6)  │      │  Agent    │
   └────┬────┘         └────────────┘      └───────────┘
        │
   ┌────┴──────────────────────────────────────────┐
   │                                                │
┌──┴──┐ ┌──┴──┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
│Lit- │ │Ide- │ │Meth│ │Exp │ │Anal│ │Writ│ │Fig │
│era- │ │ation│ │od  │ │erim│ │ysis│ │ing │ │ure │
│ture │ │     │ │    │ │ent │ │    │ │    │ │    │
└─────┘ └─────┘ └────┘ └────┘ └────┘ └────┘ └────┘
```

---

## 2. Agent 职责矩阵

| Agent | 核心职责 | 参与 Stage | 关键技能 | 质量指标 |
|-------|---------|-----------|---------|---------|
| **Literature** | 文献调研与综述 | S01-S02 | 多源搜索、文献筛选、gap 识别 | 覆盖率、相关性 |
| **Ideation** | 想法生成与评估 | S03-S05, S25 | 创造性思维、假设构建、可行性分析 | 新颖性、可证伪性 |
| **Method** | 方法论设计 | S06-S10 | 方法构建、实验设计、baseline 选择 | 严谨性、可复现性 |
| **Experiment** | 实验执行 | S11-S12, S14-S16, S20 | 代码生成、实验运行、结果收集 | 正确性、完整性 |
| **Analysis** | 结果分析 | S13, S17-S19, S21-S23 | 统计分析、模式识别、洞察提炼 | 深度、准确性 |
| **Writing** | 论文写作 | S24, S26-S31, S33, S36, S37 | 学术写作、结构组织、论证逻辑 | 清晰度、规范性 |
| **Figure** | 图表生成 | S32 | 数据可视化、图表设计、LaTeX 整合 | 美观性、准确性 |
| **Critic Team** | 多维度质量批判 | S05, S10, S13, S17, S21, S25, S34 | 见下表 | 全面性、专业性 |
| **Review** | 模拟审稿 | S35 | 同行评审、分数评定、改进建议 | 客观性、专业性 |

### Critic Team 细分

| Critic | 审查维度 | 审查对象 | 核心问题 |
|--------|---------|---------|---------|
| **Logic** | 论证链条、一致性、因果推断 | S03-S06, S10, S22, S24-S33 | "论证是否逻辑严密？" |
| **Method** | 方法正确性、实验设计、baseline 公平性 | S06-S11, S12, S14-S16, S19, S28 | "方法是否正确、实验是否严谨？" |
| **Evidence** | 统计正确性、数据质量、Claim-Evidence 映射 | S12-S13, S17, S21-S22, S29 | "Claim 是否有充分证据支撑？" |
| **Writing** | 学术规范、venue 格式、论证结构、图表 | S26-S33, S36-S37 | "论文是否符合学术写作标准？" |
| **Novelty** | 遗漏相关工作、新颖性评估、贡献定位 | S04-S06, S24, S27, S34 | "研究是否真正新颖？" |
| **Ethics** | 数据伦理、隐私、公平性、潜在危害 | S07-S08, S12, S18-S21, S29 | "研究是否负责任、符合伦理？" |

---

## 3. Agent 间协作模式

### 3.1 串行协作

最常见模式：一个 Agent 完成后，Conductor 将产出传递给下一个 Agent。

```
Literature Agent ──► Ideation Agent ──► Method Agent
   (S01-S02)           (S03-S05)          (S06-S10)
```

### 3.2 并行协作

当两个任务没有依赖时，Conductor 同时创建多个 Agent：

```
        ┌─► Writing Agent (S26: Introduction)
        │
S25 ────┼─► Writing Agent (S27: Methodology)
        │
        └─► Figure Agent (S31: Figures)
```

### 3.3 批判介入

**多个专业 Critic 并行审查**同一产出：

```
Experiment Agent ──► S13产出
        │
        ├──► Method Critic ──► 方法审查报告
        ├──► Evidence Critic ──► 证据审查报告
        └──► Ethics Critic ──► 伦理审查报告
        │
        ▼
   Conductor 聚合结果
```

### 3.4 对抗循环 (Adversarial Loop)

```
Writing Agent 产出草稿
        │
        ├──► Writing Critic ──► 写作问题
        ├──► Logic Critic ──► 逻辑问题
        └──► Evidence Critic ──► 数据一致性问题
        │
        ▼
Review Agent 审稿（评分 + 弱点列表）
        │
        ▼
Writing Agent 根据所有审查意见修改
        │
        ▼
   [循环直到收敛]
```

---

## 4. Agent 创建协议

Conductor 创建子 Agent 时，必须传递以下信息：

```yaml
# Agent 调用参数
role: "literature"          # Agent 角色名称
stage: "S01"                # 当前 Stage 编号
objective: "string"         # 明确的任务目标（一句话）
input_docs:                 # 输入文档路径列表
  - "knowledge/S01_topic_analysis.md"
  - "state/pipeline_state.yaml"
output_doc: "knowledge/S02_literature_survey.md"  # 预期输出文档路径
constraints:                # 约束条件
  max_papers: 50
  min_papers: 10
  time_range: "2020-2026"
quality_criteria:           # 质量标准
  - "覆盖该领域近5年顶会论文"
  - "识别至少3个研究空白"
  - "包含对比分析表格"
context: "string"           # 额外上下文（研究主题、已知情报等）
```

子 Agent 被创建后：

1. **首先读取** `AGENTS/{role}/AGENT.md` 了解自己的身份和能力边界
2. **然后读取** `docs/07_MD_PROTOCOL.md` 了解 MD 收发规范
3. **按接收规范解析** Conductor 指定的输入文档（9 步解析流程）
4. **执行任务** 并产出规范化文档（遵循 Universal Document Schema）
5. **汇报完成** 时提供：产出文档路径、关键发现摘要、遇到的问题、对下游的建议

---

## 5. Agent 自检清单

每个子 Agent 在提交产出前，必须自检：

- [ ] 输出文档是否符合命名规范 (`S{NN}_{name}.md`)
- [ ] 输出文档是否包含所有 Universal Document Schema 的必需章节
  - [ ] Metadata（含 Stage、Agent、Version、DependsOn、Status）
  - [ ] 核心内容
  - [ ] 推理过程 (Reasoning Trail)
  - [ ] 验证与检查
  - [ ] 风险与限制
  - [ ] 下游接口 (Downstream Interface)
  - [ ] 回溯触发器 (Backtrack Triggers)
- [ ] 引用的上游文档是否被正确引用
- [ ] "下游接口"是否包含 3-5 个关键信息
- [ ] 是否标注了已知的风险和限制
- [ ] 是否检查了输出质量（无空段落、无占位符文本）

---

## 6. Agent 故障模式

| 故障 | 症状 | 处理方案 |
|------|------|---------|
| **产出不完整** | 输出文档缺少必需章节 | Critic 打回，要求补充 |
| **质量不达标** | 内容肤浅、逻辑混乱 | Critic 打回，要求重做 |
| **与上游矛盾** | 产出与前置文档冲突 | Conductor 检查一致性，必要时回溯 |
| **超出能力范围** | Agent 表示无法完成 | Conductor 分解任务或换 Agent |
| **陷入细节** | 过度优化不重要的部分 | Critic 提醒聚焦核心目标 |
| **输入文档 stale** | 读取了过期的上游文档 | Conductor 重新派发上游 Stage |

---

## 7. 各 Agent 的 AGENT.md 文件

### 执行 Agent
- `AGENTS/literature/AGENT.md` — 文献调研 Agent
- `AGENTS/ideation/AGENT.md` — 想法生成 Agent
- `AGENTS/method/AGENT.md` — 方法论设计 Agent
- `AGENTS/experiment/AGENT.md` — 实验执行 Agent
- `AGENTS/analysis/AGENT.md` — 结果分析 Agent
- `AGENTS/writing/AGENT.md` — 论文写作 Agent
- `AGENTS/figure/AGENT.md` — 图表生成 Agent

### Critic Agent 团队
- `AGENTS/critic/AGENT.md` — Critic 团队总览（含 Gate 调用策略）
- `AGENTS/critic/logic/AGENT.md` — 逻辑审查 Agent
- `AGENTS/critic/method/AGENT.md` — 方法审查 Agent
- `AGENTS/critic/evidence/AGENT.md` — 证据审查 Agent
- `AGENTS/critic/writing/AGENT.md` — 写作审查 Agent
- `AGENTS/critic/novelty/AGENT.md` — 新颖性审查 Agent
- `AGENTS/critic/ethics/AGENT.md` — 伦理审查 Agent

### 其他
- `AGENTS/review/AGENT.md` — 模拟审稿 Agent
- `AGENTS/conductor/AGENT.md` — 主编排 Agent

---

## 8. MD 收发规范

所有 Agent 必须遵循 `docs/07_MD_PROTOCOL.md` 中定义的规范：

- **产出时**: 遵循 Universal Document Schema，包含完整 Metadata 和所有必需章节
- **接收时**: 执行 9 步解析流程（存在性检查 → 元数据解析 → 内容提取 → 推理审查 → 验证确认 → 风险加载 → 下游接口提取 → 回溯触发器检查 → 一致性交叉验证）

---

> **下一步**: 阅读 `07_MD_PROTOCOL.md` 了解详细的 MD 收发规范，然后阅读各 Agent 的 AGENT.md 文件。
