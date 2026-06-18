import pytest

from autotransition.presets import PRESETS, get_preset


def test_expected_presets_exist() -> None:
    assert "smooth-continuation" in PRESETS
    assert "energy-build" in PRESETS
    assert "dj-bridge" in PRESETS


def test_unknown_preset_lists_available_options() -> None:
    with pytest.raises(ValueError, match="Available presets"):
        get_preset("missing")
