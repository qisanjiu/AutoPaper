"""Conductor — Main orchestration entry point"""
from pathlib import Path
from typing import Optional, Tuple
from .state import PipelineState
from .project import PHASE_STAGES, AGENT_FOR_STAGE, GATE_STAGES, rename_project as _rename_project

# Mapping of which Dimension Critics to call at each Gate
GATE_CRITICS = {
    "G1": ["logic", "novelty"],
    "G2": ["logic", "method", "novelty"],
    "G3": ["method", "evidence"],
    "G4": ["method", "evidence"],
    "G5": ["logic", "evidence", "novelty"],
    "G6": ["logic", "evidence", "novelty"],
    "G7": ["logic", "writing", "evidence"],
    "G8": ["writing", "novelty", "ethics", "conductor_inspector"],
}

# Per-stage specialized checkers (run AFTER the main stage agent completes)
STAGE_CHECKERS = {
    "S11": ["code_review"],       # Code Review after Code Generation
    "S12": ["data_checker"],      # Data Quality Check after Experiment Execution
    "S15": ["code_review"],       # Code Review after Ablation Code Generation
    "S33": ["build_verifier"],    # Build Verify after Full Draft Assembly
    "S37": ["build_verifier"],    # Build Verify after Final Compilation
}

ALL_PHASES = list(PHASE_STAGES.keys())


def _phase_of_stage(stage: str) -> str:
    for ph, stages in PHASE_STAGES.items():
        if stage in stages:
            return ph
    return "P8"


