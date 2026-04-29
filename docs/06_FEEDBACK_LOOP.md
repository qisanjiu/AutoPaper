# 反馈与纠错机制

> **核心理念**: 工作流不是线性的，而是螺旋向前的。发现错误时，回溯到源头修复，然后重新前进。

---

## 1. 为什么需要螺旋机制？

传统工作流的问题是：**一旦进入下一阶段，前面的错误就被"固化"了。**

例如：
- 实验代码有 bug（S11）→ 得到了错误的结果（S12）→ 基于错误结果得出了错误结论（S23）→ 论文写错了（S29）→ 审稿人发现问题（S35）

在 AutoPaper 中，错误会在最早可能的阶段被发现，并**回溯到源头修复**：
- S12 发现代码 bug → 回溯到 S11 修复 → 重新运行 S12 → 继续前进
- 或者 Analysis 在 S13 发现结果不合理 → 回溯到 S11/S12 → 修复后重新执行

---

## 2. 双循环架构：Inner Loop + Outer Loop

借鉴 ai-research-skills 的设计，AutoPaper 的反馈机制分为两个时间尺度的循环：

### 2.1 Inner Loop（内部优化循环）

Inner Loop 用于快速迭代优化。AutoPaper 有两种 Inner Loop 模式：

#### 模式 A：单 Stage 内循环

**P6/P7 Writing - PaperOrchestra 内容精炼循环（S35）**:
```
Review Agent 审稿 → Writing Agent 修改 → Review Agent 重新审稿
                                                        │
      ┌──────────────── accept / revert ────────────────┘
      ▼
  保存快照 / 回退到上一版本
```
- 遵循严格的 Accept/Revert Halt Rules
- 只有评分真正提升的修改才被保留
- 每次迭代前保存快照

#### 模式 B：跨 Stage 循环（P3 Execution）

**P3 Execution - AutoResearch 风格实验循环（在 S12 内完成）+ S13 决策点**：

S12: 实验执行、结果收集与初步分析
```
Inner Loop within S12:
  modify code → git commit → run iteration (5-30min) → 记录结果 → preliminary analysis
        ▲
        └──────────── 持续探索，所有尝试保留 ───────────┘
  
  循环停止（指标收敛/预算耗尽/方向验证/外部中断）
        │
        ▼
S13: Analysis Agent 深度分析所有结果
        │
        ├── KEEP ──────────→ 推进到 P4
        ├── FIX ───────────→ 回溯到 S12（继续迭代）
        ├── BACKTRACK ─────→ S11（修复代码）
        ├── BACKTRACK ─────→ S06（重新设计方法）
        ├── BACKTRACK ─────→ S08（修订实验设计）
        └── BACKTRACK ─────→ S04（修正假设）
```
- 循环由 Experiment Agent 在 S12 内自主运行，**不做最终决策**
- **所有实验尝试都通过 git commit 保存，不做 `git reset`**
- 收敛后停止探索（指标收敛/预算耗尽/方向已充分探索）
- **S13 (Analysis Agent) 是 Phase 3 的唯一决策点**：基于深入分析（过拟合、数据泄露、训练稳定性等）而非仅看表面指标
- 用 empirical critique 代替实验阶段的简单指标对比
- git 提供时间机器，通过回溯实现无损回退
- **即使 S12 效果不佳（低指标收敛、预算耗尽未收敛、负向验证），也正常进入 S13 由 Analysis Agent 做出分类决策**

**Inner Loop 的特点**：
- 周期短到中等（几分钟到几十分钟 per iteration）
- 自动化程度高（无需 Conductor 介入，Agent 自主运行）
- 目标是**局部优化**

### 2.2 Outer Loop（元反思循环）

Outer Loop 发生在 **Phase 之间或整个流程层面**，用于战略级调整。典型场景：

**P6 Synthesis → P2 Design 回溯**:
```
Analysis Agent 在 S23 综合 findings
    │
    ▼
发现核心假设被否定
    │
    ▼
触发 Backward Propagation 到 S04
    │
    ▼
重新设计方法（S06）→ 重新实验（P3）→ 重新消融（P4）→ 重新分析（P5）
```

