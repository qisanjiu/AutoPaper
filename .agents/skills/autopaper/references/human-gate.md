# 人类介入审查（Human-in-the-Loop Gate）

## 设计哲学

用户是最高级别的 Critic。AutoPaper 默认全自动运行（AUTO_PROCEED），但用户可以随时自发介入，无需等待 Conductor 提问。

用户可以在**任何时刻**对**任何已完成的 Stage** 提出审查意见，系统将自动处理：记录意见 → 回溯/重置 → 重新执行 → 继续推进。

## 运行模式

### 模式 1：AUTO（默认）
- Gate 自动通过
- Conductor 不打扰用户
- 适合：用户信任系统，或时间紧迫

### 模式 2：HUMAN（用户主动触发）
- 用户随时说"审查 S05"、"S05 有问题"等
- Conductor 立即响应，记录意见并采取行动
- 适合：用户想深度参与关键决策

两种模式可以无缝切换。全自动运行时用户可随时喊停并介入。

## 介入触发词

Conductor 识别以下说法为用户介入请求：

| 触发模式 | 示例说法 | 系统响应 |
|---------|---------|---------|
| 审查请求 | "审查 S05"、"看看 S05 的产出" | 读取并展示 S05 产出 |
| 发现问题 | "S05 有问题"、"S05 需要修改" | 询问具体问题，或默认 REVISE |
| 具体意见 | "S05 假设不成立"、"S05 文献不够" | 直接记录为 REVISE 意见 |
| 确认通过 | "通过"、"S05 OK"、"没问题" | 记录为 PASS |
| 要求回溯 | "回到 S04"、"从 S04 重来" | 执行 backtrack |
| 全局审查 | "我要审查所有 Stage" | 列出所有已完成 Stage，让用户选择 |

## 处理流程

```
用户介入
    │
    ▼
识别目标 Stage + 用户意见
    │
    ├── 用户仅说"审查 S05"（无明确意见）
    │       → 读取 S05 产出文档
    │       → 展示给用户
    │       → 等待用户给出具体意见
    │
    ├── 用户给出具体意见（"S05 假设有问题"）
    │       → 保存意见到 knowledge/reviews/human_S05_review.md
    │       → 询问 verdict（或直接根据语境判断）
    │
    ▼
执行 verdict
    │
    ├── pass
    │       → 记录通过
    │       → 继续正常推进
    │
    ├── revise
    │       → 重置 pipeline_state.yaml 到该 Stage
    │       → 将该 Stage 状态设为 in_progress
    │       → 重新执行该 Stage（携带用户反馈作为约束）
    │       → 完成后继续推进
    │
    └── backtrack
            → 记录回溯日志
            → 重置到目标 Stage
            → 从该 Stage 重新执行
```

## 重新执行时的反馈传递

当用户意见触发 REVISE 时，必须将用户反馈传递给重新执行的子 Agent：

```
[Human Review Feedback for S05]
用户审查意见：{opinion}
需要修改的内容：{specific issues}
请根据以上反馈修改 S05 产出，确保问题得到解决。
```

## 与自动 Critic 的协同

用户介入审查与自动 Critic 不是互斥的，而是互补的：

1. **自动 Critic** 处理常规质量问题（格式、逻辑、统计正确性）
2. **用户审查** 处理战略性判断（研究方向、假设合理性、领域洞察）

用户的 REVISE 意见可以与自动 Critic 的 REVISE 意见合并，作为综合修改要求。

## 审查记录

所有用户审查意见保存于：

```
knowledge/reviews/
├── human_S05_review.md
├── human_S10_review.md
└── ...
```

格式：
```markdown
# Human Review — S05

**Project**: {name}
**Stage**: S05
**Verdict**: REVISE
**Time**: 2026-04-20T08:33:51

## Opinion

{用户意见原文}

---
*This review was submitted by the user via the human-gate mechanism.*
```

同时记录到 `pipeline_state.yaml` 的 `human_reviews` 数组中，便于后续追踪。
