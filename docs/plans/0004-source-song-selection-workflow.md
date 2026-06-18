# Source Song Selection Workflow Plan

## Goal

Let users load a full song, preview it, choose the exact point or region they want to continue from, and build the repaint scaffold from that selected clip rather than requiring a pre-cut audio file.

The workflow should support:

1. Loading a full source song into the UI.
2. Playing and scrubbing through the song.
3. Dragging/selecting the continuation point or selected tail region.
4. Building the ACE-Step repaint scaffold from the selected clip.
5. Preserving selection metadata so users can understand and reproduce the transition.

The scaffold should not inherit the full original song length. The selected point only defines where the source tail is taken from. The empty future region should be based on the user-configured continuation duration when ACE-Step allows it, or the effective continuation length produced by ACE-Step when the runtime constrains output length.

## User Experience

The UI should add a source timeline area, not a raw file utility.

Expected controls:

- Source audio path input.
- Load button.
- Audio player with play/pause, current time, and duration.
- Scrubbable timeline.
- Draggable continuation marker.
- Optional selected context range display.
- Numeric controls for:
  - continuation point
  - context seconds
  - repaint overlap seconds
  - generated section seconds
- Clear visual labels for:
  - preserved context
  - repaint overlap
  - generated future

The default behavior should be simple:

- User loads a full song.
- User drags the marker to the point where the next clip should start.
- App takes `context_seconds + repaint_overlap_seconds` before that marker.
- Repaint starts at `context_seconds` within the extracted tail.
- Blank generated future is appended after the extracted tail, using the configured continuation length.

Conceptually:

```text
full song:
[ earlier song ][ selected context ][ overlap zone ]| continuation point
                                      repaint starts ^

scaffold:
[ selected context ][ overlap zone ][ silence for generated future ]
                    repaint starts ^
```

The silence length is `new_section_seconds` or the selected ACE-Step runtime duration target. It is not `source_duration - continuation_point`.

## Backend Changes

Add source-selection planning and extraction helpers.

Proposed behavior:

- Validate the source audio exists.
- Probe duration.
- Validate that the selected continuation point is late enough to include the requested tail.
- Extract the selected tail ending at the continuation point.
- Append silence for the configured generated section duration.
- Write scaffold and metadata.

Metadata should include:

- original source path
- source duration
- selected continuation point seconds
- extracted tail start seconds
- extracted tail end seconds
- context seconds
- repaint overlap seconds
- repaint start seconds inside scaffold
- new section seconds
- requested continuation seconds
- effective continuation seconds when known
- preset/caption/model hints

## Proposed API Endpoints

- `POST /api/source/probe`
  - Input: source path
  - Output: duration, format basics, validation status
- `POST /api/scaffolds/from-selection`
  - Input: source path, continuation point, preset, caption, settings
  - Output: scaffold plan and metadata

Keep the existing `/api/scaffolds` endpoint for users who already have a prepared clip.

## Proposed Files

- `src/autotransition/audio/probe.py`
  - Duration and basic source metadata.
- `src/autotransition/audio/selection.py`
  - Extract selected tail and build scaffold from a full-song selection.
- `src/autotransition/pipeline/source_selection.py`
  - Serializable selection request/plan objects.
- `src/autotransition/ui/app.py`
  - Add probe and selected-scaffold routes.
- `src/autotransition/ui/static/index.html`
  - Add audio timeline/player source area.
- `src/autotransition/ui/static/styles.css`
  - Timeline, marker, and range styling.
- `src/autotransition/ui/static/app.js`
  - Load/probe source, bind audio player, update marker, submit selected scaffold.
- `tests/test_source_selection.py`
  - Pure selection math and validation.
- `tests/test_ui_api.py`
  - Probe and selected-scaffold validation tests.

## Browser Audio Handling

For local paths, browser playback cannot directly read arbitrary disk paths through normal web security rules.

Use a local media-serving endpoint:

- `GET /api/source/audio?path=...`
  - Serves the selected local audio file from the Python server.
  - Must validate that the path exists and is a file.
  - This is a local-only app, but errors should still be clear.

The frontend can then set:

```text
audio.src = /api/source/audio?path=<encoded path>
```

## UI Tradeoffs

- A native browser `<audio>` player gives reliable playback quickly.
- A custom timeline overlay gives the drag-to-continue workflow without needing a waveform dependency yet.
- A waveform view would be better later, but it likely needs an additional dependency or client-side decoding work.
- Local path serving is pragmatic for a local app, but a future desktop wrapper or upload picker would be more ergonomic.

## Risks

- Long files can be slow to probe or load depending on format.
- Browser playback support depends on codec support; ffmpeg can still process more formats than the browser can play.
- Serving arbitrary local files is only acceptable because this is a local tool; do not expose the UI on a public network by default.
- Selection math must avoid silently using the wrong tail if the marker is too early in the song.

## Validation

- Unit-test selection timing calculations.
- Unit-test early-marker validation.
- API-test missing file and valid probe behavior.
- Start the UI and verify:
  - song can be loaded from a local path
  - duration appears
  - play/scrub works for browser-supported formats
  - marker drag updates continuation point
  - scaffold metadata records selected source region

## Approval Needed

Implementation should wait until this plan is approved or revised.