**Outer Loop 的触发条件**：
- Gate 审查发现根本性问题
- Review Agent 在 S35 质疑核心贡献
- Analysis Agent 在 S23 发现研究方向需要调整
- Conductor 检测到系统性失败模式

**Outer Loop 的特点**：
- 周期长（几小时到几天）
- 涉及跨 Phase 回溯
- 目标是**战略校正**

### 2.3 两种循环的协同

```
                    Outer Loop (Backward Propagation)
                    ←─────────────────────────────────→
                    
P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8
          │              │              │
          ▼              ▼              ▼
      Inner Loop     Inner Loop     Inner Loop
       (S12)         (S23分析)      (S36精炼)
```

Inner Loop 确保每个 Stage 的产出质量达到局部最优，Outer Loop 确保整个研究方向不偏离轨道。

---

## 3. 三层反馈机制

### 3.1 第一层：Stage 内自检

每个子 Agent 在提交产出前进行自我检查：

```
Agent 产出文档
    │
    ▼
自检清单
    │
    ├── 通过 → 提交给 Conductor
    └── 发现问题 → 自我修正 → 重新自检
```

自检清单因 Agent 而异（详见各 Agent 的 AGENT.md）。

### 3.2 第二层：Gate 审查

每个 Phase 结束时，Critic Agent 进行正式审查：

```
Phase 完成
    │
    ▼
Gate (Critic Agent)
    │
    ├── PASS → 进入下一 Phase
    ├── REVISE → 在当前 Phase 内修改 → 重新 Gate
    ├── BACKTRACK → 回溯到上游 Stage → 重新执行
    └── HALT → 暂停，等待人工决策
```

Gate 是 **"硬性检查点"**，不通过就不能前进。

### 3.3 第三层：持续监控

Conductor 持续监控：
- 同一 Stage 的重复失败次数
- 回溯频率和模式
- 产出质量趋势
- **Context Compaction 风险**：监控子 Agent 的运行时间/交互轮次，在可能触发 context compaction 前主动提醒恢复

如果发现异常模式，Conductor 可以：
- 主动调用 Critic 进行额外审查
- 向用户报告系统性问题
- 调整策略（如更换 Agent、放宽/收紧标准）
- **触发 Context Recovery**：如果检测到子 Agent 可能因 context compaction 丢失记忆，要求其重新加载 AGENT.md

---

## 4. Backward Propagation 机制

### 4.1 触发条件

以下情况可能触发回溯：

| 触发场景 | 发现阶段 | 回溯目标 | 回溯发起方产出的修改方向 |
|---------|---------|---------|------------------------|
| **人类审查 (Human Review) 要求修订任意阶段** | 任意阶段 | **被修订阶段本身** | 人类直接给出修改意见（天然携带方向） |
| 代码 bug | S12 (Experiment Iteration) | S11 | S12 报告代码问题 → S13 深度分析后最终决策 |
| 结果不可复现 | S13 (Verification) | S11 或 S12 | S13 给出可靠性诊断 + 实验修复方向 |
| 效果不达预期（代码/实现层） | S13 (Verification) | S11 | S13 诊断代码层面问题 + 修复方向 |
| 效果不达预期（方法设计层） | S13 (Verification) | S06 | S13 诊断方法缺陷 + 重新设计方向 |
| 效果不达预期（实验设计层） | S13 (Verification) | S08 | S13 诊断实验设计问题 + 修订方向 |
| 效果不达预期（数据/基准层） | S13 (Verification) | S07 | S13 诊断数据集质量问题 + 替代数据集建议 |
| 效果不达预期（baseline 选择层） | S13 (Verification) | S09 | S13 诊断 baseline 选择问题 + 替换/补充建议 |
| 核心假设被否定 | S13 (Verification) | S04 | S13 给出假设否定诊断 + 新假设方向 |
| 消融执行报错 | S16 (Ablation Execution) | S15 或 S14 | S16 给出错误诊断 + 代码/设计修复方向 |
| 消融揭示方法缺陷 | S17 (Ablation Analysis) | S06 | S17 给出缺陷诊断 + 方法组件改进方向 |
| 分析实验失败 | S20 (Analysis Experiment) | S19 | S20 给出失败诊断 + 设计修改方向 |
| 分析结果不支持 | S21 (Analysis Results) | S20 或 S19 | S21 给出分析诊断 + 实验/设计修复方向 |
| 写作发现方法不清 | S34 (Internal Review) | S06 或 S28 | S34 给出方法/写作问题 + 改进方向 |
| 审稿人要求补充实验 | S35 (Peer Review) | S19 或 S10 | S35 给出审稿意见 + 实验补充方向 |
| 审稿人质疑核心假设 | S35 (Peer Review) | S04 | S35 给出质疑分析 + 假设修正方向 |

