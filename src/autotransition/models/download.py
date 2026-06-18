"""Model download and install helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from autotransition.models.registry import ModelProfile, get_model_profile
from autotransition.models.status import InstallState, ModelInstallStatus

SnapshotDownload = Callable[..., str]


class ModelInstallError(RuntimeError):
    """Raised when a model cannot be installed."""


def local_model_path(profile: ModelProfile, models_dir: Path) -> Path:
    return models_dir / profile.local_dir_name


def resolve_model_status(slug: str, models_dir: Path = Path("models")) -> ModelInstallStatus:
    profile = get_model_profile(slug)
    local_path = local_model_path(profile, models_dir)
    if local_path.exists() and any(local_path.iterdir()):
        state = InstallState.READY
        message = "Model is installed."
    else:
        state = InstallState.NOT_INSTALLED
        message = "Model is not installed."

    return ModelInstallStatus(
        slug=profile.slug,
        repo_id=profile.repo_id,
        local_path=local_path,
        state=state,
        message=message,
    )


def install_model(
    slug: str,
    models_dir: Path = Path("models"),
    *,
    snapshot_download: SnapshotDownload | None = None,
) -> ModelInstallStatus:
    """Download a registered model profile from Hugging Face."""

    profile = get_model_profile(slug)
    if not profile.supports_repaint:
        raise ModelInstallError(f"Model '{slug}' is not marked as repaint-capable.")

    local_path = local_model_path(profile, models_dir)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    downloader = snapshot_download
    if downloader is None:
        try:
            from huggingface_hub import snapshot_download as hf_snapshot_download
        except ImportError as exc:
            raise ModelInstallError("huggingface_hub is required to install models.") from exc
        downloader = hf_snapshot_download

    try:
        downloaded_path = Path(
            downloader(
                repo_id=profile.repo_id,
                local_dir=local_path,
                local_dir_use_symlinks=False,
                resume_download=True,
            )
        )
    except Exception as exc:
        raise ModelInstallError(f"Failed to download '{profile.display_name}' from {profile.repo_id}: {exc}") from exc

    return ModelInstallStatus(
        slug=profile.slug,
        repo_id=profile.repo_id,
        local_path=downloaded_path,
        state=InstallState.READY,
        message="Model installed.",
    )
