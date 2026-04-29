#!/usr/bin/env python3
"""
State Manager — Conductor 内部工具
用于读写 pipeline_state.yaml、记录历史、推进 Stage、管理 Phase 状态
由 Conductor（Root Agent）在对话中调用
"""
import os
import re
import sys
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


# Windows reserved names that cannot be used as folder/file names
_WIN_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def _sanitize_folder_name(name: str) -> str:
    """Convert to filesystem-safe folder name. Preserves Chinese characters."""
    name = name.strip()
    name = name.replace(" ", "-")
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    name = name.rstrip(" .")
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")
    if name.upper() in _WIN_RESERVED:
        name = name + "_"
    return name or "untitled"


def _load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


# ---------------------------------------------------------------------------
# Multi-project helpers
# ---------------------------------------------------------------------------
def _get_default_projects_root() -> Path:
    """Derive the default projects root from the framework location.

    scripts/state_manager.py -> scripts/ -> framework_root/ -> ../projects
    """
    framework_root = Path(__file__).parent.parent.resolve()
    return framework_root.parent / "projects"


PROJECTS_ROOT = _get_default_projects_root()
_CURRENT_PROJECT_FILE = Path.home() / ".spiral" / "current_project"


def _ensure_current_project_dir():
    _CURRENT_PROJECT_FILE.parent.mkdir(parents=True, exist_ok=True)


def _get_current_project() -> Optional[Path]:
    """Return the currently selected project directory, or None."""
    if _CURRENT_PROJECT_FILE.exists():
        path = Path(_CURRENT_PROJECT_FILE.read_text(encoding="utf-8").strip())
        if path.exists():
            return path
    return None


def _set_current_project(project_dir: str):
    """Persist the selected project as the default for subsequent commands."""
    _ensure_current_project_dir()
    path = Path(project_dir).resolve()
    _CURRENT_PROJECT_FILE.write_text(str(path), encoding="utf-8")
    print(f"[USE] Current project set to: {path}")


def _resolve_project_dir(args: list[str]) -> str:
    """
    Extract project directory from args.
    Priority:
      1. --project /path/to/project (consumed from args)
      2. First positional argument (legacy)
      3. ~/.spiral/current_project (default)
    Returns the project_dir string and mutates args in place to remove
    consumed flags.
    """
    # Check for --project flag (resolve to absolute path for CWD independence)
    for i, arg in enumerate(args):
        if arg == "--project" and i + 1 < len(args):
            project_dir = str(Path(args[i + 1]).resolve())
            del args[i : i + 2]
            return project_dir

    # Fallback to current default project
    current = _get_current_project()
    if current:
        return str(current)

    raise SystemExit(
        "[ERROR] No project specified.\n"
        "  Use one of:\n"
        "    --project /path/to/project   (flag)\n"
        "    python state_manager.py use /path/to/project   (set default)\n"
        "    Or provide <project_dir> as the first positional argument.\n"
        "  See: python state_manager.py list-projects"
    )


# Import from spiral package (single source of truth)
_framework_root = Path(__file__).parent.parent.resolve()
if str(_framework_root) not in sys.path:
    sys.path.insert(0, str(_framework_root))
from spiral.project import PHASE_STAGES, GATE_STAGES as _GATE_STAGES_MAP

PHASE_OF = {}
for ph, stages in PHASE_STAGES.items():
    for s in stages:
        PHASE_OF[s] = ph

# Gate stages as a set for O(1) membership check
GATE_STAGES = set(_GATE_STAGES_MAP.values())

ALL_PHASES = list(PHASE_STAGES.keys())


def _load_venue_registry() -> dict:
    """Load venue registry from framework templates."""
    registry_path = Path(__file__).parent.parent / "config" / "venue_registry.yaml"
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_venue_config(venue_id: str) -> dict:
    """Get venue config from registry."""
    registry = _load_venue_registry()
    return registry.get("venues", {}).get(venue_id)


def cmd_create(topic: str, display_name: str, venue: str = None):
    """Initialize a new project under the default projects root.

    The projects root is derived from the framework location (__file__-based),
    so it is independent of CWD. Use SPIRAL_PROJECTS_ROOT env var to override.
    """
    framework_root = Path(__file__).parent.parent.resolve()
    if str(framework_root) not in sys.path:
        sys.path.insert(0, str(framework_root))
    from spiral.project import create_project

    # Allow override via environment variable
    env_override = os.environ.get("SPIRAL_PROJECTS_ROOT")
    projects_root = Path(env_override) if env_override else PROJECTS_ROOT
    projects_root.mkdir(parents=True, exist_ok=True)

    proj = create_project(
        topic=topic,
        display_name=display_name,
        projects_root=projects_root,
        venue=venue,
    )
    return str(proj)


