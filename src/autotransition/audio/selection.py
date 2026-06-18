"""Build repaint scaffolds from a selected point in a longer source song."""

from __future__ import annotations

from pathlib import Path

from autotransition.audio.formats import validate_supported_source


def build_selection_scaffold(
    source_path: Path,
    output_path: Path,
    tail_start_seconds: float,
    tail_end_seconds: float,
    blank_seconds: float,
    output_format: str = "wav",
) -> Path:
    """Write ``source[tail_start:tail_end] + silence`` to ``output_path``."""

    try:
        from pydub import AudioSegment
    except ImportError as exc:
        raise RuntimeError("pydub is required to build audio scaffolds. Install the project dependencies.") from exc

    if tail_start_seconds < 0:
        raise ValueError("tail_start_seconds cannot be negative")
    if tail_end_seconds <= tail_start_seconds:
        raise ValueError("tail_end_seconds must be greater than tail_start_seconds")
    if blank_seconds <= 0:
        raise ValueError("blank_seconds must be greater than 0")
    if not source_path.exists():
        raise FileNotFoundError(f"Source audio not found: {source_path}")
    validate_supported_source(source_path)

    source = AudioSegment.from_file(source_path)
    duration_seconds = len(source) / 1000
    if tail_end_seconds > duration_seconds:
        raise ValueError(
            f"Selection ends at {tail_end_seconds:.2f}s, but source is only {duration_seconds:.2f}s."
        )

    start_ms = int(tail_start_seconds * 1000)
    end_ms = int(tail_end_seconds * 1000)
    blank_ms = int(blank_seconds * 1000)
    selected_tail = source[start_ms:end_ms]
    scaffold = selected_tail + AudioSegment.silent(duration=blank_ms, frame_rate=source.frame_rate)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    scaffold.export(output_path, format=output_format)
    return output_path
