"""Environment configuration loader — per-project config with global defaults.

Configuration priority:
    1. Project-local: {project_dir}/config/environment.yaml  (per-project overrides)
    2. Global default: {AutoPaper_root}/config/environment.yaml  (shared template)

When a project is created, the global default is copied to the project's config/ directory.
Subsequent stages read from the project-local config, which the user can customize per project.
"""
import os
import yaml
from pathlib import Path
from typing import Optional


def _find_framework_root() -> Path:
    """Find the AutoPaper framework root directory.

    Resolution order:
        1. Environment variable SPIRAL_FRAMEWORK_ROOT
        2. Current file's grandparent (spiral/env_config.py -> spiral/ -> AutoPaper/)

    Does NOT fall back to CWD — that produces false matches when running
    from inside a project directory that happens to have a config/ subdir.
    """
    env_root = os.environ.get("SPIRAL_FRAMEWORK_ROOT")
    if env_root:
        return Path(env_root).resolve()

    # spiral/env_config.py -> spiral/ -> AutoPaper/
    candidate = Path(__file__).parent.parent.resolve()
    # Both config/ and docs/ must exist for a valid framework root
    if (candidate / "config").is_dir() and (candidate / "docs").is_dir():
        return candidate

    raise RuntimeError(
        "Cannot find AutoPaper framework root. "
        "Set SPIRAL_FRAMEWORK_ROOT environment variable, "
        "or ensure spiral/env_config.py is installed under the AutoPaper directory."
    )


def get_global_config_path() -> Path:
    """Return the path to the global default environment.yaml."""
    return _find_framework_root() / "config" / "environment.yaml"


def get_project_config_path(project_dir: Path) -> Path:
    """Return the path to the project-local environment.yaml."""
    return Path(project_dir).resolve() / "config" / "environment.yaml"


def _resolve_config_path(project_dir: Optional[Path] = None) -> Path:
    """Resolve which config file to use.

    Priority:
        1. Project-local config if it exists
        2. Global default config

    Args:
        project_dir: Path to the project directory. If None, uses global config.

    Returns:
        Path to the resolved config file.
    """
    if project_dir is not None:
        local_path = get_project_config_path(project_dir)
        if local_path.exists():
            return local_path
        # If project-local doesn't exist, fall back to global but warn
        global_path = get_global_config_path()
        if global_path.exists():
            import warnings
            warnings.warn(
                f"Project-local config not found at {local_path}. "
                f"Falling back to global config at {global_path}. "
                f"Consider copying the global config to your project: "
                f"cp {global_path} {local_path}"
            )
            return global_path
        raise FileNotFoundError(
            f"Neither project-local ({local_path}) nor global ({global_path}) config found."
        )

    # No project_dir given — use global config
    global_path = get_global_config_path()
    if not global_path.exists():
        raise FileNotFoundError(
            f"Global environment config not found: {global_path}\n"
            f"Please create it from the template:\n"
            f"  cp {global_path.parent / 'environment.yaml.template'} {global_path}"
        )
    return global_path


def load_env_config(project_dir: Optional[Path] = None) -> dict:
    """Load the environment configuration.

    Priority: project-local → global default.

    Args:
        project_dir: Path to the project directory. If None, uses global config.

    Returns:
        Parsed YAML content of environment.yaml.

    Raises:
        FileNotFoundError: If no config file can be found.
    """
    path = _resolve_config_path(project_dir)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_env_mode(config: Optional[dict] = None, project_dir: Optional[Path] = None) -> str:
    """Return the execution mode (local/remote_ssh/remote_slurm)."""
    cfg = config or load_env_config(project_dir)
    return cfg.get("environment", {}).get("mode", "local")


def get_env_section(config: Optional[dict] = None, project_dir: Optional[Path] = None) -> dict:
    """Return the configuration section for the current mode."""
    cfg = config or load_env_config(project_dir)
    mode = get_env_mode(cfg)
    return cfg.get("environment", {}).get(mode, {})


def get_general_config(config: Optional[dict] = None, project_dir: Optional[Path] = None) -> dict:
    """Return the general configuration (budgets, sync settings)."""
    cfg = config or load_env_config(project_dir)
    return cfg.get("environment", {}).get("general", {})


def check_env_config(project_dir: Optional[Path] = None) -> tuple[bool, str]:
    """Validate that the environment config is usable.

    Args:
        project_dir: Path to the project directory. If None, uses global config.

    Returns:
        (ok, message): ok is True if config is valid, False otherwise.
    """
    try:
        cfg = load_env_config(project_dir)
    except FileNotFoundError as e:
        return False, str(e)

    env = cfg.get("environment", {})
    mode = env.get("mode", "local")

    if mode not in ("local", "remote_ssh", "remote_slurm"):
        return False, f"Invalid mode: {mode}. Must be local, remote_ssh, or remote_slurm."

    section = env.get(mode, {})

    if mode == "remote_ssh":
        if not section.get("host"):
            return False, "remote_ssh.host is empty. Please fill in the server IP/hostname."
        if not section.get("user"):
            return False, "remote_ssh.user is empty. Please fill in the SSH username."
        if not section.get("key_file") and not section.get("password"):
            return False, "remote_ssh: neither key_file nor password is set."

    if mode == "remote_slurm":
        if not section.get("host"):
            return False, "remote_slurm.host is empty."
        if not section.get("user"):
            return False, "remote_slurm.user is empty."
        if not section.get("partition"):
            return False, "remote_slurm.partition is empty."

    general = env.get("general", {})
    if not general.get("iteration_time_budget"):
        return False, "general.iteration_time_budget is not set."

    config_path = _resolve_config_path(project_dir)
    return True, f"Environment config valid. Mode: {mode}. Config path: {config_path}"


def get_config_path(project_dir: Optional[Path] = None) -> Path:
    """Return the actual config path being used (project-local or global).

    This is the resolved path that load_env_config() will read from.
    Useful for displaying to the user which config is active.
    """
    return _resolve_config_path(project_dir)
