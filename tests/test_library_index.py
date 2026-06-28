from pathlib import Path

from autotransition.library.index import LocalLibraryIndex


def _asset(tmp_path: Path, asset_id: str = "music-1", label: str = "Original") -> dict[str, object]:
    audio = tmp_path / f"{asset_id}.wav"
    audio.write_bytes(b"audio")
    return {
        "asset_id": asset_id,
        "category": "generation",
        "label": label,
        "audio_path": str(audio),
        "duration_seconds": 12,
        "created_at": "2026-06-27T12:00:00+00:00",
    }


def test_reindex_writes_index_and_manifest(tmp_path: Path) -> None:
    library = LocalLibraryIndex(tmp_path / "library")

    items = library.reindex_from_editor_assets([_asset(tmp_path)])

    assert len(items) == 1
    assert items[0].id == "music-1"
    assert (tmp_path / "library" / "index.json").exists()
    assert (tmp_path / "library" / "items" / "music-1" / "manifest.json").exists()


def test_reindex_preserves_user_edits(tmp_path: Path) -> None:
    library = LocalLibraryIndex(tmp_path / "library")
    library.reindex_from_editor_assets([_asset(tmp_path, label="Scanned")])

    updated = library.update_item("music-1", {"title": "Custom title", "tags": ["public", "test"]})
    assert updated.title == "Custom title"

    items = library.reindex_from_editor_assets([_asset(tmp_path, label="Scanned again")])

    assert items[0].title == "Custom title"
    assert items[0].tags == ["public", "test"]
