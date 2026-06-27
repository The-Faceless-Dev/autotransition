"""Side-Step runtime setup helpers."""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from autotransition.config import RuntimeConfig
from autotransition.runtime.ace_step import build_runtime_env, build_uv_install_command, resolve_uv_executable


SIDESTEP_REPO_URL = "https://github.com/koda-dernet/Side-Step.git"


@dataclass(frozen=True)
class SideStepRuntimeStatus:
    install_dir: Path
    installed: bool
    uv_available: bool
    command: str
    message: str

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["install_dir"] = str(self.install_dir)
        return data


def build_side_step_install_commands(config: RuntimeConfig = RuntimeConfig()) -> list[str]:
    return [
        build_uv_install_command(),
        f"git clone {SIDESTEP_REPO_URL} {config.side_step_dir}",
        f"cd {config.side_step_dir}",
        "uv sync",
    ]


def build_side_step_command(config: RuntimeConfig = RuntimeConfig()) -> str:
    return "uv run sidestep"


def side_step_status(config: RuntimeConfig = RuntimeConfig()) -> SideStepRuntimeStatus:
    installed = config.side_step_dir.exists() and (config.side_step_dir / "pyproject.toml").exists()
    uv_available = resolve_uv_executable() is not None
    if installed and uv_available:
        message = "Side-Step runtime is installed."
    elif installed:
        message = "Side-Step runtime is installed, but uv was not found."
    else:
        message = f"Side-Step runtime is not installed at {config.side_step_dir}."
    return SideStepRuntimeStatus(
        install_dir=config.side_step_dir,
        installed=installed,
        uv_available=uv_available,
        command=build_side_step_command(config),
        message=message,
    )


def run_side_step_install(config: RuntimeConfig = RuntimeConfig()) -> None:
    uv = resolve_uv_executable()
    if uv is None:
        subprocess.run(build_side_step_install_commands(config)[0], shell=True, check=True)
        uv = resolve_uv_executable()
        if uv is None:
            raise RuntimeError("uv was installed, but uv could not be found. Restart the shell and rerun setup.")

    if config.side_step_dir.exists():
        if not (config.side_step_dir / "pyproject.toml").exists():
            raise RuntimeError(f"Side-Step runtime directory exists but does not look complete: {config.side_step_dir}")
    else:
        subprocess.run(build_side_step_install_commands(config)[1], shell=True, check=True)

    env = build_runtime_env()
    Path(env["UV_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
    subprocess.run([str(uv), "sync", "--link-mode", "copy"], cwd=config.side_step_dir, env=env, check=True)
