from pathlib import Path

from autotransition.audio.merge import merge_audio_files


def make_tone(path: Path, frequency: int, duration_ms: int = 500) -> Path:
    from pydub.generators import Sine

    Sine(frequency).to_audio_segment(duration=duration_ms).export(path, format="wav")
    return path


def test_merge_audio_files_overlays_sources(tmp_path: Path) -> None:
    first = make_tone(tmp_path / "first.wav", 220)
    second = make_tone(tmp_path / "second.wav", 440)
    output = tmp_path / "merged.flac"

    result = merge_audio_files([first, second], output, "flac")

    assert result == output
    assert output.exists()
    assert output.stat().st_size > 0


def test_merge_audio_files_requires_two_sources(tmp_path: Path) -> None:
    first = make_tone(tmp_path / "first.wav", 220)

    try:
        merge_audio_files([first], tmp_path / "merged.flac", "flac")
    except ValueError as exc:
        assert "At least two" in str(exc)
    else:
        raise AssertionError("Expected merge to require at least two sources")