class Conductor:
    def __init__(self, project_root: Path):
        self.root = project_root
        self.state = PipelineState(project_root)
        self.framework_docs = Path(__file__).parent.parent / "docs"
        self.agent_docs = Path(__file__).parent.parent / "docs" / "AGENTS"

    def current_stage(self) -> str:
        return self.state.get_current_stage()

    def current_phase(self) -> str:
        return self.state.get_current_phase()

    def current_status(self) -> str:
        return self.state.get_current_status()

    def next_stage(self) -> Optional[str]:
        """Return the next stage ID, or None if at end."""
        all_stages = [s for stages in PHASE_STAGES.values() for s in stages]
        try:
            idx = all_stages.index(self.current_stage())
            return all_stages[idx + 1] if idx + 1 < len(all_stages) else None
        except ValueError:
            return "S01"

    def is_gate_stage(self, stage: str) -> Tuple[bool, Optional[str]]:
        """Check if this stage is followed by a Gate."""
        for gate, st in GATE_STAGES.items():
            if st == stage:
                return True, gate
        return False, None

    def get_agent_for_stage(self, stage: str) -> str:
        return AGENT_FOR_STAGE.get(stage, "unknown")

    def get_stage_checkers(self, stage: str) -> list[str]:
        """Return specialized checkers that should run after this stage."""
        return STAGE_CHECKERS.get(stage, [])

    def get_checker_md_path(self, checker: str) -> Path:
        """Return the AGENT.md path for a specialized checker."""
        checker_paths = {
            "code_review": "critic/code_review/AGENT.md",
            "data_checker": "critic/data_checker/AGENT.md",
            "build_verifier": "build_verifier/AGENT.md",
        }
        subpath = checker_paths.get(checker, checker)
        return self.agent_docs / subpath

    def get_agent_md_path(self, stage: str) -> Path:
        """Return the AGENT.md path for the agent responsible for this stage."""
        agent = self.get_agent_for_stage(stage)
        # Map critic sub-agents
        if agent == "method_critic":
            return self.agent_docs / "critic" / "method" / "AGENT.md"
        if agent == "critic_team":
            return self.agent_docs / "critic" / "AGENT.md"
        return self.agent_docs / agent / "AGENT.md"

    def get_stage_input_docs(self, stage: str) -> list[Path]:
        """Heuristic: list likely input documents for a stage."""
        inputs = []
        knowledge_dir = self.root / "knowledge"
        # Handoff from previous phase
        phase_map = {}
        for ph, stages in PHASE_STAGES.items():
            for s in stages:
                phase_map[s] = ph
        cur_phase = phase_map.get(stage)
        phases = list(PHASE_STAGES.keys())
        if cur_phase and phases.index(cur_phase) > 0:
            prev_phase = phases[phases.index(cur_phase) - 1]
            handoff = knowledge_dir / f"handoff_{prev_phase}_to_{cur_phase}.md"
            if handoff.exists():
                inputs.append(handoff)
        # Previous stage output (glob for actual files)
        all_stages = [s for stages in PHASE_STAGES.values() for s in stages]
        try:
            idx = all_stages.index(stage)
            if idx > 0:
                prev = all_stages[idx - 1]
                candidates = list(knowledge_dir.glob(f"{prev}_*.md"))
                if candidates:
                    inputs.extend(candidates)
                else:
                    # Fallback: check drafts directory
                    draft_dir = self.root / "drafts" / prev
                    if draft_dir.exists():
                        inputs.extend(list(draft_dir.glob(f"{prev}_*.md")))
        except ValueError:
            pass
        return inputs

    def check_phase_prerequisites(self, phase: str) -> Tuple[bool, str]:
        """
        Check if all previous phases are completed before starting a phase.
        Returns (ok, message).
        """
        if phase not in ALL_PHASES:
            return False, f"Unknown phase: {phase}"
        idx = ALL_PHASES.index(phase)
        if idx == 0:
            return True, "P1 has no prerequisites"
        prev_phase = ALL_PHASES[idx - 1]
        prev_status = self.state.get_phase_status(prev_phase).get("status", "pending")
        if prev_status != "completed":
            return False, (
                f"{prev_phase} not completed (status: {prev_status}). "
                f"Please run {prev_phase} first."
            )
        return True, f"{prev_phase} completed. Ready to start {phase}."

    def get_phase_stages(self, phase: str) -> list[str]:
        """Return all stages belonging to a phase."""
        return PHASE_STAGES.get(phase, [])

    def get_first_stage_of_phase(self, phase: str) -> Optional[str]:
        """Return the first stage of a phase."""
        stages = self.get_phase_stages(phase)
        return stages[0] if stages else None

    def get_last_stage_of_phase(self, phase: str) -> Optional[str]:
        """Return the last stage of a phase (the gate stage)."""
        stages = self.get_phase_stages(phase)
        return stages[-1] if stages else None

    def is_phase_completed(self, phase: str) -> bool:
        """Check if a phase is marked as completed."""
        return self.state.get_phase_status(phase).get("status") == "completed"

    def run_phase(self, phase: str) -> dict:
        """
        Prepare to run all stages within a specific phase.
        Checks prerequisites, sets state, and returns execution plan.
        """
        ok, msg = self.check_phase_prerequisites(phase)
        if not ok:
            return {
                "ok": False,
                "error": msg,
                "phase": phase,
                "action": "BLOCKED",
            }

        stages = self.get_phase_stages(phase)
        if not stages:
            return {
                "ok": False,
                "error": f"No stages defined for {phase}",
                "phase": phase,
                "action": "BLOCKED",
            }

        first = stages[0]
        last = stages[-1]

        # Update state to start at first stage of the phase
        self.state.set_stage(first, "in_progress")
        self.state.set_phase_status(phase, "in_progress")

        return {
            "ok": True,
            "phase": phase,
            "stages": stages,
            "first_stage": first,
            "last_stage": last,
            "gate": GATE_STAGES.get(f"G{phase[1:]}"),
            "prerequisites": msg,
            "action": "START",
        }

    def run_stage(self, stage: str):
        """Print instructions for running a stage (human-driven for now)."""
        agent = self.get_agent_for_stage(stage)
        agent_md = self.get_agent_md_path(stage)
        print(f"\n{'='*60}")
        print(f"  STAGE {stage}  |  Agent: {agent}")
        print(f"{'='*60}")
        print(f"  1. Read your AGENT.md: {agent_md}")
        print(f"  2. Read MD Protocol: {self.framework_docs / '07_MD_PROTOCOL.md'}")
        print(f"  3. Read input docs from project: {self.root / 'knowledge/'}")
        print(f"  4. Write output to: {self.root / stage}")
        print(f"  5. After completion, update state:")
        print(f"     python spiral.py --project {self.root} --complete {stage}")

    # ---- Backtrack orchestration ----

    def backtrack(self, from_stage: str, to_stage: str, reason: str,
                  direction: str = "") -> dict:
        """Execute a full backtrack: validate, update state, compute scope.

        Returns a dict with the re-execution plan.
        """
        # Validate: to_stage must be before from_stage
        all_stages = [s for stages in PHASE_STAGES.values() for s in stages]
        try:
            from_idx = all_stages.index(from_stage)
            to_idx = all_stages.index(to_stage)
        except ValueError:
            return {"ok": False, "error": f"Invalid stage(s): {from_stage} / {to_stage}"}

        if to_idx >= from_idx:
            return {"ok": False, "error": f"Backtrack target {to_stage} must be before {from_stage}"}

        target_phase = _phase_of_stage(to_stage)

        # Spiral limit check
        if self.state.is_spiral_limit_exceeded(target_phase, limit=3):
            return {
                "ok": False,
                "error": f"Spiral limit reached for {target_phase} (3 backtracks). Human intervention required.",
                "action": "HALT",
                "spiral_count": self.state.get_spiral_count(target_phase),
            }

        # Execute backtrack
        self.state.record_backtrack(from_stage, to_stage, reason, direction)

        # Update current position
        self.state.set_stage(to_stage, "in_progress")

        # Reopen affected phases
        from_phase = _phase_of_stage(from_stage)
        all_phases = list(PHASE_STAGES.keys())
        try:
            for idx in range(all_phases.index(target_phase), all_phases.index(from_phase) + 1):
                ph = all_phases[idx]
                if self.state.get_phase_status(ph).get("status") in ("completed", "phase_completed"):
                    self.state.set_phase_status(ph, "reopened")
        except (ValueError, IndexError):
            pass

        # Log decision
        self.state.log_decision(
            "backtrack", to_stage,
            f"Backtrack {from_stage} → {to_stage}",
            f"Reason: {reason}\nDirection: {direction}"
        )

        return {
            "ok": True,
            "from": from_stage,
            "to": to_stage,
            "target_phase": target_phase,
            "spiral_count": self.state.get_spiral_count(target_phase),
            "stale_stages": self.state.get_stale_stages(),
            "gates_needing_re_review": self.state.get_gates_needing_re_review(),
            "action": "RE_EXECUTE",
        }

    def compute_backtrack_target(self, from_stage: str, root_cause_phase: str) -> str:
        """Compute the minimal backtrack target given the root cause phase.

        If the root cause is in a specific phase, backtrack to the first stage
        of that phase. Otherwise, backtrack one stage at a time.
        """
        stages = PHASE_STAGES.get(root_cause_phase, [])
        if stages:
            return stages[0]  # First stage of the root cause phase
        return from_stage

    def get_re_execution_plan(self, to_stage: str) -> dict:
        """Return the list of stages that need re-execution after backtrack.

        This includes the target stage itself plus all downstream stages
        that were marked stale.
        """
        all_stages = [s for stages in PHASE_STAGES.values() for s in stages]
        stale = self.state.get_stale_stages()
        try:
            to_idx = all_stages.index(to_stage)
        except ValueError:
            return {"ok": False, "stages": []}

        # Target stage is always re-executed
        re_exec = [to_stage]
        # Plus all stale stages in order
        for s in all_stages:
            if s in stale and s > to_stage:
                re_exec.append(s)

        # Find the Gate that needs re-review after re-execution
        target_phase = _phase_of_stage(to_stage)
        last_phase = _phase_of_stage(re_exec[-1]) if len(re_exec) > 1 else target_phase
        all_phases = list(PHASE_STAGES.keys())
        try:
            last_ph_idx = all_phases.index(last_phase)
        except ValueError:
            last_ph_idx = 0

        return {
            "ok": True,
            "stages": re_exec,
            "gate_needs_re_review": self.state.get_gates_needing_re_review(),
        }

    def handle_gate_verdict(self, gate_id: str, verdicts: list[dict]) -> dict:
        """Process Gate Critic verdicts and determine action.

        Each verdict dict: {"critic": "logic", "verdict": "PASS|REVISE|BACKTRACK|HALT",
                           "target_stage": None, "reason": ""}

        Returns action plan.
        """
        # Check for HALT first
        for v in verdicts:
            if v.get("verdict") == "HALT":
                self.state.log_decision("gate_halt", gate_id,
                                        f"Gate {gate_id} HALTED by {v['critic']}",
                                        v.get("reason", ""))
                return {"action": "HALT", "reason": v.get("reason", "")}

        # Check for BACKTRACK
        for v in verdicts:
            if v.get("verdict") == "BACKTRACK":
                target = v.get("target_stage")
                if not target:
                    # Default: backtrack to first stage of current phase
                    gate_num = int(gate_id[1:])
                    ph = f"P{gate_num}"
                    target = self.get_first_stage_of_phase(ph) or "S01"
                return {
                    "action": "BACKTRACK",
                    "target_stage": target,
                    "reason": f"{v['critic']}: {v.get('reason', '')}",
                    "direction": v.get("direction", v.get("reason", "")),
                }

        # Check for REVISE
        for v in verdicts:
            if v.get("verdict") == "REVISE":
                gate_stage = GATE_STAGES.get(gate_id)
                return {
                    "action": "REVISE",
                    "target_stage": gate_stage,
                    "reason": f"{v['critic']}: {v.get('reason', '')}",
                }

        # All PASS
        self.state.clear_gate_re_review(gate_id)
        self.state.log_decision("gate_pass", gate_id,
                                f"Gate {gate_id} PASSED by all critics")
        return {"action": "PASS"}

    def resume_after_backtrack(self) -> dict:
        """Return the execution plan after a backtrack has been recorded.

        The Conductor should call this to know what to do next.
        """
        current = self.current_stage()
        stale = self.state.get_stale_stages()
        gates = self.state.get_gates_needing_re_review()

        # The next stage to execute: current if stale, otherwise the first stale stage
        next_up = []
        if self.state.is_stale(current):
            next_up.append(current)
        for s in stale:
            if s > current and s not in next_up:
                next_up.append(s)

        return {
            "ok": True,
            "current_stage": current,
            "current_status": self.current_status(),
            "stages_to_re_execute": next_up,
            "gates_needing_re_review": gates,
            "spiral_count": self.state.get_spiral_count(),
        }

    def rename(self, new_display_name: str, rename_folder: bool = False, force: bool = False) -> Path:
        """
        Rename the project. If rename_folder=True, also rename the folder on disk.
        Automatically updates self.root to the new path if folder is renamed.
        
        Returns:
            The (possibly new) project directory path.
        """
        new_path = _rename_project(self.root, new_display_name, rename_folder=rename_folder, force=force)
        if rename_folder and new_path != self.root:
            self.root = new_path
            self.state = PipelineState(new_path)
            print(f"[CONDUCTOR] Updated root path: {self.root}")
        return new_path

    def run(self):
        """Main loop — print current status and next action."""
        stage = self.current_stage()
        phase = self.current_phase()
        status = self.current_status()

        print(f"\n[Conductor] Current: {stage} (Phase {phase}) — Status: {status}")

        if status == "phase_completed":
            # Find which phase was just completed
            prev_phase = None
            for ph in ALL_PHASES:
                if self.state.get_phase_status(ph).get("status") == "completed":
                    prev_phase = ph
            completed_ph = prev_phase if prev_phase else "Previous"
            print(f"\n  ✅ {completed_ph} has been completed.")
            print(f"  Current position: {stage} (start of Phase {phase}).")
            print(f"  To continue, explicitly request: 'Run Phase {phase}' or 'Continue to next phase'")
            return

        is_gate, gate_id = self.is_gate_stage(stage)
        if is_gate and gate_id:
            critics = GATE_CRITICS.get(gate_id, [])
            print(f"  → Gate {gate_id} checkpoint — call Critic Team: {critics}")
        else:
            self.run_stage(stage)

        print(f"\n[State] {self.state.path}")
