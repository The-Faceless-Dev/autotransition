from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from autotransition.library.schema import LibraryFile, LibraryItem, audio_mime_type_for_path, utc_now_iso

RHYTHM_GAME_MODES = ("step_arrows", "orb_beat", "laser_shoot")
RHYTHM_GAME_DIFFICULTIES = ("easy", "normal", "hard")
OFFICIAL_FACELESS_VOLUME_ID = "faceless-volume-1"
OFFICIAL_FACELESS_VOLUME_LABEL = "Faceless Volume 1"


def default_supported_game_modes() -> dict[str, bool]:
    return {
        "step_arrows": True,
        "orb_beat": False,
        "laser_shoot": True,
    }


def clean_supported_game_modes(value: Any) -> dict[str, bool]:
    raw = value if isinstance(value, dict) else {}
    step_arrows = bool(raw.get("step_arrows", True))
    orb_beat = bool(raw.get("orb_beat", False))
    return {
        "step_arrows": step_arrows,
        "orb_beat": orb_beat,
        "laser_shoot": step_arrows,
    }


def rhythm_beat_root() -> Path:
    return Path("data/rhythm-beats")


def rhythm_beat_project_root() -> Path:
    return rhythm_beat_root() / "projects"


def rhythm_volume_manifest_path() -> Path:
    return rhythm_beat_root() / "volumes.json"


def safe_project_id(project_id: str) -> str:
    safe_id = Path(project_id).name
    if not safe_id or safe_id != project_id:
        raise ValueError("Invalid rhythm beat project id.")
    return safe_id


def safe_label_stem(label: str, fallback: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in label).strip("._")
    return cleaned or fallback


def safe_volume_id(volume_id: str) -> str:
    safe_id = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in volume_id.strip().lower())
    safe_id = safe_id.strip("-")
    if not safe_id:
        raise ValueError("Invalid rhythm volume id.")
    return safe_id[:80]


def slugify_volume_label(label: str) -> str:
    return safe_volume_id(label.replace("_", "-").replace(" ", "-"))


def clean_volume(volume: dict[str, Any]) -> dict[str, Any]:
    now = utc_now_iso()
    label = str(volume.get("label") or "").strip() or "New Volume"
    volume_id = safe_volume_id(str(volume.get("volume_id") or slugify_volume_label(label) or f"volume-{uuid4().hex[:10]}"))
    return {
        "volume_id": volume_id,
        "label": label,
        "slug": str(volume.get("slug") or slugify_volume_label(label) or volume_id),
        "description": str(volume.get("description") or "").strip(),
        "official": bool(volume.get("official", False)),
        "sort_order": int(volume.get("sort_order") or 0),
        "created_at": str(volume.get("created_at") or now),
        "updated_at": str(volume.get("updated_at") or now),
    }


def default_rhythm_volume_manifest() -> dict[str, Any]:
    official = clean_volume(
        {
            "volume_id": OFFICIAL_FACELESS_VOLUME_ID,
            "label": OFFICIAL_FACELESS_VOLUME_LABEL,
            "slug": OFFICIAL_FACELESS_VOLUME_ID,
            "description": "Primary official Faceless rhythm-game volume.",
            "official": True,
            "sort_order": 0,
        }
    )
    return {"updated_at": utc_now_iso(), "volumes": [official]}


def read_volume_manifest() -> dict[str, Any]:
    path = rhythm_volume_manifest_path()
    if not path.exists():
        manifest = default_rhythm_volume_manifest()
        write_volume_manifest(manifest)
        return manifest
    payload = json.loads(path.read_text(encoding="utf-8"))
    volumes = [clean_volume(volume) for volume in payload.get("volumes") or [] if isinstance(volume, dict)]
    if not any(str(volume.get("volume_id") or "") == OFFICIAL_FACELESS_VOLUME_ID for volume in volumes):
        volumes.insert(0, default_rhythm_volume_manifest()["volumes"][0])
    return {
        "updated_at": str(payload.get("updated_at") or utc_now_iso()),
        "volumes": sorted(volumes, key=lambda volume: (bool(not volume.get("official")), int(volume.get("sort_order") or 0), str(volume.get("label") or ""))),
    }