def cmd_status(project_dir: str):
    """Print project status for Conductor."""
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    if not state_file.exists():
        print(f"[ERROR] State file not found: {state_file}")
        sys.exit(1)
    data = _load(state_file)
    proj = data.get("project", {})
    cur = data.get("current", {})
    venue = proj.get("venue", {})
    print(f"PROJECT: {proj.get('display_name', proj.get('name'))}")
    print(f"TOPIC:   {proj.get('topic')}")
    print(f"VENUE:   {venue.get('name', 'N/A')} (page limit: {venue.get('page_limit', 'N/A')})")
    print(f"CURRENT: {cur.get('stage')} (Phase {cur.get('phase')})")
    print(f"STATUS:  {cur.get('status')}")
    print(f"HISTORY: {len(data.get('history', []))} stages")
    print(f"BACKTRACKS: {len(data.get('backtrack_log', []))}")
    if proj.get('renamed_from'):
        print(f"RENAMED_FROM: {proj['renamed_from']}")


def cmd_phase_status(project_dir: str):
    """Print phase-by-phase completion status."""
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    if not state_file.exists():
        print(f"[ERROR] State file not found: {state_file}")
        sys.exit(1)
    data = _load(state_file)
    phases = data.get("phases", {})
    print("\n" + "=" * 50)
    print("  PHASE STATUS")
    print("=" * 50)
    for ph in ALL_PHASES:
        info = phases.get(ph, {})
        status = info.get("status", "unknown")
        last = info.get("last_stage", "-")
        completed = info.get("completed_at", "-")
        if completed and completed != "-":
            completed = completed[:16]  # truncate to YYYY-MM-DD HH:MM
        icon = "✅" if status == "completed" else "⏳" if status == "in_progress" else "⬜"
        print(f"  {icon} {ph}: {status:12s} | last={last} | {completed}")
    print("=" * 50)


def _phase_of_stage(stage: str) -> str:
    return PHASE_OF.get(stage, "P1")


def _is_last_stage_of_phase(stage: str) -> bool:
    """Check if stage is the last stage of its phase (the gate stage)."""
    ph = _phase_of_stage(stage)
    stages = PHASE_STAGES.get(ph, [])
    return len(stages) > 0 and stages[-1] == stage


def _get_first_stage_of_phase(phase: str) -> str:
    """Get the first stage of a phase."""
    stages = PHASE_STAGES.get(phase, [])
    return stages[0] if stages else "S01"


def _check_phase_prerequisites(data: dict, target_phase: str) -> tuple[bool, str]:
    """Check if all previous phases are completed before starting target_phase."""
    if target_phase not in ALL_PHASES:
        return False, f"Unknown phase: {target_phase}"
    idx = ALL_PHASES.index(target_phase)
    if idx == 0:
        return True, "P1 has no prerequisites"
    prev_phase = ALL_PHASES[idx - 1]
    prev_status = data.get("phases", {}).get(prev_phase, {}).get("status", "pending")
    if prev_status != "completed":
        return False, (
            f"{prev_phase} is not completed (status: {prev_status}). "
            f"Please run {prev_phase} first."
        )
    return True, f"{prev_phase} completed. Ready to start {target_phase}."


def cmd_advance(project_dir: str, stage: str, agent: str, output_file: str):
    """Mark a stage complete and advance to next."""
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    data = _load(state_file)

    # Record completion
    history_entry = {
        "stage": stage,
        "agent": agent,
        "completed_at": datetime.now().isoformat(),
        "output": output_file,
    }
    data["history"].append(history_entry)

    # Determine next stage
    ALL_STAGES = [f"S{i:02d}" for i in range(1, 38)]  # S01-S37
    idx = ALL_STAGES.index(stage)
    next_stage = ALL_STAGES[idx + 1] if idx + 1 < len(ALL_STAGES) else None

    if next_stage:
        data["current"]["stage"] = next_stage
        data["current"]["phase"] = PHASE_OF.get(next_stage, "P8")

        # If we just completed a gate stage, mark the phase as completed
        # and set status to phase_completed (wait for user to explicitly start next phase)
        if stage in GATE_STAGES:
            completed_phase = PHASE_OF.get(stage, "P1")
            if "phases" not in data:
                data["phases"] = {}
            data["phases"][completed_phase] = {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "last_stage": stage,
            }
            data["current"]["status"] = "phase_completed"
            _save(state_file, data)
            print(f"[ADVANCED] {stage} → {next_stage}")
            print(f"[PHASE COMPLETE] {completed_phase} finished at {stage}. "
                  f"Status: phase_completed. Waiting for user to start next phase.")
        else:
            data["current"]["status"] = "in_progress"
            _save(state_file, data)
            print(f"[ADVANCED] {stage} → {next_stage}")
    else:
        # Last stage (S37) completed
        data["current"]["status"] = "completed"
        data["phases"]["P8"] = {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "last_stage": stage,
        }
        _save(state_file, data)
        print(f"[COMPLETED] {stage} → ALL DONE")
        print(f"[PHASE COMPLETE] P8 finished. Project fully completed.")


