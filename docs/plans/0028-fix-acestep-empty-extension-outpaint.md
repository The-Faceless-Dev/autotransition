# Fix ACE-Step Empty Extension Outpaint Plan

## Problem

Empty-extension generation still produces garbled speech/random audio. Research shows Autotransition is using ACE-Step repaint incorrectly for outpainting.

## Findings

- ACE-Step repaint can extend beyond source audio, but its runtime only creates right-side outpaint padding when `repainting_end` is greater than the uploaded source audio duration.
- Autotransition currently uploads a scaffold that already contains appended silence and sends `repainting_end=-1`.
- In ACE-Step, `repainting_end=-1` means "to the end of uploaded source audio." Because our uploaded source already includes silence, ACE-Step treats that silence as real source material instead of invoking its outpaint padding path.
- ACE-Step repaint ignores `audio_duration` for repaint tasks and locks duration to source/padded source duration internally.
- ACE-Step docs state repaint operation range is 3 to 90 seconds. Some Autotransition presets are within this range, but the app should avoid implying arbitrarily long blank repaint spans are reliable.
- ACE-Step treats empty lyrics as instrumental, but we should still make lyrics/vocal intent configurable later because vocal artifacts can happen when prompt/lyrics/vocal-language intent is ambiguous.

## Approach

- For `Extend after marker`, upload only the real source tail (`context + overlap`) with no appended silence.
- Set `repainting_end` to `context + overlap + new_section_seconds` so ACE-Step pads the right side internally and performs actual outpainting.
- Keep `Repaint existing audio` as the full source-tail-plus-existing-target scaffold path, with `repainting_end=-1` or an explicit scaffold end because that mode intentionally repaints existing non-empty source.
- Record the effective scaffold target mode and repaint end in plan metadata.
- Update UI copy/readouts if needed so "Extend after marker" reflects ACE-Step outpainting rather than prebuilt silence.
- Make runtime checkpoint validation less brittle so app-installed/runtime-installed model folders are not repeatedly quarantined when they use a valid sharded safetensors/bin layout.
- Improve checkpoint repair messages so future warnings say what file pattern was missing.

## Affected Files

- `src/autotransition/audio/selection.py`
- `src/autotransition/pipeline/source_selection.py`
- `src/autotransition/models/acestep_api.py`
- `src/autotransition/runtime/checkpoints.py`
- `src/autotransition/ui/app.py`
- tests for source selection, scaffold construction, and ACE-Step payloads

## Tests

- Extend mode writes only real selected tail to the uploaded scaffold.
- Extend mode sends a positive `repainting_end` equal to tail length plus new-section seconds.
- Existing-audio repaint still includes source audio after the marker.
- ACE-Step payload respects plan `repainting_end_seconds` instead of hardcoding `-1`.
- Checkpoint validation accepts top-level `*.safetensors`, `*.bin`, and index-backed sharded model folders.

## Risks

- Existing generated metadata/scaffold expectations change for extend mode.
- ACE-Step quality can still vary by prompt/model/seed, but this fixes the concrete outpaint API misuse.