#### 4.1.1 人类审查 (Human Review) 触发回溯的通用规则 **[核心规范]**

> **⚠️ 这是 AutoPaper 的强制性核心流程，适用于所有 37 个 Stage。**

**规则**：当人类审查（用户、导师、审稿人）指出**任意阶段**的产出存在需要修改的问题时，必须触发 **该阶段及其所有下游阶段** 的回溯更新。

**判断是否需要回溯的标准**：

| 修改类型 | 是否触发回溯 | 说明 |
|---------|------------|------|
| **Major Revision**（重大修订） | **必须回溯** | 包括但不限于：新增/删除/修改 Gap、μGap、核心假设、方法设计、实验结论、主要图表、新颖性声明 |
| **Minor Revision**（轻微修订） | **不触发回溯** | 仅限于：错别字修正、格式调整、参考文献补充、措辞优化、不影响结论的表述微调 |
| **不确定时** | **默认触发回溯** | 如果无法明确判断是 major 还是 minor，按 major 处理，触发回溯 |

**回溯执行流程**：

```
1. 人类审查指出 Stage N 需要修订
       │
       ▼
2. Conductor 判断修订类型（Major / Minor）
       │
       ├── Minor → 直接修改 Stage N，不触发回溯
       │
       └── Major → 执行步骤 3-7
       │
       ▼
3. 执行回溯命令：
   python scripts/state_manager.py backtrack <current_stage> <stage_N> \
     "Human review: [简要说明修订内容]. Stage N and all downstream stages need update."
       │
       ▼
4. 修改 Stage N 的产出文档
       │
       ▼
5. 重新执行 Stage N+1, N+2, ... 直到当前阶段
   （每个下游阶段必须检查：Stage N 的修改是否影响本阶段的逻辑/结论）
       │
       ▼
6. 更新所有受影响阶段的版本号（vX → vX+1）和 Metadata
       │
       ▼
7. 在 spiral_log.md 中记录本次回溯和重新执行轨迹
       │
       ▼
8. **自动推进到 Gate（新增）**：
   - 重新执行所有下游 Stage 直到 Gate Stage
   - 每个 Stage 完成后自动 advance，无需用户确认
   - 更新所有受影响 Stage 的版本号和 Metadata
       │
       ▼
9. **自动触发 Gate 审查（新增）**：
   - 到达 Gate Stage 后，自动调用 Critic Team 进行 Gate 审查
   - 更新 handoff_P{phase}_P{phase+1}.md
   - 标记旧 Gate 审查报告为 stale
   - 聚合 Critic 结果，向用户汇报最终 verdict
```

**关键原则**：
- **版本一致性原则**：任何时刻，当前阶段之前的所有阶段产出必须基于**同一版本**的上游文档。不允许"S02 是 v3，但 S03 还是基于 S02-v1"的状态存在。
- **全链路回溯原则**：Major Revision 不能只修改单个阶段就继续前进，必须从修订点重新走完整条链路。
- **诚实标注原则**：回溯后的重新执行必须在文档中显式标注更新内容和原因，不能悄然修改不留痕迹。
- **Gate 重审原则（新增）**：**任何回溯操作发生后，对应 Gate 必须重新审查**。回溯 = 该 Phase 的 Gate 状态失效，必须重新走 Gate 流程。
- **一体化原则（新增）**：用户审查 Stage N 后，Conductor 应自动完成"修改 → 推进 → Gate 审查 → 汇报结果"的全流程，用户只需交互 1 次。

