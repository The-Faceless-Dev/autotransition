"""Shared pydub segment helpers."""

from __future__ import annotations


def matching_silence(reference, duration_ms: int):
    """Return silence with the same audio layout as ``reference``."""

    from pydub import AudioSegment

    return (
        AudioSegment.silent(duration=duration_ms, frame_rate=reference.frame_rate)
        .set_channels(reference.channels)
        .set_sample_width(reference.sample_width)
    )
