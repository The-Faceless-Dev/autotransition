# ACE-Step Extend Generation UI Plan

## Goal

Make generation the user-facing workflow, with scaffold creation handled internally:

1. User loads/selects source audio.
2. User chooses the continuation point and prompt/settings.
3. User clicks `Generate Transition`.
4. App builds the necessary scaffold in the background.
5. App runs ACE-Step repaint using that scaffold.
6. UI shows generated output candidates, logs, and output paths.

The current app exposes scaffold creation as the main action. That should be demoted to an internal debug/detail artifact. The app is for getting generated transition results, not for making scaffolds.

## User Experience

The primary action should be:

- `Generate Transition`

The UI can still show scaffold path and metadata in a details/output panel after generation starts or completes, but users should not need to understand or manually create scaffolds.

The button should be disabled until:

- A source file is loaded.
- A continuation point is selected.
- A repaint-capable ACE-Step model is selected.
- The selected model is installed, or the user allows auto-install.

If the model is missing, the button area should offer:

- `Install Model`
- `Install Then Generate`

Generation status should show:

- Preparing model
- Downloading model, if needed
- Running repaint
- Writing output
- Complete or failed

## Backend Behavior

Add a generation endpoint that does scaffold preparation internally:

- `POST /api/generate/from-selection`

Input:

- source path
- continuation point seconds
- preset/caption/settings
- selected model slug
- auto-install flag
- runtime options:
  - inference steps
  - seed
  - device
  - offload
  - quantization

Output:

- generation id
- internal scaffold path
- internal scaffold metadata path
- model slug
- generated audio path
- generated metadata path
- logs/status

## ACE-Step Runtime Adapter

Implement a runtime adapter behind the existing model interface:

- Load the selected ACE-Step profile from the local model path.
- Run repaint with:
  - `task_type="repaint"`
  - `src_audio=<scaffold path>`
  - `repainting_start=<metadata repainting_start_seconds>`
  - `repainting_end=-1`
  - `caption=<metadata caption>`
  - `duration=<scaffold duration or requested duration when required>`
  - seed and runtime settings

The adapter must not hardcode one model path. It should use the selected model profile and local install path.

## Important Unknowns

The exact ACE-Step Python API needs to be confirmed against the installed/runtime package before coding the real adapter.

If the official package is not installed yet, implement this in two phases:

1. UI and API generation flow with clear “ACE-Step runtime not installed” errors.
2. Real runtime adapter once the ACE-Step package/install method is confirmed.

Do not fake successful audio generation.

## Proposed Files

- `src/autotransition/generation/`
  - Generation request/status/result objects.
- `src/autotransition/models/acestep.py`
  - ACE-Step repaint adapter.
- `src/autotransition/ui/app.py`
  - Add generation endpoint.
- `src/autotransition/ui/static/index.html`
  - Replace scaffold-first actions with `Generate Transition` and candidates/output area.
- `src/autotransition/ui/static/app.js`
  - Call generation endpoint directly from loaded source selection.
- `src/autotransition/ui/static/styles.css`
  - Generation status and candidate output styling.
- `docs/ace-step-runtime.md`
  - Explain how ACE-Step runtime is installed/configured.
- `tests/`
  - Generation request validation, missing runtime behavior, missing model behavior.

## UI States

- No scaffold yet
- Source not loaded
- Selection ready
- Model missing
- Installing model
- Ready to generate
- Preparing scaffold
- Generating
- Output ready
- Failed

## Risks

- ACE-Step runtime may be heavy or require GPU-specific dependencies.
- The official API may differ by version.
- Model downloads can be very large.
- Generation can take long enough that a synchronous HTTP request may be a poor fit.

## First Implementation Scope

For the first pass, add the complete UI/API path and robust status/errors. The endpoint should build the scaffold internally and then attempt real generation only if ACE-Step runtime is available and callable.

If the runtime is missing, the UI should say exactly that and point to the docs instead of silently doing nothing.

## Approval Needed

Implementation should wait until this plan is approved or revised.
