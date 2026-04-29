# LEARNED — 经验知识库

> **说明**: 本目录存放 AutoPaper 框架从项目执行中学习到的经验教训。
> 所有内容均为**可清除的临时经验**，非框架核心定义。
> 当经验过时或不再适用时，可直接删除对应文件。

## 文件命名规范

```
docs/LEARNED/
├── README.md              # 本文件
├── conductor.md           # Conductor 编排经验
├── writing.md             # 论文写作常见陷阱
├── experiment.md          # 实验执行常见错误
├── {agent}.md             # 各 Agent 的经验教训
└── stage/
    ├── S05.md             # S05 特有的陷阱
    ├── S11.md             # S11 特有的陷阱
    └── ...                # 其他 Stage 的经验
```

## 文件格式

每个 `.md` 文件必须以 YAML frontmatter 开头：

```markdown
---
type: learned              # 必填，标识这是学习到的内容
learned_from: "project-name-timestamp"  # 来源项目
stage: "S05"               # 关联 Stage（可选）
date: "2026-04-20"         # 学习日期
clear_after: "3 projects"  # 清除条件：3个项目后 / 1个月后 / never
severity: high             # 严重程度：high | medium | low
---

## 问题描述

[简要描述遇到的问题]

## 根因分析

[为什么会出现这个问题]

## 预防措施

[下次执行时必须如何做才能避免]

## 验证方法

[如何确认问题已避免]
```

## 使用方式

Conductor 在执行 Stage 前，先检查 `docs/LEARNED/stage/S{NN}.md` 和 `docs/LEARNED/{agent}.md`。
如果存在，将内容作为**前置约束**传递给子 Agent。

## 清除规则

- `clear_after: "3 projects"` — 在 3 个新项目创建后自动归档
- `clear_after: "1 month"` — 在 1 个月后自动归档
- `clear_after: "never"` — 永久保留（仅用于根本性架构经验）

**手动清除**: 直接删除文件即可。不影响框架运行。
