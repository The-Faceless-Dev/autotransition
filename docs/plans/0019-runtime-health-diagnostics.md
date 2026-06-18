# Runtime Health Diagnostics Plan

## Problem

The UI can report `ACE-Step API is not running` even after the user has waited for startup. That message is too generic and does not distinguish between:

- the API process is still booting
- the configured host/port is wrong
- the health endpoint is returning an HTML/proxy page
- the health endpoint is returning a non-200 status
- generation is using a different runtime config than the UI status panel

## Approach

- Add a health detail helper that returns both readiness and the reason.
- Use the health detail in runtime status and doctor messages.
- Pass the UI runtime config into the ACE-Step repaint adapter so generation checks the same host/port the UI displays.
- Keep existing defaults unchanged for simple local use.
- Add regression tests for health detail and config propagation.

## Affected Files

- `src/autotransition/runtime/ace_step.py`
- `src/autotransition/models/acestep.py`
- `src/autotransition/ui/app.py`
- `tests/test_runtime.py`
- `tests/test_ui_api.py`

## Tradeoffs and Risks

- Health diagnostics are still limited to what `/health` and connection errors expose.
- This does not make ACE-Step faster; it makes not-ready and misconfigured states explicit.
