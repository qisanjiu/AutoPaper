"""Project lifecycle: create, initialize, archive"""
import re
import shutil
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .state import PipelineState

# Phase -> Stage mapping
PHASE_STAGES = {
    "P1": ["S01", "S02", "S03", "S04", "S05"],
    "P2": ["S06", "S07", "S08", "S09", "S10"],
    "P3": ["S11", "S12", "S13"],
    "P4": ["S14", "S15", "S16", "S17"],
    "P5": ["S18", "S19", "S20", "S21"],
    "P6": ["S22", "S23", "S24", "S25"],
    "P7": ["S26", "S27", "S28", "S29", "S30", "S31", "S32", "S33"],
    "P8": ["S34", "S35", "S36", "S37"],
}

GATE_STAGES = {"G1": "S05", "G2": "S10", "G3": "S13", "G4": "S17", "G5": "S21", "G6": "S25", "G7": "S33", "G8": "S37"}

AGENT_FOR_STAGE = {
    "S01": "literature", "S02": "literature",
    "S03": "ideation", "S04": "ideation", "S05": "ideation",
    "S06": "method", "S07": "method", "S08": "method", "S09": "method", "S10": "method",
    "S11": "experiment", "S12": "experiment", "S13": "analysis",
    "S14": "experiment", "S15": "experiment", "S16": "experiment", "S17": "analysis",
    "S18": "analysis", "S19": "analysis", "S20": "experiment", "S21": "analysis",
    "S22": "analysis", "S23": "analysis", "S24": "writing", "S25": "ideation",
    "S26": "writing", "S27": "writing", "S28": "writing", "S29": "writing",
    "S30": "writing", "S31": "writing", "S32": "figure", "S33": "writing",
    "S34": "critic_team", "S35": "review", "S36": "writing", "S37": "writing",
}

# Windows reserved names that cannot be used as folder/file names
_WIN_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_folder_name(name: str) -> str:
    """
    Convert to filesystem-safe folder name. Preserves Chinese characters.
    Handles both Windows (via WSL2 /mnt/c/) and Linux filesystems.
    """
    name = name.strip()
    # Replace spaces with hyphens
    name = name.replace(" ", "-")
    # Remove filesystem-unsafe characters but keep Chinese, English, digits, hyphens, dots
    # Windows illegal: < > : " / \ | ? *
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    # Windows: cannot end with a space or dot
    name = name.rstrip(" .")
    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)
    # Trim hyphens from ends
    name = name.strip("-")
    # Avoid Windows reserved names by appending an underscore
    if name.upper() in _WIN_RESERVED:
        name = name + "_"
    return name or "untitled"


