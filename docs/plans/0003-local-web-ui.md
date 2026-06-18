# Local Web UI Plan

## Goal

Build a professional, user-friendly local web UI for Autotransition with a simple Python launch command.

The UI should make the transition workflow understandable without exposing users to raw model internals first, while still keeping advanced settings configurable.

## User-Facing Command

Add:

```powershell
autotransition ui
```

This should start a local web server and print the URL, for example:

```text
Autotransition UI running at http://127.0.0.1:7860
```

The command should accept host/port options:

```powershell
autotransition ui --host 127.0.0.1 --port 7860
```

## Intended Approach

Use a lightweight Python-served web UI:

- `FastAPI` for local API endpoints and static file serving.
- `uvicorn` for the development/local app server.
- Plain HTML/CSS/JavaScript in `src/autotransition/ui/static/`.

This avoids adding a Node build system at this stage and keeps the app runnable from the conda Python environment.

## UI Structure

The first screen should be the actual tool, not a landing page.

Primary layout:

- Header with tasteful The Faceless Dancer branding and system status.
- Left workflow column:
  - Source clip path/input
  - Preset selector
  - Target prompt/caption editor
  - Model selector and install status
- Center work area:
  - Tail/context settings
  - Repaint overlap and generated duration
  - BPM/key/seed controls
  - Scaffold/generation action buttons
- Right operational column:
  - System status
  - Model status
  - Recent outputs
  - Logs

The UI should use restrained dark-neutral styling with strong contrast, readable type, precise spacing, and clear controls. Avoid a bare developer-panel feel.

## Required UI Capabilities

1. Presets and direct input
   - Show creator-friendly presets.
   - Allow caption and numeric settings to be edited directly.
2. Model management
   - Show repaint-capable ACE-Step profiles.
   - Show installed/not installed status.
   - Provide an install button per selected model.
   - Warn that actual checkpoints can be large.
3. Scaffold preparation
   - Let users enter/select a local source audio path.
   - Build `tail + silence` scaffold using existing backend code.
   - Show created scaffold and metadata paths.
4. System status
   - Python version
   - ffmpeg availability
   - configured model directory
   - known model count
   - current working directory
5. Logs
   - Show API/server-side events in the UI.
   - Include user actions, scaffold creation, install start/success/failure, and validation errors.
   - Keep logs local and readable.

## Proposed API Endpoints

- `GET /api/status`
  - Returns system status and environment checks.
- `GET /api/presets`
  - Returns preset metadata and default settings.
- `GET /api/models`
  - Returns repaint-capable model profiles plus install status.
- `POST /api/models/{slug}/install`
  - Installs the selected model from Hugging Face.
- `POST /api/scaffolds`
  - Builds a scaffold from source path, preset, caption, and direct setting overrides.
- `GET /api/logs`
  - Returns recent in-memory logs.

## Proposed Files

- `src/autotransition/ui/__init__.py`
- `src/autotransition/ui/app.py`
  - FastAPI app factory, routes, and static file mounting.
- `src/autotransition/ui/state.py`
  - In-memory logs and status helpers.
- `src/autotransition/ui/static/index.html`
  - App shell.
- `src/autotransition/ui/static/styles.css`
  - Polished creator-facing UI styles.
- `src/autotransition/ui/static/app.js`
  - Frontend interactions and API calls.
- `src/autotransition/cli.py`
  - Add `ui` command.
- `README.md`
  - Add UI launch instructions.
- `tests/test_ui_api.py`
  - API smoke tests for status, presets, models, and scaffold validation.

## Dependencies

Add:

- `fastapi`
  - Local API and static UI server.
- `uvicorn`
  - Runs the local server from the Python command.

Do not add frontend build tooling yet.

## Tradeoffs

- Plain JavaScript avoids build complexity, but it requires careful organization to avoid a messy single file.
- FastAPI is an extra dependency, but it gives a clean path toward a future API-backed UI.
- In-memory logs are simple and useful for early local runs, but later releases may need persisted run logs under `data/logs/`.
- Source path entry is simpler than browser file upload for local audio processing, but a future UI should add file picker/upload ergonomics.

## Risks

- Long model downloads can block a request in the first version. The UI should show activity and log progress, but a later version should move downloads to background jobs.
- Browser security prevents direct native file browsing without upload or a desktop wrapper.
- The UI can become cluttered if all advanced settings are visible at once, so advanced controls should be grouped and compact.
- Actual ACE-Step generation is not implemented yet, so the UI must label generation as pending and focus current action on scaffold creation/model install.

## Validation

- Run unit/API tests.
- Start `autotransition ui` locally.
- Open the app in a browser and verify:
  - nonblank polished layout
  - presets load
  - models load with install status
  - system status loads
  - logs load
  - scaffold creation returns a helpful validation error for missing source path

## Approval Needed

Implementation should wait until this plan is approved or revised.
