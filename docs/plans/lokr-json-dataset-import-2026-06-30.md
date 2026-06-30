# LoKr JSON Dataset Import 2026-06-30

## Goal

Allow users to import dataset JSON into both LoKr Training and Dataset Editor, even when entries do not yet include valid audio locations.

## Current State

Datasets can currently be created by:

- creating an empty dataset shell
- uploading audio files
- adding existing creation assets
- editing and saving dataset entries in the UI

There is no import path for external dataset JSON.

## Required Import Behavior

The incoming JSON may contain only a minimal shape per entry:

- `name`
- `caption`

But import should also accept richer per-entry fields when present:

- `lyrics`
- `audio location`
- `genre`
- `language`
- `bpm`
- `keyscale`
- `timesignature`
- `custom_tag`
- `prompt_override`
- other compatible entry metadata

Audio locations in the imported JSON are optional and may be missing or unusable.

## Intended Change

### Backend

- Add JSON import endpoints for LoKr datasets.
- Accept uploaded `.json` files in:
  - LoKr Training
  - Dataset Editor
- Parse the input into the project’s normalized dataset shape.
- Support multiple common entry keys:
  - `name` -> label fallback
  - `label`
  - `caption`
  - `lyrics`
  - `audio_path` / `audio` / `audio_location`
  - `genre`
  - `language`
  - `bpm`
  - `keyscale`
  - `timesignature`
- If audio path is missing or cannot be resolved, keep the entry as draft/missing-audio rather than rejecting the whole import.

### Import modes

- Import into a newly created dataset
- Import into the currently selected dataset by appending entries

### Validation

- Imported entries without usable audio remain valid drafts.
- Existing missing-audio validation for preprocess/train remains the execution gate.

## Files Likely Affected

- `src/autotransition/ui/app.py`
- `src/autotransition/ui/static/app.js`
- `src/autotransition/ui/static/index.html`

## Implementation Approach

1. Add backend helpers to normalize external JSON entry shapes into the internal LoKr dataset entry shape.
2. Add import endpoints:
   - create dataset from JSON
   - append JSON entries into existing dataset
3. Reuse the current dataset cleaner so imported entries and manual entries behave the same.
4. Add UI controls in both LoKr Training and Dataset Editor for JSON import.
5. Refresh dataset state after import and surface missing-audio counts immediately.

## Tradeoffs

### Pros

- supports real dataset preparation workflows outside Dance Station
- avoids forcing users to rebuild dataset metadata manually
- stays compatible with incomplete imported datasets

### Cons

- imported JSON shapes can vary a lot, so normalization needs sensible fallback rules
- audio path interpretation must stay conservative to avoid misleading users

## Risks

1. Over-assuming external JSON field names.
   - Mitigation: support a clear set of aliases and ignore unknown fields safely.

2. Importing misleading audio paths that do not exist locally.
   - Mitigation: preserve the path text, but mark the entry as missing audio unless the file resolves successfully.

3. Dataset duplication from repeated append imports.
   - Mitigation: treat import as explicit append/create behavior, not hidden dedupe.