def _load_venue_registry() -> Dict[str, Any]:
    """Load the venue template registry from framework root."""
    registry_path = Path(__file__).parent.parent / "config" / "venue_registry.yaml"
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_venue_config(venue_id: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific venue from registry."""
    registry = _load_venue_registry()
    venues = registry.get("venues", {})
    return venues.get(venue_id)


def create_project(topic: str, display_name: Optional[str], projects_root: Path, venue: Optional[str] = None) -> Path:
    """
    Create a new research project directory next to the framework.

    Args:
        topic: The research topic (used for initial description)
        display_name: Optional human-readable project name. If None, uses topic.
        projects_root: Where to create the project folder.
        venue: Target venue ID (e.g., 'neurips', 'icml', 'iclr', 'acl', 'cvpr', 'ieee_trans').
               If None, uses default from registry.

    Layout: projects_root / {folder_name}-{timestamp} /
    """
    # Validate projects_root is not inside the framework directory
    _fw_root = Path(__file__).parent.parent.resolve()
    try:
        _ = projects_root.resolve().relative_to(_fw_root)
    except ValueError:
        pass  # Not inside framework — correct
    else:
        raise ValueError(
            f"projects_root ({projects_root}) must NOT be inside the framework root ({_fw_root}). "
            f"Projects should live at {_fw_root.parent / 'projects'} or another location "
            f"outside the framework directory."
        )

    # Load venue registry
    registry = _load_venue_registry()
    default_venue = registry.get("default_venue", "arxiv")
    venue_id = venue if venue else default_venue
    venue_config = _get_venue_config(venue_id)
    
    if venue_config is None:
        available = list(registry.get("venues", {}).keys())
        raise ValueError(
            f"Unknown venue '{venue_id}'. Available venues: {available}. "
            f"Please specify a valid venue or add it to templates/venue/registry.yaml"
        )

    # Use display_name for folder if provided, otherwise use topic
    folder_base = display_name if display_name else topic
    folder_name = sanitize_folder_name(folder_base)
    
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    proj_dir = projects_root / f"{folder_name}-{ts}"
    proj_dir.mkdir(parents=True, exist_ok=False)

    # Stage draft folders
    drafts_dir = proj_dir / "drafts"
    drafts_dir.mkdir(exist_ok=True)
    for phase, stages in PHASE_STAGES.items():
        for stage in stages:
            (drafts_dir / stage).mkdir(exist_ok=True)

    # Supporting directories
    for sub in ["state", "knowledge", "knowledge/reviews", "artifacts", "experiments", "config", "artifacts/latex_template"]:
        (proj_dir / sub).mkdir(parents=True, exist_ok=True)

    # Copy venue template files to project
    template_dir = Path(__file__).parent.parent / "templates" / "venue" / venue_config.get("template_dir", venue_id)
    latex_template_dir = proj_dir / "artifacts" / "latex_template"
    if template_dir.exists():
        # Copy key template files
        for pattern in ["*.sty", "*.bst", "*.cls", "*.tex", "README.md"]:
            for src in template_dir.rglob(pattern):
                if src.is_file():
                    rel = src.relative_to(template_dir)
                    dst = latex_template_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

    # Copy environment config template to project
    env_template = Path(__file__).parent.parent / "config" / "environment.yaml.template"
    if env_template.exists():
        shutil.copy(env_template, proj_dir / "config" / "environment.yaml")
        print(f"          Environment config: {proj_dir / 'config' / 'environment.yaml'}")
        print(f"            → Edit this file to customize per-project settings (GPU, SSH, etc.)")
    else:
        # Fallback: copy the actual global config if template doesn't exist
        global_env = Path(__file__).parent.parent / "config" / "environment.yaml"
        if global_env.exists():
            shutil.copy(global_env, proj_dir / "config" / "environment.yaml")
            print(f"          Environment config: {proj_dir / 'config' / 'environment.yaml'} (copied from global default)")

    # Initialize pipeline_state.yaml
    state = PipelineState(proj_dir)
    state.data["project"]["name"] = folder_name
    state.data["project"]["display_name"] = display_name if display_name else topic
    state.data["project"]["topic"] = topic
    state.data["project"]["created_at"] = datetime.now().isoformat()
    state.data["project"]["renamed_at"] = None
    state.data["project"]["renamed_from"] = None
    state.set_venue(venue_id, venue_config)
    state.save()

    # Initialize decision_log.md
    display_str = display_name if display_name else topic
    (proj_dir / "state" / "decision_log.md").write_text(
        f"# Decision Log — {display_str}\n\n"
        f"> Project: `{folder_name}`\n"
        f"> Display Name: {display_str}\n"
        f"> Topic: {topic}\n"
        f"> Created: {ts}\n\n",
        encoding="utf-8"
    )

    # Initialize spiral_log.md
    (proj_dir / "state" / "spiral_log.md").write_text(
        f"# Spiral Log — {display_str}\n\n",
        encoding="utf-8"
    )

    # Copy templates
    tpl_root = Path(__file__).parent.parent / "templates"
    if tpl_root.exists():
        for stage in [s for stages in PHASE_STAGES.values() for s in stages]:
            tpl = tpl_root / "stage" / f"{stage}_template.md"
            if tpl.exists():
                shutil.copy(tpl, drafts_dir / stage / f"{stage}_draft.md")

    print(f"[PROJECT] Created {proj_dir}")
    print(f"          Display Name: {display_str}")
    print(f"          Topic: {topic}")
    print(f"          Venue: {venue_config.get('name', venue_id)} ({venue_config.get('full_name', '')})")
    print(f"          Page Limit: {venue_config.get('page_limit', 'N/A')} pages ({venue_config.get('page_limit_note', '')})")
    print(f"          Template copied to: {latex_template_dir}")
    return proj_dir


def rename_project(proj_dir: Path, new_display_name: str, rename_folder: bool = False, force: bool = False) -> Path:
    """
    Rename a project. By default, only allowed after Phase 2 (Design) is complete,
    because the research direction is finalized at that point.
    
    Args:
        proj_dir: Current project directory path
        new_display_name: New project display name (Chinese or English)
        rename_folder: If True, also rename the folder on disk
        force: If True, bypass Phase 2 completion check (use with caution)
    
    Returns:
        The project directory path (may be different if folder was renamed)
    
    Raises:
        RuntimeError: If Phase 2 is not completed and force=False
    """
    state = PipelineState(proj_dir)
    
    # Enforce Phase 2 completion before renaming
    p2_status = state.get_phase_status("P2").get("status", "pending")
    if p2_status != "completed" and not force:
        current_phase = state.get_current_phase()
        current_stage = state.get_current_stage()
        raise RuntimeError(
            f"Cannot rename project before Phase 2 (Design) is complete. "
            f"Current position: {current_stage} ({current_phase}). "
            f"Phase 2 status: {p2_status}. "
            f"Please complete S10 (Full Experiment Plan) and pass Gate G2 first. "
            f"Use force=True to override (not recommended)."
        )
    
    old_display = state.data["project"].get("display_name", state.data["project"]["name"])
    old_folder = state.data["project"]["name"]
    
    # Update state
    state.data["project"]["display_name"] = new_display_name
    state.data["project"]["renamed_at"] = datetime.now().isoformat()
    state.data["project"]["renamed_from"] = old_display
    state.save()
    
    # Update logs
    decision_log = proj_dir / "state" / "decision_log.md"
    if decision_log.exists():
        text = decision_log.read_text(encoding="utf-8")
        text += f"\n## Rename at Phase 2 (S10 complete)\n"
        text += f"- From: `{old_display}`\n"
        text += f"- To: `{new_display_name}`\n"
        text += f"- Time: {datetime.now().isoformat()}\n\n"
        decision_log.write_text(text, encoding="utf-8")
    
    spiral_log = proj_dir / "state" / "spiral_log.md"
    if spiral_log.exists():
        text = spiral_log.read_text(encoding="utf-8")
        text += f"\n## Rename\n- `{old_display}` → `{new_display_name}`\n\n"
        spiral_log.write_text(text, encoding="utf-8")
    
    new_proj_dir = proj_dir
    
    if rename_folder:
        new_folder_name = sanitize_folder_name(new_display_name)
        # Keep the timestamp suffix
        ts = proj_dir.name.split("-")[-1]
        if len(ts) == 15 and ts[:8].isdigit():  # YYYYMMDD-HHMMSS
            new_folder_name = f"{new_folder_name}-{ts}"
        else:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            new_folder_name = f"{new_folder_name}-{ts}"
        
        new_proj_dir = proj_dir.parent / new_folder_name
        
        # Check if target already exists
        if new_proj_dir.exists():
            raise FileExistsError(
                f"Cannot rename: target directory already exists: {new_proj_dir}\n"
                f"Please remove it first or choose a different name."
            )
        
        # Attempt rename with fallback for Windows file-locking issues
        try:
            proj_dir.rename(new_proj_dir)
            print(f"[RENAME] Folder renamed: {proj_dir.name} → {new_proj_dir.name}")
        except (OSError, PermissionError) as e:
            print(f"[WARN] Direct rename failed ({e}). Trying copy-then-delete fallback...")
            try:
                shutil.copytree(proj_dir, new_proj_dir)
                print(f"[RENAME] Copied to: {new_proj_dir.name}")
                try:
                    shutil.rmtree(proj_dir)
                    print(f"[RENAME] Removed old: {proj_dir.name}")
                except (OSError, PermissionError) as del_err:
                    print(
                        f"[WARN] Could not remove old directory: {del_err}\n"
                        f"       Old directory remains at: {proj_dir}\n"
                        f"       New directory is at: {new_proj_dir}\n"
                        f"       You may need to manually remove the old directory later."
                    )
            except Exception as copy_err:
                raise RuntimeError(
                    f"Failed to rename folder from {proj_dir} to {new_proj_dir}. "
                    f"Copy fallback also failed: {copy_err}"
                ) from copy_err
    
    print(f"[RENAME] Project renamed: `{old_display}` → `{new_display_name}`")
    return new_proj_dir
