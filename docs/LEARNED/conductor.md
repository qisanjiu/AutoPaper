---
type: learned
learned_from: "mmwave-breath-dl"
stage: "ALL"
date: "2026-04-21"
clear_after: "never"
severity: high
---

## 问题描述

回溯后重新执行了 S03-S05，但忘记重新执行对应 Gate (G1) 的 Critic 审查。同时 handoff_P1_P2.md 也未更新，导致下游 Agent 可能基于过时的信息执行。

具体表现：
1. S03-S05 从 v2 回溯后重新执行为 v3，核心研究问题从"四合一"收缩为"静态单目标+物理先验"
2. 但 handoff_P1_P2.md 仍保留 v2 内容（运动鲁棒+多目标）
3. G1 审查报告（reviews/G1_*）仍为 v2 版本审查结果
4. 如果直接推进到 S06，Method Agent 会读取过时的 handoff 和 Gate 结果，导致方法设计方向错误

## 根因分析

1. **框架流程缺失明确规则**：SKILL.md 和 AGENT.md 中未明确"回溯后必须重新审查对应 Gate"的强制规则
2. **自动化盲区**：state_manager.py advance 命令在 S05（Gate Stage）advance 时自动标记 Phase 为 completed，但未检查这是回溯后的重新执行
3. **Conductor 遗漏**：Conductor Agent 在 advance 后未验证 handoff 和 Gate 审查是否需要更新

## 预防措施

### 规则 1：回溯 = 对应 Gate 必须重新审查

**任何回溯操作发生后，Conductor 必须：**
1. 识别回溯影响范围（从 to_stage 到 Gate Stage）
2. 在重新执行的 Stage 全部 advance 后，**强制重新审查对应 Gate**
3. 更新 handoff_P{phase}_P{phase+1}.md
4. 标记旧 Gate 审查报告为 stale

**示例**：
- 回溯 S05 → S03（P1 内）→ 重新执行 S03-S05 → 必须重新审查 G1
- 回溯 S10 → S06（P2 内）→ 重新执行 S06-S10 → 必须重新审查 G2
- 回溯 S15 → S11（P3 内）→ 重新执行 S11-S15 → 必须重新审查 G3

### 规则 2：handoff 文档必须与 Stage 版本同步

**每次 Gate 重新审查后，Conductor 必须：**
1. 读取最新版本的 S03-S05（或对应 Stage）产出
2. 重新生成/更新 handoff_P{phase}_P{phase+1}.md
3. 在 handoff 中明确标注版本号（v3 等）和变更摘要
4. 在 handoff 中添加警告："本 handoff 为 vX 版本，旧版本已失效"

### 规则 3：用户审查触发的一体化自动推进流程

**当用户主动审查某个 Stage 并提出修改意见时，Conductor 应执行一体化处理：**

```
用户审查 Stage N → 发现问题 → Conductor 自动完成以下全部操作：
    │
    ├── 判断修改类型（局部 / 结构性）
    │
    ├── 局部修改 → 直接修改 Stage N → advance → 若 N 是 Gate Stage 则自动触发 Gate 审查
    │
    └── 结构性修改 → 回溯到 Stage N → 修改 → 重新执行 N+1... → 自动触发 Gate 审查
    │
    └── 聚合 Gate 结果 → 向用户汇报最终 verdict
```

**关键原则**：
- **单交互原则**：用户只需提出审查意见，后续所有操作自动完成
- **无中断推进**：修改完成后立即自动 advance，不等待用户确认"推进"
- **Gate 自动触发**：到达 Gate Stage 后自动调用 Critic Team，不等待用户确认"审查"

### 规则 4：state_manager.py advance 时增加回溯检测

Conductor 执行 advance 时，对 Gate Stage 增加以下检查：
```
IF current_stage IS Gate Stage:
    IF backtrack_log 中存在影响当前 Phase 的回溯记录:
        CHECK: handoff_P{X}_P{Y}.md 是否为最新版本
        CHECK: Gate 审查报告是否已重新执行
        IF 任一检查失败:
            HALT advance
            REPORT: "Gate Stage advance 被阻止：检测到回溯后未重新审查 Gate / 未更新 handoff"
            TRIGGER: Gate 重新审查流程
```

## 验证方法

- 在 state_manager.py 的 advance 逻辑中添加回溯检测
- 在 Conductor 的决策流程中添加 Gate 重审检查清单
- 每次回溯后在 pipeline_state.yaml 的 gates 字段标记对应 Gate 为 "needs_re_review"
- 人类审查后，Conductor 应自动完成"修改 → 推进 → Gate 审查 → 汇报结果"的全流程

### 规则 5：单文件原则 — 禁止版本后缀文件

**任何 Stage、Handoff、Gate 审查有且仅有一个文件。**

```
# 禁止
S03_research_questions_rev2.md
S06_methodology_design_v3.md
G1_logic_review_v3.md

# 正确
S03_research_questions.md      # 直接覆盖，版本记录在内
S06_methodology_design.md      # 直接覆盖，版本记录在内
reviews/G1_aggregate.md        # 单一聚合文件
```

**Conductor 执行回溯后的文件操作**：
1. 读取最新版本内容
2. **直接覆盖**原文件（不创建新文件）
3. 在原文件的 `## 7. 版本记录` 中追加新版本说明
4. Stage 的补充内容（数据集核实、参数调研等）作为原文件的附录章节合并

**示例**：
- S02 的数据集核实和采样参数调研 → 合并为 `S02_literature_survey.md` 的附录 A/B
- 不创建 `S02_dataset_verification.md` 或 `S02_dataset_sampling_parameters.md`

## 已实施的框架更新

以下文档已更新以反映上述规则：
- `docs/AGENTS/conductor/AGENT.md` — 新增 §6 "用户审查触发的一体化自动推进流程"
- `docs/06_FEEDBACK_LOOP.md` — §4.1.1 和 §4.2 已更新，新增 Gate 重审规则和自动推进流程
- `docs/07_MD_PROTOCOL.md` — 新增 §1.5 "文件命名与版本管理规范"
- `.agents/skills/autopaper/SKILL.md` — 本项目入口 skill 文件
- `spiral/state.py` — backtrack spiral_count 已修正为递增目标 Phase
