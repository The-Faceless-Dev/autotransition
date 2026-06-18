# Generation Progress Feedback Plan

## Goal

Make the UI clearly show what is happening after the user clicks `Generate Transition`, especially during long first-run ACE-Step model downloads and model initialization.

## Problem

The browser sends one long blocking request to `/api/generate/from-selection`. While that request is pending, the UI only shows `Generating`. The logs panel is polled on a timer, but the current flow does not surface ACE-Step runtime logs or download progress in the generation area, so users cannot tell whether generation is active, downloading, stuck, or failed.

## Approach

1. Add a UI-facing runtime activity endpoint that summarizes:
   - ACE-Step API health
   - latest ACE-Step stdout/stderr lines
   - detected model download progress when present
   - current high-level phase such as `downloading`, `initializing`, `generating`, `complete`, or `error`
2. While `Generate Transition` is pending, poll logs/runtime activity every few seconds.
3. Update the action state and output panel with the latest useful status, for example:
   - `Downloading ACE-Step model: 3.00G/4.79G (63%)`
   - `ACE-Step API is initializing models`
   - `Waiting for generated audio`
4. Keep the existing synchronous backend generation path for now to avoid a larger queue refactor.
5. Add backend parsing helpers and tests for common ACE-Step progress lines.

## Affected Files

- `src/autotransition/ui/app.py`
- `src/autotransition/ui/static/app.js`
- `src/autotransition/ui/static/index.html`
- `src/autotransition/ui/static/styles.css` if the generation status needs dedicated layout
- `tests/test_ui_api.py`

## Tradeoffs

This keeps implementation small by polling server-side log summaries instead of building a full job queue. A queue would be better long-term, but it is a larger architecture change. This plan gives users immediate visibility without changing the generation contract.

## Risks

ACE-Step progress output can change format. The parser should be defensive and fall back to showing the latest log line instead of failing.