def cmd_human_review(project_dir: str, stage: str, opinion: str, verdict: str = "revise"):
    """
    Record user's review opinion for a stage and take action.

    This allows the user to spontaneously intervene at any point without
    waiting for the Conductor to ask. The user's opinion becomes part of
    the Gate review record and can trigger revise/backtrack.

    Args:
        stage: Stage ID being reviewed (e.g. "S05")
        opinion: User's review text
        verdict: "pass" | "revise" | "backtrack"
    """
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    if not state_file.exists():
        print(f"[ERROR] State file not found: {state_file}")
        sys.exit(1)

    data = _load(state_file)
    proj_name = data.get("project", {}).get("display_name", "Project")

    # Record human review
    review_entry = {
        "stage": stage,
        "opinion": opinion,
        "verdict": verdict,
        "reviewer": "human",
        "timestamp": datetime.now().isoformat(),
    }
    if "human_reviews" not in data:
        data["human_reviews"] = []
    data["human_reviews"].append(review_entry)

    # Save review to knowledge/reviews/
    review_dir = Path(project_dir) / "knowledge" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_file = review_dir / f"human_{stage}_review.md"
    review_file.write_text(
        f"# Human Review — {stage}\n\n"
        f"**Project**: {proj_name}\n"
        f"**Stage**: {stage}\n"
        f"**Verdict**: {verdict.upper()}\n"
        f"**Time**: {review_entry['timestamp']}\n\n"
        f"## Opinion\n\n{opinion}\n\n"
        f"---\n"
        f"*This review was submitted by the user via the human-gate mechanism.*\n",
        encoding="utf-8",
    )

    # Take action based on verdict
    if verdict == "pass":
        data["current"]["status"] = "in_progress"
        _save(state_file, data)
        print(f"[HUMAN REVIEW] {stage}: PASS")
        print(f"  Opinion saved to: {review_file}")
        print(f"  Action: Continue to next stage/phase.")

    elif verdict == "revise":
        # Mark the stage for re-execution by resetting state to that stage
        target_phase = PHASE_OF.get(stage, "P1")
        data["current"]["stage"] = stage
        data["current"]["phase"] = target_phase
        data["current"]["status"] = "in_progress"
        _save(state_file, data)
        print(f"[HUMAN REVIEW] {stage}: REVISE")
        print(f"  Opinion saved to: {review_file}")
        print(f"  Action: State reset to {stage} ({target_phase}). Re-execute this stage.")
        print(f"  Next: Re-run the stage with user's feedback incorporated.")

    elif verdict == "backtrack":
        # Backtrack to the reviewed stage — the stage being reviewed IS the
        # source (where the problem was found) AND the target (re-execute it).
        # The "from" in the log is the current stage (where the system was
        # when the user intervened), not an arbitrary next stage.
        current_stage = data["current"]["stage"]
        from_stage = current_stage  # Stage where user noticed the problem

        backtrack_entry = {
            "from": from_stage,
            "to": stage,
            "reason": f"Human review: {opinion[:100]}",
            "direction": opinion[:200],
            "timestamp": datetime.now().isoformat(),
        }
        data.setdefault("backtrack_log", []).append(backtrack_entry)

        target_phase = PHASE_OF.get(stage, "P1")
        data["current"]["stage"] = stage
        data["current"]["phase"] = target_phase
        data["current"]["status"] = "in_progress"

        # Mark downstream stages as stale (from target to current)
        all_stages_flat = [s for stages in PHASE_STAGES.values() for s in stages]
        try:
            to_idx = all_stages_flat.index(stage)
            from_idx = all_stages_flat.index(from_stage)
            stale_stages = all_stages_flat[to_idx + 1 : from_idx + 1]
            existing_stale = set(data.get("stale_stages", []))
            existing_stale.update(stale_stages)
            data["stale_stages"] = sorted(existing_stale, key=lambda s: all_stages_flat.index(s))
        except (ValueError, IndexError):
            pass

        # Decision log
        data.setdefault("decision_log", []).append({
            "type": "human_backtrack",
            "stage": stage,
            "summary": f"Human backtrack from {from_stage} to {stage}",
            "details": opinion[:200],
            "timestamp": datetime.now().isoformat(),
        })

        _save(state_file, data)
        print(f"[HUMAN REVIEW] {stage}: BACKTRACK")
        print(f"  Opinion saved to: {review_file}")
        print(f"  Action: Backtracked from {from_stage} to {stage} ({target_phase}).")
        print(f"  Next: Re-execute from {stage} with user's feedback.")

    else:
        print(f"[ERROR] Unknown verdict: {verdict}. Use: pass | revise | backtrack")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Learning from mistakes — Experience KB
# ---------------------------------------------------------------------------