**示例**：

```
示例 1：S02 人类审查要求新增 μGap
- 回溯：S06 → S03
- 修改：S02-v2（新增 μGap-1~3）
- 重新执行：S03（新增子问题对应 μGap）→ S04（新增辅助假设）→ S05（更新新颖性声明）
- 结果：S02-v2, S03-v2, S04-v2, S05-v2

示例 2：S06 人类审查要求修改方法架构
- 回溯：S11 → S06
- 修改：S06-v2（修改网络架构设计）
- 重新执行：S07（更新基准选择）→ S08（更新实验协议）→ S09（更新 baseline）→ S10（更新完整计划）
- 结果：S06-v2, S07-v2, S08-v2, S09-v2, S10-v2

示例 3：S27 人类审查要求修改 Introduction 的一个段落
- 判断：措辞优化，不影响研究问题/假设/结论
- 处理：Minor Revision，直接修改 S27，不触发回溯
```

### 4.2 回溯执行流程（携带修改方向）

```
1. Critic/Review Agent / Analysis Agent 发现问题，建议 BACKTRACK
   或 用户审查提出结构性修改意见
       │
       ▼
2. 回溯发起方产出「回溯修改方向」(Backtrack Direction)
   - 问题诊断（根因分析）
   - 修改方向/建议（非代码级具体方案）
   - 预期效果与验证方式
   → 保存到当前 Stage 产出文档的「回溯修改方向」章节
       │
       ▼
3. Conductor 读取「回溯修改方向」，确认回溯目标 Stage
   - 验证修改方向与回溯目标的合理性
   - 计算最小影响范围
       │
       ▼
4. Conductor 更新 pipeline_state.yaml：
   - current.phase = target_phase
   - current.stage = target_stage
   - current.status = "in_progress"
   - 标记目标 Stage 之后所有 Stage 为 "stale"
   - 标记对应 Gate 为 "needs_re_review"
       │
       ▼
5. Conductor 记录回溯日志：
   - from: 发现问题的 Stage
   - to: 回溯目标 Stage
   - reason: 根因分析（来自「回溯修改方向」）
   - direction: 修改方向摘要
   - timestamp
       │
       ▼
6. Conductor 将「回溯修改方向」作为输入传递给回溯目标 Agent
   - 在创建回溯目标 Agent 的 prompt 中附加修改方向
   - Agent 基于方向自主制定具体修改方案
       │
       ▼
7. 回溯目标 Agent 读取修改方向，制定并执行具体修改方案
       │
       ▼
8. 重新执行所有下游 Stage 直到 Gate Stage
   （每个 Stage 完成后自动 advance）
       │
       ▼
9. 强制触发对应 Gate 重新审查
   - 调用 Critic Team
   - 产出新的 Gate 审查报告
   - 更新 handoff_P{phase}_P{phase+1}.md
   - 标记旧 Gate 审查报告为 "stale"
       │
       ▼
10. 聚合 Gate 结果，向用户汇报最终 verdict
       │
       ├── PASS → 进入下一 Phase
       ├── REVISE → 在当前 Phase 内修改 → 重新 Gate
       ├── BACKTRACK → 继续回溯（携带新的修改方向）
       └── HALT → 暂停，等待人工决策
```

**⚠️ 关键新增规则：回溯后必须重新审查 Gate**

任何回溯操作完成后，无论 state 是否已自动标记 phase_completed，都必须：
1. 重新审查对应 Gate（调用 Critic Team）
2. 更新 handoff 文档
3. 标记旧 Gate 报告为 stale

**违反此规则的后果**：
- 下游 Agent 读取过时的 handoff，方法设计方向错误
- 旧 Gate 审查报告与重新执行的 Stage 版本不匹配
- 项目状态出现"Phase 已完成但 Gate 未审查"的逻辑漏洞

### 4.3 最小回溯原则（携带修改方向）

回溯时**只重置必要的 Stage**，且**必须携带修改方向**：

