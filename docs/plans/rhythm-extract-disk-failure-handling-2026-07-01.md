# Rhythm Extract Disk Failure Handling

## Problem

Rhythm Beat Lab track extraction can report success even when no extracted audio was produced.

Two concrete failure modes were observed on Windows:

1. ACE-Step finishes diffusion but fails to save the output audio because the drive is full.
2. ACE-Step fails earlier while parsing the upload request because the temp directory is on a full drive.

Current UI behavior is misleading because the rhythm extraction action marks the result as `Extracted` whenever the request returns `200`, even if the backend payload says the extraction `status` is `failed`.

## Root Cause

- `D:` is effectively full, so ACE-Step cannot reliably write temp uploads or output audio.
- Backend extraction metadata already captures failure in these cases.
- Frontend rhythm extraction flow does not branch on `response.extraction.status === "failed"` and incorrectly shows success.
- There is no preflight disk-space guard before launching extraction.

## Proposed Changes

1. Add backend disk-space preflight before ACE extraction starts.
   - Fail fast with a clear error when free space is below a conservative threshold.
   - Include the current free-space amount in the message.

2. Tighten extraction result validation.
   - Treat missing output audio path or missing output file as extraction failure.
   - Keep failure metadata explicit and consistent.

3. Fix Rhythm Beat Lab UI handling.
   - Show success only when `response.extraction.status` is actually `complete`.
   - Show error toast/pill for `failed`.
   - Keep `recovering` behavior as-is.

4. Improve user-facing messaging.
   - Surface "no space left on device" as a direct actionable error instead of a generic completed state.

## Files

- `src/autotransition/ui/app.py`
- `src/autotransition/ui/static/app.js`
- optionally a small helper in an existing utility module if disk-space checks should be reused

## Risks

- Disk-space threshold that is too aggressive could block valid work on small drives.
- Disk-space threshold that is too small could still allow late-stage save failures.

## Tradeoffs

- A conservative preflight will reject some borderline extractions earlier, but that is preferable to spending GPU time and then failing during save.
- This does not solve the underlying storage shortage; it makes the failure explicit and prevents false success.

## Immediate User Action

Free several GB on `D:` before retrying base extraction. Current free space is about 8 MB, which is not enough for request temp files plus extracted audio output.