def cmd_list_learned():
    """List all learned experience notes under docs/LEARNED/."""
    learned_dir = Path(__file__).parent.parent / "docs" / "LEARNED"
    if not learned_dir.exists():
        print("[INFO] No LEARNED directory found.")
        return

    files = sorted(learned_dir.rglob("*.md"))
    # Exclude README.md
    files = [f for f in files if f.name != "README.md"]
    if not files:
        print("[INFO] No learned experience notes found.")
        return

    print("\n" + "=" * 90)
    print("  LEARNED EXPERIENCE NOTES")
    print("=" * 90)
    print(f"  {'File':<40} {'Stage':<8} {'Date':<12} {'Severity':<8} {'Clear After'}")
    print("-" * 90)

    import re
    for f in files:
        content = f.read_text(encoding="utf-8")
        # Extract frontmatter
        stage = "—"
        date = "—"
        severity = "—"
        clear_after = "—"
        if content.startswith("---"):
            fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if fm_match:
                try:
                    fm = yaml.safe_load(fm_match.group(1))
                    stage = fm.get("stage", "—")
                    date = fm.get("date", "—")
                    severity = fm.get("severity", "—")
                    clear_after = fm.get("clear_after", "—")
                except Exception:
                    pass
        rel = f.relative_to(learned_dir)
        print(f"  {str(rel):<40} {stage:<8} {date:<12} {severity:<8} {clear_after}")
    print("=" * 90 + "\n")


def cmd_learn_report(project_dir: str):
    """Generate a learning report based on project's backtrack_log and human_reviews."""
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    if not state_file.exists():
        print(f"[ERROR] State file not found: {state_file}")
        sys.exit(1)

    data = _load(state_file)
    proj_name = data.get("project", {}).get("display_name", "Project")
    backtracks = data.get("backtrack_log", [])
    human_reviews = data.get("human_reviews", [])

    learned_dir = Path(__file__).parent.parent / "docs" / "LEARNED"
    learned_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = learned_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_file = reports_dir / f"report-{proj_name}-{datetime.now().strftime('%Y%m%d')}.md"

    lines = [
        f"# Learning Report — {proj_name}",
        f"",
        f"**Generated**: {datetime.now().isoformat()}",
        f"**Backtracks**: {len(backtracks)}",
        f"**Human Reviews**: {len(human_reviews)}",
        f"",
        f"---",
        f"",
        f"## Backtrack Analysis",
        f"",
    ]

    if backtracks:
        for i, bt in enumerate(backtracks, 1):
            lines.append(f"### Backtrack #{i}")
            lines.append(f"- **From**: {bt.get('from', '?')}")
            lines.append(f"- **To**: {bt.get('to', '?')}")
            lines.append(f"- **Reason**: {bt.get('reason', 'N/A')}")
            lines.append(f"- **Time**: {bt.get('timestamp', 'N/A')}")
            lines.append(f"")
            # Suggest learned note
            lines.append(f"> **Suggested Learned Note**: Create `docs/LEARNED/stage/{bt.get('to', 'S01')}.md` with prevention for this issue.")
            lines.append(f"")
    else:
        lines.append("No backtracks recorded.")
        lines.append("")

    lines.extend([
        f"## Human Review Analysis",
        f"",
    ])

    if human_reviews:
        for i, hr in enumerate(human_reviews, 1):
            lines.append(f"### Review #{i}")
            lines.append(f"- **Stage**: {hr.get('stage', '?')}")
            lines.append(f"- **Verdict**: {hr.get('verdict', 'N/A')}")
            lines.append(f"- **Opinion**: {hr.get('opinion', 'N/A')}")
            lines.append(f"- **Time**: {hr.get('timestamp', 'N/A')}")
            lines.append(f"")
    else:
        lines.append("No human reviews recorded.")
        lines.append("")

    lines.extend([
        f"## Recommendations",
        f"",
        f"Based on the above, consider creating/updating the following learned notes:",
        f"",
    ])

    # Collect unique stages from backtracks and reviews
    stages = set()
    for bt in backtracks:
        stages.add(bt.get("to", "S01"))
    for hr in human_reviews:
        stages.add(hr.get("stage", "S01"))

    for stage in sorted(stages):
        lines.append(f"- `docs/LEARNED/stage/{stage}.md` — Review issues related to {stage}")

    lines.append(f"")
    lines.append(f"---")
    lines.append(f"*This report is auto-generated. Review and convert relevant items into formal learned notes.*")
    lines.append(f"")

    report_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[LEARN REPORT] Generated: {report_file}")
    print(f"  Backtracks: {len(backtracks)}")
    print(f"  Human Reviews: {len(human_reviews)}")
    print(f"  Review the report and create formal learned notes in docs/LEARNED/")


