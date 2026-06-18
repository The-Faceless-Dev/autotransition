"""Summarize ACE-Step runtime activity for the local UI."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
PROGRESS_RE = re.compile(
    r"(?P<file>[\w.-]+):\s+"
    r"(?P<percent>\d{1,3})%.*?\|\s*"
    r"(?P<done>[\d.]+[KMGTP]?)/(?P<total>[\d.]+[KMGTP]?)",
    re.IGNORECASE,
)
BRACKET_PROGRESS_RE = re.compile(
    r"Downloading \[(?P<file>[^\]]+)\]:\s+"
    r"(?P<percent>\d{1,3})%.*?\|\s*"
    r"(?P<done>[\d.]+[KMGTP]?)/(?P<total>[\d.]+[KMGTP]?)",
    re.IGNORECASE,
)
STEP_PROGRESS_RE = re.compile(
    r"(?P<percent>\d{1,3})%\|.*?\|\s*(?P<done>\d+)/(?P<total>\d+)\s*\[.*?(?:steps/s|s/steps)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RuntimeActivity:
    phase: str
    message: str
    detail: str | None
    latest_lines: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def summarize_runtime_activity(log_dir: Path = Path("data/logs")) -> RuntimeActivity:
    lines = _read_runtime_lines(log_dir)
    return summarize_lines(lines)


def summarize_lines(lines: list[str]) -> RuntimeActivity:
    clean_lines = [_clean_line(line) for line in lines]
    clean_lines = [line for line in clean_lines if line]
    latest = clean_lines[-12:]

    for line in reversed(clean_lines):
        step_progress = _parse_step_progress(line)
        if step_progress:
            percent, done, total = step_progress
            return RuntimeActivity(
                phase="generating",
                message=f"Generating audio: step {done}/{total} ({percent}%)",
                detail=None,
                latest_lines=latest,
            )
        lowered = line.lower()
        if (
            "generating audio" in lowered
            or "starting generation" in lowered
            or "decoding latents" in lowered
            or "vae decode" in lowered
        ):
            return RuntimeActivity(phase="generating", message=line, detail=None, latest_lines=latest)

    for line in reversed(clean_lines):
        progress = _parse_progress(line)
        if progress:
            filename, percent, done, total = progress
            return RuntimeActivity(
                phase="downloading",
                message=f"Downloading ACE-Step asset: {done}/{total} ({percent}%)",
                detail=filename,
                latest_lines=latest,
            )

    for line in reversed(clean_lines):
        lowered = line.lower()
        if "traceback" in lowered or "failed" in lowered or "error" in lowered:
            return RuntimeActivity(phase="error", message=line, detail=None, latest_lines=latest)
        if "starting automatic download" in lowered or "[model download] downloading" in lowered:
            return RuntimeActivity(phase="downloading", message=line, detail=None, latest_lines=latest)
        if "models will be lazy-loaded" in lowered or "initializing" in lowered or "/v1/init" in lowered:
            return RuntimeActivity(phase="initializing", message=line, detail=None, latest_lines=latest)
        if "release_task" in lowered or "query_result" in lowered:
            return RuntimeActivity(phase="generating", message="ACE-Step generation request is active.", detail=line, latest_lines=latest)
        if "server is ready" in lowered:
            return RuntimeActivity(phase="ready", message="ACE-Step API is ready.", detail=line, latest_lines=latest)

    return RuntimeActivity(
        phase="idle",
        message="No ACE-Step activity yet.",
        detail=None,
        latest_lines=latest,
    )


def _read_runtime_lines(log_dir: Path) -> list[str]:
    lines: list[str] = []
    for filename in ("ace-step-api.log", "ace-step-api.err.log"):
        path = log_dir / filename
        if not path.exists():
            continue
        lines.extend(_read_tail(path).splitlines())
    return lines


def _read_tail(path: Path, max_bytes: int = 96_000) -> str:
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - max_bytes))
        data = handle.read()
    return data.decode("utf-8", errors="replace").replace("\r", "\n")


def _clean_line(line: str) -> str:
    return ANSI_RE.sub("", line).strip()


def _parse_progress(line: str) -> tuple[str, str, str, str] | None:
    match = PROGRESS_RE.search(line) or BRACKET_PROGRESS_RE.search(line)
    if not match:
        return None
    return (
        match.group("file"),
        match.group("percent"),
        match.group("done"),
        match.group("total"),
    )


def _parse_step_progress(line: str) -> tuple[str, str, str] | None:
    match = STEP_PROGRESS_RE.search(line)
    if not match:
        return None
    return match.group("percent"), match.group("done"), match.group("total")
