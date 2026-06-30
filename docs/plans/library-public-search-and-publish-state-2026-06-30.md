## Library Public Search And Publish State

### Goal

Improve the library UI by making public assets searchable and by showing publish progress directly on the asset card that is being published or updated.

### Approach

1. Add a public library search input and filter the currently loaded public items client-side.
2. Track in-flight local library publish and revoke actions by item id in UI state.
3. Render the active publish state directly on the card and disable the publish button while the request is in flight.

### Files

- `src/autotransition/ui/static/index.html`
- `src/autotransition/ui/static/app.js`

### Tradeoffs

- Public search is client-side over the loaded page of assets, which is simple and fast enough for the current library size.
- Publish state lives in frontend state only, which is enough for per-session progress feedback.

### Risks

- If public library item counts grow much larger, search should eventually move server-side alongside paged queries.
