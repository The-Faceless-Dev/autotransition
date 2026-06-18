# Repair Incomplete ACE Checkpoints Plan

## Goal

Prevent ACE-Step initialization failures caused by incomplete checkpoint folders left behind by interrupted or failed downloads.

## Problem

ACE-Step's API-side downloader can treat a non-empty checkpoint directory as installed even when it has no final model weights. In the observed failure, `checkpoints/acestep-v15-base` contained config/code files and `._____temp/model.safetensors`, but no final `model.safetensors`, so `AutoModel.from_pretrained` failed during initialization.

## Approach

1. Add an Autotransition runtime checkpoint validation helper.
2. Before requesting ACE-Step `/v1/init`, check the selected ACE-Step runtime checkpoint folder.
3. If the folder exists but contains no recognized model weight file, move it to a quarantine directory under `data/runtime/broken-checkpoints/`.
4. Let ACE-Step perform a fresh download on the next `/v1/init`.
5. Keep complete folders untouched.
6. Add tests for complete, missing, and incomplete checkpoint detection.

## Affected Files

- `src/autotransition/runtime/checkpoints.py`
- `src/autotransition/models/acestep_api.py`
- `tests/test_runtime_checkpoints.py`

## Tradeoffs

Quarantining instead of deleting preserves evidence for debugging while still unblocking a fresh download. This can require re-downloading a large partially downloaded model, but it is safer than leaving the app stuck on an unusable checkpoint.

## Risks

If a download is actively in progress and the app validates the same folder concurrently, it could quarantine active partial files. The helper should only run immediately before model initialization and should consider only folders without final weights incomplete.