def write_volume_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    clean = {
        "updated_at": utc_now_iso(),
        "volumes": [clean_volume(volume) for volume in manifest.get("volumes") or [] if isinstance(volume, dict)],
    }
    path = rhythm_volume_manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    return clean


def list_volumes() -> list[dict[str, Any]]:
    return list(read_volume_manifest().get("volumes") or [])


def upsert_volume(volume: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = read_volume_manifest()
    volumes = list(manifest.get("volumes") or [])
    clean = clean_volume(volume)
    if clean["volume_id"] == OFFICIAL_FACELESS_VOLUME_ID and not bool(volume.get("official", False)):
        raise ValueError("The official Faceless volume is reserved and cannot be changed here.")
    updated = False
    next_volumes: list[dict[str, Any]] = []
    for existing in volumes:
        if str(existing.get("volume_id") or "") == clean["volume_id"]:
            next_volumes.append({**existing, **clean, "updated_at": utc_now_iso()})
            updated = True
        else:
            next_volumes.append(existing)
    if not updated:
        next_volumes.append(clean)
    return list(write_volume_manifest({"volumes": next_volumes}).get("volumes") or [])


def remove_volume(volume_id: str) -> list[dict[str, Any]]:
    safe_id = safe_volume_id(volume_id)
    if safe_id == OFFICIAL_FACELESS_VOLUME_ID:
        raise ValueError("The official Faceless volume cannot be removed.")
    manifest = read_volume_manifest()
    volumes = [volume for volume in manifest.get("volumes") or [] if str(volume.get("volume_id") or "") != safe_id]
    return list(write_volume_manifest({"volumes": volumes}).get("volumes") or [])


def project_path(project_id: str) -> Path:
    return rhythm_beat_project_root() / safe_project_id(project_id) / "project.json"


def project_dir(project_id: str) -> Path:
    return project_path(project_id).parent


def chart_export_path(project_id: str) -> Path:
    return project_dir(project_id) / "chart.json"


def source_audio_dir(project_id: str) -> Path:
    return project_dir(project_id) / "source"


def _sort_by_time(rows: list[dict[str, Any]], time_key: str = "timeSeconds") -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: float(row.get(time_key) or 0))


def create_project(label: str) -> dict[str, Any]:
    now = utc_now_iso()
    project_id = f"rhythm-{uuid4().hex[:12]}"
    clean_label = label.strip() or "New rhythm beat project"
    return clean_project(
        {
            "project_id": project_id,
            "label": clean_label,
            "created_at": now,
            "updated_at": now,
            "source": {},
            "lyrics": {
                "enabled": False,
                "source": "edited",
                "provider": "",
                "model": "",
                "language": None,
                "language_probability": None,
                "text": "",
                "segments": [],
                "updated_at_iso": now,
            },
            "tracks": [],
            "analyses": [],
            "selections": [],
            "merges": [],
            "final_result_id": None,
            "game_asset": {
                "game_enabled": False,
                "volume_id": "",
                "volume_label": "",
                "volume_slug": "",
                "official_volume": False,
                "sort_order": 0,
                "supported_game_modes": default_supported_game_modes(),
            },
        }
    )


