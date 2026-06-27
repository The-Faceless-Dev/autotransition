from pathlib import Path

from autotransition.library.schema import library_item_from_editor_asset


def test_library_item_from_editor_asset_maps_existing_creation(tmp_path: Path) -> None:
    audio = tmp_path / "music.flac"
    audio.write_bytes(b"audio")

    item = library_item_from_editor_asset(
        {
            "asset_id": "music-1",
            "category": "generation",
            "label": "Cinematic test",
            "audio_path": str(audio),
            "duration_seconds": 30,
            "created_at": "2026-06-27T12:00:00+00:00",
            "metadata_path": "data/generations/music-1/generation.json",
        }
    )

    assert item is not None
    assert item.id == "music-1"
    assert item.kind == "generation"
    assert item.visibility == "local"
    assert item.title == "Cinematic test"
    assert item.files[0].role == "audio"
    assert item.files[0].mime_type == "audio/flac"
    assert item.files[0].size_bytes == 5
    assert item.metadata["metadata_path"] == "data/generations/music-1/generation.json"


def test_library_item_from_editor_asset_skips_missing_audio(tmp_path: Path) -> None:
    assert library_item_from_editor_asset({"audio_path": str(tmp_path / "missing.wav")}) is None
