"""Generation result objects for repaint workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path


class GenerationStatus(StrEnum):
    PREPARED = "prepared"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(frozen=True)
class GenerationResult:
    generation_id: str
    status: GenerationStatus
    message: str
    model_slug: str
    scaffold_path: Path
    scaffold_metadata_path: Path
    generated_audio_path: Path | None = None
    generated_metadata_path: Path | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        data["scaffold_path"] = str(self.scaffold_path)
        data["scaffold_metadata_path"] = str(self.scaffold_metadata_path)
        data["generated_audio_path"] = str(self.generated_audio_path) if self.generated_audio_path else None
        data["generated_metadata_path"] = str(self.generated_metadata_path) if self.generated_metadata_path else None
        return data
