"""Interfaces for ranking generated transition candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CandidateScore:
    candidate_path: Path
    score: float
    notes: list[str]


class CandidateScorer(Protocol):
    def score(self, candidate_path: Path) -> CandidateScore:
        """Return a normalized candidate score and human-readable notes."""
