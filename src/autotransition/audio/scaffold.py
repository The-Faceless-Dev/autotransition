"""Audio scaffold creation for repaint/outpainting workflows."""

from __future__ import annotations

from pathlib import Path

from autotransition.audio.formats import validate_supported_source


def build_repaint_scaffold(
    source_path: Path,
    output_path: Path,
    tail_seconds: float,
    blank_seconds: float,
    output_format: str = "wav",
) -> Path:
    """Write ``tail(source) + silence`` to ``output_path``."""

    try:
        from pydub import AudioSegment
    except ImportError as exc:
        raise RuntimeError("pydub is required to build audio scaffolds. Install the project dependencies.") from exc

    if tail_seconds <= 0:
        raise ValueError("tail_seconds must be greater than 0")
    if blank_seconds <= 0:
        raise ValueError("blank_seconds must be greater than 0")
    if not source_path.exists():
        raise FileNotFoundError(f"Source audio not found: {source_path}")
    validate_supported_source(source_path)

    source = AudioSegment.from_file(source_path)
    tail_ms = int(tail_seconds * 1000)
    blank_ms = int(blank_seconds * 1000)

    if len(source) < tail_ms:
        raise ValueError(
            f"Source audio is {len(source) / 1000:.2f}s, but the requested tail is {tail_seconds:.2f}s."
        )

    scaffold = source[-tail_ms:] + AudioSegment.silent(duration=blank_ms, frame_rate=source.frame_rate)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scaffold.export(output_path, format=output_format)
    return output_path
