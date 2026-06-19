# Handle ACE-Step HTTP Timeouts Plan

## Problem

Generation can crash the FastAPI route with a 500 when an ACE-Step HTTP call times out. The observed failure timed out during `/v1/init` while ACE-Step was initializing/loading a model:

```text
httpx.ReadTimeout: timed out
```

This bypasses `AceStepApiError`, so the UI sees an internal server error instead of a normal failed/in-progress generation message.

## Approach

- Use the long generation timeout for `/v1/init`, `/release_task`, and `/query_result` calls that may block while ACE-Step loads or generates.
- Wrap `httpx` transport exceptions in `AceStepApiError` with operation context.
- Keep `/v1/models` on the short API timeout because it is a readiness/listing check.
- Add regression coverage for timeout wrapping.

## Affected Files

- `src/autotransition/models/acestep_api.py`
- `tests/test_acestep_api.py`

## Tradeoffs and Risks

- Blocking requests can keep the generate endpoint open longer. That is already how the current synchronous generation flow works.
- A future queue-based backend would improve this, but this fix prevents crashes now.