```
例子 1：S13 发现代码实现有问题
- S13 产出「回溯修改方向」：问题诊断（模型某层未正确实现）+ 修改方向（检查 XX 模块的实现）
- 回溯到 S11
- S11 读取修改方向，自主修复代码 → 重新执行 S12, S13...

例子 2：S13 发现结果不可复现
- S13 产出「回溯修改方向」：问题诊断（随机种子未固定）+ 修改方向（在 train.py 中固定所有随机种子）
- 回溯到 S11（修复随机种子）
- S11 读取修改方向，执行修复 → 重新执行 S12, S13...

例子 3：S13 发现方法核心架构设计不合理（效果不达预期）
- S13 产出「回溯修改方向」：问题诊断（跨模态融合机制过于简单导致指标仅与 baseline 持平）+ 修改方向（增加注意力机制、增加特征交互层）
- 回溯到 S06（重新设计方法）
- S06 读取修改方向，重新设计核心架构 → S07→S08→S09→S10→重新执行 P3

例子 4：S13 发现核心假设被实验否定
- S13 产出「回溯修改方向」：问题诊断（假设的自监督预训练会提升下游性能，但实验证明无显著效果）+ 修改方向（探索替代的特征学习策略或修正假设范围）
- 回溯到 S04（修正假设）
- S04 读取修改方向，调整假设 → S05→S06(部分)→...→重新执行 P3

例子 4a：S13 发现数据集存在系统性问题
- S13 产出「回溯修改方向」：问题诊断（数据集标注错误率 > 15%，验证集与测试集分布漂移显著）+ 修改方向（更换为标注质量更高的数据集 X 或 Y）
- 回溯到 S07（更换基准数据集）
- S07 读取修改方向，重新选择数据集 → S08→S09→S10→S11→S12→S13
- **关键**：更换数据集后，baseline 也需要在新数据集上重新评估

例子 4b：S13 发现 baseline 选择不当导致虚假结论
- S13 产出「回溯修改方向」：问题诊断（选用的 baseline 为 2018 年方法且已知在该任务上表现弱，所有方法均超过它导致 superiority 虚假；缺少 2023 年的 SOTA 方法 X 作为对比）+ 修改方向（补充 baseline X，移除不适用方法 Y）
- 回溯到 S09（重新选择 baseline）
- S09 读取修改方向，调整 baseline 列表 → S10→S11→S12→S13

例子 5：S16 消融执行报错
- S16 产出「回溯修改方向」：问题诊断（消融变量隔离错误）+ 修改方向（检查消融代码）
- 回溯到 S15（修复消融代码）
- S15 读取修改方向，修复代码 → 重新执行 S16, S17...

例子 6：S21 发现分析实验结果不支持假设
- S21 产出「回溯修改方向」：问题诊断（分析维度选择不当）+ 修改方向（重新设计分析实验）
- 回溯到 S19（重新设计分析实验）
- S19 读取修改方向，调整设计 → 重新执行 S20, S21...

例子 7：S35 审稿人质疑核心假设
- S35 产出「回溯修改方向」：问题诊断（假设普适性不足）+ 修改方向（限定假设适用范围）
- 回溯到 S04（重新论证假设）
- S04 读取修改方向，调整假设 → 重新执行 S05, S06(部分), S28, S30, S33-S36, S37
```

### 4.4 回溯保护机制

防止无限回溯：

```
IF 同一 Stage 的 spiral_count >= 3:
    Conductor 必须：
    1. 向用户报告反复失败的情况
    2. 提供选项：
       a) 人工介入指导
       b) 降低该 Gate 标准继续
       c) 跳过当前 Phase（不推荐）
    3. 记录用户选择到 decision_log
    4. 如果用户选择继续，标记为 "forced proceed"
```

---

## 5. 螺旋日志

### 5.1 记录内容

`state/spiral_log.md` 记录每次螺旋的完整轨迹：

