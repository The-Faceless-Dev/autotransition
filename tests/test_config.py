from autotransition.config import TransitionConfig


def test_transition_config_computes_repaint_timing() -> None:
    config = TransitionConfig(
        context_seconds=20.0,
        repaint_overlap_seconds=4.0,
        new_section_seconds=32.0,
    )

    assert config.tail_seconds == 24.0
    assert config.scaffold_seconds == 56.0
    assert config.repainting_start_seconds == 20.0
