# Base Extract Runtime Recycle

## Problem

On Windows with a 10 GB GPU, repeated ACE-Step base-model extractions can leave the system paging volume in a bad state even when the extraction itself succeeds. The process may free tensors, but Windows does not reliably return pagefile pressure between runs.

This leads to follow-on failures such as:

- `No space left on device`
- extract requests that fail during temp upload handling
- extract requests that finish diffusion but cannot save output audio

## Approach

Recycle the ACE-Step runtime after each base extraction on Windows.

Instead of relying only on in-process cleanup, terminate and restart the ACE runtime after the extraction result has been recorded. This forces the memory-heavy process to exit and gives Windows a clean chance to release committed memory and paging pressure.

## Changes

1. Add a runtime recycle helper in `src/autotransition/runtime/ace_step.py`
   - restart even when the runtime is still healthy
   - expose recycle state through the same recovery-state mechanism already used for crash recovery

2. Trigger runtime recycle after base extraction in `src/autotransition/ui/app.py`
   - after successful extract completion
   - after non-crash extract failure
   - do not interfere with the existing crash-recovery path

3. Fix extraction UI state in `src/autotransition/ui/static/app.js`
   - Rhythm Beat Lab must not mark failed extract responses as success
   - if extraction completed and runtime recycle is active, show recovering/restarting state instead of idle success

## Files

- `src/autotransition/runtime/ace_step.py`
- `src/autotransition/ui/app.py`
- `src/autotransition/ui/static/app.js`

## Tradeoffs

- Base extraction requests on Windows will pay a restart cost after each run.
- This is heavier than in-process cleanup, but it is much more reliable for pagefile release.
- This is not a full dedicated worker architecture, but it is the shortest reliable step toward the same outcome.

## Risk

- If users queue extractions back-to-back, the second one may land while the runtime is restarting. The UI therefore needs to surface recovery/restarting state clearly and disable actions while ACE is unavailable.