def cmd_clear_learned(dry_run: bool = False):
    """Clear outdated learned experience notes based on clear_after rules."""
    learned_dir = Path(__file__).parent.parent / "docs" / "LEARNED"
    if not learned_dir.exists():
        print("[INFO] No LEARNED directory found.")
        return

    files = sorted(learned_dir.rglob("*.md"))
    files = [f for f in files if f.name != "README.md"]
    if not files:
        print("[INFO] No learned notes to clear.")
        return

    import re
    cleared = []
    kept = []

    for f in files:
        content = f.read_text(encoding="utf-8")
        clear_after = None
        if content.startswith("---"):
            fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if fm_match:
                try:
                    fm = yaml.safe_load(fm_match.group(1))
                    clear_after = fm.get("clear_after", None)
                except Exception:
                    pass

        if clear_after == "never":
            kept.append((f, "never"))
        else:
            # For now, only clear explicitly marked items
            # A full implementation would track project count / dates
            if dry_run:
                cleared.append((f, clear_after or "unspecified"))
            else:
                # Only clear if clear_after is set and not "never"
                if clear_after and clear_after != "never":
                    cleared.append((f, clear_after))
                    f.unlink()
                else:
                    kept.append((f, clear_after or "unspecified"))

    print("\n" + "=" * 70)
    print("  CLEAR LEARNED NOTES")
    print("=" * 70)

    if dry_run:
        print("  [DRY RUN] No files will be deleted.")

    if cleared:
        print(f"\n  Cleared ({len(cleared)}):")
        for f, reason in cleared:
            print(f"    - {f.relative_to(learned_dir)} ({reason})")
    else:
        print("\n  No files cleared.")

    if kept:
        print(f"\n  Kept ({len(kept)}):")
        for f, reason in kept:
            print(f"    - {f.relative_to(learned_dir)} ({reason})")

    print("=" * 70 + "\n")


def cmd_run_phase(project_dir: str, phase: str):
    """Prepare to run a specific phase. Checks prerequisites and sets state."""
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    if not state_file.exists():
        print(f"[ERROR] State file not found: {state_file}")
        sys.exit(1)
    data = _load(state_file)

    ok, msg = _check_phase_prerequisites(data, phase)
    if not ok:
        print(f"[BLOCKED] Cannot start {phase}: {msg}")
        sys.exit(1)

    first_stage = _get_first_stage_of_phase(phase)
    data["current"]["phase"] = phase
    data["current"]["stage"] = first_stage
    data["current"]["status"] = "in_progress"

    # Mark phase as in_progress
    if "phases" not in data:
        data["phases"] = {}
    data["phases"][phase] = {
        "status": "in_progress",
        "completed_at": None,
        "last_stage": None,
    }

    _save(state_file, data)
    print(f"[PHASE START] {phase} starting at {first_stage}")
    print(f"  Prerequisites: {msg}")


def cmd_backtrack(project_dir: str, from_stage: str, to_stage: str, reason: str,
                  direction: str = ""):
    """Trigger backward propagation with full state management.

    Args:
        from_stage: Stage where the problem was discovered.
        to_stage: Target stage to backtrack to (must be earlier than from_stage).
        reason: Why the backtrack is needed.
        direction: Modification guidance for the target stage agent.
    """
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    data = _load(state_file)

    target_phase = PHASE_OF.get(to_stage, "P1")

    # ---- Spiral limit protection ----
    spiral_count = data.get("spiral_count", {}).get(target_phase, 0)
    if spiral_count >= 3:
        print(f"[HALT] Spiral limit reached for {target_phase} ({spiral_count} backtracks).")
        print(f"  Cannot backtrack {from_stage} → {to_stage} without human intervention.")
        print(f"  Action: Review the root cause manually before re-attempting.")
        print(f"  提示：{target_phase} 已回溯 {spiral_count} 次，超过上限。请人工分析根因。")
        sys.exit(1)

    # ---- Record backtrack ----
    data.setdefault("backtrack_log", []).append({
        "from": from_stage,
        "to": to_stage,
        "reason": reason,
        "direction": direction,
        "target_phase": target_phase,
        "timestamp": datetime.now().isoformat(),
    })

    # ---- Update current state ----
    data["current"]["stage"] = to_stage
    data["current"]["phase"] = target_phase
    data["current"]["status"] = "in_progress"

    # ---- Reopen affected phases ----
    all_phases = list(PHASE_STAGES.keys())
    all_stages_flat = [s for stages in PHASE_STAGES.values() for s in stages]
    try:
        to_idx = all_stages_flat.index(to_stage)
        from_idx = all_stages_flat.index(from_stage)
        target_ph_idx = all_phases.index(target_phase)
        # Reopen all phases from target phase through the phase containing from_stage
        from_phase = PHASE_OF.get(from_stage, target_phase)
        from_ph_idx = all_phases.index(from_phase)
        for idx in range(target_ph_idx, from_ph_idx + 1):
            ph = all_phases[idx]
            if "phases" in data and ph in data["phases"]:
                if data["phases"][ph].get("status") in ("completed", "phase_completed"):
                    data["phases"][ph]["status"] = "reopened"
                    data["phases"][ph]["completed_at"] = None
                    print(f"  [REOPENED] {ph}")
    except (ValueError, IndexError):
        pass

    # ---- Increment spiral count (start from 0) ----
    data.setdefault("spiral_count", {})[target_phase] = spiral_count + 1

    # ---- Mark downstream stages as stale ----
    try:
        to_idx = all_stages_flat.index(to_stage)
        from_idx = all_stages_flat.index(from_stage)
        stale_stages = all_stages_flat[to_idx + 1 : from_idx + 1]
        existing_stale = set(data.get("stale_stages", []))
        existing_stale.update(stale_stages)
        data["stale_stages"] = sorted(existing_stale, key=lambda s: all_stages_flat.index(s))
        if stale_stages:
            print(f"  [STALE] Marked {len(stale_stages)} stage(s) for re-execution: "
                  f"{stale_stages[0]} → {stale_stages[-1]}")
    except (ValueError, IndexError):
        pass

    # ---- Flag Gate re-review ----
    from_phase = PHASE_OF.get(from_stage, target_phase)
    try:
        for idx in range(all_phases.index(target_phase), all_phases.index(from_phase) + 1):
            ph = all_phases[idx]
            gate_id = f"G{ph[1:]}"
            data.setdefault("gate_re_review", {})[gate_id] = {
                "needs_re_review": True,
                "flagged_at": datetime.now().isoformat(),
                "reason": f"Backtrack {from_stage} → {to_stage}",
            }
            print(f"  [GATE FLAG] {gate_id} needs re-review")
    except (ValueError, IndexError):
        pass

    # ---- Decision log ----
    data.setdefault("decision_log", []).append({
        "type": "backtrack",
        "from_stage": from_stage,
        "to_stage": to_stage,
        "summary": f"Backtrack from {from_stage} to {to_stage}",
        "details": f"Reason: {reason}\nDirection: {direction}\nSpiral count for {target_phase}: {spiral_count + 1}",
        "timestamp": datetime.now().isoformat(),
    })

    _save(state_file, data)
    print(f"[BACKTRACK] {from_stage} → {to_stage}: {reason}")
    if spiral_count + 1 >= 3:
        print(f"  ⚠  {target_phase} spiral count is now {spiral_count + 1}/3 — next backtrack will HALT.")


