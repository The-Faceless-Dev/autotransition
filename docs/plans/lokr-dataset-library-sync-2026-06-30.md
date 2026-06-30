## LoKr Dataset Library Sync

### Goal

Make LoKr datasets appear in the private library immediately after create/import/save flows, without requiring the user to understand or manually run a separate reindex step.

### Approach

1. Add a local-library sync helper in the FastAPI app that rebuilds the library index from scanned items.
2. Call that helper from the shared LoKr dataset write path so all dataset mutations update the private library automatically.
3. Change the library UI refresh button to run a reindex rather than only reloading the current index file.

### Files

- `src/autotransition/ui/app.py`
- `src/autotransition/ui/static/app.js`

### Tradeoffs

- Reindexing on each dataset write is a bit heavier than a plain file save, but dataset edits are infrequent and the behavior is much clearer.
- Reusing the existing reindex path keeps the fix small and avoids inventing a second indexing mechanism.

### Risks

- If future local library scanning becomes much more expensive, this may need throttling or targeted item updates instead of full reindex.
