"""pipeline_state.yaml manager"""
import yaml
from pathlib import Path
from datetime import datetime

DEFAULT_STATE = {
    "project": {"name": "", "topic": "", "created_at": "", "venue": {"id": "arxiv", "name": "arXiv"}},
    "current": {"phase": "P1", "stage": "S01", "status": "initialized"},
    "phases": {
        "P1": {"status": "pending", "completed_at": None, "last_stage": None},
        "P2": {"status": "pending", "completed_at": None, "last_stage": None},
        "P3": {"status": "pending", "completed_at": None, "last_stage": None},
        "P4": {"status": "pending", "completed_at": None, "last_stage": None},
        "P5": {"status": "pending", "completed_at": None, "last_stage": None},
        "P6": {"status": "pending", "completed_at": None, "last_stage": None},
        "P7": {"status": "pending", "completed_at": None, "last_stage": None},
        "P8": {"status": "pending", "completed_at": None, "last_stage": None},
    },
    "history": [],
    "backtrack_log": [],
    "spiral_count": {},
    "agents": {},
    "gates": {},
    "stale_stages": [],
    "gate_re_review": {},
    "human_reviews": [],
    "decision_log": [],
}


def _get_phase_stages():
    """Lazy-load PHASE_STAGES to avoid circular import with project.py."""
    from .project import PHASE_STAGES
    return PHASE_STAGES


def _get_phase_of(stage: str) -> str:
    """Get the phase (P1-P8) for a given stage (S01-S37)."""
    for ph, stages in _get_phase_stages().items():
        if stage in stages:
            return ph
    return "P1"


def _get_all_stages() -> list:
    """Get flat list of all stages S01-S37 in order."""
    return [s for stages in _get_phase_stages().values() for s in stages]