def clean_project(project: dict[str, Any]) -> dict[str, Any]:
    now = utc_now_iso()
    project_id = safe_project_id(str(project.get("project_id") or f"rhythm-{uuid4().hex[:12]}"))
    source = project.get("source") if isinstance(project.get("source"), dict) else {}
    lyrics = project.get("lyrics") if isinstance(project.get("lyrics"), dict) else {}

    tracks: list[dict[str, Any]] = []
    for index, raw in enumerate(project.get("tracks") or []):
        if not isinstance(raw, dict):
            continue
        tracks.append(
            {
                "track_id": str(raw.get("track_id") or f"track-{index + 1}"),
                "label": str(raw.get("label") or raw.get("track_name") or f"Track {index + 1}"),
                "audio_path": str(raw.get("audio_path") or ""),
                "audio_url": str(raw.get("audio_url") or ""),
                "duration_seconds": float(raw.get("duration_seconds") or 0),
                "source_asset_id": str(raw.get("source_asset_id") or ""),
                "source_category": str(raw.get("source_category") or ""),
                "created_at": str(raw.get("created_at") or now),
            }
        )

    analyses: list[dict[str, Any]] = []
    for index, raw in enumerate(project.get("analyses") or []):
        if not isinstance(raw, dict):
            continue
        analyses.append(
            {
                "analysis_id": str(raw.get("analysis_id") or f"analysis-{index + 1}"),
                "label": str(raw.get("label") or f"Analysis {index + 1}"),
                "source_type": str(raw.get("source_type") or "source"),
                "source_ref": str(raw.get("source_ref") or "source"),
                "source_label": str(raw.get("source_label") or raw.get("source_ref") or "Source"),
                "algorithm": str(raw.get("algorithm") or "energy_peaks_v1"),
                "settings": dict(raw.get("settings") or {}),
                "beat_points": _sort_by_time([row for row in raw.get("beat_points") or [] if isinstance(row, dict)]),
                "source_events": _sort_by_time([row for row in raw.get("source_events") or [] if isinstance(row, dict)], "startSeconds"),
                "duration_seconds": float(raw.get("duration_seconds") or 0),
                "tempo_bpm": float(raw.get("tempo_bpm") or 0),
                "created_at": str(raw.get("created_at") or now),
            }
        )

    selections: list[dict[str, Any]] = []
    for index, raw in enumerate(project.get("selections") or []):
        if not isinstance(raw, dict):
            continue
        selections.append(
            {
                "selection_id": str(raw.get("selection_id") or f"selection-{index + 1}"),
                "label": str(raw.get("label") or f"Selection {index + 1}"),
                "analysis_id": str(raw.get("analysis_id") or ""),
                "source": str(raw.get("source") or ""),
                "ranges": [
                    {
                        "start_seconds": float(row.get("start_seconds") or 0),
                        "end_seconds": float(row.get("end_seconds") or 0),
                    }
                    for row in raw.get("ranges") or []
                    if isinstance(row, dict)
                ]
                or [
                    {
                        "start_seconds": float(raw.get("range_start_seconds") or 0),
                        "end_seconds": float(raw.get("range_end_seconds") or 0),
                    }
                ],
                "range_start_seconds": float(raw.get("range_start_seconds") or 0),
                "range_end_seconds": float(raw.get("range_end_seconds") or 0),
                "game_beats": _sort_by_time([row for row in raw.get("game_beats") or [] if isinstance(row, dict)]),
                "game_notes": _sort_by_time([row for row in raw.get("game_notes") or [] if isinstance(row, dict)]),
                "game_beat_selections": [row for row in raw.get("game_beat_selections") or [] if isinstance(row, dict)],
                "game_beat_config": dict(raw.get("game_beat_config") or {}),
                "created_at": str(raw.get("created_at") or now),
            }
        )

    merges: list[dict[str, Any]] = []
    for index, raw in enumerate(project.get("merges") or []):
        if not isinstance(raw, dict):
            continue
        merges.append(
            {
                "merge_id": str(raw.get("merge_id") or f"merge-{index + 1}"),
                "label": str(raw.get("label") or f"Merge {index + 1}"),
                "selection_ids": [str(value) for value in raw.get("selection_ids") or [] if str(value).strip()],
                "game_beats": _sort_by_time([row for row in raw.get("game_beats") or [] if isinstance(row, dict)]),
                "game_notes": _sort_by_time([row for row in raw.get("game_notes") or [] if isinstance(row, dict)]),
                "game_beat_selections": [row for row in raw.get("game_beat_selections") or [] if isinstance(row, dict)],
                "game_beat_config": dict(raw.get("game_beat_config") or {}),
                "created_at": str(raw.get("created_at") or now),
            }
        )

    raw_game_asset = project.get("game_asset") if isinstance(project.get("game_asset"), dict) else {}
    game_asset = {
        "game_enabled": bool(raw_game_asset.get("game_enabled", False)),
        "volume_id": str(raw_game_asset.get("volume_id") or "").strip(),
        "volume_label": str(raw_game_asset.get("volume_label") or "").strip(),
        "volume_slug": str(raw_game_asset.get("volume_slug") or "").strip(),
        "official_volume": bool(raw_game_asset.get("official_volume", False)),
        "sort_order": int(raw_game_asset.get("sort_order") or 0),
        "supported_game_modes": clean_supported_game_modes(raw_game_asset.get("supported_game_modes")),
    }

    return {
        "project_id": project_id,
        "label": str(project.get("label") or "Rhythm beat project").strip() or "Rhythm beat project",
        "created_at": str(project.get("created_at") or now),
        "updated_at": str(project.get("updated_at") or now),
        "source": {
            "label": str(source.get("label") or ""),
            "audio_path": str(source.get("audio_path") or ""),
            "audio_url": str(source.get("audio_url") or ""),
            "duration_seconds": float(source.get("duration_seconds") or 0),
            "source_asset_id": str(source.get("source_asset_id") or ""),
            "source_category": str(source.get("source_category") or ""),
        },
        "lyrics": {
            "enabled": bool(lyrics.get("enabled", False)),
            "source": str(lyrics.get("source") or "edited"),
            "provider": str(lyrics.get("provider") or ""),
            "model": str(lyrics.get("model") or ""),
            "language": lyrics.get("language"),
            "language_probability": lyrics.get("language_probability"),
            "text": str(lyrics.get("text") or ""),
            "segments": [row for row in lyrics.get("segments") or [] if isinstance(row, dict)],
            "updated_at_iso": str(lyrics.get("updated_at_iso") or now),
        },
        "tracks": tracks,
        "analyses": analyses,
        "selections": selections,
        "merges": merges,
        "final_result_id": str(project.get("final_result_id") or "") or None,
        "game_asset": game_asset,
    }


