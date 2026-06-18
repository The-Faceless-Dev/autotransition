from pathlib import Path

import pytest

from autotransition.config import OutputConfig, TransitionConfig
from autotransition.pipeline import SourceSelectionRequest, create_source_selection_plan


def test_source_selection_plan_extracts_tail_before_marker(tmp_path: Path) -> None:
    config = TransitionConfig(
        context_seconds=10.0,
        repaint_overlap_seconds=2.0,
        new_section_seconds=24.0,
        output=OutputConfig(scaffold_dir=tmp_path / "scaffolds"),
    )

    plan = create_source_selection_plan(
        SourceSelectionRequest(
            source_path=Path("song.wav"),
            source_duration_seconds=180.0,
            continuation_point_seconds=60.0,
            caption="continue",
            config=config,
            transition_id="selected",
        )
    )

    assert plan.tail_start_seconds == 48.0
    assert plan.tail_end_seconds == 60.0
    assert plan.source_extension == ".wav"
    assert plan.source_format == "WAV"
    assert plan.requested_continuation_seconds == 24.0
    assert plan.scaffold_path == tmp_path / "scaffolds" / "selected" / "scaffold.wav"


def test_source_selection_rejects_marker_too_early() -> None:
    config = TransitionConfig(context_seconds=10.0, repaint_overlap_seconds=4.0)

    with pytest.raises(ValueError, match="too early"):
        create_source_selection_plan(
            SourceSelectionRequest(
                source_path=Path("song.wav"),
                source_duration_seconds=180.0,
                continuation_point_seconds=8.0,
                caption="continue",
                config=config,
            )
        )
