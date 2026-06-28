import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from autotransition.config import RuntimeConfig
from autotransition.ui import create_app


def make_wav(path: Path, duration_ms: int = 3000) -> Path:
    from pydub import AudioSegment

    AudioSegment.silent(duration=duration_ms, frame_rate=44100).export(path, format="wav")
    return path


def test_ui_status_endpoint_reports_environment(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["models_dir"] == str(tmp_path)
    assert data["repaint_model_count"] >= 1
    assert ".mp3" in data["supported_input_formats"]
    assert data["default_scaffold_format"] == "wav"
    assert "python_version" in data


def test_ui_presets_endpoint_returns_creator_presets(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.get("/api/presets")

    assert response.status_code == 200
    slugs = {preset["slug"] for preset in response.json()}
    assert "smooth-continuation" in slugs
    assert "dj-bridge" in slugs


def test_ui_models_endpoint_includes_install_status(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.get("/api/models")

    assert response.status_code == 200
    models = response.json()
    assert any(model["slug"] == "acestep-v15-turbo" for model in models)
    assert all("status" in model for model in models)


def test_ui_index_includes_audio_editor_tab(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "Dance Station" in response.text
    assert "Instrument Lab" in response.text
    assert "LoKr Training" in response.text
    assert "Audio Editor" in response.text
    assert "Local Library" in response.text
    assert "Dance Station Assets" in response.text
    assert "Save Edited Result" in response.text
    assert 'src="/audiomass/"' in response.text


def test_ui_local_library_reindexes_existing_creations(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    audio = make_wav(tmp_path / "music.wav", duration_ms=1000)
    generation_dir = tmp_path / "data" / "generations" / "music-1"
    generation_dir.mkdir(parents=True)
    (generation_dir / "generation.json").write_text(
        json.dumps(
            {
                "generation_id": "music-1",
                "label": "Library test",
                "generated_audio_path": str(audio),
                "created_at": "2026-06-27T12:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.post("/api/library/local/reindex")
    update = client.patch("/api/library/local/music-1", json={"title": "Renamed library item", "tags": ["test"]})
    listed = client.get("/api/library/local")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert update.status_code == 200
    assert listed.status_code == 200
    item = listed.json()["items"][0]
    assert item["id"] == "music-1"
    assert item["kind"] == "generation"
    assert item["title"] == "Renamed library item"
    assert item["tags"] == ["test"]
    assert Path(tmp_path / "data" / "library" / "items" / "music-1" / "manifest.json").exists()


def test_ui_local_library_reindexes_lokr_datasets(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    dataset_dir = tmp_path / "data" / "lokr-training" / "datasets" / "lokr-data-1"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "dataset.json").write_text(
        json.dumps(
            {
                "metadata": {
                    "dataset_id": "lokr-data-1",
                    "label": "Artist dataset",
                    "custom_tag": "artist_token",
                    "default_genre": "funk pop",
                    "default_language": "en",
                    "all_instrumental": False,
                    "created_at": "2026-06-27T12:00:00+00:00",
                    "updated_at": "2026-06-27T12:05:00+00:00",
                },
                "samples": [],
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.post("/api/library/local/reindex")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["id"] == "lokr-data-1"
    assert item["kind"] == "dataset"
    assert item["title"] == "Artist dataset"
    assert item["files"][0]["role"] == "dataset_manifest"
    assert item["metadata"]["custom_tag"] == "artist_token"
    assert Path(tmp_path / "data" / "library" / "items" / "lokr-data-1" / "manifest.json").exists()


def test_ui_local_library_reindexes_lokr_adapters(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "data" / "lokr-training" / "runs" / "train-a"
    weights = run_dir / "adapter" / "best" / "lokr_weights.safetensors"
    weights.parent.mkdir(parents=True)
    weights.write_bytes(b"weights")
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": "train-a",
                "type": "train",
                "status": "complete",
                "adapter_type": "lokr",
                "label": "Artist LoKr",
                "dataset_id": "lokr-data-1",
                "model": "turbo",
                "epochs": 12,
                "output_dir": str(run_dir / "adapter"),
                "created_at": "2026-06-27T12:00:00+00:00",
                "completed_at": "2026-06-27T12:30:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.post("/api/library/local/reindex")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["id"] == "train-a"
    assert item["kind"] == "lokr"
    assert item["title"] == "Artist LoKr"
    assert item["files"][0]["role"] == "adapter_weights"
    assert item["metadata"]["dataset_id"] == "lokr-data-1"
    assert item["source_lineage"]["dataset_id"] == "lokr-data-1"


def test_ui_serves_instrument_bank_manifest(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.get("/static/instruments/bank.json")
    sample_response = client.get("/static/instruments/samples/basic-piano/c4.wav")

    assert response.status_code == 200
    body = response.json()
    categories = {item["category"] for item in body["instruments"]}
    assert "Synths" in categories
    assert "Bass" in categories
    assert "Keys" in categories
    assert any(item["type"] == "sample" and item["id"] == "keys.basic-piano" for item in body["instruments"])
    assert sample_response.status_code == 200
    assert sample_response.content.startswith(b"RIFF")


def test_ui_imports_sfz_instrument(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    sample = make_wav(tmp_path / "c4.wav", duration_ms=250)
    sfz = tmp_path / "basic.sfz"
    sfz.write_text("<region> sample=c4.wav key=60 lokey=48 hikey=72 pitch_keycenter=60", encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path))

    with sfz.open("rb") as sfz_file, sample.open("rb") as sample_file:
        response = client.post(
            "/api/instrument-lab/instruments/sfz",
            data={"label": "Imported Piano"},
            files=[
                ("sfz_file", ("basic.sfz", sfz_file, "text/plain")),
                ("sample_files", ("c4.wav", sample_file, "audio/wav")),
            ],
        )
    instruments = client.get("/api/instrument-lab/instruments")

    assert response.status_code == 200
    instrument = response.json()["instrument"]
    assert instrument["name"] == "Imported Piano"
    assert instrument["source"] == "sfz"
    assert instrument["samples"][0]["root"] == 60
    assert instruments.status_code == 200
    assert any(item["id"] == instrument["id"] for item in instruments.json())


def test_ui_imports_sfz_with_quoted_sample_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    sample = make_wav(tmp_path / "c 4.wav", duration_ms=250)
    sfz = tmp_path / "quoted.sfz"
    sfz.write_text('<region> sample="samples/c 4.wav" key=C4', encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path))

    with sfz.open("rb") as sfz_file, sample.open("rb") as sample_file:
        response = client.post(
            "/api/instrument-lab/instruments/sfz",
            data={"label": "Quoted Piano"},
            files=[
                ("sfz_file", ("quoted.sfz", sfz_file, "text/plain")),
                ("sample_files", ("c 4.wav", sample_file, "audio/wav")),
            ],
        )

    assert response.status_code == 200
    instrument = response.json()["instrument"]
    assert instrument["samples"][0]["root"] == 60


def test_ui_sfz_import_reports_missing_samples(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    sfz = tmp_path / "missing.sfz"
    sfz.write_text("<region> sample=missing.wav key=60", encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path))

    with sfz.open("rb") as sfz_file:
        response = client.post(
            "/api/instrument-lab/instruments/sfz",
            data={"label": "Missing"},
            files=[("sfz_file", ("missing.sfz", sfz_file, "text/plain"))],
        )
    logs = client.get("/api/logs").json()

    assert response.status_code == 400
    assert "missing.wav" in response.json()["detail"]
    assert any("SFZ import failed" in item["message"] for item in logs)


def test_audiomass_static_editor_is_served(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    index_response = client.get("/audiomass/")
    script_response = client.get("/audiomass/ui.js")
    license_response = client.get("/audiomass/LICENSE")

    assert index_response.status_code == 200
    assert "AudioMass - Audio Editor" in index_response.text
    assert script_response.status_code == 200
    assert "PKAudioEditor" in script_response.text
    assert license_response.status_code == 200
    assert "MIT License" in license_response.text


def test_ui_models_endpoint_exposes_working_xl_base_generation_defaults(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.get("/api/models")

    assert response.status_code == 200
    models = response.json()
    xl_base = next(model for model in models if model["slug"] == "acestep-v15-xl-base")
    assert xl_base["generation_defaults"]["inference_steps"] == 50
    assert xl_base["generation_defaults"]["guidance_scale"] == 7.0
    assert xl_base["generation_defaults"]["shift"] == 1.0


def test_ui_runtime_status_endpoint_returns_setup_commands(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.get("/api/runtime/status")

    assert response.status_code == 200
    data = response.json()
    assert "install_commands" in data
    assert "uv sync" in data["install_commands"]
    assert data["simple_setup_command"] == "autotransition runtime setup"
    assert data["simple_start_command"] == "autotransition runtime start"


def test_ui_runtime_status_uses_configured_runtime_port(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            models_dir=tmp_path,
            runtime_config=RuntimeConfig(ace_step_dir=tmp_path / "runtime", api_port=9101),
        )
    )

    response = client.get("/api/runtime/status")

    assert response.status_code == 200
    assert response.json()["api_url"] == "http://127.0.0.1:9101"


def test_ui_scaffold_endpoint_validates_missing_source(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))

    response = client.post(
        "/api/scaffolds",
        json={
            "source_path": str(tmp_path / "missing.wav"),
            "preset": "smooth-continuation",
        },
    )

    assert response.status_code == 400
    assert "Source audio not found" in response.json()["detail"]


def test_ui_logs_endpoint_records_validation_errors(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))
    client.post(
        "/api/scaffolds",
        json={
            "source_path": str(tmp_path / "missing.wav"),
            "preset": "smooth-continuation",
        },
    )

    response = client.get("/api/logs")

    assert response.status_code == 200
    assert any("Source audio not found" in entry["message"] for entry in response.json())


def test_ui_logs_endpoint_can_clear_session_logs(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path))
    client.post(
        "/api/scaffolds",
        json={
            "source_path": str(tmp_path / "missing.wav"),
            "preset": "smooth-continuation",
        },
    )

    assert client.get("/api/logs").json()
    response = client.delete("/api/logs")

    assert response.status_code == 200
    assert response.json() == []
    assert client.get("/api/logs").json() == []


def test_ui_source_probe_endpoint_returns_duration(tmp_path: Path) -> None:
    source = make_wav(tmp_path / "song.wav", duration_ms=3000)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post("/api/source/probe", json={"source_path": str(source)})

    assert response.status_code == 200
    data = response.json()
    assert data["path"] == str(source)
    assert data["source_extension"] == ".wav"
    assert data["source_format"] == "WAV"
    assert data["duration_seconds"] == 3.0


def test_ui_source_audio_endpoint_serves_file(tmp_path: Path) -> None:
    source = make_wav(tmp_path / "song.wav", duration_ms=1000)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.get("/api/source/audio", params={"path": str(source)})

    assert response.status_code == 200
    assert response.content


def test_ui_generated_audio_can_be_loaded_as_next_source(tmp_path: Path) -> None:
    generated = make_wav(tmp_path / "generated-transition.wav", duration_ms=2500)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    probe = client.post("/api/source/probe", json={"source_path": str(generated)})
    audio = client.get("/api/source/audio", params={"path": str(generated)})

    assert probe.status_code == 200
    assert probe.json()["duration_seconds"] == 2.5
    assert audio.status_code == 200
    assert audio.content


def test_ui_extraction_tracks_endpoint_lists_ace_tracks(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.get("/api/extractions/tracks")

    assert response.status_code == 200
    assert "vocals" in response.json()
    assert "drums" in response.json()


def test_ui_run_extraction_writes_history(tmp_path: Path, monkeypatch) -> None:
    from autotransition.models.acestep_api import AceStepApiClient
    from autotransition.models.base import RepaintResult

    monkeypatch.chdir(tmp_path)
    source = make_wav(tmp_path / "song.wav", duration_ms=3000)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    def fake_extract_track(
        self,
        source_path,
        track_name,
        save_dir,
        *,
        audio_format="flac",
        inference_steps=80,
        guidance_scale=1.0,
        shift=1.0,
        infer_method="sde",
        use_tiled_decode=True,
        dcw_enabled=False,
        velocity_norm_threshold=0.0,
        velocity_ema_factor=0.0,
        seed=None,
        instruction=None,
    ):
        assert source_path == source
        assert track_name == "vocals"
        assert audio_format == "flac"
        assert inference_steps == 80
        assert guidance_scale == 1.0
        assert shift == 1.0
        assert infer_method == "sde"
        assert use_tiled_decode is True
        assert dcw_enabled is False
        assert velocity_norm_threshold == 0.0
        assert velocity_ema_factor == 0.0
        output = save_dir / "vocals.flac"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"audio")
        metadata = save_dir / "vocals.json"
        metadata.write_text("{}", encoding="utf-8")
        return RepaintResult(output_path=output, metadata_path=metadata, model_name="ACE-Step API")

    monkeypatch.setattr(AceStepApiClient, "extract_track", fake_extract_track)

    response = client.post(
        "/api/extractions/run",
        json={
            "source_path": str(source),
            "track_name": "vocals",
            "output_format": "flac",
        },
    )
    history = client.get("/api/extractions")

    assert response.status_code == 200
    extraction = response.json()["extraction"]
    assert extraction["status"] == "complete"
    assert extraction["track_name"] == "vocals"
    assert Path(extraction["generated_audio_path"]).exists()
    assert history.status_code == 200
    assert history.json()[0]["extraction_id"] == extraction["extraction_id"]


def test_ui_base_generation_test_writes_playable_history(tmp_path: Path, monkeypatch) -> None:
    from autotransition.models.acestep_api import AceStepApiClient
    from autotransition.models.base import RepaintResult

    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    def fake_base_test(
        self,
        *,
        prompt,
        save_dir,
        audio_duration=30.0,
        audio_format="flac",
        inference_steps=80,
        guidance_scale=0.6,
        shift=1.0,
        infer_method="sde",
        use_tiled_decode=True,
        dcw_enabled=False,
        velocity_norm_threshold=0.0,
        velocity_ema_factor=0.0,
        seed=None,
        lokr_path=None,
        lokr_scale=1.0,
        lokr_adapter_name=None,
    ):
        assert prompt == "dark strings"
        assert audio_duration == 30.0
        assert inference_steps == 80
        assert guidance_scale == 0.6
        assert shift == 1.0
        assert infer_method == "sde"
        assert use_tiled_decode is True
        assert dcw_enabled is False
        assert velocity_norm_threshold == 0.0
        assert velocity_ema_factor == 0.0
        output = save_dir / "base.flac"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"audio")
        metadata = save_dir / "base.json"
        metadata.write_text("{}", encoding="utf-8")
        return RepaintResult(output_path=output, metadata_path=metadata, model_name="ACE-Step API")

    monkeypatch.setattr(AceStepApiClient, "text2music_base_test", fake_base_test)

    response = client.post(
        "/api/extractions/base-test",
        json={
            "prompt": "dark strings",
            "audio_duration": 30,
        },
    )
    history = client.get("/api/extractions")

    assert response.status_code == 200
    item = response.json()["extraction"]
    assert item["type"] == "base_test"
    assert item["status"] == "complete"
    assert item["prompt"] == "dark strings"
    assert Path(item["generated_audio_path"]).exists()
    assert history.json()[0]["extraction_id"] == item["extraction_id"]


def write_extraction_metadata(
    root: Path,
    extraction_id: str,
    audio_path: Path,
    *,
    item_type: str | None = None,
    label: str = "Stem",
) -> Path:
    import json
    import datetime as _datetime

    metadata = {
        "extraction_id": extraction_id,
        "type": item_type or "extraction",
        "status": "complete",
        "message": "Complete.",
        "created_at": _datetime.datetime.now(_datetime.UTC).isoformat(),
        "label": label,
        "track_name": label.lower(),
        "source_path": str(root / "source.wav"),
        "generated_audio_path": str(audio_path),
        "metadata_path": str(root / extraction_id / "extraction.json"),
    }
    path = root / extraction_id / "extraction.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path


def write_result_metadata(
    root: Path,
    item_id: str,
    filename: str,
    audio_path: Path,
    *,
    category: str,
    label: str,
    id_key: str,
) -> Path:
    import json
    import datetime as _datetime

    metadata = {
        id_key: item_id,
        "type": category,
        "status": "complete",
        "message": "Complete.",
        "created_at": _datetime.datetime.now(_datetime.UTC).isoformat(),
        "label": label,
        "generated_audio_path": str(audio_path),
        "metadata_path": str(root / item_id / filename),
    }
    path = root / item_id / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path


def test_ui_extraction_rename_updates_metadata(tmp_path: Path, monkeypatch) -> None:
    import json

    monkeypatch.chdir(tmp_path)
    audio = make_wav(tmp_path / "vocals.wav", duration_ms=500)
    metadata_path = write_extraction_metadata(tmp_path / "data" / "extractions", "extraction-a", audio)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post("/api/extractions/extraction-a/rename", json={"label": "Lead vocal"})

    assert response.status_code == 200
    assert response.json()["extraction"]["label"] == "Lead vocal"
    assert json.loads(metadata_path.read_text(encoding="utf-8"))["label"] == "Lead vocal"


def test_ui_editor_assets_lists_dance_station_outputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    transition_audio = make_wav(tmp_path / "transition.wav", duration_ms=400)
    music_audio = make_wav(tmp_path / "music.wav", duration_ms=400)
    extraction_audio = make_wav(tmp_path / "vocals.wav", duration_ms=400)
    merge_audio = make_wav(tmp_path / "merge.wav", duration_ms=400)
    edit_audio = make_wav(tmp_path / "edit.wav", duration_ms=400)
    instrument_audio = make_wav(tmp_path / "instrument.wav", duration_ms=400)
    write_result_metadata(
        tmp_path / "data" / "generated",
        "generation-a",
        "result.json",
        transition_audio,
        category="transition",
        label="Bridge transition",
        id_key="generation_id",
    )
    write_result_metadata(
        tmp_path / "data" / "generations",
        "music-a",
        "generation.json",
        music_audio,
        category="generation",
        label="Horror cue",
        id_key="generation_id",
    )
    write_extraction_metadata(tmp_path / "data" / "extractions", "extraction-a", extraction_audio, label="Vocals")
    write_extraction_metadata(
        tmp_path / "data" / "extractions",
        "merge-a",
        merge_audio,
        item_type="merge",
        label="Stem blend",
    )
    write_result_metadata(
        tmp_path / "data" / "edits",
        "edit-a",
        "edit.json",
        edit_audio,
        category="edit",
        label="Clean edit",
        id_key="edit_id",
    )
    write_result_metadata(
        tmp_path / "data" / "instrument-lab",
        "instrument-a",
        "clip.json",
        instrument_audio,
        category="instrument",
        label="Bass phrase",
        id_key="clip_id",
    )
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.get("/api/editor/assets")

    assert response.status_code == 200
    assets = response.json()
    labels = {item["label"]: item["category"] for item in assets}
    assert labels["Bridge transition"] == "transition"
    assert labels["Horror cue"] == "generation"
    assert labels["Vocals"] == "extraction"
    assert labels["Stem blend"] == "merge"
    assert labels["Clean edit"] == "edit"
    assert labels["Bass phrase"] == "instrument"
    assert all(item["audio_url"].startswith("/api/editor/audio?path=") for item in assets)


def test_ui_lokr_dataset_create_upload_save_and_delete(tmp_path: Path, monkeypatch) -> None:
    import json

    monkeypatch.chdir(tmp_path)
    source = make_wav(tmp_path / "song.wav", duration_ms=500)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    created = client.post(
        "/api/lokr/datasets",
        json={
            "label": "Horror style",
            "custom_tag": "horrorstyle",
            "default_genre": "Cinematic horror",
            "default_language": "en",
            "genre_ratio": 0,
        },
    )
    assert created.status_code == 200
    dataset = created.json()["dataset"]
    dataset_id = dataset["metadata"]["dataset_id"]

    with source.open("rb") as audio_file:
        uploaded = client.post(
            f"/api/lokr/datasets/{dataset_id}/entries/upload",
            files={"file": ("song.wav", audio_file, "audio/wav")},
        )
    assert uploaded.status_code == 200
    dataset = uploaded.json()["dataset"]
    sample = dataset["samples"][0]
    assert sample["audio_path"].startswith("./audio/")
    assert sample["genre"] == "Cinematic horror"
    assert sample["language"] == "en"
    assert sample["lyrics"] == "[Instrumental]"
    assert Path(sample["resolved_audio_path"]).exists()

    dataset["metadata"]["all_instrumental"] = False
    saved_toggle = client.post(f"/api/lokr/datasets/{dataset_id}", json={"dataset": dataset})
    assert saved_toggle.status_code == 200
    assert saved_toggle.json()["dataset"]["metadata"]["all_instrumental"] is False

    sample["caption"] = "Suspenseful horror cue with low strings"
    sample["is_instrumental"] = False
    sample["lyrics"] = "[Verse]\nShadows rise"
    sample["formatted_lyrics"] = sample["lyrics"]
    saved = client.post(f"/api/lokr/datasets/{dataset_id}", json={"dataset": dataset})
    assert saved.status_code == 200
    saved_dataset = saved.json()["dataset"]
    assert saved_dataset["metadata"]["num_samples"] == 1
    assert saved_dataset["metadata"]["all_instrumental"] is False
    assert saved_dataset["samples"][0]["caption"] == "Suspenseful horror cue with low strings"

    dataset_json = tmp_path / "data" / "lokr-training" / "datasets" / dataset_id / "dataset.json"
    body = json.loads(dataset_json.read_text(encoding="utf-8"))
    assert body["samples"][0]["lyrics"] == "[Verse]\nShadows rise"
    assert "resolved_audio_path" not in body["samples"][0]

    deleted = client.delete(f"/api/lokr/datasets/{dataset_id}/entries/{sample['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["dataset"]["samples"] == []


def test_ui_lokr_dataset_imports_existing_creation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    music_audio = make_wav(tmp_path / "music.wav", duration_ms=400)
    write_result_metadata(
        tmp_path / "data" / "generations",
        "music-a",
        "generation.json",
        music_audio,
        category="generation",
        label="Generated cue",
        id_key="generation_id",
    )
    client = TestClient(create_app(models_dir=tmp_path / "models"))
    dataset = client.post(
        "/api/lokr/datasets",
        json={"label": "Generated dataset", "default_genre": "Dark ambient", "default_language": "unknown"},
    ).json()["dataset"]
    dataset_id = dataset["metadata"]["dataset_id"]

    response = client.post(f"/api/lokr/datasets/{dataset_id}/entries/from-asset", json={"asset_id": "music-a"})

    assert response.status_code == 200
    sample = response.json()["dataset"]["samples"][0]
    assert sample["label"] == "Generated cue"
    assert sample["genre"] == "Dark ambient"
    assert sample["language"] == "unknown"
    assert sample["source_asset_id"] == "music-a"
    assert sample["source_category"] == "generation"
    assert Path(sample["resolved_audio_path"]).exists()


def test_ui_lokr_preprocess_starts_sidestep_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = make_wav(tmp_path / "song.wav", duration_ms=400)
    popen_calls = []

    class Process:
        returncode = None
        pid = 1234

        def poll(self):
            return None

    def fake_popen(command, stdout=None, stderr=None, cwd=None, **kwargs):
        popen_calls.append(command)
        return Process()

    monkeypatch.setattr("autotransition.ui.app.subprocess.Popen", fake_popen)
    side_step_dir = tmp_path / "Side-Step"
    side_step_dir.mkdir()
    (side_step_dir / "pyproject.toml").write_text("[project]\nname='side-step'\n", encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path / "models", runtime_config=RuntimeConfig(side_step_dir=side_step_dir)))
    dataset = client.post("/api/lokr/datasets", json={"label": "Train set"}).json()["dataset"]
    dataset_id = dataset["metadata"]["dataset_id"]
    with source.open("rb") as audio_file:
        client.post(
            f"/api/lokr/datasets/{dataset_id}/entries/upload",
            files={"file": ("song.wav", audio_file, "audio/wav")},
        )

    response = client.post(
        f"/api/lokr/datasets/{dataset_id}/preprocess",
        json={
            "model": "turbo",
            "sidestep_command": "uv run sidestep",
            "checkpoint_dir": "runtimes/ACE-Step-1.5/checkpoints",
        },
    )

    assert response.status_code == 200
    run = response.json()["run"]
    assert run["type"] == "preprocess"
    assert run["status"] == "running"
    assert run["pid"] == 1234
    assert popen_calls[0][0:4] == ["uv", "run", "sidestep", "preprocess"]
    assert run["cwd"] == str(side_step_dir)
    assert "--dataset-json" in popen_calls[0]
    assert Path(popen_calls[0][popen_calls[0].index("--dataset-json") + 1]).is_absolute()
    assert Path(popen_calls[0][popen_calls[0].index("--audio-dir") + 1]).is_absolute()
    assert Path(popen_calls[0][popen_calls[0].index("--output") + 1]).is_absolute()
    assert "--model" in popen_calls[0]
    assert popen_calls[0][popen_calls[0].index("--model") + 1] == "turbo"


def test_ui_lokr_blocks_second_run_while_running(tmp_path: Path, monkeypatch) -> None:
    import autotransition.ui.app as ui_app

    monkeypatch.chdir(tmp_path)
    ui_app._LOKR_PROCESSES.clear()
    source = make_wav(tmp_path / "song.wav", duration_ms=400)

    class Process:
        returncode = None
        pid = 1234

        def poll(self):
            return None

    monkeypatch.setattr("autotransition.ui.app.subprocess.Popen", lambda *args, **kwargs: Process())
    side_step_dir = tmp_path / "Side-Step"
    side_step_dir.mkdir()
    (side_step_dir / "pyproject.toml").write_text("[project]\nname='side-step'\n", encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path / "models", runtime_config=RuntimeConfig(side_step_dir=side_step_dir)))
    dataset = client.post("/api/lokr/datasets", json={"label": "Train set"}).json()["dataset"]
    dataset_id = dataset["metadata"]["dataset_id"]
    with source.open("rb") as audio_file:
        client.post(
            f"/api/lokr/datasets/{dataset_id}/entries/upload",
            files={"file": ("song.wav", audio_file, "audio/wav")},
        )

    first = client.post(f"/api/lokr/datasets/{dataset_id}/preprocess", json={"model": "turbo"})
    second = client.post(f"/api/lokr/datasets/{dataset_id}/preprocess", json={"model": "turbo"})

    assert first.status_code == 200
    assert second.status_code == 400
    assert "already running" in second.json()["detail"]


def test_ui_lokr_stop_managed_running_process(tmp_path: Path, monkeypatch) -> None:
    import autotransition.ui.app as ui_app

    monkeypatch.chdir(tmp_path)
    ui_app._LOKR_PROCESSES.clear()
    source = make_wav(tmp_path / "song.wav", duration_ms=400)

    class Process:
        returncode = None
        pid = 1234
        terminated = False
        killed = False

        def poll(self):
            return -15 if self.terminated else None

        def terminate(self):
            self.terminated = True
            self.returncode = -15

        def kill(self):
            self.killed = True
            self.returncode = -9

        def wait(self, timeout=None):
            return self.poll()

    process = Process()
    monkeypatch.setattr("autotransition.ui.app.subprocess.Popen", lambda *args, **kwargs: process)
    side_step_dir = tmp_path / "Side-Step"
    side_step_dir.mkdir()
    (side_step_dir / "pyproject.toml").write_text("[project]\nname='side-step'\n", encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path / "models", runtime_config=RuntimeConfig(side_step_dir=side_step_dir)))
    dataset = client.post("/api/lokr/datasets", json={"label": "Train set"}).json()["dataset"]
    dataset_id = dataset["metadata"]["dataset_id"]
    with source.open("rb") as audio_file:
        client.post(
            f"/api/lokr/datasets/{dataset_id}/entries/upload",
            files={"file": ("song.wav", audio_file, "audio/wav")},
        )
    started = client.post(f"/api/lokr/datasets/{dataset_id}/preprocess", json={"model": "turbo"}).json()["run"]

    stopped = client.post(f"/api/lokr/runs/{started['run_id']}/stop")

    assert stopped.status_code == 200
    run = stopped.json()["run"]
    assert run["status"] == "stopped"
    assert run["message"] == "Stopped by user."
    assert process.terminated is True
    assert process.killed is False
    assert started["run_id"] not in ui_app._LOKR_PROCESSES


def test_ui_lokr_stop_reports_unmanaged_running_process(tmp_path: Path, monkeypatch) -> None:
    import json
    import autotransition.ui.app as ui_app

    monkeypatch.chdir(tmp_path)
    ui_app._LOKR_PROCESSES.clear()
    run_dir = tmp_path / "data" / "lokr-training" / "runs" / "train-unmanaged"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": "train-unmanaged",
                "type": "train",
                "dataset_id": "dataset-a",
                "label": "Train LoKr",
                "status": "running",
                "model": "turbo",
                "command": ["uv", "run", "sidestep", "--yes", "train"],
                "log_path": str(run_dir / "sidestep-train.log"),
                "created_at": "2026-06-26T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post("/api/lokr/runs/train-unmanaged/stop")

    assert response.status_code == 409
    assert "not managed" in response.json()["detail"]


def test_ui_lokr_train_uses_latest_completed_tensor_run(tmp_path: Path, monkeypatch) -> None:
    import json

    monkeypatch.chdir(tmp_path)
    popen_calls = []

    class Process:
        returncode = None
        pid = 1234

        def poll(self):
            return None

    def fake_popen(command, stdout=None, stderr=None, cwd=None, **kwargs):
        popen_calls.append(command)
        return Process()

    monkeypatch.setattr("autotransition.ui.app.subprocess.Popen", fake_popen)
    side_step_dir = tmp_path / "Side-Step"
    side_step_dir.mkdir()
    (side_step_dir / "pyproject.toml").write_text("[project]\nname='side-step'\n", encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path / "models", runtime_config=RuntimeConfig(side_step_dir=side_step_dir)))
    dataset = client.post("/api/lokr/datasets", json={"label": "Train set"}).json()["dataset"]
    dataset_id = dataset["metadata"]["dataset_id"]
    tensor_dir = tmp_path / "data" / "lokr-training" / "runs" / "preprocess-a" / "tensors"
    tensor_dir.mkdir(parents=True)
    run_json = tmp_path / "data" / "lokr-training" / "runs" / "preprocess-a" / "run.json"
    run_json.write_text(
        json.dumps(
            {
                "run_id": "preprocess-a",
                "type": "preprocess",
                "dataset_id": dataset_id,
                "label": "Preprocess",
                "status": "complete",
                "model": "turbo",
                "tensor_dir": str(tensor_dir),
                "created_at": "2026-06-26T00:00:00+00:00",
                "log_path": str(tmp_path / "preprocess.log"),
            }
        ),
        encoding="utf-8",
    )

    response = client.post(
        f"/api/lokr/datasets/{dataset_id}/train",
        json={
            "model": "base",
            "sidestep_command": "uv run sidestep",
            "checkpoint_dir": "runtimes/ACE-Step-1.5/checkpoints",
            "epochs": 25,
            "lokr_linear_dim": 32,
            "lokr_linear_alpha": 64,
            "save_every": 5,
            "optimizer_type": "adamw8bit",
            "batch_size": 1,
            "gradient_accumulation": 4,
            "gradient_checkpointing": True,
            "offload_encoder": True,
        },
    )

    assert response.status_code == 200
    run = response.json()["run"]
    assert run["type"] == "train"
    assert run["adapter_type"] == "lokr"
    assert popen_calls[0][0:5] == ["uv", "run", "sidestep", "--yes", "train"]
    assert run["cwd"] == str(side_step_dir)
    assert popen_calls[0][popen_calls[0].index("--model") + 1] == "base"
    assert popen_calls[0][popen_calls[0].index("--adapter-type") + 1] == "lokr"
    assert popen_calls[0][popen_calls[0].index("--lokr-linear-dim") + 1] == "32"
    assert popen_calls[0][popen_calls[0].index("--lokr-linear-alpha") + 1] == "64"
    assert popen_calls[0][popen_calls[0].index("--batch-size") + 1] == "1"
    assert popen_calls[0][popen_calls[0].index("--gradient-accumulation") + 1] == "4"
    assert popen_calls[0][popen_calls[0].index("--dataset-dir") + 1] == str(tensor_dir.resolve())
    assert "--gradient-checkpointing" in popen_calls[0]
    assert "--offload-encoder" in popen_calls[0]


def test_ui_lokr_preprocess_reports_missing_sidestep_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = make_wav(tmp_path / "song.wav", duration_ms=400)

    def fake_popen(command, stdout=None, stderr=None, cwd=None, **kwargs):
        raise FileNotFoundError("[WinError 2] The system cannot find the file specified")

    monkeypatch.setattr("autotransition.ui.app.subprocess.Popen", fake_popen)
    side_step_dir = tmp_path / "Side-Step"
    side_step_dir.mkdir()
    (side_step_dir / "pyproject.toml").write_text("[project]\nname='side-step'\n", encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path / "models", runtime_config=RuntimeConfig(side_step_dir=side_step_dir)))
    dataset = client.post("/api/lokr/datasets", json={"label": "Train set"}).json()["dataset"]
    dataset_id = dataset["metadata"]["dataset_id"]
    with source.open("rb") as audio_file:
        client.post(
            f"/api/lokr/datasets/{dataset_id}/entries/upload",
            files={"file": ("song.wav", audio_file, "audio/wav")},
        )

    response = client.post(
        f"/api/lokr/datasets/{dataset_id}/preprocess",
        json={"model": "turbo", "sidestep_command": "missing-sidestep"},
    )

    assert response.status_code == 200
    run = response.json()["run"]
    assert run["status"] == "failed"
    assert "WinError 2" in run["message"]


def test_ui_lokr_runs_marks_zero_processed_preprocess_failed(tmp_path: Path, monkeypatch) -> None:
    import json
    import autotransition.ui.app as ui_app

    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "data" / "lokr-training" / "runs" / "preprocess-zero"
    run_dir.mkdir(parents=True)
    log_path = run_dir / "sidestep-preprocess.log"
    log_path.write_text("No audio files found\nProcessed: 0/0\n", encoding="utf-8")
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": "preprocess-zero",
                "type": "preprocess",
                "dataset_id": "dataset-a",
                "label": "Preprocess",
                "status": "running",
                "model": "turbo",
                "command": ["uv", "run", "sidestep", "preprocess"],
                "log_path": str(log_path),
                "created_at": "2026-06-26T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    class Process:
        returncode = 0

        def poll(self):
            return 0

    monkeypatch.setitem(ui_app._LOKR_PROCESSES, "preprocess-zero", Process())
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    runs = client.get("/api/lokr/runs").json()

    assert runs[0]["status"] == "failed"
    assert "without processing any audio" in runs[0]["message"]


def test_ui_lokr_runs_marks_completed_preprocess_ready_from_log(tmp_path: Path, monkeypatch) -> None:
    import json

    monkeypatch.chdir(tmp_path)
    tensor_dir = tmp_path / "data" / "lokr-training" / "runs" / "preprocess-ready" / "tensors"
    tensor_dir.mkdir(parents=True)
    log_path = tensor_dir.parent / "sidestep-preprocess.log"
    log_path.write_text("Preprocessing complete: 20/20 processed, 0 failed\n", encoding="utf-8")
    (tensor_dir.parent / "run.json").write_text(
        json.dumps(
            {
                "run_id": "preprocess-ready",
                "type": "preprocess",
                "dataset_id": "dataset-a",
                "label": "Preprocess",
                "status": "running",
                "model": "turbo",
                "command": ["uv", "run", "sidestep", "preprocess"],
                "log_path": str(log_path),
                "tensor_dir": str(tensor_dir),
                "created_at": "2026-06-26T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    runs = client.get("/api/lokr/runs").json()

    assert runs[0]["status"] == "complete"
    assert runs[0]["ready_to_train"] is True
    assert runs[0]["processed_samples"] == 20
    assert runs[0]["summary"] == "Processed 20/20 samples"


def test_ui_lokr_runs_includes_training_log_summary(tmp_path: Path, monkeypatch) -> None:
    import json

    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "data" / "lokr-training" / "runs" / "train-a"
    run_dir.mkdir(parents=True)
    output_dir = run_dir / "adapter"
    output_dir.mkdir()
    (output_dir / ".progress.jsonl").write_text(
        '{"kind":"step","step":60,"epoch":12,"max_epochs":500,"loss":1.2387}\n',
        encoding="utf-8",
    )
    session_dir = output_dir / "session_logs"
    session_dir.mkdir()
    (session_dir / "session_ui.log").write_text("Epoch 12/500, Step 60, Loss: 1.2387\n", encoding="utf-8")
    log_path = run_dir / "sidestep-train.log"
    log_path.write_text("PreprocessedTensorDataset: 20 samples from tensors\n[Side-Step] Using AdamW8bit optimizer (lower VRAM)\n", encoding="utf-8")
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": "train-a",
                "type": "train",
                "dataset_id": "dataset-a",
                "label": "Train LoKr",
                "status": "running",
                "model": "turbo",
                "command": ["uv", "run", "sidestep", "--yes", "train"],
                "log_path": str(log_path),
                "output_dir": str(output_dir),
                "created_at": "2026-06-26T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    runs = client.get("/api/lokr/runs").json()
    logs = client.get("/api/lokr/runs/train-a/logs").json()

    assert runs[0]["summary"] == "Training Epoch 12/500 | step 60 | loss 1.2387"
    assert runs[0]["current_epoch"] == 12
    assert "Epoch 12/500, Step 60, Loss: 1.2387" in logs["text"]


def test_ui_instrument_lab_save_records_history_and_asset(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = make_wav(tmp_path / "instrument.wav", duration_ms=500)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    with source.open("rb") as audio_file:
        response = client.post(
            "/api/instrument-lab/clips",
            data={
                "label": "Bass phrase",
                "project_json": '{"bpm":120,"tracks":[]}',
            },
            files={"file": ("instrument.wav", audio_file, "audio/wav")},
        )
    history = client.get("/api/instrument-lab/clips")
    assets = client.get("/api/editor/assets")

    assert response.status_code == 200
    clip = response.json()["clip"]
    assert clip["label"] == "Bass phrase"
    assert clip["project"]["bpm"] == 120
    assert Path(clip["generated_audio_path"]).exists()
    assert history.json()[0]["clip_id"] == clip["clip_id"]
    assert any(item["category"] == "instrument" and item["label"] == "Bass phrase" for item in assets.json())


def test_ui_instrument_lab_track_save_records_instrumenttrack_asset(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = make_wav(tmp_path / "instrument-track.wav", duration_ms=500)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    project = '{"bpm":120,"tracks":[{"id":"track-a","kind":"instrument","notes":[{"pitch":48,"start":0,"duration":1}]}]}'
    with source.open("rb") as audio_file:
        response = client.post(
            "/api/instrument-lab/clips",
            data={
                "label": "Bass track",
                "clip_type": "instrumenttrack",
                "project_json": project,
            },
            files={"file": ("instrument-track.wav", audio_file, "audio/wav")},
        )
    assets = client.get("/api/editor/assets")

    assert response.status_code == 200
    clip = response.json()["clip"]
    assert clip["type"] == "instrumenttrack"
    assert clip["project"]["tracks"][0]["id"] == "track-a"
    assert any(item["category"] == "instrumenttrack" and item["label"] == "Bass track" for item in assets.json())


def test_ui_editor_save_edit_records_history_and_asset(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = make_wav(tmp_path / "edited.wav", duration_ms=500)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    with source.open("rb") as audio_file:
        response = client.post(
            "/api/edits",
            data={
                "label": "Clean transition",
                "source_asset_id": "generation-a",
                "source_category": "transition",
            },
            files={"file": ("edited.wav", audio_file, "audio/wav")},
        )
    history = client.get("/api/edits")
    assets = client.get("/api/editor/assets")

    assert response.status_code == 200
    edit = response.json()["edit"]
    assert edit["label"] == "Clean transition"
    assert edit["source_asset_id"] == "generation-a"
    assert Path(edit["generated_audio_path"]).exists()
    assert history.json()[0]["edit_id"] == edit["edit_id"]
    assert any(item["category"] == "edit" and item["label"] == "Clean transition" for item in assets.json())


def test_ui_editor_rename_endpoints_update_metadata(tmp_path: Path, monkeypatch) -> None:
    import json

    monkeypatch.chdir(tmp_path)
    transition_audio = make_wav(tmp_path / "transition.wav", duration_ms=400)
    music_audio = make_wav(tmp_path / "music.wav", duration_ms=400)
    edit_audio = make_wav(tmp_path / "edit.wav", duration_ms=400)
    transition_metadata = write_result_metadata(
        tmp_path / "data" / "generated",
        "generation-a",
        "result.json",
        transition_audio,
        category="transition",
        label="Old transition",
        id_key="generation_id",
    )
    music_metadata = write_result_metadata(
        tmp_path / "data" / "generations",
        "music-a",
        "generation.json",
        music_audio,
        category="generation",
        label="Old music",
        id_key="generation_id",
    )
    edit_metadata = write_result_metadata(
        tmp_path / "data" / "edits",
        "edit-a",
        "edit.json",
        edit_audio,
        category="edit",
        label="Old edit",
        id_key="edit_id",
    )
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    transition = client.post("/api/transitions/generation-a/rename", json={"label": "New transition"})
    music = client.post("/api/music-generations/music-a/rename", json={"label": "New music"})
    edit = client.post("/api/edits/edit-a/rename", json={"label": "New edit"})

    assert transition.status_code == 200
    assert music.status_code == 200
    assert edit.status_code == 200
    assert json.loads(transition_metadata.read_text(encoding="utf-8"))["label"] == "New transition"
    assert json.loads(music_metadata.read_text(encoding="utf-8"))["label"] == "New music"
    assert json.loads(edit_metadata.read_text(encoding="utf-8"))["label"] == "New edit"


def test_ui_merge_extractions_writes_playable_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "data" / "extractions"
    first = make_wav(tmp_path / "vocals.wav", duration_ms=500)
    second = make_wav(tmp_path / "drums.wav", duration_ms=700)
    write_extraction_metadata(root, "extraction-vocals", first, label="Vocals")
    write_extraction_metadata(root, "extraction-drums", second, label="Drums")
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/extractions/merge",
        json={
            "extraction_ids": ["extraction-vocals", "extraction-drums"],
            "label": "Vocals and drums",
            "output_format": "flac",
        },
    )
    history = client.get("/api/extractions")

    assert response.status_code == 200
    item = response.json()["extraction"]
    assert item["type"] == "merge"
    assert item["label"] == "Vocals and drums"
    assert item["source_extraction_ids"] == ["extraction-vocals", "extraction-drums"]
    assert Path(item["generated_audio_path"]).exists()
    assert history.json()[0]["extraction_id"] == item["extraction_id"]


def test_ui_merge_rejects_base_test_items(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "data" / "extractions"
    first = make_wav(tmp_path / "vocals.wav", duration_ms=500)
    second = make_wav(tmp_path / "base.wav", duration_ms=500)
    write_extraction_metadata(root, "extraction-vocals", first, label="Vocals")
    write_extraction_metadata(root, "base-test-a", second, item_type="base_test", label="Base test")
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/extractions/merge",
        json={
            "extraction_ids": ["extraction-vocals", "base-test-a"],
            "label": "Bad merge",
            "output_format": "flac",
        },
    )

    assert response.status_code == 400
    assert "Base Test" in response.json()["detail"]


def test_ui_music_generation_runs_and_records_history(tmp_path: Path, monkeypatch) -> None:
    from autotransition.models.acestep_api import AceStepApiClient
    from autotransition.models.base import RepaintResult

    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    def fake_music(
        self,
        *,
        prompt,
        model,
        save_dir,
        lyrics="[Instrumental]",
        vocal_language="unknown",
        audio_duration=30.0,
        audio_format="flac",
        inference_steps=8,
        guidance_scale=1.0,
        shift=3.0,
        infer_method="ode",
        use_tiled_decode=True,
        dcw_enabled=False,
        velocity_norm_threshold=0.0,
        velocity_ema_factor=0.0,
        seed=None,
        lokr_path=None,
        lokr_scale=1.0,
        lokr_adapter_name=None,
    ):
        assert prompt == "dark music"
        assert model == "acestep-v15-turbo"
        assert lyrics == "This is the hook"
        assert vocal_language == "en"
        assert audio_duration == 300.0
        assert inference_steps == 8
        assert guidance_scale == 1.0
        output = save_dir / "music.flac"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"audio")
        metadata = save_dir / "ace.json"
        metadata.write_text("{}", encoding="utf-8")
        return RepaintResult(output_path=output, metadata_path=metadata, model_name="ACE-Step API")

    monkeypatch.setattr(AceStepApiClient, "text2music_standalone", fake_music)

    response = client.post(
        "/api/music-generations/run",
        json={
            "prompt": "dark music",
            "model": "acestep-v15-turbo",
            "label": "Dark cue",
            "instrumental": False,
            "lyrics": "This is the hook",
            "vocal_language": "en",
            "audio_duration": 300,
            "inference_steps": 8,
            "guidance_scale": 1.0,
            "shift": 3.0,
        },
    )
    history = client.get("/api/music-generations")

    assert response.status_code == 200
    item = response.json()["generation"]
    assert item["status"] == "complete"
    assert item["label"] == "Dark cue"
    assert item["settings"]["instrumental"] is False
    assert item["settings"]["lyrics"] == "This is the hook"
    assert item["settings"]["vocal_language"] == "en"
    assert Path(item["generated_audio_path"]).exists()
    assert history.json()[0]["generation_id"] == item["generation_id"]


def test_ui_music_generation_accepts_legacy_xl_base_model_value(tmp_path: Path, monkeypatch) -> None:
    from autotransition.models.acestep_api import AceStepApiClient, RepaintResult

    client = TestClient(create_app(runtime_config=RuntimeConfig(ace_step_dir=tmp_path / "runtime")))

    def fake_music(self, *, prompt, model, save_dir, **kwargs):
        assert model == "acestep-v15-base"
        output = save_dir / "music.flac"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"audio")
        metadata = save_dir / "ace.json"
        metadata.write_text("{}", encoding="utf-8")
        return RepaintResult(output_path=output, metadata_path=metadata, model_name="ACE-Step API")

    monkeypatch.setattr(AceStepApiClient, "text2music_standalone", fake_music)

    response = client.post(
        "/api/music-generations/run",
        json={
            "prompt": "dark music",
            "model": "acestep-v15-xl-base",
            "vocal_language": "auto",
            "audio_duration": 30,
            "inference_steps": 8,
            "guidance_scale": 1.0,
            "shift": 3.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["generation"]["model"] == "acestep-v15-base"


def test_ui_lokr_adapters_lists_completed_training_weights(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "data" / "lokr-training" / "runs" / "train-a"
    weights = run_dir / "adapter" / "best" / "lokr_weights.safetensors"
    weights.parent.mkdir(parents=True, exist_ok=True)
    weights.write_bytes(b"weights")
    run_json = run_dir / "run.json"
    run_json.write_text(
        json.dumps(
            {
                "run_id": "train-a",
                "type": "train",
                "dataset_id": "dataset-a",
                "label": "Train LoKr Artist Style",
                "status": "complete",
                "model": "turbo",
                "adapter_type": "lokr",
                "output_dir": str(run_dir / "adapter"),
                "created_at": "2026-06-26T00:00:00+00:00",
                "completed_at": "2026-06-26T01:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    client = TestClient(create_app(models_dir=tmp_path / "models"))
    response = client.get("/api/lokr/adapters")

    assert response.status_code == 200
    adapters = response.json()
    assert adapters[0]["adapter_id"] == "train-a"
    assert adapters[0]["label"] == "Artist Style"
    assert adapters[0]["model"] == "acestep-v15-turbo"
    assert adapters[0]["weights_path"] == str(weights)


def test_ui_music_generation_applies_selected_lokr_adapter(tmp_path: Path, monkeypatch) -> None:
    from autotransition.models.acestep_api import AceStepApiClient, RepaintResult

    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "data" / "lokr-training" / "runs" / "train-a"
    weights = run_dir / "adapter" / "best" / "lokr_weights.safetensors"
    weights.parent.mkdir(parents=True, exist_ok=True)
    weights.write_bytes(b"weights")
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": "train-a",
                "type": "train",
                "dataset_id": "dataset-a",
                "label": "Train LoKr Artist Style",
                "status": "complete",
                "model": "turbo",
                "adapter_type": "lokr",
                "output_dir": str(run_dir / "adapter"),
                "created_at": "2026-06-26T00:00:00+00:00",
                "completed_at": "2026-06-26T01:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    captured = {}

    def fake_music(self, *, save_dir, lokr_path=None, lokr_scale=1.0, lokr_adapter_name=None, **kwargs):
        captured["lokr_path"] = lokr_path
        captured["lokr_scale"] = lokr_scale
        captured["lokr_adapter_name"] = lokr_adapter_name
        output = save_dir / "music.flac"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"audio")
        metadata = save_dir / "ace.json"
        metadata.write_text("{}", encoding="utf-8")
        return RepaintResult(output_path=output, metadata_path=metadata, model_name="ACE-Step API")

    monkeypatch.setattr(AceStepApiClient, "text2music_standalone", fake_music)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/music-generations/run",
        json={
            "prompt": "artist style pop",
            "model": "acestep-v15-turbo",
            "lokr_adapter_id": "train-a",
            "lokr_scale": 0.65,
            "audio_duration": 30,
        },
    )

    assert response.status_code == 200
    item = response.json()["generation"]
    assert captured == {
        "lokr_path": str(weights),
        "lokr_scale": 0.65,
        "lokr_adapter_name": "dance_station_train-a",
    }
    assert item["lokr_adapter"]["adapter_id"] == "train-a"
    assert item["lokr_adapter"]["label"] == "Artist Style"
    assert item["lokr_scale"] == 0.65


def test_ui_selection_scaffold_uses_configured_future_length(tmp_path: Path) -> None:
    from pydub import AudioSegment

    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    output_dir = tmp_path / "out"
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/scaffolds/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "output_dir": str(output_dir),
            "continuation_point_seconds": 4.0,
            "context_seconds": 2.0,
            "repaint_overlap_seconds": 1.0,
            "new_section_seconds": 5.0,
        },
    )

    assert response.status_code == 200
    plan = response.json()["plan"]
    assert plan["tail_start_seconds"] == 2.0
    assert plan["tail_end_seconds"] == 4.0
    assert plan["source_format"] == "WAV"
    assert plan["audio_format"] == "wav"
    assert plan["requested_continuation_seconds"] == 5.0
    assert plan["repainting_end_seconds"] == 7.0
    assert Path(plan["scaffold_path"]).exists()
    assert len(AudioSegment.from_file(plan["scaffold_path"])) == 2000


def test_ui_selection_scaffold_rejects_early_marker(tmp_path: Path) -> None:
    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/scaffolds/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "continuation_point_seconds": 1.0,
            "context_seconds": 2.0,
            "repaint_overlap_seconds": 1.0,
            "new_section_seconds": 5.0,
        },
    )

    assert response.status_code == 400
    assert "too early" in response.json()["detail"]


def test_ui_selection_scaffold_honors_zero_repaint_margin(tmp_path: Path) -> None:
    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/scaffolds/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "continuation_point_seconds": 4.0,
            "context_seconds": 2.0,
            "repaint_overlap_seconds": 0.0,
            "new_section_seconds": 5.0,
        },
    )

    assert response.status_code == 200
    plan = response.json()["plan"]
    assert plan["repaint_overlap_seconds"] == 0.0
    assert plan["repainting_start_seconds"] == 2.0


def test_ui_source_upload_accepts_audio_file(tmp_path: Path) -> None:
    source = make_wav(tmp_path / "picked.wav", duration_ms=1200)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    with source.open("rb") as audio_file:
        response = client.post(
            "/api/source/upload",
            files={"file": ("picked.wav", audio_file, "audio/wav")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "picked.wav"
    assert Path(data["stored_path"]).exists()
    assert data["probe"]["source_format"] == "WAV"
    assert data["probe"]["duration_seconds"] == 1.2


def test_ui_source_upload_rejects_unsupported_extension(tmp_path: Path) -> None:
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/source/upload",
        files={"file": ("notes.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported audio format" in response.json()["detail"]


def test_ui_generate_from_selection_does_not_block_on_app_model_install_status(tmp_path: Path, monkeypatch) -> None:
    import autotransition.runtime.ace_step as ace_step_runtime
    from autotransition.models.acestep_api import AceStepApiClient
    from autotransition.models.base import RepaintResult

    monkeypatch.setattr(
        ace_step_runtime,
        "runtime_status",
        lambda config=None: SimpleNamespace(api_running=True, message="ACE-Step API is ready."),
    )

    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    output_dir = tmp_path / "out"
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    def fake_text2music(self, plan, profile, save_dir):
        generated = output_dir / "generated.flac"
        generated.parent.mkdir(parents=True, exist_ok=True)
        from pydub import AudioSegment

        AudioSegment.silent(duration=1000, frame_rate=44100).export(generated, format="flac")
        metadata = output_dir / "generated.json"
        metadata.write_text("{}", encoding="utf-8")
        return RepaintResult(output_path=generated, metadata_path=metadata, model_name="ACE-Step API")

    def fake_repaint_transition(self, plan, profile, save_dir):
        generated = output_dir / "repainted.wav"
        generated.parent.mkdir(parents=True, exist_ok=True)
        from pydub import AudioSegment

        AudioSegment.silent(duration=5000, frame_rate=44100).export(generated, format="wav")
        metadata = output_dir / "repainted.json"
        metadata.write_text("{}", encoding="utf-8")
        return RepaintResult(output_path=generated, metadata_path=metadata, model_name="ACE-Step API")

    monkeypatch.setattr(AceStepApiClient, "text2music", fake_text2music)
    monkeypatch.setattr(AceStepApiClient, "repaint_transition", fake_repaint_transition)

    response = client.post(
        "/api/generate/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "model_slug": "acestep-v15-turbo",
            "output_dir": str(output_dir),
            "continuation_point_seconds": 4.0,
            "context_seconds": 2.0,
            "repaint_overlap_seconds": 0.0,
            "new_section_seconds": 5.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["status"] == "complete"
    assert payload["plan"]["requested_continuation_seconds"] == 5.0
    assert payload["plan"]["repainting_end_seconds"] == 7.0


def test_ui_generate_from_selection_records_advanced_settings_and_region(tmp_path: Path) -> None:
    source = make_wav(tmp_path / "song.wav", duration_ms=10000)
    output_dir = tmp_path / "out"
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/generate/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "model_slug": "acestep-v15-turbo",
            "output_dir": str(output_dir),
            "continuation_point_seconds": 4.0,
            "generation_region": "repaint_existing",
            "context_seconds": 2.0,
            "repaint_overlap_seconds": 1.0,
            "new_section_seconds": 5.0,
            "ace_step": {
                "inference_steps": 16,
                "chunk_mask_mode": "auto",
                "repaint_mode": "aggressive",
                "repaint_strength": 0.8,
            },
        },
    )

    assert response.status_code == 200
    plan = response.json()["plan"]
    assert plan["generation_region"] == "repaint_existing"
    assert plan["repainting_start_seconds"] == 1.0
    assert plan["repainting_end_seconds"] == 7.0
    assert plan["ace_step_settings"]["inference_steps"] == 16
    assert plan["ace_step_settings"]["chunk_mask_mode"] == "auto"
    assert plan["ace_step_settings"]["repaint_mode"] == "aggressive"
    assert plan["ace_step_settings"]["repaint_strength"] == 0.8


def test_ui_generate_from_selection_rejects_existing_repaint_without_enough_audio(tmp_path: Path) -> None:
    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/generate/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "model_slug": "acestep-v15-turbo",
            "continuation_point_seconds": 4.0,
            "generation_region": "repaint_existing",
            "context_seconds": 2.0,
            "repaint_overlap_seconds": 1.0,
            "new_section_seconds": 5.0,
        },
    )

    assert response.status_code == 400
    assert "not enough source audio" in response.json()["detail"]


def test_ui_generate_from_selection_reports_missing_runtime_when_model_ready(tmp_path: Path, monkeypatch) -> None:
    import autotransition.runtime.ace_step as ace_step_runtime

    monkeypatch.setattr(
        ace_step_runtime,
        "runtime_status",
        lambda config=None: SimpleNamespace(api_running=False, message="ACE-Step API is not ready."),
    )
    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    model_dir = tmp_path / "models" / "acestep-v15-turbo"
    model_dir.mkdir(parents=True)
    (model_dir / "model.safetensors").write_text("fake", encoding="utf-8")
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/generate/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "model_slug": "acestep-v15-turbo",
            "continuation_point_seconds": 4.0,
            "context_seconds": 2.0,
            "repaint_overlap_seconds": 1.0,
            "new_section_seconds": 5.0,
        },
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "failed"
    assert "ACE-Step API is not ready" in result["message"]
    assert Path(result["scaffold_metadata_path"]).exists()


def test_ui_generate_from_selection_uses_text2music_and_composite_by_default(tmp_path: Path, monkeypatch) -> None:
    import json
    import autotransition.ui.app as ui_app
    from autotransition.models.base import RepaintResult

    calls = []

    class Adapter:
        def __init__(self, profile, model_path, runtime_config=None) -> None:
            pass

        def text2music(self, plan):
            calls.append(("text2music", plan.transition_id))
            raw_dir = tmp_path / "raw"
            raw_dir.mkdir()
            raw_audio = make_wav(raw_dir / "raw.wav", duration_ms=1000)
            raw_metadata = raw_dir / "raw.json"
            raw_metadata.write_text("{}", encoding="utf-8")
            return RepaintResult(output_path=raw_audio, metadata_path=raw_metadata, model_name="fake")

        def repaint_transition(self, plan):
            calls.append(("repaint", plan.transition_id))
            final_dir = tmp_path / "final"
            final_dir.mkdir()
            final_audio = make_wav(final_dir / "final.wav", duration_ms=2000)
            final_metadata = final_dir / "final.json"
            final_metadata.write_text("{}", encoding="utf-8")
            return RepaintResult(output_path=final_audio, metadata_path=final_metadata, model_name="fake")

    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    output_dir = tmp_path / "out"
    model_dir = tmp_path / "models" / "acestep-v15-turbo"
    model_dir.mkdir(parents=True)
    (model_dir / "model.safetensors").write_text("fake", encoding="utf-8")
    monkeypatch.setattr(ui_app, "AceStepRepaintAdapter", Adapter)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/generate/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "model_slug": "acestep-v15-turbo",
            "output_dir": str(output_dir),
            "continuation_point_seconds": 2.0,
            "context_seconds": 1.0,
            "repaint_overlap_seconds": 0.0,
            "new_section_seconds": 1.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["status"] == "complete"
    assert calls == [
        ("text2music", payload["plan"]["transition_id"]),
        ("repaint", payload["plan"]["transition_id"]),
    ]
    assert Path(payload["result"]["generated_audio_path"]).exists()
    assert payload["result"]["generated_audio_path"].endswith("final.wav")
    result_metadata = Path(payload["result"]["metadata_path"])
    assert result_metadata.exists()
    assert json.loads(result_metadata.read_text(encoding="utf-8"))["type"] == "transition"


def test_ui_generate_from_selection_can_boundary_repaint_composite(tmp_path: Path, monkeypatch) -> None:
    import autotransition.ui.app as ui_app
    from autotransition.models.base import RepaintResult

    seen_boundary = {}

    class Adapter:
        def __init__(self, profile, model_path, runtime_config=None) -> None:
            pass

        def text2music(self, plan):
            raw_dir = tmp_path / "raw-boundary"
            raw_dir.mkdir()
            raw_audio = make_wav(raw_dir / "raw.wav", duration_ms=2000)
            raw_metadata = raw_dir / "raw.json"
            raw_metadata.write_text("{}", encoding="utf-8")
            return RepaintResult(output_path=raw_audio, metadata_path=raw_metadata, model_name="fake")

        def repaint_transition(self, plan):
            seen_boundary["start"] = plan.repainting_start_seconds
            seen_boundary["end"] = plan.repainting_end_seconds
            seen_boundary["scaffold_path"] = str(plan.scaffold_path)
            final_dir = tmp_path / "final-boundary"
            final_dir.mkdir()
            final_audio = make_wav(final_dir / "final.wav", duration_ms=4000)
            final_metadata = final_dir / "final.json"
            final_metadata.write_text("{}", encoding="utf-8")
            return RepaintResult(output_path=final_audio, metadata_path=final_metadata, model_name="fake")

    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    output_dir = tmp_path / "out"
    model_dir = tmp_path / "models" / "acestep-v15-turbo"
    model_dir.mkdir(parents=True)
    (model_dir / "model.safetensors").write_text("fake", encoding="utf-8")
    monkeypatch.setattr(ui_app, "AceStepRepaintAdapter", Adapter)
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.post(
        "/api/generate/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "model_slug": "acestep-v15-turbo",
            "output_dir": str(output_dir),
            "continuation_point_seconds": 3.0,
            "context_seconds": 1.0,
            "repaint_overlap_seconds": 1.0,
            "new_section_seconds": 2.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["status"] == "complete"
    assert seen_boundary["start"] == 2.0
    assert seen_boundary["end"] == 5.0
    assert Path(seen_boundary["scaffold_path"]).exists()
    assert payload["result"]["generated_audio_path"].endswith("final.wav")


def test_ui_generate_from_selection_passes_configured_runtime_port(tmp_path: Path, monkeypatch) -> None:
    import autotransition.ui.app as ui_app

    seen_ports = []

    class Adapter:
        def __init__(self, profile, model_path, runtime_config=None) -> None:
            seen_ports.append(runtime_config.api_port)

        def text2music(self, plan):
            from autotransition.models import AceStepRuntimeError

            raise AceStepRuntimeError("stop after config capture")

    source = make_wav(tmp_path / "song.wav", duration_ms=6000)
    model_dir = tmp_path / "models" / "acestep-v15-turbo"
    model_dir.mkdir(parents=True)
    (model_dir / "model.safetensors").write_text("fake", encoding="utf-8")
    monkeypatch.setattr(ui_app, "AceStepRepaintAdapter", Adapter)
    client = TestClient(
        create_app(
            models_dir=tmp_path / "models",
            runtime_config=RuntimeConfig(api_port=9101),
        )
    )

    response = client.post(
        "/api/generate/from-selection",
        json={
            "source_path": str(source),
            "preset": "smooth-continuation",
            "model_slug": "acestep-v15-turbo",
            "continuation_point_seconds": 4.0,
            "context_seconds": 2.0,
            "repaint_overlap_seconds": 1.0,
            "new_section_seconds": 5.0,
        },
    )

    assert response.status_code == 200
    assert seen_ports == [9101]
