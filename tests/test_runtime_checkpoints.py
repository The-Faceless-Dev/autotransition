from pathlib import Path

from autotransition.config import RuntimeConfig
from autotransition.models.registry import get_model_profile
from autotransition.runtime.checkpoints import checkpoint_has_weights, repair_incomplete_checkpoint


def test_checkpoint_has_weights_requires_final_weight_file(tmp_path: Path) -> None:
    checkpoint = tmp_path / "acestep-v15-base"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text("{}", encoding="utf-8")
    (checkpoint / "._____temp").mkdir()
    (checkpoint / "._____temp" / "model.safetensors").write_text("partial", encoding="utf-8")

    assert not checkpoint_has_weights(checkpoint)


def test_repair_incomplete_checkpoint_moves_folder(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "ACE-Step-1.5"
    checkpoint = runtime_dir / "checkpoints" / "acestep-v15-base"
    checkpoint.mkdir(parents=True)
    (checkpoint / "config.json").write_text("{}", encoding="utf-8")
    quarantine_root = tmp_path / "quarantine"

    result = repair_incomplete_checkpoint(
        get_model_profile("acestep-v15-base"),
        RuntimeConfig(ace_step_dir=runtime_dir),
        quarantine_root=quarantine_root,
    )

    assert result.repaired
    assert not checkpoint.exists()
    assert result.quarantine_path is not None
    assert (result.quarantine_path / "config.json").exists()


def test_repair_incomplete_checkpoint_leaves_complete_folder(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "ACE-Step-1.5"
    checkpoint = runtime_dir / "checkpoints" / "acestep-v15-base"
    checkpoint.mkdir(parents=True)
    (checkpoint / "model.safetensors").write_text("weights", encoding="utf-8")

    result = repair_incomplete_checkpoint(
        get_model_profile("acestep-v15-base"),
        RuntimeConfig(ace_step_dir=runtime_dir),
        quarantine_root=tmp_path / "quarantine",
    )

    assert not result.repaired
    assert checkpoint.exists()
    assert (checkpoint / "model.safetensors").exists()