def read_project(project_id: str) -> dict[str, Any]:
    metadata_path = project_path(project_id)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Rhythm beat project not found: {project_id}")
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    clean = clean_project(payload)
    clean["metadata_path"] = str(metadata_path)
    clean["chart_path"] = str(chart_export_path(project_id))
    return clean


def write_project(project: dict[str, Any]) -> dict[str, Any]:
    clean = clean_project(project)
    clean["updated_at"] = utc_now_iso()
    metadata_path = project_path(str(clean["project_id"]))
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    _write_chart_export(clean)
    clean["metadata_path"] = str(metadata_path)
    clean["chart_path"] = str(chart_export_path(str(clean["project_id"])))
    return clean


def list_projects() -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for metadata_path in rhythm_beat_project_root().glob("*/project.json"):
        try:
            project = read_project(metadata_path.parent.name)
        except Exception:
            continue
        projects.append(project_summary(project))
    return sorted(projects, key=lambda item: str(item.get("updated_at") or ""), reverse=True)


def project_summary(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": project.get("project_id"),
        "label": project.get("label"),
        "created_at": project.get("created_at"),
        "updated_at": project.get("updated_at"),
        "source_label": (project.get("source") or {}).get("label") or "",
        "source_duration_seconds": (project.get("source") or {}).get("duration_seconds") or 0,
        "track_count": len(project.get("tracks") or []),
        "analysis_count": len(project.get("analyses") or []),
        "selection_count": len(project.get("selections") or []),
        "merge_count": len(project.get("merges") or []),
        "final_result_id": project.get("final_result_id"),
        "has_final_asset": bool(final_merge(project)),
        "metadata_path": project.get("metadata_path") or str(project_path(str(project.get("project_id") or ""))),
        "game_asset": dict(project.get("game_asset") or {}),
    }