def cmd_set_venue(project_dir: str, venue_id: str):
    """Change the target venue for a project."""
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    if not state_file.exists():
        print(f"[ERROR] State file not found: {state_file}")
        sys.exit(1)
    data = _load(state_file)
    
    venue_config = _get_venue_config(venue_id)
    if venue_config is None:
        available = list(_load_venue_registry().get("venues", {}).keys())
        print(f"[ERROR] Unknown venue '{venue_id}'. Available: {available}")
        sys.exit(1)
    
    old_venue = data.get("project", {}).get("venue", {}).get("id", "unknown")
    data["project"]["venue"] = {
        "id": venue_id,
        "name": venue_config.get("name", venue_id),
        "page_limit": venue_config.get("page_limit"),
        "page_limit_note": venue_config.get("page_limit_note", ""),
        "format": venue_config.get("format", ""),
        "style_package": venue_config.get("style_package", ""),
        "template_dir": venue_config.get("template_dir", ""),
        "set_at": datetime.now().isoformat(),
    }
    _save(state_file, data)
    
    # Copy new template files
    proj = Path(project_dir)
    template_dir = Path(__file__).parent.parent / "templates" / "venue" / venue_config.get("template_dir", venue_id)
    latex_template_dir = proj / "artifacts" / "latex_template"
    if template_dir.exists():
        if latex_template_dir.exists():
            shutil.rmtree(latex_template_dir)
        latex_template_dir.mkdir(parents=True, exist_ok=True)
        for pattern in ["*.sty", "*.bst", "*.cls", "*.tex", "README.md"]:
            for src in template_dir.rglob(pattern):
                if src.is_file():
                    rel = src.relative_to(template_dir)
                    dst = latex_template_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
    
    print(f"[VENUE] Changed from '{old_venue}' to '{venue_id}'")
    print(f"  Name: {venue_config.get('name', venue_id)}")
    print(f"  Page Limit: {venue_config.get('page_limit', 'N/A')} pages")
    print(f"  Template: {latex_template_dir}")


def cmd_list_venues():
    """List all available venues from registry."""
    registry = _load_venue_registry()
    venues = registry.get("venues", {})
    default = registry.get("default_venue", "arxiv")
    print("\n" + "=" * 70)
    print("  AVAILABLE VENUES")
    print("=" * 70)
    for vid, vcfg in venues.items():
        marker = " [DEFAULT]" if vid == default else ""
        print(f"\n  {vid}{marker}")
        print(f"    Name:        {vcfg.get('full_name', vcfg.get('name', vid))}")
        print(f"    Type:        {vcfg.get('type', 'unknown')}")
        print(f"    Page Limit:  {vcfg.get('page_limit', 'N/A')} pages")
        print(f"    Format:      {vcfg.get('format', 'unknown')}, {vcfg.get('paper_size', '')}")
        print(f"    Style:       \\usepackage{vcfg.get('style_package', 'N/A')}")
        print(f"    Anonymous:   {vcfg.get('anonymous', True)}")
    print("\n" + "=" * 70)
    print(f"  Usage: create <topic> <display_name> [venue]")
    print(f"  Usage: set-venue <project_dir> <venue_id>")
    print("=" * 70 + "\n")


