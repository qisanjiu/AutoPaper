# AutoPaper — Autonomous Research Framework

> **Version**: 0.3.0  
> **Execution Model**: Native subagent strategy  
> **Core Philosophy**: Spiral progression, 3-layer critique, empirical inner loops

---

## Usage Model

**You (User) give commands → I (Conductor) execute automatically**

The entire research workflow is orchestrated by the Conductor (me, the Root Agent). You only need to tell me your requirements in natural language, and I will:

1. Create project directories and initialize state
2. Read current Stage and status
3. Create sub-Agents via the `Agent` tool
4. Save sub-Agent outputs to the project directory
5. Invoke critique mechanisms to review outputs
6. Automatically advance to the next step or backtrack for fixes

### Auto-Loading Skill

This project includes an auto-loading skill at `.agents/skills/autopaper/` that activates when you mention research-related keywords. Even if my context is compacted, the skill ensures I immediately know:

- The 8 Phase × 37 Stage architecture
- How to create and manage projects
- How to advance stages and run Gate reviews
- The Context Recovery protocol

**Trigger words**: "AutoPaper", "AutoPaper", "全自动科研", "自动写论文", "运行 P3", "执行 S11", "创建新项目", "切换 venue", or any request to create/run/advance/backtrack a research project.

### Execution Modes

#### Mode A: Full Auto (Run everything at once)

```
User: I want to do a research project on "Breath Detection via Deep Learning and mmWave Radar"

Conductor (Me):
→ Create project in ../projects/
→ Initialize pipeline_state.yaml
→ Invoke Literature Agent for S01 (Topic Analysis)
→ Save S01_topic_analysis.md
→ Invoke Stage Inspector for review
→ Advance to S02
→ ... (continue automatically through all 37 stages)
```

#### Environment Setup (Before Running Experiments)

All research projects share a **single global environment config** at the framework root:

```
AutoPaper/
├── config/
│   └── environment.yaml      # ← Fill this once, used by all projects
```

Fill in `{AutoPaper}/config/environment.yaml` before Phase 3 (Execution):

```yaml
environment:
  mode: "remote_ssh"          # local | remote_ssh | remote_slurm
  remote_ssh:
    host: "192.168.1.100"     # Your server IP
    user: "your_username"
    key_file: "~/.ssh/id_rsa" # SSH private key path
    gpu_devices: "0,1"
    setup_commands:
      - "conda activate myenv"
  general:
    iteration_time_budget: 30  # Minutes per experiment iteration
    total_gpu_budget: 24       # Total GPU hours
```

Experiment Agent reads this config before **every** experiment run (S13, S18, etc.).
If critical fields are empty, it will ask you to fill them in.

> **Security note**: `config/environment.yaml` is in `.gitignore` — it may contain credentials.

### Mode B: Phase-by-Phase (Recommended for complex projects)

```
User: Run Phase 1: Discovery

Conductor (Me):
→ Check prerequisites (P1 has none)
→ Start at S01, execute S01→S02→S03→S04→S05
→ Gate G1 review
→ Stop. Report: "Phase 1 complete. S05 passed G1."
→ Status: phase_completed
```

```
User: Run Phase 2: Design

Conductor (Me):
→ Check prerequisites: P1 must be completed
→ If P1 not done: "Please complete Phase 1 first."
→ If P1 done: Start at S06, execute S06→S07→S08→S09→S10
→ Gate G2 review
→ Stop. Report: "Phase 2 complete."
```

```
User: Check phase status

Conductor (Me):
→ Show table:
  ✅ P1: completed | last=S05 | 2024-01-15 09:30
  ⏳ P2: in_progress | last=S07
  ⬜ P3: pending
  ⬜ P4: pending
  ⬜ P5: pending
  ⬜ P6: pending
  ⬜ P7: pending
  ⬜ P8: pending
```

```
User: Continue to next step / proceed to experiment phase / backtrack to S11 to fix code

Conductor (Me):
→ Read current state
→ Execute your command
→ Update pipeline_state.yaml
```

```
User: The research design is finalized, rename the project to the final paper title

Conductor (Me):
→ Check: Phase 2 (Design) completed? (S10 passed Gate G2)
→ If YES: Rename project display_name, update state and logs
→ If YES + user requests folder rename: Rename folder on disk with fallback for Windows file-locking
→ If NO: "Cannot rename before Phase 2 is complete. Research direction not yet finalized."
```

### Multi-Project Management

