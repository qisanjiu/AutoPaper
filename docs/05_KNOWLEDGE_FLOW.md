# 知识流转规范

> **原则**: 知识通过规范化 Markdown 文档在 Stage 之间流转，Agent 不依赖内存传递信息

---

## 1. 核心理念

AutoPaper 的一个核心设计是 **"知识即文档"**。Agent 之间的所有信息传递都通过读写 Markdown 文档完成，而不是通过对话上下文或内存状态。

**为什么？**

1. **可审查性**：任何人（包括人类）都可以随时查看 `knowledge/` 目录，了解项目的完整历史
2. **可回溯性**：回溯到任意 Stage 时，该 Stage 的输入文档就是当时的完整上下文
3. **Agent 独立性**：子 Agent 被创建时不需要继承父 Agent 的全部上下文，只需读取指定的输入文档
4. **容错性**：即使某个 Agent 崩溃，其产出已经保存为文档，不会丢失

---

## 2. 文档类型

### 2.1 Stage 产出文档

命名规范：`S{NN}_{stage_name}.md`

每个 Stage 产出文档必须包含以下章节：

```markdown
# [Stage 标题]

## 1. [核心内容章节]
（Stage 的具体产出内容）

## 2. [附加分析章节]
（如适用）

## N. 传递给下游的信息
- 关键发现 1: ...
- 关键发现 2: ...
- 下游需要特别注意: ...
- 建议的下一步: ...
```

**"传递给下游的信息"是强制章节。** 它让下游 Agent 无需阅读整个文档就能抓住重点。

### 2.2 Handoff 文档

命名规范：`handoff_P{X}_to_P{Y}.md`

当 Phase X 通过 Gate 后，Conductor 生成 Handoff 文档，作为 Phase Y 的"入职手册"。

结构：

```markdown
# Handoff: Phase X → Phase Y

## 已完成的工作摘要
（3-5 句话）

## 关键决策记录
- 决策 1: ...
- 决策 2: ...

## 传递给下游的核心信息
- 核心发现: ...
- 核心假设: ...
- 验证状态: ...
- **方法论/技术方案库**（来自 S02 §5）:
  - 可用于解决 Gap 的核心方法/架构: ...
  - 最具潜力的新兴模块: ...
  - 建议优先考察的技术路线: ...

## 已知风险与限制
- 风险 1: ... → 缓解: ...

## 下游需要特别注意的事项
- 注意 1: ...

## 回溯历史
- 本 Phase 经历了 N 次回溯
- 原因: ...
```

### 2.3 状态文件

**pipeline_state.yaml**：全局状态
```yaml
project:
  name: "string"
  topic: "string"
  venue: "ICLR"  # 目标投稿 venue
current:
  phase: "P1"
  stage: "S01"
  status: "in_progress"
  started_at: "ISO8601"
history:
  - stage: "S01"
    agent: "literature"
    status: "completed"
    output: "knowledge/S01_topic_analysis.md"
    started_at: "..."
    completed_at: "..."
backtrack_log:
  - from: "S16"
    to: "S11"
    reason: "..."
    timestamp: "..."
spiral_count:
  P1: 1
  P2: 1
  # ...
gates:
  G1:
    status: "passed"
    score: "8/10"
    timestamp: "..."
```

**decision_log.md**：决策记录
```markdown
# Decision Log

## [YYYY-MM-DD HH:MM:SS] #{N}
**Context**: Stage XX / Gate GY
**Trigger**: ...
**Decision**: ...
**Reasoning**: ...
**Agent**: ...
**Documents**: ...
```

**spiral_log.md**：螺旋进度记录
```markdown
# Spiral Log

## Spiral 1 (2026-04-15)
- P1: PASS (Gate G1, 8/10)
- P2: PASS (Gate G2, 7/10)
- P3: BACKTRACK (S16 → S11, code bug)
- P3 (retry): PASS (Gate G3, 8/10)
- P4: PASS (Gate G4, 9/10)
- P5: PASS (Gate G5, 8/10)
- P6: IN_PROGRESS
```

### 2.4 Agent 注册表

**agent_registry.yaml**：记录所有 Agent 的调用历史
```yaml
agents:
  literature:
    invocations:
      - stage: "S01"
        started_at: "..."
        completed_at: "..."
        status: "success"
  ideation:
    invocations:
      - stage: "S03"
        started_at: "..."
        status: "success"
```

---

## 3. 文档流转图

```
用户输入主题
    │
    ▼
knowledge/S01_topic_analysis.md ──► S02 使用 S01
    │                                    │
    ▼                                    ▼
knowledge/S02_literature_survey.md ──► S03 使用 S01+S02
    │                                    │
    ▼                                    ▼
knowledge/S03_research_question.md ──► S04 使用 S02+S03
    │                                    │
    ▼                                    ▼
knowledge/S04_hypothesis_generation.md ──► S05 使用 S03+S04
    │                                        │
    ▼                                        ▼
knowledge/S05_novelty_feasibility.md ──► Gate G1
                                              │
                                              ▼
                                    knowledge/handoff_P1_to_P2.md
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
              S06 使用 handoff          S07 使用 S06             S08 使用 S06+S07
                    │                         │                         │
                    ▼                         ▼                         ▼
              S09 使用 S08               S10 使用 S06-S09
                    │                         │
                    └─────────────────────────┘
                                │
                                ▼
                          Gate G2
                                │
                                ▼
                    knowledge/handoff_P2_to_P3.md
                                │
                                ▼
                    ...（后续 Phase 类似）...
```

