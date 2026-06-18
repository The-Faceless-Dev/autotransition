from pathlib import Path

import pytest

from autotransition.models import InstallState, ModelInstallError, install_model, resolve_model_status


def test_resolve_model_status_reports_missing_model(tmp_path: Path) -> None:
    status = resolve_model_status("acestep-v15-turbo", models_dir=tmp_path)

    assert status.state == InstallState.NOT_INSTALLED
    assert status.local_path == tmp_path / "acestep-v15-turbo"


def test_resolve_model_status_reports_ready_model(tmp_path: Path) -> None:
    model_dir = tmp_path / "acestep-v15-turbo"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    status = resolve_model_status("acestep-v15-turbo", models_dir=tmp_path)

    assert status.state == InstallState.READY


def test_install_model_uses_hugging_face_snapshot_download(tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def fake_snapshot_download(**kwargs: object) -> str:
        calls.append(kwargs)
        local_dir = Path(kwargs["local_dir"])
        local_dir.mkdir(parents=True)
        (local_dir / "model.safetensors").write_text("fake", encoding="utf-8")
        return str(local_dir)

    status = install_model("acestep-v15-turbo", models_dir=tmp_path, snapshot_download=fake_snapshot_download)

    assert status.state == InstallState.READY
    assert status.local_path == tmp_path / "acestep-v15-turbo"
    assert calls[0]["repo_id"] == "ACE-Step/Ace-Step1.5"


def test_install_model_wraps_download_failures(tmp_path: Path) -> None:
    def failing_snapshot_download(**_: object) -> str:
        raise OSError("network down")

    with pytest.raises(ModelInstallError, match="Failed to download"):
        install_model("acestep-v15-turbo", models_dir=tmp_path, snapshot_download=failing_snapshot_download)
