"""Interfaces for future repaint-capable model integrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from autotransition.pipeline import ScaffoldPlan


@dataclass(frozen=True)
class RepaintResult:
    output_path: Path
    metadata_path: Path
    model_name: str


class RepaintModel(Protocol):
    """A model that can repaint the generated region of a scaffold."""

    def repaint(self, plan: ScaffoldPlan) -> RepaintResult:
        """Generate a continuation from a scaffold plan."""
