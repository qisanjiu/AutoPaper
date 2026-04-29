"""Remote experiment executor — SSH connection, file sync, remote command execution.

Handles all three environment modes:
    - local: run experiments via subprocess
    - remote_ssh: rsync experiments/ → remote, run via ssh, rsync results back
    - remote_slurm: same as remote_ssh but submit sbatch jobs instead of direct execution

Design principles:
    - Zero additional Python dependencies (uses system ssh/rsync/sbatch)
    - Only syncs experiments/ directory (not entire project)
    - Remote directory mirrors local: ~/AutoPaper/projects/{project_name}/experiments
    - Creates a project-specific conda environment on remote if needed
"""
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from spiral.env_config import load_env_config, get_env_mode, get_env_section, get_general_config


def _find_project_root(project_dir: Path) -> Path:
    """Find the project root (parent of the AutoPaper projects directory)."""
    # project_dir is like .../projects/{project_name}
    # We want the parent of 'projects'
    if project_dir.parent.name == "projects":
        return project_dir.parent.parent
    return project_dir


class RemoteExecutor:
    """Execute experiments locally or on a remote machine via SSH.

    Config resolution: reads project-local config first, falls back to global default.

    Usage:
        executor = RemoteExecutor(project_name="my-project", project_dir=Path("..."))
        executor.setup()              # validate connection, sync code, setup env
        executor.run_remote("python train.py --config main_exp.yaml")
        executor.sync_from_remote()   # pull results back to local
    """

    def __init__(self, project_name: str, project_dir: Path, config: Optional[dict] = None):
        self.project_name = project_name
        self.project_dir = Path(project_dir).resolve()

        # Load project-local config (with global fallback)
        if config is not None:
            self.config = config
        else:
            self.config = load_env_config(self.project_dir)

        self.mode = get_env_mode(self.config)
        env_section = get_env_section(self.config)
        self.general = get_general_config(self.config)

        # Remote connection params (None if local mode)
        self.host = env_section.get("host", "")
        self.port = env_section.get("port", 22)
        self.user = env_section.get("user", "")
        self.key_file = os.path.expanduser(env_section.get("key_file", "~/.ssh/id_rsa"))
        self.password = env_section.get("password", "")
        self.remote_gpus = env_section.get("gpu_devices", "")

        # Paths
        self.local_experiments_dir = self.project_dir / "experiments"
        self.remote_base = env_section.get("remote_working_dir", "~/experiments")
        self.remote_base = os.path.expanduser(self.remote_base)
        # Remote path mirrors local structure
        self.remote_experiments_dir = f"{self.remote_base}/AutoPaper/projects/{self.project_name}/experiments"

        # Setup commands
        self.setup_commands = env_section.get("setup_commands", [])
        self.env_name = f"autopaper_{self.project_name.replace('-', '_').replace(' ', '_')}"

        # Sync settings
        self.auto_sync = self.general.get("auto_sync", True)
        self.sync_excludes = self.general.get("sync_excludes", [])

        # SSH base command
        if self.mode != "local":
            self._ssh_base = self._build_ssh_base()

    # ── SSH connection management ──────────────────────────────────────────

    def _build_ssh_base(self) -> list:
        """Build the base SSH command from config."""
        cmd = ["ssh"]
        if self.key_file and os.path.exists(self.key_file):
            cmd.extend(["-i", self.key_file])
        if self.password:
            cmd.extend(["-o", f"PasswordAuthentication=yes"])
        cmd.extend([
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=30",
            "-p", str(self.port),
        ])
        return cmd

    def _ssh_cmd(self, remote_command: str) -> list:
        """Build a full SSH command to run on the remote."""
        return self._ssh_base + [f"{self.user}@{self.host}", remote_command]

    def _rsync_cmd(self, source: str, dest: str, excludes: Optional[list] = None) -> list:
        """Build an rsync command respecting SSH config."""
        excludes = excludes or self.sync_excludes
        ssh_cmd = "ssh"
        if self.key_file and os.path.exists(self.key_file):
            ssh_cmd += f" -i {self.key_file}"
        ssh_cmd += f" -p {self.port} -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"

        cmd = [
            "rsync", "-avz", "--progress",
            "-e", ssh_cmd,
            "--timeout=60",
        ]
        for pattern in excludes:
            cmd.extend(["--exclude", pattern])
        cmd.extend([source, dest])
        return cmd

    # ── Public API ─────────────────────────────────────────────────────────

    def check_ssh_connection(self) -> tuple[bool, str]:
        """Verify SSH connection to the remote host.

        Returns:
            (ok, message): True if connection succeeds, False with error message.
        """
        if self.mode == "local":
            return True, "Local mode — no SSH needed."

        print(f"[RemoteExecutor] Testing SSH connection to {self.user}@{self.host}:{self.port}...")
        try:
            result = subprocess.run(
                self._ssh_cmd("echo 'SSH_OK'"),
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0 and "SSH_OK" in result.stdout:
                return True, f"SSH connection to {self.host} successful."
            else:
                stderr = result.stderr.strip() or "Unknown error"
                return False, f"SSH connection failed: {stderr}"
        except subprocess.TimeoutExpired:
            return False, f"SSH connection to {self.host} timed out (15s). Check host/port/network."
        except FileNotFoundError:
            return False, "ssh command not found. Is OpenSSH client installed?"
        except Exception as e:
            return False, f"SSH connection error: {e}"

    def setup_remote_env(self) -> tuple[bool, str]:
        """Create remote directory structure and conda environment.

        Does NOT install packages — that's done via requirements.txt sync.
        Creates the conda env with just Python if it doesn't exist.

        Returns:
            (ok, message)
        """
        if self.mode == "local":
            self.local_experiments_dir.mkdir(parents=True, exist_ok=True)
            return True, "Local mode — experiments directory ready."

        print(f"[RemoteExecutor] Setting up remote environment...")

        # 1. Check if conda is available on remote
        ok, msg = self._check_remote_conda()
        if not ok:
            return False, msg

        # 2. Create directory structure on remote
        ok, msg = self._create_remote_dirs()
        if not ok:
            return False, msg

        # 3. Create project-specific conda environment if needed
        ok, msg = self._setup_conda_env()
        if not ok:
            return False, msg

        return True, f"Remote environment ready at {self.remote_experiments_dir}"

    def sync_to_remote(self) -> tuple[bool, str]:
        """Sync local experiments/ to remote via rsync.

        Only syncs the experiments directory, not the entire project.
        Respects sync_excludes from config.

        Returns:
            (ok, message)
        """
        if self.mode == "local":
            return True, "Local mode — no sync needed."

        if not self.auto_sync:
            return True, "auto_sync is disabled — skipping sync."

        if not self.local_experiments_dir.exists():
            return False, f"Local experiments directory not found: {self.local_experiments_dir}"

        print(f"[RemoteExecutor] Syncing {self.local_experiments_dir} → {self.remote_experiments_dir}...")

        remote_dest = f"{self.user}@{self.host}:{self.remote_experiments_dir}"
        # Remove trailing /experiments so rsync creates it correctly
        remote_parent = f"{self.user}@{self.host}:{os.path.dirname(self.remote_experiments_dir)}"

        try:
            result = subprocess.run(
                self._rsync_cmd(
                    str(self.local_experiments_dir) + "/",
                    remote_parent + "/experiments/",
                ),
                capture_output=True, text=True, timeout=300,  # 5 min timeout for large sync
            )
            if result.returncode == 0:
                return True, f"Synced to {self.remote_experiments_dir}"
            else:
                stderr = result.stderr.strip()
                return False, f"rsync failed: {stderr}"
        except subprocess.TimeoutExpired:
            return False, "rsync timed out (5 min). Consider reducing sync size via sync_excludes."
        except FileNotFoundError:
            return False, "rsync command not found. Please install rsync."
        except Exception as e:
            return False, f"rsync error: {e}"

    def sync_from_remote(self) -> tuple[bool, str]:
        """Sync results/checkpoints from remote back to local.

        Pulls: results/, checkpoints/, logs/ from remote experiments directory.

        Returns:
            (ok, message)
        """
        if self.mode == "local":
            return True, "Local mode — no sync needed."

        if not self.auto_sync:
            return True, "auto_sync is disabled — skipping sync."

        print(f"[RemoteExecutor] Pulling results from {self.remote_experiments_dir}...")

        remote_source = f"{self.user}@{self.host}:{self.remote_experiments_dir}/"
        # Pull only results/checkpoints/logs — not code
        pull_dirs = ["results", "checkpoints", "logs"]
        all_ok = True
        messages = []

        for subdir in pull_dirs:
            try:
                result = subprocess.run(
                    self._rsync_cmd(
                        f"{remote_source}{subdir}/",
                        f"{self.local_experiments_dir}/{subdir}/",
                    ),
                    capture_output=True, text=True, timeout=300,
                )
                if result.returncode == 0:
                    messages.append(f"Pulled {subdir}/ successfully.")
                else:
                    all_ok = False
                    # Not having checkpoints or logs is not always an error
                    if "No such file" in result.stderr:
                        messages.append(f"No {subdir}/ to pull (not yet created on remote).")
                    else:
                        messages.append(f"Failed to pull {subdir}/: {result.stderr.strip()}")
            except Exception as e:
                all_ok = False
                messages.append(f"Error pulling {subdir}/: {e}")

        return all_ok, "; ".join(messages)

    def run_remote(self, command: str, cwd: Optional[str] = None,
                   timeout: Optional[int] = None,
                   env_vars: Optional[dict] = None) -> subprocess.CompletedProcess:
        """Execute a command on the remote machine via SSH.

        Args:
            command: Shell command to run.
            cwd: Working directory on remote (defaults to remote_experiments_dir).
            timeout: Timeout in seconds.
            env_vars: Extra environment variables to set before the command.

        Returns:
            subprocess.CompletedProcess with stdout/stderr.
        """
        if self.mode == "local":
            cmd_list = ["bash", "-c", command]
            return subprocess.run(cmd_list, capture_output=True, text=True,
                                  timeout=timeout, cwd=str(self.local_experiments_dir))

        work_dir = cwd or self.remote_experiments_dir

        # Build the full remote command with conda activation and env vars
        parts = []
        # Apply setup commands first
        for sc in self.setup_commands:
            parts.append(sc)

        # Activate the project conda environment (overrides any setup_commands conda activate)
        parts.append(f"conda activate {self.env_name}")

        # Set GPU visibility if needed
        if self.remote_gpus:
            parts.append(f"export CUDA_VISIBLE_DEVICES={self.remote_gpus}")

        # Extra env vars
        if env_vars:
            for k, v in env_vars.items():
                parts.append(f"export {k}={v}")

        # Change to working directory
        parts.append(f"cd {work_dir}")

        # The actual command
        parts.append(command)

        remote_cmd = " && ".join(parts)

        print(f"[RemoteExecutor] Running on {self.host}: {command}")
        try:
            return subprocess.run(
                self._ssh_cmd(remote_cmd),
                capture_output=True, text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            return subprocess.CompletedProcess(
                args=e.cmd, returncode=-1,
                stdout=e.stdout or "", stderr=e.stderr or f"Command timed out after {timeout}s.",
            )

    def run_local(self, command: str, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute a command locally."""
        return subprocess.run(
            ["bash", "-c", command],
            capture_output=True, text=True,
            timeout=timeout,
            cwd=str(self.local_experiments_dir),
        )

    # ── Setup helpers ──────────────────────────────────────────────────────

    def _check_remote_conda(self) -> tuple[bool, str]:
        """Check if conda/mamba is available on the remote machine."""
        for mgr in ["conda", "mamba", "micromamba"]:
            result = subprocess.run(
                self._ssh_cmd(f"{mgr} --version 2>/dev/null"),
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                self._conda_bin = mgr
                return True, f"{mgr} found on remote."
        return False, (
            "Neither conda, mamba, nor micromamba found on remote machine. "
            "Please install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
        )

    def _create_remote_dirs(self) -> tuple[bool, str]:
        """Create the remote directory structure."""
        parent_dir = os.path.dirname(self.remote_experiments_dir)
        result = subprocess.run(
            self._ssh_cmd(f"mkdir -p {self.remote_experiments_dir}/{{results,checkpoints,logs,configs,src,baselines}}"),
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return True, f"Remote directories created at {self.remote_experiments_dir}"
        return False, f"Failed to create remote directories: {result.stderr.strip()}"

    def _setup_conda_env(self) -> tuple[bool, str]:
        """Create project-specific conda environment with Python + PyTorch if not exists.

        Reads requirements.txt from the synced experiments/ directory to install deps.
        """
        # Check if env already exists
        result = subprocess.run(
            self._ssh_cmd(f"{self._conda_bin} env list | grep '{self.env_name}' || true"),
            capture_output=True, text=True, timeout=10,
        )
        if self.env_name in result.stdout:
            print(f"[RemoteExecutor] Conda env '{self.env_name}' already exists.")
            return True, f"Conda env '{self.env_name}' already exists."

        print(f"[RemoteExecutor] Creating conda env '{self.env_name}' with Python 3.10...")
        # Read python version from local env if available, default to 3.10
        python_version = "3.10"
        local_python = os.popen("python3 --version 2>/dev/null").read().strip()
        if local_python:
            # e.g., "Python 3.9.18" → "3.9"
            parts = local_python.split()
            if len(parts) >= 2:
                python_version = ".".join(parts[1].split(".")[:2])

        create_cmd = (
            f"{self._conda_bin} create -n {self.env_name} "
            f"python={python_version} pytorch pytorch-cuda -c pytorch -c nvidia -y -q"
        )
        result = subprocess.run(
            self._ssh_cmd(create_cmd),
            capture_output=True, text=True, timeout=600,  # 10 min for conda create
        )
        if result.returncode != 0:
            # Fallback: try without PyTorch (user can install manually)
            print(f"[RemoteExecutor] PyTorch conda install failed, trying minimal env...")
            result = subprocess.run(
                self._ssh_cmd(
                    f"{self._conda_bin} create -n {self.env_name} python={python_version} -y -q"
                ),
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode != 0:
                return False, f"Failed to create conda env: {result.stderr.strip()}"
            return True, (
                f"Conda env '{self.env_name}' created (Python {python_version} only). "
                f"Install PyTorch manually on remote: conda activate {self.env_name} && "
                f"conda install pytorch -c pytorch"
            )

        return True, f"Conda env '{self.env_name}' created with Python {python_version} + PyTorch."

    def install_requirements(self) -> tuple[bool, str]:
        """Install packages from requirements.txt on the remote."""
        if self.mode == "local":
            return True, "Local mode — install manually."

        req_path = f"{self.remote_experiments_dir}/requirements.txt"
        # Check if requirements.txt exists on remote
        result = subprocess.run(
            self._ssh_cmd(f"test -f {req_path} && echo 'EXISTS' || echo 'MISSING'"),
            capture_output=True, text=True, timeout=10,
        )
        if "MISSING" in result.stdout:
            return True, "No requirements.txt on remote — skipping pip install."

        print(f"[RemoteExecutor] Installing requirements from {req_path}...")
        install_cmd = (
            f"conda activate {self.env_name} && "
            f"pip install -r {req_path}"
        )
        result = subprocess.run(
            self._ssh_cmd(install_cmd),
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode == 0:
            return True, "Requirements installed successfully."
        return False, f"pip install failed: {result.stderr.strip()[-500:]}"

    # ── Full lifecycle ─────────────────────────────────────────────────────

    def setup(self) -> tuple[bool, str]:
        """Complete setup: validate connection, create env, sync code, install deps.

        Returns:
            (ok, message)
        """
        # 1. Validate SSH connection
        ok, msg = self.check_ssh_connection()
        if not ok:
            return False, f"Connection check failed: {msg}"
        print(f"  [OK] {msg}")

        # 2. Setup remote environment (dirs + conda env)
        ok, msg = self.setup_remote_env()
        if not ok:
            return False, f"Remote environment setup failed: {msg}"
        print(f"  [OK] {msg}")

        # 3. Sync code to remote
        ok, msg = self.sync_to_remote()
        if not ok:
            return False, f"Code sync failed: {msg}"
        print(f"  [OK] {msg}")

        # 4. Install Python dependencies
        ok, msg = self.install_requirements()
        if not ok:
            print(f"  [WARN] {msg} (continuing anyway)")
        else:
            print(f"  [OK] {msg}")

        return True, "Remote environment ready."

    def teardown(self) -> tuple[bool, str]:
        """Pull results and clean up (does NOT delete remote files)."""
        ok, msg = self.sync_from_remote()
        return ok, f"Teardown: {msg}"


# ── Module-level convenience ──────────────────────────────────────────────

def create_executor(project_name: str, project_dir: Path) -> RemoteExecutor:
    """Create a RemoteExecutor from the project-local environment config.

    Reads {project_dir}/config/environment.yaml. Falls back to global default
    if the project-local config doesn't exist.

    Args:
        project_name: Project name (used for conda env and remote path).
        project_dir: Absolute path to the project directory.
    """
    return RemoteExecutor(project_name, project_dir)
