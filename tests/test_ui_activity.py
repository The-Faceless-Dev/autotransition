from pathlib import Path

from fastapi.testclient import TestClient

from autotransition.ui import create_app
from autotransition.ui.activity import summarize_lines


def test_summarize_lines_extracts_huggingface_progress() -> None:
    activity = summarize_lines(
        [
            "[Model Download] Downloading unified repo ACE-Step/Ace-Step1.5 to checkpoints...",
            "model.safetensors:  63%|######2   | 3.00G/4.79G [07:45<02:12, 13.5MB/s]",
        ]
    )

    assert activity.phase == "downloading"
    assert activity.message == "Downloading ACE-Step asset: 3.00G/4.79G (63%)"
    assert activity.detail == "model.safetensors"


def test_summarize_lines_extracts_bracket_progress() -> None:
    activity = summarize_lines(
        [
            "Downloading [model.safetensors]:   2%|1         | 91.0M/4.46G [03:16<4:26:00, 294kB/s]",
        ]
    )

    assert activity.phase == "downloading"
    assert activity.message == "Downloading ACE-Step asset: 91.0M/4.46G (2%)"


def test_summarize_lines_prefers_generation_progress_over_completed_download() -> None:
    activity = summarize_lines(
        [
            "Fetching 11 files: 100%|##########| 11/11 [01:44<00:00,  9.54s/steps]",
            "2026-06-18 16:28:49.002 | INFO | [service_generate] Generating audio... (DiT backend: PyTorch (cuda))",
            " 74%|#######4  | 37/50 [00:10<00:03,  3.74steps/s]",
        ]
    )

    assert activity.phase == "generating"
    assert activity.message == "Generating audio: step 37/50 (74%)"


def test_runtime_activity_endpoint_reads_log_tail(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    log_dir = tmp_path / "data/logs"
    log_dir.mkdir(parents=True)
    (log_dir / "ace-step-api.err.log").write_text(
        "model.safetensors:  45%|####5     | 2.17G/4.79G [06:49<02:21, 18.5MB/s]\n",
        encoding="utf-8",
    )
    client = TestClient(create_app(models_dir=tmp_path / "models"))

    response = client.get("/api/runtime/activity")

    assert response.status_code == 200
    data = response.json()
    assert data["phase"] == "downloading"
    assert data["message"] == "Downloading ACE-Step asset: 2.17G/4.79G (45%)"
    assert "api_running" in data
