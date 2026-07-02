## Goal

Make ACE-Step base-model extraction failures survivable in Dance Station so a Windows runtime crash does not leave the user with a dead workflow and no explanation.

## Problem

Current behavior during base-model track extraction:

1. ACE-Step can crash natively inside its Windows/PyTorch offload path during repeated extract runs.
2. The backend catches the resulting API failure, writes failed extraction metadata, and still returns `200 OK`.
3. The UI refreshes as if extraction completed, but no track appears.
4. Once the runtime is down, the user is left to manually restart the full app.

## Approach

1. Add a small ACE runtime recovery helper in the runtime layer:
   - detect when the API is no longer reachable
   - detect whether the managed runtime PID is dead or stale
   - restart the ACE runtime in the background when safe
   - expose a clear recovery status/message for the UI

2. Tighten extraction failure handling:
   - when ACE extract fails because the runtime is unreachable or died mid-request, return a non-success API result instead of a silent `200`
   - distinguish:
     - runtime crashed / unavailable
     - runtime is being restarted
     - extraction task itself failed while runtime stayed alive

3. Surface recovery state in the UI:
   - show when ACE runtime is reloading after a crash
   - disable extraction/generation actions while recovery is in progress
   - display a direct message instead of making the user infer failure from missing output

4. Reduce recurrence of the crashing path:
   - apply a Windows-specific mitigation for the base extract path by changing runtime/offload behavior conservatively
   - keep the change scoped to extraction/runtime stability work

## Affected Files

- `src/autotransition/runtime/ace_step.py`
- `src/autotransition/ui/app.py`
- `src/autotransition/ui/activity.py`
- `src/autotransition/ui/static/app.js`
- `src/autotransition/ui/static/index.html`
- `src/autotransition/ui/static/styles.css`

## Tradeoffs

- Automatic runtime restart is better UX, but it adds statefulness and requires careful handling of stale PID files.
- Returning a real failure for extract requests may expose issues users were previously “shielded” from, but that is the correct behavior.
- Offload mitigation may cost some memory headroom or change runtime performance, but stability is the priority for repeated extraction.

## Risks

- Restart logic could fight with an already-starting runtime if not guarded properly.
- If ACE-Step crashes for a deeper upstream bug unrelated to offload, restart alone will not fully solve the issue.
- UI polling must not spam restart attempts.

## Validation

- Repeated base extract requests after successful earlier extracts
- Confirm runtime crash becomes visible as a recovery state
- Confirm runtime can come back without restarting the full app
- Confirm actions stay disabled while recovery is active
