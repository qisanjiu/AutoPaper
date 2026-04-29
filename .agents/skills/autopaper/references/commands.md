# AutoPaper CLI 命令使用指南

所有命令通过 `python scripts/state_manager.py` 执行。`scripts/` 位于框架根目录（本文件所在目录的父目录）下。所有命令均应在框架根目录执行。

## 目录

- [多项目管理](#多项目管理)
- [项目生命周期](#项目生命周期)
- [Stage 推进](#stage-推进)
- [人类介入审查](#人类介入审查)
- [经验学习](#经验学习)
- [Venue 管理](#venue-管理)
- [Python API](#python-api)

---

## 多项目管理

### 使用 list-projects 列出项目

```bash
python scripts/state_manager.py list-projects
```

列出 `../projects/` 下所有项目及当前状态。输出包含项目名、当前 Stage、Phase、Status、当前默认项目标记(👈)。

### 使用 use 设置默认项目

```bash
python scripts/state_manager.py use ../projects/PROJECT-NAME
```

持久化到 `~/.spiral/current_project`。后续命令无需再指定路径。

### 使用 --project 指定单次项目

```bash
python scripts/state_manager.py --project /path/to/project status
python scripts/state_manager.py status --project /path/to/project
```

为单次命令指定项目，不修改默认项目。`--project` 可放在命令前或后。

---

## 项目生命周期

### 使用 create 创建项目

```bash
python scripts/state_manager.py create \
  <topic> <display_name> [venue]
```

- `topic`: 研究主题
- `display_name`: 显示名称（也用作项目文件夹名，自动 sanitize）
- `venue`: 可选，默认 `arxiv`。可选值：`arxiv`, `neurips`, `icml`, `iclr`, `acl`, `cvpr`, `ieee_trans`

项目自动创建在 `../projects/`（从框架的 `__file__` 推导，CWD 无关）。可通过 `SPIRAL_PROJECTS_ROOT` 环境变量覆盖。

创建后自动：复制 venue LaTeX 模板、复制 `config/environment.yaml`（从全局默认）、初始化 `pipeline_state.yaml`（P1/S01/in_progress）。

### 使用 status 查看状态

```bash
python scripts/state_manager.py status            # 使用默认项目
python scripts/state_manager.py status /path      # 指定项目（兼容旧语法）
```

输出：项目名称、主题、venue、当前 Stage/Phase、Status、历史记录数、回溯次数。

### 使用 phase-status 查看 Phase 状态

```bash
python scripts/state_manager.py phase-status
```

输出各 Phase 的完成状态表格（✅/⏳/⬜）。

### 使用 rename 重命名

```bash
python scripts/state_manager.py rename "New Name" [--rename-folder] [--force]
```

限制：P2 完成后才能重命名（除非 `--force`）。

---

## Stage 推进

### 使用 advance 推进 Stage

```bash
python scripts/state_manager.py advance <stage> <agent> <output_file>
```

- `stage`: 完成的 Stage ID（如 `S01`）
- `agent`: 执行该 Stage 的 Agent 角色（如 `literature`）
- `output_file`: 产出文件路径（如 `knowledge/S01_topic_analysis.md`）

自动行为：若 `stage` 是 Gate Stage（S05, S10, S13, S17, S21, S25, S33, S37），标记当前 Phase 为 completed；若已是 S37，标记项目为 completed。

### 使用 run-phase 标记 Phase

```bash
python scripts/state_manager.py run-phase <phase>
```

标记一个 Phase 为 in_progress（用于用户手动干预时）。

### 使用 backtrack 回溯

```bash
python scripts/state_manager.py backtrack <from_stage> <to_stage> <reason>
```

---

## 人类介入审查

### 使用 human-review 提交审查意见

```bash
python scripts/state_manager.py human-review <stage> <opinion> [pass|revise|backtrack]
```

用户随时可对任何已完成的 Stage 提出审查意见，无需等待 Conductor 提问。

- `stage`: 目标 Stage ID（如 `S05`）
- `opinion`: 审查意见文本
- `verdict`: 可选，默认 `revise`。可选值：
  - `pass` — 记录通过，继续推进
  - `revise` — 重置到该 Stage 并重新执行
  - `backtrack` — 回溯到该 Stage 并从那里重新执行

示例：
```bash
python scripts/state_manager.py human-review S05 "假设过于宽泛，需要限定数据集"
python scripts/state_manager.py human-review S05 "假设OK" pass
python scripts/state_manager.py human-review S05 "方法设计有问题" backtrack
```

审查意见保存到 `knowledge/reviews/human_S{NN}_review.md`，同时记录到 `pipeline_state.yaml` 的 `human_reviews` 数组。

## 经验学习

### 使用 list-learned 查看学习笔记

```bash
python scripts/state_manager.py list-learned
```

列出 `docs/LEARNED/` 下所有学习笔记，显示来源、日期、严重程度、清除条件。

### 使用 learn-report 生成学习报告

```bash
python scripts/state_manager.py learn-report
```

基于当前项目的 `backtrack_log` 和 `human_reviews`，自动分析重复出现的问题模式，生成建议的学习笔记条目。

输出保存到 `docs/LEARNED/reports/report-{project-name}-{date}.md`。

### 使用 clear-learned 清除过时笔记

```bash
python scripts/state_manager.py clear-learned [--dry-run]
```

按 `clear_after` 规则清除过时的学习笔记。`--dry-run` 只显示将要清除的文件。

### 手动管理

直接增删改 `docs/LEARNED/` 下的文件即可。每个文件必须包含 YAML frontmatter（`type: learned`, `clear_after`, `severity` 等）。

## Venue 管理

### 使用 list-venues 查看 venue

```bash
python scripts/state_manager.py list-venues
```

### 使用 set-venue 切换 venue

```bash
python scripts/state_manager.py set-venue <venue_id>
```

为当前默认项目切换 venue，自动重新复制 LaTeX 模板。

---

## Python API

### 读取项目状态

```python
from spiral.state import PipelineState
from pathlib import Path

state = PipelineState(Path("../projects/PROJECT"))
current_stage = state.get_current_stage()   # "S01"
current_phase = state.get_current_phase()   # "P1"
venue = state.get_venue()                   # dict with id, name, page_limit, ...
```

### 获取 Agent 映射

```python
from spiral.project import AGENT_FOR_STAGE, PHASE_STAGES, GATE_STAGES

agent = AGENT_FOR_STAGE["S01"]              # "literature"
phases = PHASE_STAGES["P1"]                 # ["S01", ..., "S05"]
gate_stage = GATE_STAGES["G1"]              # "S05"
```

### 获取 Stage 输入文档

```python
from scripts.conductor_helper import get_input_docs
inputs = get_input_docs(Path(project_dir), "S01")
# 返回前置产出文档的路径列表
```

### 确定 Stage 所属 Phase

```python
from scripts.state_manager import PHASE_OF
phase = PHASE_OF["S01"]                     # "P1"
```
