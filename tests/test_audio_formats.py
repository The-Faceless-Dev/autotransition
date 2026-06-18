from pathlib import Path

import pytest

from autotransition.audio.formats import source_format_label, validate_supported_source


@pytest.mark.parametrize(
    ("filename", "label"),
    [
        ("song.mp3", "MP3"),
        ("song.wav", "WAV"),
        ("song.flac", "FLAC"),
        ("song.ogg", "OGG"),
        ("song.m4a", "M4A"),
    ],
)
def test_supported_source_formats(filename: str, label: str) -> None:
    path = Path(filename)

    validate_supported_source(path)

    assert source_format_label(path) == label


def test_unsupported_source_format_lists_supported_formats() -> None:
    with pytest.raises(ValueError, match="Supported formats"):
        validate_supported_source(Path("song.aiff"))
