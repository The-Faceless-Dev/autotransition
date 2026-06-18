"""Transition planning primitives."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

from autotransition.config import TransitionConfig


@dataclass(frozen=True)
class TransitionRequest:
    """User-facing request for a transition scaffold."""

    source_path: Path
    caption: str
    config: TransitionConfig
    transition_id: str | None = None


@dataclass(frozen=True)
class ScaffoldPlan:
    """Serializable plan that can feed a CLI, API, or UI."""

    transition_id: str
    source_path: Path
    source_extension: str
    source_format: str
    scaffold_path: Path
    metadata_path: Path
    caption: str
    context_seconds: float
    repaint_overlap_seconds: float
    new_section_seconds: float
    repainting_start_seconds: float
    repainting_end_seconds: float
    audio_format: str
    bpm_hint: float | None
    key_hint: str | None
    seed: int | None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["source_path"] = str(self.source_path)
        data["scaffold_path"] = str(self.scaffold_path)
        data["metadata_path"] = str(self.metadata_path)
        return data


def create_scaffold_plan(request: TransitionRequest) -> ScaffoldPlan:
    from autotransition.audio.formats import source_extension, source_format_label

    config = request.config
    transition_id = request.transition_id or f"transition-{uuid4().hex[:12]}"
    output_dir = config.output.scaffold_dir / transition_id
    scaffold_path = output_dir / f"scaffold.{config.output.audio_format}"
    metadata_path = output_dir / "metadata.json"

    return ScaffoldPlan(
        transition_id=transition_id,
        source_path=request.source_path,
        source_extension=source_extension(request.source_path),
        source_format=source_format_label(request.source_path),
        scaffold_path=scaffold_path,
        metadata_path=metadata_path,
        caption=request.caption,
        context_seconds=config.context_seconds,
        repaint_overlap_seconds=config.repaint_overlap_seconds,
        new_section_seconds=config.new_section_seconds,
        repainting_start_seconds=config.repainting_start_seconds,
        repainting_end_seconds=-1.0,
        audio_format=config.output.audio_format,
        bpm_hint=config.bpm_hint,
        key_hint=config.key_hint,
        seed=config.seed,
    )
