"""Audio format policy for source inputs and scaffold outputs."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_INPUT_FORMATS: dict[str, str] = {
    ".mp3": "MP3",
    ".wav": "WAV",
    ".flac": "FLAC",
    ".ogg": "OGG",
    ".m4a": "M4A",
}

DEFAULT_SCAFFOLD_FORMAT = "wav"


def source_extension(path: Path) -> str:
    return path.suffix.lower()


def source_format_label(path: Path) -> str:
    extension = source_extension(path)
    return SUPPORTED_INPUT_FORMATS.get(extension, extension.lstrip(".").upper() or "Unknown")


def validate_supported_source(path: Path) -> None:
    extension = source_extension(path)
    if extension not in SUPPORTED_INPUT_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_INPUT_FORMATS))
        raise ValueError(f"Unsupported audio format '{extension or 'none'}'. Supported formats: {supported}")