```markdown
# Spiral Log

## Spiral 1 (2026-04-15 14:30 - 2026-04-16 08:00)

### Phase 1: Discovery
- S01: completed (Literature Agent)
- S02: completed (Literature Agent)
- S03: completed (Ideation Agent)
- S04: completed (Ideation Agent)
- S05: completed (Ideation Agent)
- Gate G1: PASS (8/10)
  - Critic 评价: "研究问题清晰，gap 识别准确"

### Phase 2: Design
- S06: completed (Method Agent)
- S07: completed (Method Agent)
- S08: completed (Method Agent)
- S09: completed (Method Agent)
- S10: completed (Method Agent)
- Gate G2: PASS (7/10)
  - Critic 评价: "实验设计合理，但消融设计可以更完整"

### Phase 3: Execution
- S11: completed (Experiment Agent)
- S12: completed (Experiment Agent)
  - Exploration Loop: 7 iterations (all recorded via git commit)
  - Best surface metric: 0.847 (vs baseline 0.812)
  - Stop reason: 指标收敛（连续 3 轮 < 1% 改善）
  - S12 不做决策，将完整记录移交给 S13
- S13: completed (Analysis Agent)
  - 深度分析：过拟合检查通过，数据泄露检查通过，训练稳定
  - 决策: KEEP（3 个主要 benchmark 上显著优于 baseline，p < 0.01）
  - 回溯修改方向：无（KEEP 决策）
- Gate G3: PASS (8/10)

### Phase 4: Ablation
- S14: completed (Experiment Agent)
- S15: completed (Experiment Agent)
- S16: completed (Experiment Agent)
- S17: completed (Analysis Agent)
- Gate G4: PASS (9/10)

### Phase 5: Further Analysis
- S18: completed (Analysis Agent)
  - Found interesting failure mode patterns
- S19: completed (Analysis Agent)
- S20: completed (Experiment Agent)
- S21: completed (Analysis Agent)
- Gate G5: PASS (8/10)

### Phase 6: Synthesis
- S22: completed (Analysis Agent)
- S23: completed (Analysis Agent)
- S24: completed (Writing Agent)
- S25: completed (Ideation Agent)
- Gate G6: PASS (8/10)

### Phase 7: Writing
- S26: completed (Writing Agent)
- S27-S31: completed (Writing Agent, parallel with S32)
- S32: completed (Figure Agent)
- S33: completed (Writing Agent)
- Gate G7: REVISE
  - Critic 评价: "Introduction 的 motivation 不够强"
  - 修改: S27 重写 Introduction
  - Gate G7 (retry): PASS (8/10)

### Phase 8: Refinement
- S34: completed (Critic Agent)
- S35: completed (Review Agent)
  - 审稿人 A: 6/10 (方法有新意但实验不够充分)
  - 审稿人 B: 7/10 (写作清晰但 related work 有遗漏)
  - 审稿人 C: 5/10 (质疑核心假设的普适性)
- S36: completed (Writing Agent + Review Agent)
  - Iteration 1: 回应审稿人 A (补充实验) → score 5.5→6.5 → ACCEPT
  - Iteration 2: 回应审稿人 B (补充文献) → score 6.5→6.5 → HALT (无改善且无新可操作弱点，迭代饱和)
  - Final accepted version: iter1
- Gate G8: PASS (7/10)

### Phase 8: Refinement (cont'd)
- S37: completed (Writing Agent) — 最终编译 + 提交包生成

### 最终产出
- 论文 PDF: artifacts/paper.pdf
- 提交包: artifacts/submission/
- 完整知识文档: knowledge/
```

### 5.2 回溯记录

```markdown
## Backtrack History

### Backtrack #1
- **时间**: 2026-04-15 20:30
- **从**: S13 (Result Verification)
- **到**: S11 (Code Generation)
- **原因**: 结果不可复现，发现随机种子未固定
- **修复**: 在代码中添加随机种子设置
- **重新执行**: S12, S13
- **结果**: 修复成功，结果可复现

### Backtrack #2
- **时间**: 2026-04-15 22:00
- **从**: S13 (Result Verification)
- **到**: S06 (Methodology Design)
- **原因**: S13 深度分析发现最佳效果仅 0.812（baseline 0.810），统计不显著，根因分析为方法核心架构设计不合理，非代码实现问题
- **修复**: 重新设计核心网络架构，增加跨模态注意力机制
- **重新执行**: S06→S07→S08→S09→S10→S11→S12→S13
- **结果**: 重新设计后指标提升至 0.847，统计显著

### Backtrack #3
- **时间**: 2026-04-16 02:00
- **从**: S35 (Peer Review, 审稿人 C)
- **到**: S04 (Hypothesis Generation)
- **原因**: 审稿人质疑核心假设的普适性
- **修复**: 重新限定假设的适用范围，补充边界条件分析
- **重新执行**: S05, S06(部分), S28, S30, S33-S36, S37
- **结果**: 修改后审稿人 C 的模拟评分提升到 6/10
```

