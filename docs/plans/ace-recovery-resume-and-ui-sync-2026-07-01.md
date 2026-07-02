## Goal

Tighten ACE-Step crash recovery so the UI reflects the real runtime state and interrupted extraction jobs resume automatically after recovery instead of being dropped.

## Problem

Current recovery behavior is better than before, but still incomplete:

1. The backend can recover the ACE runtime, but the UI can remain stuck in a stale "Recovering" state.
2. If ACE crashes in the middle of an extraction, the runtime comes back, but the interrupted extraction request is not retried.
3. The user therefore loses the in-flight extraction even though recovery succeeded.

## Approach

1. Add a small runtime recovery job queue for resumable ACE operations:
   - start with base-model track extraction only
   - capture the request payload and output destination before dispatch
   - when the runtime crashes and recovery starts, mark the job as pending retry
   - when recovery completes, retry the queued extraction automatically

2. Add extraction job state to backend responses:
   - queued for retry
   - retrying
   - recovered and completed
   - recovery failed

3. Tighten UI/runtime state synchronization:
   - poll runtime status while recovery is active
   - stop showing "Recovering" immediately when backend recovery state is no longer active
   - show whether the interrupted extraction is waiting to retry, retrying now, or failed after recovery

4. Keep scope narrow:
   - do not attempt to resume every ACE operation yet
   - implement robustly for track extraction first, since that is the crashing path under active investigation

## Affected Files

- `src/autotransition/runtime/ace_step.py`
- `src/autotransition/ui/app.py`
- `src/autotransition/ui/activity.py`
- `src/autotransition/ui/static/app.js`

## Tradeoffs

- Retrying automatically is better UX, but it means the backend owns a small amount of in-memory recovery state.
- If the process exits fully, in-memory retry state is lost. That is acceptable for now; the goal is surviving runtime crashes without restarting the app.
- Restricting resume to extraction first keeps risk down and avoids building a generic queue prematurely.

## Risks

- A retry loop could repeat forever if the runtime keeps crashing on the same request.
- UI and backend state could diverge again if retry state is not surfaced clearly.
- If the retried extract writes to the same output path incorrectly, metadata could become inconsistent.

## Validation

- Start an extraction, force the ACE runtime crash path, confirm:
  - UI shows recovery
  - recovery completes
  - extraction retries automatically
  - extracted track appears without restarting the app
- Confirm stale recovery banners clear once runtime status says ready
