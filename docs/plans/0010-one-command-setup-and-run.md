# One Command Setup And Run Plan

## Goal

Make Autotransition have exactly two normal user commands:

```powershell
autotransition setup
autotransition run
```

`setup` prepares everything needed for first use.

`run` starts the full local app, including the Autotransition UI and the ACE-Step runtime API when available.

Advanced/debug commands can remain under `autotransition runtime ...`, but they should not be the main user path.

## Desired User Flow

Fresh clone:

```powershell
conda activate autotransition
autotransition setup
autotransition run
```

Then open:

```text
http://127.0.0.1:7860
```

## `autotransition setup`

Responsibilities:

1. Verify conda/Python dependencies are installed enough to run Autotransition.
2. Install/resolve `uv`.
3. Clone ACE-Step runtime if missing.
4. Resume if ACE-Step clone already exists.
5. Run `uv sync`.
6. Print final status and next command:

```text
Setup complete.
Run the app with: autotransition run
```

Options:

- `--runtime-dir`
- `--skip-runtime`
- `--print-only`

## `autotransition run`

Responsibilities:

1. Check ACE-Step runtime status.
2. If runtime installed and API not running, start ACE-Step API in the background.
3. Start Autotransition UI on `127.0.0.1:7860`.
4. Print both URLs:

```text
Autotransition UI: http://127.0.0.1:7860
ACE-Step API: http://127.0.0.1:8001
```

5. Keep the UI server in the foreground.
6. Write ACE-Step API logs to:

```text
data/logs/ace-step-api.log
data/logs/ace-step-api.err.log
```

If runtime is missing:

- Print a clear message:

```text
ACE-Step runtime is not installed. Run: autotransition setup
```

- Start the UI anyway only if `--ui-only` is passed.

Options:

- `--host`
- `--port`
- `--runtime-host`
- `--runtime-port`
- `--ui-only`
- `--no-runtime-autostart`

## CLI Changes

Add top-level commands:

- `setup`
- `run`

Keep:

- `ui`
- `runtime setup`
- `runtime start`
- `runtime doctor`

But README should present only:

```powershell
autotransition setup
autotransition run
```

## Backend Changes

Add helper:

- `ensure_runtime_api(config) -> RuntimeStartResult`

Behavior:

- If API already running, do nothing.
- If runtime missing, return missing status.
- If runtime installed and API stopped, start background process.
- Poll briefly until API is reachable or timeout.

Add result object:

- `started`
- `already_running`
- `api_url`
- `pid`
- `message`

## UI Changes

No major UI layout change required.

Runtime panel should reflect:

- Running
- Started by `autotransition run`
- Missing setup
- Logs path

## Tests

Add tests for:

- top-level setup calls runtime install helper
- top-level run refuses missing runtime unless `--ui-only`
- runtime autostart skips when API already running
- runtime autostart starts background when installed/stopped
- CLI help exposes `setup` and `run`

Do not start real ACE-Step in unit tests.

## Approval Needed

Implementation should wait until approved.
