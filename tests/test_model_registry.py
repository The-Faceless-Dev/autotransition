import pytest

from autotransition.models import get_model_profile, repaint_capable_models


def test_repaint_capable_models_only_include_repaint_profiles() -> None:
    profiles = repaint_capable_models()

    assert profiles
    assert all(profile.supports_repaint for profile in profiles)
    assert "acestep-v15-turbo" in {profile.slug for profile in profiles}
    assert "acestep-v15-xl-turbo" in {profile.slug for profile in profiles}


def test_unknown_model_lists_available_options() -> None:
    with pytest.raises(ValueError, match="Available models"):
        get_model_profile("missing")