---

## 4. 文档规范

### 4.1 Markdown 格式规范

- 使用 ATX 标题（`#` 而非 underline）
- 表格使用标准 Markdown 表格语法
- 代码块标注语言
- 使用相对路径引用其他文档
- 所有数值必须标注单位

### 4.2 引用规范

引用其他文档时使用：
```markdown
详见 [S02 文献综述](knowledge/S02_literature_survey.md) 中的 Gap 分析。
```

引用具体部分时使用：
```markdown
根据 S04 的 [H1 假设](knowledge/S04_hypothesis_generation.md#h1)...
```

### 4.3 版本控制

每个文档在修改时保留时间戳版本：

```
knowledge/
├── S01_topic_analysis.md              # 当前版本
├── S01_topic_analysis_20260415_143022.md  # 历史版本
├── S02_literature_survey.md
└── ...
```

Conductor 在更新文档时：
1. 将当前版本复制为带时间戳的版本
2. 写入新内容到主文件
3. 在 `state/pipeline_state.yaml` 中记录版本历史

---

## 5. Agent 读取规范

子 Agent 被创建后，必须按以下顺序读取文档：

```
1. AGENTS/{role}/AGENT.md        # 了解自己的身份和职责
2. state/pipeline_state.yaml      # 了解项目全局状态
3. 输入文档（由 Conductor 指定）   # 了解具体任务
4. （可选）相关的上游文档           # 获取额外上下文
```

**禁止**：子 Agent 不读取不相关的下游文档（避免信息泄露和偏见）。

---

## 6. 知识流转的可靠性保证

### 6.1 文档存在性检查

Conductor 在派发任务前必须检查：
```
FOR each input_doc in task.input_docs:
    IF not exists(input_doc):
        LOG error
        IF input_doc is critical:
            HALT
        ELSE:
            NOTIFY user
```

### 6.2 文档完整性检查

每个产出文档必须包含自检清单。Conductor 在接收产出时检查：
- 文档是否存在
- 是否包含必需的章节（特别是 "传递给下游的信息"）
- 是否为空或只有占位符
- 是否有内部矛盾（与上游文档冲突）

### 6.3 知识一致性

当 Backward Propagation 发生时，Conductor 必须：
1. 标记被回溯的 Stage 的文档为 "stale"
2. 确保下游 Agent 不会意外读取 stale 文档
3. 在新版本产出后更新引用

---

## 7. 最小知识集

每个 Stage 的最小输入知识集：

| Stage | 最小输入 | 推荐额外输入 |
|-------|---------|-------------|
| S01 | topic | 无 |
| S02 | S01 | 无 |
| S03 | S01, S02 | 无 |
| S04 | S02, S03 | S01 |
| S05 | S03, S04 | S02 |
| S06 | handoff_P1_P2 | S03-S05 |
| S07 | S06, S02 | S01 |
| S08 | S06, S07, S01, S02 | 无 |
| S09 | S08, S02 | 无 |
| S10 | S06-S09, S02 | handoff_P1_P2 |
| S11 | handoff_P2_P3, S06-S10, **S02** | 无 |
| S12 | S11, S10 | S08 |
| S13 | S11, S12, S08, S07, S09, S04 | handoff_P2_P3 |
| S14 | S13, S06, S02 | 无 |
| S15 | S14, S11 | 无 |
| S16 | S15 | S13 |
| S17 | S16, S14, S02 | S13 |
| S18 | S12, S16, S17, S02 | 无 |
| S19 | S18, S06, S02 | 无 |
| S20 | S19, S11 | 无 |
| S21 | S20, S18 | S12 |
| S22 | S12, S17, S21, S04 | handoff_P3_P4, handoff_P4_P5 |
| S23 | S22 | S04 |
| S24 | S22-S23 | handoff_P5_P6 |
| S25 | S23, S24 | S02 |
| S26 | handoff_P6_P7, S24, S02 | 无 |
| S27 | S26, S02, S24 | handoff_P1_P2 |
| S28 | S26, S06 | S08, S10 |
| S29 | S26, S12, S16, S17, S21 | S22 |
| S30 | S26, S23, S18, S12, S16 | S22 |
| S31 | S26, S23, S24, S29 | S22 |
| S32 | S26, S12, S06, S16 | S22 |
| S33 | S27-S31, S32 | handoff_P6_P7 |
| S34 | S33 | S22 |
| S35 | S34, S33 | S22, S23 |
| S36 | S35, S33 | S34 |
| S37 | S36 | S26, S33 |

---

> **下一步**: 阅读 `06_FEEDBACK_LOOP.md` 了解螺旋向前的反馈与纠错机制。