---

## 6. 收敛条件

螺旋工作流在什么情况下结束？

### 6.1 正常收敛

满足以下全部条件：
1. 所有 37 个 Stage 完成
2. 所有 Gate 通过（G1-G8）
3. S37（Final Compilation）完成

### 6.2 提前收敛（用户决定）

用户在任何时候可以：
- 要求暂停/停止
- 要求跳过某些 Stage
- 要求直接跳到特定 Stage

Conductor 必须记录用户的干预到 decision_log。

### 6.3 异常收敛

以下情况可能导致工作流异常结束：
- 同一 Stage 回溯超过 3 次，用户选择停止
- 关键资源不可用（如无法访问 GPU）
- 预算耗尽
- 用户明确要求停止

---

## 7. 与现有工作流的对比

| 机制 | AutoPaper | ARIS | PaperOrchestra | AutoResearchClaw | ai-research-skills |
|------|---------------|------|----------------|-----------------|-------------------|
| **Inner Loop** | **AutoResearch (S12) + PaperOrchestra (S36)** | 无 | Content Refinement | 快速实验 | 快速迭代 |
| **Outer Loop** | **Backward Propagation + findings synthesis** | 重新运行 skill | 无 | --from-stage | findings.md 驱动 |
| **错误发现** | Gate + 任意 Stage Critic | 运行后审查 | Content Refinement | Stage 5,9,20 Gates | 自我审查 |
| **回溯能力** | 显式 Backward Propagation | 重新运行 skill | 无（线性） | --from-stage | Outer Loop 转向 |
| **回溯粒度** | Stage 级别 | Skill 级别 | N/A | Stage 级别 | 任务级别 |
| **回溯自动化** | Conductor 自动决策 | 用户触发 | N/A | 手动指定 | 半自动 |
| **保护机制** | 3次回溯上限 | 无 | N/A | 无 | 进度报告 |
| **螺旋记录** | spiral_log.md | 无 | 无 | pipeline_summary.json | research-state.yaml |

---

## 8. 最佳实践

### 8.1 对于 Conductor

- **尽早发现问题**：在 Stage 完成时就做基本验证，不要等到 Gate
- **最小化回溯范围**：只重置必要的 Stage
- **记录回溯原因**：防止重复犯同样的错误
- **区分 Inner/Outer Loop**：Inner Loop 由 Agent 自主运行，Outer Loop 由你调度
- **保护用户时间**：回溯是正常过程，不需要每次都通知用户

### 8.2 对于 Critic

- **区分表面问题和根因**：不只说 "有问题"，要说 "根因在 Stage X"
- **给出明确建议**：BACKTRACK 时必须指出回溯目标
- **避免完美主义**：REVISE 和 BACKTRACK 要有明确标准

### 8.3 对于执行 Agent

- **诚实报告问题**：如果发现上游文档有问题，立即报告
- **保留修改痕迹**：回溯后重新执行时，记录与之前的差异
- **从错误中学习**：读取 spiral_log，了解之前为什么失败
- **Inner Loop 要节俭**：用固定时间预算的完整配置实验快速迭代，根据结果决定保留或回退。除非有明确的验证需求且计划后续回归完整运行，否则不要使用简化模型。
- **Simplicity Criterion**：小改进不值得大复杂化，勇于 discard
- **Accept/Revert 要果断**：如果修改没有真正提升质量，revert 不可惜

---

> **总结**: AutoPaper 的反馈与纠错机制确保工作流不是盲目的线性推进，而是能够**发现错误、回溯修复、螺旋前进**。这是真实科研过程的忠实模拟——科研从来不是在第一次就做对的。
