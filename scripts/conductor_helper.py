#!/usr/bin/env python3
"""
Conductor Helper — Conductor（Root Agent）的决策辅助工具
输入项目目录，输出下一步应该执行的 Stage、Agent、输入文档、输出路径
"""
import sys
import yaml
from pathlib import Path

# Import from spiral package (single source of truth)
_framework_root = Path(__file__).parent.parent.resolve()
if str(_framework_root) not in sys.path:
    sys.path.insert(0, str(_framework_root))
from spiral.project import PHASE_STAGES, AGENT_FOR_STAGE, GATE_STAGES as GATE_STAGES_MAP

# Build AGENT_MD dynamically from AGENT_FOR_STAGE
_AGENT_DIR_OVERRIDE = {
    "critic_team": "critic",
}
AGENT_MD = {}
for stage in [s for stages in PHASE_STAGES.values() for s in stages]:
    agent = AGENT_FOR_STAGE.get(stage, "conductor")
    agent_dir = _AGENT_DIR_OVERRIDE.get(agent, agent)
    AGENT_MD[stage] = str(_framework_root / "docs" / "AGENTS" / agent_dir / "AGENT.md")

# Gate stages dict for conductor_helper (G1 -> S05, etc.)
GATE_STAGES = GATE_STAGES_MAP

PHASE_ORDER = list(PHASE_STAGES.keys())

# Build phase-of-stage lookup
PHASE_OF = {}
for ph, stages in PHASE_STAGES.items():
    for s in stages:
        PHASE_OF[s] = ph

ALL_STAGES = [s for stages in PHASE_STAGES.values() for s in stages]

# Cross-stage inputs: stages that need upstream documents beyond the immediate predecessor.
# These are documents whose information is not fully replicated in the handoff or the
# immediately preceding stage, and which the downstream stage must consult directly.
CROSS_STAGE_INPUTS = {
    # P2 experiment design stages need S01/S02 for literature experiment conventions
    "S07": ["S01", "S02"],   # benchmark selection: S02 §6 experiment details, S01 venue/team info
    "S08": ["S01", "S02"],   # experiment protocol: S01 §4 tech bottlenecks, S02 §6 experiment conventions
    "S09": ["S02"],          # baseline selection: S02 §3 literature matrix, §6 experiment details
    "S10": ["S02"],          # full experiment plan: S02 §6.5 sufficiency standards
    # P3 execution
    "S11": ["S02"],          # code generation: S02 §3 literature matrix (method details for baseline impl)
    "S13": ["S04", "S07", "S08", "S09"],   # result verification: hypotheses + benchmark + protocol + baselines
    # P4 ablation
    "S14": ["S02", "S06"],   # ablation design: S02 §6 ablation conventions, S06 components
    "S17": ["S02"],          # ablation analysis: compare findings with literature ablation results
    # P5 further analysis
    "S18": ["S02", "S12", "S16"],  # findings: S02 lit reference, S12/S16 raw results
    "S19": ["S02"],          # analysis experiment design: S02 §6 analysis conventions
    # P6 synthesis
    "S22": ["S04"],          # claim-evidence: original hypotheses
    "S23": ["S04"],          # finding synthesis: hypothesis verification
    # P7 writing
    "S26": ["S02"],          # paper outline: S02 §7 paper framework conventions
    "S27": ["S02"],          # intro & related work: literature survey
    "S28": ["S06", "S08"],   # method section: method design + experiment protocol
    "S29": ["S22"],          # experiments section: claim-evidence map
    "S30": ["S22", "S23", "S12", "S16"],  # analysis & discussion: findings, claims, raw data
    "S31": ["S29"],          # abstract & conclusion: experiments section for numerical consistency
    "S32": ["S26", "S06", "S12", "S16"],  # figure generation: plotting plan, method design, data
}


def get_input_docs(proj_dir: Path, stage: str) -> list:
    """Find likely input documents for a stage.

    Returns (in order):
      1. Phase handoff doc (if crossing a phase boundary)
      2. Cross-stage inputs from earlier phases (from CROSS_STAGE_INPUTS)
      3. Immediately preceding stage output
    """
    inputs = []
    knowledge = proj_dir / "knowledge"

    cur_phase = PHASE_OF.get(stage)
    if cur_phase and PHASE_ORDER.index(cur_phase) > 0:
        prev = PHASE_ORDER[PHASE_ORDER.index(cur_phase) - 1]
        handoff = knowledge / f"handoff_{prev}_to_{cur_phase}.md"
        if handoff.exists():
            inputs.append(str(handoff))

    # Cross-stage inputs (upstream docs from earlier phases)
    cross_stages = CROSS_STAGE_INPUTS.get(stage, [])
    for src_stage in cross_stages:
        candidates = list(knowledge.glob(f"{src_stage}_*.md"))
        if candidates:
            inputs.append(str(candidates[0]))

    # Previous stage output (immediate predecessor in sequence)
    idx = ALL_STAGES.index(stage)
    if idx > 0:
        prev = ALL_STAGES[idx - 1]
        candidates = list(knowledge.glob(f"{prev}_*.md"))
        if candidates:
            inputs.append(str(candidates[0]))
        else:
            candidates = list((proj_dir / "drafts" / prev).glob(f"{prev}_*.md"))
            if candidates:
                inputs.append(str(candidates[0]))

    return inputs


def main():
    if len(sys.argv) < 3:
        print("Usage: conductor_helper.py <framework_root> <project_dir>")
        sys.exit(1)

    framework = Path(sys.argv[1])
    proj_dir = Path(sys.argv[2])
    state_file = proj_dir / "state" / "pipeline_state.yaml"

    if not state_file.exists():
        print(f"[ERROR] No state file: {state_file}")
        sys.exit(1)

    with open(state_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    stage = data["current"]["stage"]
    agent_md = framework / AGENT_MD.get(stage, "docs/AGENTS/conductor/AGENT.md")
    output_dir = proj_dir / "drafts" / stage
    output_file = output_dir / f"{stage}_output.md"

    # Check if it's a Gate stage
    is_gate = stage in GATE_STAGES.values()

    print(f"STAGE: {stage}")
    print(f"AGENT_MD: {agent_md}")
    print(f"MD_PROTOCOL: {framework / 'docs/07_MD_PROTOCOL.md'}")
    print(f"OUTPUT_DIR: {output_dir}")
    print(f"OUTPUT_FILE: {output_file}")
    print(f"IS_GATE: {is_gate}")
    print(f"INPUT_DOCS: {get_input_docs(proj_dir, stage)}")
    print(f"STATUS: {data['current']['status']}")

    if is_gate:
        gate_num = [k for k, v in GATE_STAGES.items() if v == stage][0]
        print(f"GATE: {gate_num}")
        print("ACTION: Call Critic Team (parallel Agent invocations)")
    else:
        print("ACTION: Create sub-Agent via Agent tool")


if __name__ == "__main__":
    main()
