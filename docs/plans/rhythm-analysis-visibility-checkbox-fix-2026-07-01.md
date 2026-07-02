# Rhythm Analysis Visibility Checkbox Fix

## Problem

In Rhythm Beat Lab, checking `Show on chart` for later analyses does not stick. The first analysis remains the only visible one, and the checkboxes appear not to check.

## Likely Cause

Two frontend state issues overlap:

1. The visibility checkbox sits inside a clickable analysis row, so checkbox interaction can bubble into the row click handler and trigger an immediate rerender.
2. Project load currently resets `visibleRhythmAnalysisIds` to all analyses every time the project is reloaded, which can overwrite user visibility choices.

## Approach

1. Stop checkbox interaction from bubbling into the row-level selection handler.
2. Preserve visible-analysis state across project reloads for the same project, trimming only removed analysis ids.
3. Keep selected analysis behavior intact.

## Files

- `src/autotransition/ui/static/app.js`

## Risk

- Low. This is scoped to Rhythm Beat Lab frontend state handling.