def final_merge(project: dict[str, Any]) -> dict[str, Any] | None:
    final_id = str(project.get("final_result_id") or "")
    if not final_id:
        return None
    for merge in project.get("merges") or []:
        if str(merge.get("merge_id") or "") == final_id:
            return merge
    return None


def _build_export_mode_difficulty_charts(
    final: dict[str, Any],
    game_asset: dict[str, Any],
    updated_at: str,
) -> dict[str, Any]:
    supported_modes = clean_supported_game_modes(game_asset.get("supported_game_modes"))
    base_chart = {
        "gameBeats": list(final.get("game_beats") or []),
        # Export source events separately, but keep playable note arrays empty here so
        # game clients derive arrows from the beat list rather than misreading segment rows.
        "gameNotes": [],
        "gameBeatSelections": list(final.get("game_beat_selections") or []),
        "gameBeatConfig": {
            **dict(final.get("game_beat_config") or {}),
            "gameMode": "step_arrows",
        },
        "gameBeatsUpdatedAtIso": updated_at,
    }
    charts: dict[str, Any] = {}
    if supported_modes.get("step_arrows", True):
        charts["step_arrows"] = {"normal": base_chart}
    if supported_modes.get("orb_beat", False):
        charts["orb_beat"] = {
            "normal": {
                **base_chart,
                "gameBeatConfig": {
                    **dict(base_chart.get("gameBeatConfig") or {}),
                    "gameMode": "orb_beat",
                },
            }
        }
    return charts


def build_chart_export(project: dict[str, Any]) -> dict[str, Any] | None:
    final = final_merge(project)
    source = project.get("source") or {}
    audio_path = str(source.get("audio_path") or "")
    if not final or not audio_path:
        return None
    path = Path(audio_path)
    if not path.exists() or not path.is_file():
        return None
    lyrics = project.get("lyrics") or {}
    game_asset = dict(project.get("game_asset") or {})
    updated_at = str(project.get("updated_at") or utc_now_iso())
    mode_difficulty_charts = _build_export_mode_difficulty_charts(final, game_asset, updated_at)
    return {
        "id": str(project.get("project_id") or ""),
        "savedAtIso": updated_at,
        "entry": {
            "id": str(project.get("project_id") or ""),
            "name": str(project.get("label") or path.stem),
            "fileName": path.name,
            "durationSeconds": float(source.get("duration_seconds") or 0),
        },
        "audio": {
            "fileName": path.name,
            "mimeType": audio_mime_type_for_path(path),
        },
        "majorBeats": list(final.get("game_beats") or []),
        "sourceEvents": list(final.get("game_notes") or []),
        "lyrics": {
            "enabled": bool(lyrics.get("enabled", False)),
            "source": str(lyrics.get("source") or "edited"),
            "provider": str(lyrics.get("provider") or ""),
            "model": str(lyrics.get("model") or ""),
            "language": lyrics.get("language"),
            "languageProbability": lyrics.get("language_probability"),
            "updatedAtIso": str(lyrics.get("updated_at_iso") or project.get("updated_at") or utc_now_iso()),
            "segments": list(lyrics.get("segments") or []),
        },
        "gameBeats": list(final.get("game_beats") or []),
        "gameNotes": [],
        "gameBeatSelections": list(final.get("game_beat_selections") or []),
        "gameBeatConfig": {
            **dict(final.get("game_beat_config") or {}),
            "gameMode": "step_arrows",
        },
        "gameBeatsUpdatedAtIso": updated_at,
        "modeDifficultyCharts": mode_difficulty_charts,
        "metadata": {
            "projectId": str(project.get("project_id") or ""),
            "projectLabel": str(project.get("label") or ""),
            "selectionCount": len(project.get("selections") or []),
            "mergeCount": len(project.get("merges") or []),
            "trackCount": len(project.get("tracks") or []),
            "finalMergeId": str(final.get("merge_id") or ""),
            "finalMergeLabel": str(final.get("label") or ""),
            "rhythmGame": {
                "game_enabled": bool(game_asset.get("game_enabled", False)),
                "volume_id": str(game_asset.get("volume_id") or ""),
                "volume_label": str(game_asset.get("volume_label") or ""),
                "volume_slug": str(game_asset.get("volume_slug") or ""),
                "official_volume": bool(game_asset.get("official_volume", False)),
                "sort_order": int(game_asset.get("sort_order") or 0),
                "supported_game_modes": clean_supported_game_modes(game_asset.get("supported_game_modes")),
            },
        },
    }


