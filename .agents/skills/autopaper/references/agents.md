# Agent 与 Critic 详细定义

## 17 个 Agent（按执行阶段分组）

| Agent | 职责 | 负责的 Stages |
|-------|------|--------------|
| **literature** | 文献调研、选题分析 | S01, S02 |
| **ideation** | 想法生成与评估 | S03-S05, S25 |
| **method** | 方法论设计、实验设计、baseline 选择 | S06-S10 |
| **experiment** | 代码生成、实验运行、结果收集 | S11-S12, S14-S16, S20 |
| **analysis** | 统计分析、模式识别、洞察提炼 | S13, S17-S19, S21-S23 |
| **writing** | 论文写作 | S24, S26-S31, S33, S36, S37 |
| **figure** | 图表生成、数据可视化 | S32 |
| **critic_team** | 多维度质量批判（执行 + 审查） | S34（内部审查） |
| **review** | 模拟审稿人 | S35 |

## Critic Team 三层架构

### Layer 1: Stage Inspector（纵向）
- 每个 Stage 有专属 Inspector
- 审查内容 + MD 格式
- 产出：内容评分 + 格式评分 + PASS/REVISE/BACKTRACK
- 文件：`docs/AGENTS/critic/stage/inspectors/S{NN}.md`

### Layer 2: Dimension Critic（横向）
- 6 个专业维度，Gate 时并行调用 2-3 个

| Critic | 审查维度 | 审查范围 |
|--------|---------|---------|
| Logic | 论证链条、一致性、因果推断 | S03-S06, S10, S22, S24-S33 |
| Method | 方法正确性、实验设计、baseline 公平性 | S06-S11, S12, S14-S16, S19, S28 |
| Evidence | 统计正确性、claim-evidence 映射 | S12-S13, S17, S21-S22, S29 |
| Writing | 学术写作、venue 格式、orphan cites | S26-S33, S36-S37 |
| Novelty | 相关工作覆盖、新颖性声明 | S04-S06, S24, S27, S34 |
| Ethics | 数据伦理、隐私、公平性 | S07-S08, S12, S18-S21, S29 |

### Layer 3: Meta Critic（元）
- **Conductor Inspector**：审查 Conductor 的编排决策
- **Format Inspector**：深度 MD 格式验证

## Gate 审查决策标准

Gate 审查结果有四种：

- **PASS** — 所有 Critic 认可，继续下一阶段
- **REVISE** — 问题局限于当前 Phase，在当前范围内修改后重新 Gate
- **BACKTRACK** — 根因在前序 Phase，回溯到指定 Stage 重新执行
- **HALT** — 无法继续，向用户报告并等待指示

决策原则：
- 若问题可通过当前 Phase 内修改解决 → REVISE
- 若问题根因在前序 Phase（如方法设计错误、假设不成立）→ BACKTRACK
- 若发现伦理问题或无法修复的根本性缺陷 → HALT

## Anti-Leakage Prompt（强制）

在任何生成论文内容的 LLM 调用前，system prompt 前必须附加：

```
Anti-Leakage Instruction:
You must not reproduce or closely paraphrase any copyrighted text,
including but not limited to: textbook explanations, Wikipedia passages,
or source code from existing implementations. Generate all explanations,
descriptions, and code from first principles or using your own words.
Cite sources using [Author, Year] format but do not copy their prose.
```

## Venue 模板与编译约束

- 项目创建时，venue 的 LaTeX 模板（`.sty`/`.cls`/`.bst`/`.tex`）自动复制到 `artifacts/latex_template/`
- S33 和 S37 必须使用此目录下的模板文件，严禁使用其他来源模板
- S33 和 S37 必须执行多次编译：`pdflatex → bibtex → pdflatex × 2`
- 编译检查使用 `utils/latex_sanity.py`
- 页数合规检查根据 `config/venue_registry.yaml` 中的 `page_limit`
- Orphan Cite 检查使用 `utils/orphan_cite_gate.py`
- Anti-Leakage 检查使用 `utils/anti_leakage_check.py`