def cmd_rename(project_dir: str, new_name: str, rename_folder: bool = False, force: bool = False):
    """Rename project display name. Only allowed after Phase 2 is complete."""
    state_file = Path(project_dir) / "state" / "pipeline_state.yaml"
    data = _load(state_file)
    
    # Enforce Phase 2 completion before renaming
    p2_status = data.get("phases", {}).get("P2", {}).get("status", "pending")
    if p2_status != "completed" and not force:
        current_phase = data.get("current", {}).get("phase", "P1")
        current_stage = data.get("current", {}).get("stage", "S01")
        print(
            f"[BLOCKED] Cannot rename project before Phase 2 (Design) is complete. "
            f"Current position: {current_stage} ({current_phase}). "
            f"Phase 2 status: {p2_status}. "
            f"Please complete S10 (Full Experiment Plan) and pass Gate G2 first."
        )
        sys.exit(1)
    
    old = data["project"].get("display_name", data["project"]["name"])
    data["project"]["display_name"] = new_name
    data["project"]["renamed_at"] = datetime.now().isoformat()
    data["project"]["renamed_from"] = old
    _save(state_file, data)
    print(f"[RENAMED] {old} → {new_name}")
    
    if rename_folder:
        proj_path = Path(project_dir)
        new_folder_name = _sanitize_folder_name(new_name)
        ts = proj_path.name.split("-")[-1]
        if len(ts) == 15 and ts[:8].isdigit():
            new_folder_name = f"{new_folder_name}-{ts}"
        else:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            new_folder_name = f"{new_folder_name}-{ts}"
        
        new_proj_path = proj_path.parent / new_folder_name
        
        if new_proj_path.exists():
            print(f"[ERROR] Target directory already exists: {new_proj_path}")
            sys.exit(1)
        
        try:
            proj_path.rename(new_proj_path)
            print(f"[RENAME] Folder renamed: {proj_path.name} → {new_proj_path.name}")
            print(f"[IMPORTANT] New project path: {new_proj_path}")
        except (OSError, PermissionError) as e:
            print(f"[WARN] Direct rename failed ({e}). Trying copy-then-delete fallback...")
            try:
                shutil.copytree(proj_path, new_proj_path)
                print(f"[RENAME] Copied to: {new_proj_path.name}")
                try:
                    shutil.rmtree(proj_path)
                    print(f"[RENAME] Removed old: {proj_path.name}")
                except (OSError, PermissionError) as del_err:
                    print(
                        f"[WARN] Could not remove old directory: {del_err}\n"
                        f"       Old directory remains at: {proj_path}\n"
                        f"       New directory is at: {new_proj_path}\n"
                        f"       You may need to manually remove the old directory later."
                    )
                print(f"[IMPORTANT] New project path: {new_proj_path}")
            except Exception as copy_err:
                print(f"[ERROR] Rename failed: {copy_err}")
                sys.exit(1)


def cmd_list_projects():
    """List all projects under projects/ with their current status."""
    if not PROJECTS_ROOT.exists():
        print(f"[INFO] Projects directory not found: {PROJECTS_ROOT}")
        print("  No projects yet. Create one with:")
        print("    python scripts/state_manager.py create <topic> <display_name> [venue]")
        return

    projects = sorted([d for d in PROJECTS_ROOT.iterdir() if d.is_dir()])
    if not projects:
        print("[INFO] No projects found.")
        return

    current = _get_current_project()
    print("\n" + "=" * 90)
    print(f"  PROJECTS  (root: {PROJECTS_ROOT})")
    print("=" * 90)
    print(f"  {'#':<3} {'Name':<40} {'Stage':<8} {'Phase':<6} {'Status':<16} {'Current'}")
    print("-" * 90)

    for i, proj_dir in enumerate(projects, 1):
        state_file = proj_dir / "state" / "pipeline_state.yaml"
        marker = " 👈" if current and proj_dir.resolve() == current.resolve() else ""
        if not state_file.exists():
            print(f"  {i:<3} {proj_dir.name:<40} {'—':<8} {'—':<6} {'no state':<16}{marker}")
            continue

        data = _load(state_file)
        proj = data.get("project", {})
        cur = data.get("current", {})
        name = proj.get("display_name", proj.get("name", proj_dir.name))
        stage = cur.get("stage", "—")
        phase = cur.get("phase", "—")
        status = cur.get("status", "—")
        venue = proj.get("venue", {})
        venue_name = venue.get("name", "") if isinstance(venue, dict) else str(venue)
        venue_str = f" [{venue_name}]" if venue_name else ""
        print(f"  {i:<3} {name:<40} {stage:<8} {phase:<6} {status:<16}{marker}{venue_str}")

    print("=" * 90)
    if current:
        print(f"  Current default: {current}")
    print("  Set default:  python scripts/state_manager.py use <project_dir>")
    print("  Or use flag:  python scripts/state_manager.py --project <dir> status")
    print("=" * 90 + "\n")


