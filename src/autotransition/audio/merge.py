"""Audio merge helpers for extracted tracks."""

from __future__ import annotations

from pathlib import Path

from autotransition.audio.ffmpeg import require_pydub
from autotransition.audio.formats import validate_supported_source


def merge_audio_files(source_paths: list[Path], output_path: Path, output_format: str = "flac") -> Path:
    """Overlay audio files from time zero and write the merged result."""

    AudioSegment = require_pydub("merge audio")

    if len(source_paths) < 2:
        raise ValueError("At least two audio files are required for merge.")

    loaded: list[AudioSegment] = []
    for source_path in source_paths:
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {source_path}")
        validate_supported_source(source_path)
        loaded.append(AudioSegment.from_file(source_path))

    base = loaded[0]
    merged = AudioSegment.silent(duration=max(len(item) for item in loaded), frame_rate=base.frame_rate)
    merged = merged.set_channels(base.channels).set_sample_width(base.sample_width)
    for item in loaded:
        normalized = item.set_frame_rate(base.frame_rate).set_channels(base.channels).set_sample_width(base.sample_width)
        merged = merged.overlay(normalized)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.export(output_path, format=output_format)
    return output_path
