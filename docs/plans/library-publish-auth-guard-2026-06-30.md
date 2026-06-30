## Library Publish Auth Guard

### Goal

Make publish and revoke respect the real current wallet session state, even if the UI has stale connection data.

### Approach

1. Refresh the public library connection state from the backend at the start of publish/revoke actions.
2. Update the rendered connection state immediately from that response.
3. If the session is not authenticated, stop before sending any publish or revoke request and show a clear message.

### Files

- `src/autotransition/ui/static/app.js`

### Tradeoffs

- Adds one lightweight API call before publish/revoke.
- In exchange, the UI stops relying on stale local state for auth-sensitive actions.

### Risks

- Slightly slower button response on publish/revoke, but the behavior is more correct.
