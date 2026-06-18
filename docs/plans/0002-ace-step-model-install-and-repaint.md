# ACE-Step Model Install and Repaint Plan

## Goal

Add ACE-Step model management and repaint generation support while keeping the app user-friendly and configurable.

Users should be able to:

1. Pick an ACE-Step model/profile in the UI.
2. Manually install/download that model from Hugging Face before generating.
3. Let the app automatically download the selected model during generation if it is missing.
4. Use any ACE-Step version/profile that supports repaint, not only one hardcoded checkpoint.

## Research Notes

As of June 18, 2026, ACE-Step 1.5 documents repaint support across the main 2B DiT model family:

- `acestep-v15-base`
- `acestep-v15-sft`
- `acestep-v15-turbo`

The 1.5 XL family also lists repaint support:

- `acestep-v15-xl-base`
- `acestep-v15-xl-sft`
- `acestep-v15-xl-turbo`

The XL docs warn that XL models need more VRAM, with lower-end support relying on CPU offload and quantization. The app should surface this clearly before users download large checkpoints.

## Intended Approach

1. Add a model registry layer.
   - Store model display name, Hugging Face repo id, local directory, repaint support, recommended VRAM tier, default inference steps, and notes.
   - Keep this registry editable and separate from inference code.
2. Add model install/download service.
   - Use `huggingface_hub` rather than shelling out to `huggingface-cli`.
   - Support explicit install from UI/CLI.
   - Support lazy install when generation starts and the selected model is missing.
   - Track install status, download progress, local path, and errors in UI-friendly state.
3. Add ACE-Step runtime adapter.
   - Convert existing `ScaffoldPlan` metadata into ACE-Step repaint parameters.
   - Use `src_audio`, `task_type="repaint"`, `repainting_start`, `repainting_end=-1`, and caption from the plan.
   - Keep runtime settings configurable: device, offload, quantization, inference steps, seed, guidance/CFG, and output format.
4. Add UI/API-ready state objects.
   - Model not installed
   - Downloading
   - Ready
   - Generating
   - Failed with actionable message
5. Add CLI commands as a backend proving ground before the full UI.
   - `autotransition models list`
   - `autotransition models install <model-slug>`
   - `autotransition generate --model <model-slug> ...`

## Proposed Files

- `src/autotransition/models/registry.py`
  - ACE-Step model profile definitions.
- `src/autotransition/models/download.py`
  - Hugging Face download/install service.
- `src/autotransition/models/acestep.py`
  - ACE-Step repaint adapter.
- `src/autotransition/models/status.py`
  - Serializable model install/generation status objects.
- `src/autotransition/config.py`
  - Extend with model cache path and runtime defaults.
- `src/autotransition/cli.py`
  - Add model install/list and repaint generation commands.
- `docs/model-management.md`
  - Explain manual install, auto install, storage paths, VRAM expectations, and Hugging Face access.
- `tests/`
  - Registry tests, missing-model behavior, and mocked download behavior.

## Dependencies

Proposed new dependency:

- `huggingface_hub`
  - Needed for reliable programmatic model downloads, cache control, progress reporting, and future auth/private-token handling.

Do not add the full ACE-Step runtime dependency until the adapter is implemented against the official package/API shape. That dependency may be heavy and may need optional install groups.

## UI Expectations

The UI should not ask users to understand repo IDs first.

It should show:

- Friendly model names
- Quality/speed labels
- Approximate download size when known
- VRAM guidance
- Repaint support indicator
- Install button
- Installed/ready status
- Automatic install prompt before first generation
- Clear failure states for network, disk space, missing Hugging Face auth, or unsupported hardware

Advanced users should still be able to enter a custom Hugging Face repo id if it declares repaint support or if they explicitly override compatibility checks.

## Tradeoffs

- A curated registry gives non-technical users safe choices, but a custom repo option keeps the tool hackable.
- Lazy download improves first-run experience, but the UI must ask before downloading very large models.
- `huggingface_hub` adds a dependency, but it avoids brittle subprocess parsing and gives better integration for UI progress.
- Supporting all repaint-capable ACE-Step versions means the adapter must separate model capability metadata from generation workflow logic.

## Risks

- ACE-Step package APIs may change between versions.
- Model sizes and hardware requirements vary substantially.
- Hugging Face downloads can fail due to network, auth, rate limits, disk space, or interrupted transfers.
- Custom models may claim compatibility but fail at runtime.
- Automatic install can surprise users if download size is not shown clearly.

## Validation

- Unit-test registry capability filtering for repaint models.
- Unit-test install-state transitions with mocked Hugging Face downloads.
- Unit-test lazy install behavior when generation requests a missing model.
- Integration-test CLI model listing.
- After ACE-Step runtime is added, test repaint against a tiny local scaffold and verify output metadata records model slug, repo id, local path, seed, repaint start/end, and runtime settings.

## Approval Needed

Implementation should wait until this plan is approved or revised.