def cmd_use(project_dir: str):
    """Set the default project for subsequent commands."""
    path = Path(project_dir)
    if not path.exists():
        print(f"[ERROR] Project directory not found: {path}")
        sys.exit(1)
    state_file = path / "state" / "pipeline_state.yaml"
    if not state_file.exists():
        print(f"[WARN] No state file found. Setting anyway.")
    _set_current_project(str(path))


def _print_help():
    print("Usage: state_manager.py <command> [options] [args...]")
    print("\nProject selection (for commands that need a project):")
    print("  --project /path/to/project    Specify project for this command")
    print("  use /path/to/project          Set default project (persisted)")
    print("\nCommands:")
    print("  create <topic> <display_name> [venue]")
    print("  status                        Show current project status")
    print("  phase-status                  Show phase completion status")
    print("  advance <stage> <agent> <output_file>")
    print("  run-phase <phase>")
    print("  backtrack <from_stage> <to_stage> <reason>")
    print("  rename <new_name> [--rename-folder] [--force]")
    print("  set-venue <venue_id>")
    print("  human-review <stage> <opinion> [pass|revise|backtrack]")
    print("                                Submit user review for a stage")
    print("  list-learned                  List learned experience notes")
    print("  learn-report                  Generate learning report for project")
    print("  clear-learned [--dry-run]     Clear outdated learned notes")
    print("  list-projects                 List all projects")
    print("  list-venues                   List available venues")


def main():
    args = sys.argv[1:]
    if not args:
        _print_help()
        sys.exit(1)

    # Pre-scan for --project flag (can appear anywhere)
    project_dir_override = None
    i = 0
    while i < len(args):
        if args[i] == "--project" and i + 1 < len(args):
            project_dir_override = args[i + 1]
            del args[i : i + 2]
            break
        i += 1

    if not args:
        _print_help()
        sys.exit(1)

    cmd = args.pop(0)

    # Commands that don't need a project
    if cmd == "create":
        if len(args) < 2:
            print("Usage: create <topic> <display_name> [venue]")
            print(f"  Projects root: {PROJECTS_ROOT}")
            sys.exit(1)
        venue = args[2] if len(args) > 2 else None
        cmd_create(args[0], args[1], venue)
        return

    if cmd == "list-projects":
        cmd_list_projects()
        return

    if cmd == "list-venues":
        cmd_list_venues()
        return

    if cmd == "list-learned":
        cmd_list_learned()
        return

    if cmd == "clear-learned":
        dry_run = "--dry-run" in args
        cmd_clear_learned(dry_run=dry_run)
        return

    if cmd == "use":
        if not args:
            print("Usage: use <project_dir>")
            sys.exit(1)
        cmd_use(args[0])
        return

    # Commands that need a project — resolve project_dir
    if project_dir_override:
        project_dir = project_dir_override
    else:
        try:
            project_dir = _resolve_project_dir(args)
        except SystemExit as e:
            msg = e.code if isinstance(e.code, str) else str(e)
            print(msg)
            sys.exit(1)

    if cmd == "status":
        cmd_status(project_dir)
    elif cmd == "phase-status":
        cmd_phase_status(project_dir)
    elif cmd == "advance":
        if len(args) < 3:
            print("Usage: advance <stage> <agent> <output_file>  (--project <dir>)")
            sys.exit(1)
        cmd_advance(project_dir, args[0], args[1], args[2])
    elif cmd == "run-phase":
        if len(args) < 1:
            print("Usage: run-phase <phase>  (--project <dir>)")
            sys.exit(1)
        cmd_run_phase(project_dir, args[0])
    elif cmd == "backtrack":
        if len(args) < 3:
            print("Usage: backtrack <from_stage> <to_stage> <reason> [direction]  (--project <dir>)")
            sys.exit(1)
        direction = args[3] if len(args) >= 4 else ""
        cmd_backtrack(project_dir, args[0], args[1], args[2], direction)
    elif cmd == "rename":
        if len(args) < 1:
            print("Usage: rename <new_name> [--rename-folder] [--force]  (--project <dir>)")
            sys.exit(1)
        rename_folder_flag = "--rename-folder" in args
        force_flag = "--force" in args
        cmd_rename(project_dir, args[0], rename_folder=rename_folder_flag, force=force_flag)
    elif cmd == "set-venue":
        if len(args) < 1:
            print("Usage: set-venue <venue_id>  (--project <dir>)")
            sys.exit(1)
        cmd_set_venue(project_dir, args[0])
    elif cmd == "learn-report":
        cmd_learn_report(project_dir)
    elif cmd == "human-review":
        if len(args) < 2:
            print("Usage: human-review <stage> <opinion> [pass|revise|backtrack]  (--project <dir>)")
            sys.exit(1)
        stage = args[0]
        opinion = args[1]
        verdict = args[2] if len(args) > 2 else "revise"
        cmd_human_review(project_dir, stage, opinion, verdict)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
