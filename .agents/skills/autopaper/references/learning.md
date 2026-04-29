# 经验学习机制（Learning from Mistakes）

## 设计哲学

AutoPaper 不是静态框架。每次项目执行都是一次学习机会。

**核心原则**：
1. 犯过的错必须被记住，下次避免
2. 学习笔记是**可清除的临时经验**，非框架核心定义
3. 学习笔记必须明确标注来源和清除条件
4. 执行 Stage 前自动加载相关学习笔记，作为前置约束

## 学习笔记生命周期

```
发现问题
    │
    ▼
根因分析（为什么发生？为什么本可提前规避？）
    │
    ▼
记录经验 → docs/LEARNED/{agent}.md 或 stage/S{NN}.md
    │
    ▼
下次执行同类型 Stage 前 → 自动加载学习笔记
    │
    ▼
作为约束传入子 Agent prompt
    │
    ▼
按 clear_after 规则清除（或手动清除）
```

## 文件格式规范

### 文件位置

```
docs/LEARNED/
├── README.md              # 本机制说明
├── conductor.md           # Conductor 编排层面的经验
├── writing.md             # Writing Agent 的写作陷阱
├── experiment.md          # Experiment Agent 的实验错误
├── {agent}.md             # 其他 Agent 的经验
└── stage/
    ├── S05.md             # S05 特有的陷阱
    ├── S11.md             # S11 特有的陷阱
    └── ...
```

### Frontmatter 规范

每个 `.md` 文件必须以 YAML frontmatter 开头：

```yaml
---
type: learned              # 必填。标识这是学习到的内容
learned_from: "project-name-timestamp"  # 来源项目名
stage: "S05"               # 关联 Stage（Agent 级经验可省略）
date: "2026-04-20"         # 学习日期
clear_after: "3 projects"  # 清除条件："3 projects" | "1 month" | "never"
severity: high             # 严重程度：high | medium | low
---
```

**clear_after 规则**：
- `"3 projects"` — 在 3 个新项目创建后自动清除
- `"1 month"` — 在 1 个月后自动清除
- `"never"` — 永久保留（仅用于根本性架构经验）

### Body 格式

```markdown
## 问题描述

[简明描述遇到的问题，包含触发场景]

## 根因分析

[为什么发生？是哪个环节缺失导致的问题？]

## 预防措施

[下次执行时必须如何做。使用祈使句，具体可操作]

## 验证方法

[如何确认问题已避免。可检查的指标或条件]
```

## 使用学习笔记

### Conductor 执行流程

执行 Stage 前，Conductor 必须：

1. 检查 Agent 级学习笔记：`docs/LEARNED/{agent_role}.md`
2. 检查 Stage 级学习笔记：`docs/LEARNED/stage/S{NN}.md`
3. 若存在，读取内容并提取 "预防措施" 部分
4. 将预防措施作为约束附加到子 Agent prompt

### 子 Agent Prompt 附加模板

```
[Learned Experience — 必须遵守]
以下是从过往项目中学习到的经验教训。执行本 Stage 时必须遵守，
避免重复相同的错误：

{learned_preventions}

请在产出中明确说明你已遵守以上预防措施。
```

### 示例

```python
from pathlib import Path

def get_learned_constraints(agent_role: str, stage: str) -> str:
    """Load learned experience for a given agent and stage."""
    constraints = []
    
    # Agent-level learned
    agent_learned = Path(f"docs/LEARNED/{agent_role}.md")
    if agent_learned.exists():
        content = agent_learned.read_text()
        # Extract "预防措施" section
        constraints.append(f"## Agent-level lessons ({agent_role}):\n{content}")
    
    # Stage-level learned
    stage_learned = Path(f"docs/LEARNED/stage/{stage}.md")
    if stage_learned.exists():
        content = stage_learned.read_text()
        constraints.append(f"## Stage-level lessons ({stage}):\n{content}")
    
    return "\n\n".join(constraints) if constraints else ""
```

## CLI 命令

### list-learned

```bash
python scripts/state_manager.py list-learned
```

列出 `docs/LEARNED/` 下所有学习笔记，显示来源、日期、严重程度、清除条件。

### learn-report

```bash
python scripts/state_manager.py learn-report
```

为当前项目生成学习报告。基于项目的 `backtrack_log` 和 `human_reviews`，自动分析重复出现的问题模式，生成建议的学习笔记条目。

输出保存到 `docs/LEARNED/reports/report-{project-name}-{date}.md`。

### clear-learned

```bash
python scripts/state_manager.py clear-learned [--dry-run]
```

按 `clear_after` 规则清除过时的学习笔记。

- `--dry-run`：只显示将要清除的文件，不实际删除

### 手动清除

直接删除 `docs/LEARNED/` 下的文件即可。不影响框架运行。

## 与框架演进的关系

**临时经验 vs 核心框架**：

- **临时经验**（`docs/LEARNED/`）：针对具体项目发现的问题，可能随时间过时
- **核心框架**（`docs/`）：经过验证的通用设计，不应频繁变更

**升级路径**：

当一个学习笔记在多个项目中反复被验证有效时，应考虑将其提升为框架核心：
1. 将预防措施写入对应的 `docs/04_STAGES.md` 中该 Stage 的"检查清单"
2. 或写入对应的 `docs/AGENTS/{role}/AGENT.md` 中
3. 然后删除 `docs/LEARNED/` 中的对应条目

## 最佳实践

1. **问题发生后立即记录**：趁记忆清晰时记录根因和预防措施
2. **预防措施必须具体可操作**：避免模糊的"注意质量"，要具体到"检查 X 字段非空"
3. **验证方法可检查**：不要写"确保正确"，要写"运行 X 脚本，输出应为 Y"
4. **定期回顾**：每 3 个项目后回顾 `docs/LEARNED/`，清除过时经验
5. **不要过度记录**：只记录会导致 BACKTRACK 或 REVISE 的严重问题
