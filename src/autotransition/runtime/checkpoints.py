"""Checkpoint validation helpers for external ACE-Step runtime folders."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from autotransition.config import RuntimeConfig
from autotransition.models.registry import ModelProfile


WEIGHT_FILENAMES = (
    "model.safetensors",
    "pytorch_model.bin",
    "model.ckpt",
    "tf_model.h5",
    "flax_model.msgpack",
)
WEIGHT_PATTERNS = (
    "*.safetensors",
    "*.bin",
    "*.ckpt",
)
WEIGHT_INDEX_FILENAMES = (
    "model.safetensors.index.json",
    "pytorch_model.bin.index.json",
)


@dataclass(frozen=True)
class CheckpointRepairResult:
    model_slug: str
    checkpoint_path: Path
    repaired: bool
    quarantine_path: Path | None
    message: str


def checkpoint_has_weights(path: Path) -> bool:
    if not path.is_dir():
        return False
    if any((path / filename).exists() for filename in WEIGHT_FILENAMES + WEIGHT_INDEX_FILENAMES):
        return True
    return any(file.is_file() for pattern in WEIGHT_PATTERNS for file in path.glob(pattern))


def checkpoint_missing_weights_message(path: Path) -> str:
    expected = ", ".join((*WEIGHT_FILENAMES, *WEIGHT_INDEX_FILENAMES, *WEIGHT_PATTERNS))
    found = ", ".join(sorted(file.name for file in path.iterdir() if file.is_file())[:12])
    if not found:
        found = "no top-level files"
    return f"No top-level checkpoint weights found in {path}. Expected one of: {expected}. Found: {found}."


def repair_incomplete_checkpoint(
    profile: ModelProfile,
    config: RuntimeConfig = RuntimeConfig(),
    quarantine_root: Path = Path("data/runtime/broken-checkpoints"),
) -> CheckpointRepairResult:
    checkpoint_path = config.ace_step_dir / "checkpoints" / profile.local_dir_name
    if not checkpoint_path.exists():
        return CheckpointRepairResult(
            model_slug=profile.slug,
            checkpoint_path=checkpoint_path,
            repaired=False,
            quarantine_path=None,
            message=f"Checkpoint folder does not exist yet: {checkpoint_path}",
        )
    if checkpoint_has_weights(checkpoint_path):
        return CheckpointRepairResult(
            model_slug=profile.slug,
            checkpoint_path=checkpoint_path,
            repaired=False,
            quarantine_path=None,
            message=f"Checkpoint folder is complete: {checkpoint_path}",
        )
    if not checkpoint_path.is_dir():
        return CheckpointRepairResult(
            model_slug=profile.slug,
            checkpoint_path=checkpoint_path,
            repaired=False,
            quarantine_path=None,
            message=f"Checkpoint path is not a directory: {checkpoint_path}",
        )

    quarantine_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    quarantine_path = quarantine_root / f"{profile.local_dir_name}-{stamp}"
    counter = 1
    while quarantine_path.exists():
        quarantine_path = quarantine_root / f"{profile.local_dir_name}-{stamp}-{counter}"
        counter += 1

    shutil.move(str(checkpoint_path), str(quarantine_path))
    return CheckpointRepairResult(
        model_slug=profile.slug,
        checkpoint_path=checkpoint_path,
        repaired=True,
        quarantine_path=quarantine_path,
        message=f"{checkpoint_missing_weights_message(quarantine_path)} Incomplete checkpoint moved to {quarantine_path}.",
    )
