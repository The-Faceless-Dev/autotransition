"""Serializable model install state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path


class InstallState(StrEnum):
    NOT_INSTALLED = "not_installed"
    DOWNLOADING = "downloading"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True)
class ModelInstallStatus:
    slug: str
    repo_id: str
    local_path: Path
    state: InstallState
    message: str

    def to_dict(self) -> dict[str, str]:
        data = asdict(self)
        data["local_path"] = str(self.local_path)
        data["state"] = self.state.value
        return data
