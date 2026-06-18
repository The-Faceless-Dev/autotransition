# Device File Picker and Upload Plan

## Goal

Let users choose audio files from their device using a normal file picker, instead of requiring them to type or paste a local path.

The UI should still keep the direct path input for advanced users, but the default flow should be:

1. Click a file picker button.
2. Select an MP3/WAV/FLAC/OGG/M4A file.
3. App uploads/copies it into the local workspace.
4. App probes it and loads it into the player.
5. User chooses the continuation point and builds a scaffold.

## Intended Behavior

Add a browser file input:

```text
[ Choose Audio File ]  selected-file.mp3
```

When a file is selected:

- Upload it to the local Python server.
- Store it under `data/input/`.
- Preserve the original filename where practical.
- Avoid overwriting existing files by adding a short unique suffix when needed.
- Return the server-side stored path.
- Set the UI source path to that stored path.
- Probe and load that stored path into the audio player.

The direct path input should remain available because local power users may want to use existing files without copying them.

## Backend Changes

Add:

- `POST /api/source/upload`
  - Accepts multipart file upload.
  - Validates extension against supported audio formats.
  - Writes to `data/input/`.
  - Returns:
    - original filename
    - stored path
    - source format
    - probe metadata

Use existing `probe_audio` after the file is stored.

## UI Changes

Source panel:

- Add a file picker control near the path input.
- Show selected filename and stored path.
- Keep `Load Song` for typed paths.
- When a file is picked, automatically upload and load it.

The UI should make this feel like the primary flow:

- File picker first.
- Path input still visible but secondary.

## Proposed Files

- `src/autotransition/ui/app.py`
  - Add upload endpoint.
- `src/autotransition/ui/static/index.html`
  - Add file input.
- `src/autotransition/ui/static/styles.css`
  - Style file picker area.
- `src/autotransition/ui/static/app.js`
  - Upload selected file and load returned stored path.
- `tests/test_ui_api.py`
  - Upload endpoint tests.

## Dependencies

FastAPI multipart uploads require:

- `python-multipart`

Add it as a runtime dependency.

## Risks

- Large uploads may take time.
- File names need sanitization to avoid path traversal.
- Browser upload copies the file into `data/input/`, so disk usage can grow.
- Users may choose unsupported files with a supported extension but unsupported codec; probing should catch that.

## Validation

- Unit/API test upload rejects unsupported extensions.
- API test upload accepts a tiny WAV fixture and returns probe metadata.
- Manual UI check:
  - Choose file opens OS file picker.
  - Selected file uploads.
  - Source path is populated.
  - Audio player loads.
  - Selection scaffold can be built from uploaded file.

## Approval Needed

Implementation should wait until this plan is approved or revised.
