# Managed ACE-Step Runtime Install Plan

## Goal

Autotransition must not stop at "runtime missing." It needs a managed ACE-Step runtime path:

1. Detect whether ACE-Step runtime is installed.
2. Install it automatically when the user asks or when generation requires it and auto-install is enabled.
3. Provide explicit commands/config for users who need to install manually.
4. Start or connect to the ACE-Step REST API.
5. Submit repaint jobs to ACE-Step and retrieve generated output.

## Official Runtime Basis

ACE-Step 1.5's official install path is:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
git clone https://github.com/ACE-Step/ACE-Step-1.5.git
cd ACE-Step-1.5
uv sync
uv run acestep-api
```

The official docs state:

- Python 3.11-3.12 is required.
- CUDA GPU is recommended, with CPU/MPS/ROCm/Intel paths also supported.
- The REST API server runs on port `8001` by default.
- Models are downloaded automatically on first run.
- Repaint uses source audio and skips the LM planner.

The REST API workflow is:

1. `POST /release_task`
2. Poll `POST /query_result`
3. Download generated audio from `GET /v1/audio?path=...`

For repaint, the API accepts:

- `task_type="repaint"`
- `src_audio_path`
- `repainting_start`
- `repainting_end=-1`
- `prompt` / `caption`
- `model`
- `audio_duration`
- `inference_steps`
- `seed`
- `bpm`
- `key_scale`

Sources:

- https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md
- https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md

## Runtime Layout

Use a repo-local ignored runtime folder:

```text
runtimes/
  ACE-Step-1.5/
```

This keeps the heavy runtime and its virtual environment outside source control.

Add to `.gitignore`:

```text
runtimes/
```

## Commands To Add

CLI:

```powershell
autotransition runtime status
autotransition runtime install
autotransition runtime start-api
autotransition runtime doctor
```

Generated manual installer command:

```powershell
autotransition runtime print-install-command
```

Expected Windows install command sequence:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
git clone https://github.com/ACE-Step/ACE-Step-1.5.git runtimes\ACE-Step-1.5
cd runtimes\ACE-Step-1.5
uv sync
```

Start command:

```powershell
cd runtimes\ACE-Step-1.5
uv run acestep-api
```

## UI Changes

Add a Runtime panel or fold it into System/Model:

- ACE-Step runtime status:
  - Not installed
  - Installed
  - API running
  - API unreachable
  - Install failed
- Buttons:
  - Install Runtime
  - Start Runtime API
  - Copy Install Command
  - Doctor

Generation behavior:

- If runtime missing and auto-install enabled:
  - install runtime
  - start API
  - submit repaint
- If runtime missing and auto-install disabled:
  - show `Install Runtime` / `Install Then Generate`
- If runtime installed but API stopped:
  - start API automatically when allowed
- If API running:
  - submit repaint directly

## Backend Modules

Add:

- `src/autotransition/runtime/ace_step.py`
  - Runtime paths, status, install, start, health check.
- `src/autotransition/runtime/process.py`
  - Safe process launching and log capture.
- `src/autotransition/models/acestep_api.py`
  - REST API client for `/release_task`, `/query_result`, `/v1/audio`.
- `src/autotransition/config.py`
  - Runtime config: install dir, API host/port, auto-install, auto-start.

## Generation Integration

Replace the current "runtime not installed" stub with:

1. Ensure runtime installed if allowed.
2. Ensure ACE-Step API running if allowed.
3. Submit repaint task:

```json
{
  "task_type": "repaint",
  "src_audio_path": "<absolute scaffold path>",
  "repainting_start": 18.0,
  "repainting_end": -1,
  "prompt": "<caption>",
  "model": "acestep-v15-turbo",
  "audio_duration": 57.0,
  "audio_format": "wav",
  "inference_steps": 8,
  "seed": 123
}
```

4. Poll until success/failure.
5. Download/copy generated audio into `data/generated/`.
6. Write generation metadata.

## Safety and Practical Limits

- Runtime install should be explicit from UI unless user enabled auto-install.
- Generation auto-install may take a long time and use significant disk space.
- Never expose ACE-Step API publicly by default; bind to `127.0.0.1`.
- Keep runtime logs available in the UI.
- If `git` or `uv` is missing, show the exact command and failure reason.

## Tests

Add mocked tests for:

- Runtime status when folder missing.
- Runtime status when folder exists.
- Install command construction.
- API client payload for repaint.
- Generation endpoint calls runtime ensure/install/start steps.
- Failure response when install command fails.

Do not run real ACE-Step install in unit tests.

## Approval Needed

Implementation should wait until approved because this adds subprocess execution, runtime installation, external repo management, and long-running generation behavior.
