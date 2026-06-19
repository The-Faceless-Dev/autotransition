# Debug ACE-Step Repaint Quality Plan

## Problem

Generated repaint continuations are garbled across multiple ACE-Step models, including 1.5 Base and XL SFT. Because the failure reproduces across model families, this likely points to Autotransition's scaffold or API parameter usage rather than a single bad model.

## Research Approach

- Compare Autotransition's repaint request payload against ACE-Step's official API docs and local runtime implementation.
- Compare Autotransition's scaffold shape against ACE-Step's repaint expectations.
- Inspect ACE-Step's request parser and generation setup for parameters that affect repaint masks, source audio, and duration.
- Patch the integration only after identifying a concrete mismatch.

## Finding

Autotransition was relying on ACE-Step's default `chunk_mask_mode`, which is `auto`. In the local ACE-Step runtime, `auto` replaces the explicit repaint range with an automatic full-track mask, so the selected repaint boundary is not guaranteed to be respected. That is a bad fit for Autotransition's scaffold shape of real source tail followed by blank continuation space.

Autotransition also generated the blank scaffold tail with only the source frame rate preserved. Matching the selected source segment's channel count and sample width removes another avoidable mismatch before the scaffold is sent to ACE-Step.

## Implementation

- Send `chunk_mask_mode=explicit` on ACE-Step repaint requests.
- Use ACE-Step's balanced repaint strength rather than extra-conservative source preservation for the blank future region.
- Build scaffold silence with the same frame rate, channels, and sample width as the selected source segment.
- Add tests for the request payload and scaffold audio layout.

## Likely Areas

- Repaint start/end boundaries relative to source scaffold duration.
- Silence scaffold causing ACE-Step to preserve or condition on silence incorrectly.
- Missing or wrong repaint mode/strength/crossfade values.
- Wrong field names or defaults for uploaded source audio.
- Duration mismatch between scaffold length and `audio_duration`.

## Affected Files

Likely:

- `src/autotransition/models/acestep_api.py`
- `src/autotransition/audio/selection.py`
- `src/autotransition/pipeline/source_selection.py`
- related tests

## Risks

- ACE-Step behavior may differ between local API and Gradio UI paths.
- Quality validation still requires listening, but request/scaffold correctness can be tested structurally.