You can run multiple projects in parallel. I automatically track which one is current.

```
User: List all my projects

Conductor (Me):
→ Show table of all projects in ../projects/
→ Display: name, current stage, phase, status
→ Mark the current default project with 👈
```

```
User: Switch to project "Breath Detection"

Conductor (Me):
→ Set default project to ../projects/breath-detection-...
→ All subsequent commands target this project automatically
```

```
User: Check status of the other project without switching

Conductor (Me):
→ Use --project flag to query a specific project without changing default
```

### Human-in-the-Loop Review

You can spontaneously review any completed Stage at any time — no need to wait for me to ask.

```
User: Review S05

Conductor (Me):
→ Read S05 output from the project
→ Show you the full content for review
→ Wait for your feedback
```

```
User: S05's hypothesis is too broad, limit it to indoor scenarios

Conductor (Me):
→ Record your opinion as human review
→ Verdict: REVISE
→ Reset state to S05
→ Re-execute S05 with your feedback as constraint
→ Continue from S05 after completion
```

```
User: Backtrack to S04

Conductor (Me):
→ Execute backtrack from current stage to S04
→ Record reason in backtrack_log
→ Reset state to S04, set status to in_progress
```

---

## Architecture

```
AutoPaper/                     # Framework
├── spiral/                    # Core Python package
│   ├── state.py               # pipeline_state.yaml manager
│   └── project.py             # Project creation & layout
├── scripts/                   # Internal tools (used by Conductor)
│   ├── state_manager.py       # Read/write state, advance/backtrack
│   └── conductor_helper.py    # Next-step decision helper
├── .agents/skills/autopaper/  # Auto-loading skill (trigger words)
│   ├── SKILL.md               # Skill definition
│   └── references/            # Commands, stages, agents refs
├── .agents/                   # Agent prompt templates
├── templates/stage/           # 37 Stage markdown templates
├── utils/                     # Deterministic checkers
│   ├── md_validator.py
│   ├── orphan_cite_gate.py
│   ├── anti_leakage_check.py
│   └── latex_sanity.py
└── docs/                      # Framework design docs (64 files)
```

Generated projects live in `../projects/` (sibling to AutoPaper).

---

## Key Design Features

| Feature | Implementation |
|---------|---------------|
| **8 Phases × 37 Stages** | Atomic stages with explicit inputs/outputs |
| **3-Layer Critic** | 37 Stage Inspectors + 6 Dimension Critics + 2 Meta Critics |
| **Inner Loop** | AutoResearch experiment iteration loop (S12, git commit, evaluate in-loop) + PaperOrchestra content refinement (S36) |
| **Outer Loop** | Backward Propagation with minimum-backtrack principle |
| **Venue Template System** | 6 mainstream LaTeX templates (NeurIPS/ICML/ICLR/ACL/CVPR/IEEE Trans) with page-limit enforcement |
| **Deterministic Checkers** | Orphan Cite Gate, Anti-Leakage Check, LaTeX Sanity |
| **Context Recovery** | Every agent re-loads AGENT.md after context compaction |
| **Agent-Native** | All orchestration via native Agent tooling |

---

## Generated Project Structure

```
/projects/
└── project-name-timestamp/
    ├── S01/ ~ S37/           # One folder per Stage 
    │   └── S{NN}_output.md   # Stage output
    ├── state/
    │   ├── pipeline_state.yaml
    │   ├── decision_log.md
    │   └── spiral_log.md
    ├── knowledge/
    │   ├── handoff_P1_to_P2.md
    │   └── reviews/
    └── artifacts/
        └── paper.pdf
```

---

## Docs Index

| File | Content |
|------|---------|
| `docs/01_ARCHITECTURE.md` | Overall architecture, 3-layer stack, Phase-Gate model |
| `docs/02_CONDUCTOR_AGENT.md` | Conductor orchestration details |
| `docs/03_SUB_AGENTS.md` | Agent team overview & collaboration patterns |
| `docs/04_STAGES.md` | 37 Stages detailed design |
| `docs/05_KNOWLEDGE_FLOW.md` | Knowledge transfer between stages |
| `docs/06_FEEDBACK_LOOP.md` | Inner/Outer Loop, Backward Propagation |
| `docs/07_MD_PROTOCOL.md` | Universal Document Schema, Input/Output protocol |
| `docs/AGENTS/**/AGENT.md` | 19 Agent identity & capability definitions |

---

## License

MIT
