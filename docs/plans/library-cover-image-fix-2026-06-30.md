## Library Cover Image Fix

### Goal

Make local library card images reliable when replacing an existing image and when reindexing the local library.

### Approach

1. Fix `set_cover_image()` so replacing a cover with the same extension does not delete the newly copied file.
2. Preserve the existing `cover` file record during reindex when scanned items do not provide one.

### Files

- `src/autotransition/library/index.py`

### Tradeoffs

- Reindex now intentionally preserves user-managed cover files instead of treating scanned files as the full source of truth.

### Risks

- If new user-managed file roles are added later, they may need the same preservation behavior as `cover`.
