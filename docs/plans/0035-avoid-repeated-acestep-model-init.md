# Avoid Repeated ACE-Step Model Initialization

## Problem

Text generation can repeatedly call `/v1/init` with `init_llm=true`. ACE-Step's init route initializes the DiT and then initializes the LM; repeated calls can accumulate or fragment CUDA allocations inside the long-lived runtime process. The user hit an OOM after a few generations with almost all VRAM held by the ACE-Step process.

The current model check also treats installed models from `/v1/models` as available, even when they are not loaded.

## Approach

- Parse `/v1/models` as runtime inventory, distinguishing installed models from loaded models.
- Skip `/v1/init` when the selected DiT is loaded and the requested LM is already initialized.
- Keep calling `/v1/init` when the selected DiT is not loaded, the LM is not initialized, or the loaded LM does not match the requested LM.
- Add regression tests for the text-generation fast path.

## Affected Files

- `src/autotransition/models/acestep_api.py`
- `tests/test_acestep_api.py`

## Risks

- If an older ACE-Step runtime omits `is_loaded` from `/v1/models`, the client will conservatively initialize rather than assuming readiness.
- Switching LM models still requires reinitialization and may require a runtime restart if ACE-Step cannot free the previous LM cleanly.