class PipelineState:
    def __init__(self, project_root: Path):
        self.path = project_root / "state" / "pipeline_state.yaml"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        else:
            self.data = dict(DEFAULT_STATE)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.dump(self.data, f, allow_unicode=True, sort_keys=False)

    # ---- Current stage/phase/status ----

    def get_current_stage(self) -> str:
        return self.data.get("current", {}).get("stage", "S01")

    def get_current_phase(self) -> str:
        return self.data.get("current", {}).get("phase", "P1")

    def get_current_status(self) -> str:
        return self.data.get("current", {}).get("status", "initialized")

    def set_stage(self, stage: str, status: str = "in_progress"):
        self.data["current"]["stage"] = stage
        self.data["current"]["phase"] = _get_phase_of(stage)
        self.data["current"]["status"] = status
        self.save()

    def get_phase_status(self, phase: str) -> dict:
        """Return the status dict for a given phase."""
        return self.data.get("phases", {}).get(phase, {"status": "unknown"})

    def set_phase_status(self, phase: str, status: str, last_stage: str = None):
        """Update phase status."""
        if "phases" not in self.data:
            self.data["phases"] = dict(DEFAULT_STATE["phases"])
        self.data["phases"][phase] = {
            "status": status,
            "completed_at": datetime.now().isoformat() if status == "completed" else None,
            "last_stage": last_stage,
        }
        self.save()

    def mark_phase_completed(self, phase: str, last_stage: str):
        """Mark a phase as completed."""
        self.set_phase_status(phase, "completed", last_stage)

    # ---- Venue ----

    def get_venue(self) -> dict:
        """Return venue configuration."""
        return self.data.get("project", {}).get("venue", {"id": "arxiv", "name": "arXiv"})

    def set_venue(self, venue_id: str, venue_config: dict = None):
        """Set the target venue for this project."""
        if "project" not in self.data:
            self.data["project"] = {}
        self.data["project"]["venue"] = {
            "id": venue_id,
            "name": venue_config.get("name", venue_id) if venue_config else venue_id,
            "page_limit": venue_config.get("page_limit") if venue_config else None,
            "page_limit_note": venue_config.get("page_limit_note", "") if venue_config else "",
            "format": venue_config.get("format", "") if venue_config else "",
            "style_package": venue_config.get("style_package", "") if venue_config else "",
            "template_dir": venue_config.get("template_dir", "") if venue_config else "",
            "set_at": datetime.now().isoformat(),
        }
        self.save()

    # ---- History ----

    def record_completion(self, stage: str, agent: str, output: Path):
        entry = {
            "stage": stage,
            "agent": agent,
            "completed_at": datetime.now().isoformat(),
            "output": str(output),
        }
        self.data["history"].append(entry)
        self.save()

    # ---- Backtrack ----

    def record_backtrack(self, from_stage: str, to_stage: str, reason: str,
                         direction: str = ""):
        """Record a backtrack event with full metadata.

        Args:
            from_stage: Stage where problem was discovered.
            to_stage: Target stage to backtrack to.
            reason: Why the backtrack is needed.
            direction: Guidance on what to fix (from Critic or human review).
        """
        target_phase = _get_phase_of(to_stage)
        entry = {
            "from": from_stage,
            "to": to_stage,
            "reason": reason,
            "direction": direction,
            "target_phase": target_phase,
            "timestamp": datetime.now().isoformat(),
        }
        self.data.setdefault("backtrack_log", []).append(entry)

        # Increment spiral count for the target phase (start from 0)
        count = self.data.setdefault("spiral_count", {}).get(target_phase, 0)
        self.data["spiral_count"][target_phase] = count + 1

        # Mark downstream stages as stale
        self._mark_downstream_stale(from_stage, to_stage)

        # Mark the corresponding Gate as needing re-review
        self._flag_gate_re_review(to_stage)

        self.save()

    def _mark_downstream_stale(self, from_stage: str, to_stage: str):
        """Mark all stages between to_stage and from_stage as stale."""
        all_stages = _get_all_stages()
        try:
            to_idx = all_stages.index(to_stage)
            from_idx = all_stages.index(from_stage)
        except ValueError:
            return
        stale = all_stages[to_idx + 1 : from_idx + 1]
        existing = set(self.data.get("stale_stages", []))
        existing.update(stale)
        self.data["stale_stages"] = sorted(existing, key=lambda s: all_stages.index(s))

    def _flag_gate_re_review(self, to_stage: str, from_stage: str = ""):
        """Flag Gates covering phases affected by this backtrack as needing re-review."""
        target_phase = _get_phase_of(to_stage)
        from_phase = _get_phase_of(from_stage) if from_stage else self.get_current_phase()
        phases = list(_get_phase_stages().keys())
        try:
            t_idx = phases.index(target_phase)
            f_idx = phases.index(from_phase)
            for idx in range(t_idx, f_idx + 1):
                ph = phases[idx]
                gate_id = f"G{ph[1:]}"
                self.data.setdefault("gate_re_review", {})[gate_id] = {
                    "needs_re_review": True,
                    "flagged_at": datetime.now().isoformat(),
                    "reason": f"Backtrack to {to_stage} (Phase {target_phase})",
                }
        except ValueError:
            gate_id = f"G{target_phase[1:]}"
            self.data.setdefault("gate_re_review", {})[gate_id] = {
                "needs_re_review": True,
                "flagged_at": datetime.now().isoformat(),
                "reason": f"Backtrack to {to_stage}",
            }

    def get_spiral_count(self, phase: str = None) -> int:
        """Get spiral count for a phase, or max across all phases."""
        counts = self.data.get("spiral_count", {})
        if phase:
            return counts.get(phase, 0)
        return max(counts.values()) if counts else 0

    def is_spiral_limit_exceeded(self, phase: str, limit: int = 3) -> bool:
        """Check if a phase has been backtracked >= limit times."""
        return self.data.get("spiral_count", {}).get(phase, 0) >= limit

    # ---- Staleness tracking ----

    def is_stale(self, stage: str) -> bool:
        """Check if a stage is marked as stale (needs re-execution after backtrack)."""
        return stage in self.data.get("stale_stages", [])

    def get_stale_stages(self) -> list[str]:
        """Return all stages currently marked as stale."""
        return list(self.data.get("stale_stages", []))

    def clear_stale(self, stage: str):
        """Remove a stage from the stale list (called after re-execution)."""
        stale = self.data.get("stale_stages", [])
        if stage in stale:
            stale.remove(stage)
            self.data["stale_stages"] = stale
            self.save()

    def clear_all_stale(self):
        """Clear all stale markers (e.g., after full re-execution)."""
        self.data["stale_stages"] = []
        self.save()

    # ---- Gate re-review ----

    def gate_needs_re_review(self, gate_id: str) -> bool:
        """Check if a Gate needs re-review after backtrack."""
        return self.data.get("gate_re_review", {}).get(gate_id, {}).get("needs_re_review", False)

    def get_gates_needing_re_review(self) -> list[str]:
        """Return all Gate IDs that need re-review."""
        return [g for g, v in self.data.get("gate_re_review", {}).items()
                if v.get("needs_re_review", False)]

    def clear_gate_re_review(self, gate_id: str):
        """Mark a Gate's re-review as completed."""
        if gate_id in self.data.get("gate_re_review", {}):
            self.data["gate_re_review"][gate_id]["needs_re_review"] = False
            self.data["gate_re_review"][gate_id]["reviewed_at"] = datetime.now().isoformat()
            self.save()

    # ---- Decision log ----

    def log_decision(self, decision_type: str, stage: str, summary: str, details: str = ""):
        """Append a decision entry to the decision log."""
        entry = {
            "type": decision_type,
            "stage": stage,
            "summary": summary,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.data.setdefault("decision_log", []).append(entry)
        self.save()
