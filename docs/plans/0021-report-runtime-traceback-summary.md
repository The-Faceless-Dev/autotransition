# Report Runtime Traceback Summary Plan

## Problem

When ACE-Step crashes during startup, Autotransition can report only:

```text
ACE-Step startup: error - Traceback (most recent call last):
```

That line confirms a Python crash, but it hides the useful exception line at the bottom of the traceback.

## Approach

- Update runtime activity summarization to detect traceback blocks.
- Report the final exception line from the traceback as the primary error message.
- Keep recent log lines available for UI/log inspection.
- Add regression coverage for traceback summarization.

## Affected Files

- `src/autotransition/ui/activity.py`
- `tests/test_ui_activity.py`

## Tradeoffs and Risks

- Traceback parsing is best-effort. If logs are truncated mid-traceback, the parser will still fall back to the latest traceback/error line.