def _write_chart_export(project: dict[str, Any]) -> None:
    export = build_chart_export(project)
    export_path = chart_export_path(str(project.get("project_id") or ""))
    if export is None:
        try:
            export_path.unlink(missing_ok=True)
        except Exception:
            pass
        return
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(json.dumps(export, indent=2), encoding="utf-8")


def copy_uploaded_source_audio(project_id: str, source_path: Path) -> dict[str, Any]:
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {source_path}")
    target_dir = source_audio_dir(project_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = safe_label_stem(source_path.stem, "source")
    target_path = target_dir / f"{safe_name}{source_path.suffix.lower()}"
    if source_path.resolve() != target_path.resolve():
        shutil.copyfile(source_path, target_path)
    return {
        "label": source_path.stem,
        "audio_path": str(target_path),
        "audio_url": f"/api/audio?path={quote(str(target_path))}",
        "source_asset_id": "",
        "source_category": "",
    }


def library_item_from_rhythm_project(project: dict[str, Any]) -> LibraryItem | None:
    export = build_chart_export(project)
    if export is None:
        return None
    project_id = str(project.get("project_id") or "")
    chart_path = chart_export_path(project_id)
    source = project.get("source") or {}
    audio_path = Path(str(source.get("audio_path") or ""))
    if not chart_path.exists() or not audio_path.exists():
        return None

    files = [
        LibraryFile(
            role="chart",
            mime_type="application/json",
            size_bytes=chart_path.stat().st_size,
            path=str(chart_path),
        ),
        LibraryFile(
            role="project",
            mime_type="application/json",
            size_bytes=project_path(project_id).stat().st_size,
            path=str(project_path(project_id)),
        ),
        LibraryFile(
            role="audio",
            mime_type=audio_mime_type_for_path(audio_path),
            size_bytes=audio_path.stat().st_size,
            path=str(audio_path),
            metadata={
                "duration_seconds": source.get("duration_seconds") or 0,
                "audio_url": f"/api/audio?path={quote(str(audio_path))}",
            },
        ),
    ]

    return LibraryItem(
        id=project_id,
        visibility="local",
        status="draft",
        kind="rhythm_game",
        title=str(project.get("label") or project_id),
        files=files,
        metadata={
            "category": "rhythm_game",
            "metadata_path": str(project_path(project_id)),
            "chart_path": str(chart_path),
            "final_result_id": project.get("final_result_id") or "",
            "track_count": len(project.get("tracks") or []),
            "analysis_count": len(project.get("analyses") or []),
            "selection_count": len(project.get("selections") or []),
            "merge_count": len(project.get("merges") or []),
            "game_enabled": bool((project.get("game_asset") or {}).get("game_enabled", False)),
            "volume_id": str((project.get("game_asset") or {}).get("volume_id") or ""),
            "volume_label": str((project.get("game_asset") or {}).get("volume_label") or ""),
            "volume_slug": str((project.get("game_asset") or {}).get("volume_slug") or ""),
            "official_volume": bool((project.get("game_asset") or {}).get("official_volume", False)),
            "sort_order": int((project.get("game_asset") or {}).get("sort_order") or 0),
            "supported_game_modes": clean_supported_game_modes(
                (project.get("game_asset") or {}).get("supported_game_modes")
            ),
        },
        source_lineage={
            "source_asset_id": source.get("source_asset_id") or "",
            "source_category": source.get("source_category") or "",
        },
        created_at=str(project.get("created_at") or utc_now_iso()),
        updated_at=str(project.get("updated_at") or utc_now_iso()),
    )
