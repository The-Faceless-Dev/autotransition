# Simplify Runtime Commands Plan

## Goal

Make ACE-Step runtime setup and startup simple enough that users never need to:

- `cd` into `runtimes/ACE-Step-1.5`
- know where `uv.exe` was installed
- copy a long full-path command
- manually recover from a partial setup

The public commands should work from the Autotransition repo root:

```powershell
autotransition runtime setup
autotransition runtime start
autotransition runtime status
```

No manual path targeting should be required.

## Current Problem

The current setup/start guidance exposes implementation details:

```powershell
cd runtimes\ACE-Step-1.5
C:\Users\...\uv.exe run acestep-api --server-name 127.0.0.1 --port 8001
```

That is not acceptable for a creator-facing tool. The app knows the runtime folder and can locate `uv.exe`; it should do that work.

## Desired User Flow

First run:

```powershell
conda activate autotransition
autotransition runtime setup
```

Behavior:

1. Install `uv` if missing.
2. Clone ACE-Step if missing.
3. Resume safely if the clone already exists.
4. Run `uv sync` using the resolved `uv.exe`.
5. Print next step:

```powershell
autotransition runtime start
```

Start API:

```powershell
autotransition runtime start
```

Behavior:

1. Check runtime installed.
2. Resolve `uv.exe`.
3. Start `uv run acestep-api --server-name 127.0.0.1 --port 8001` with `cwd` set internally.
4. Stream logs to console by default.
5. Keep the process running until Ctrl+C.

Optional background start:

```powershell
autotransition runtime start --background
```

Behavior:

1. Start hidden/background process.
2. Write logs to `data/logs/ace-step-api.log` and `.err.log`.
3. Print API URL and log paths.

## CLI Changes

Replace/confine awkward commands:

- Keep `runtime setup`, but make it execute by default.
- Add `runtime setup --print-only` for dry-run command inspection.
- Add `runtime start`.
- Keep `runtime start-command` only as advanced/debug.
- Add `runtime doctor`.

Proposed command behavior:

```powershell
autotransition runtime setup
```

Runs setup.

```powershell
autotransition runtime setup --print-only
```

Prints commands only.

```powershell
autotransition runtime start
```

Runs ACE-Step API in the current terminal.

```powershell
autotransition runtime start --background
```

Runs ACE-Step API in the background and writes logs.

```powershell
autotransition runtime doctor
```

Checks:

- conda env active enough to run Autotransition
- `git` available
- `uv` available/resolvable
- ACE-Step repo exists
- `uv sync` appears complete enough
- API port available/running
- API health reachable

## Backend Changes

Update `src/autotransition/runtime/ace_step.py`:

- `run_install` should be resumable and idempotent:
  - install `uv` only if missing
  - clone only if folder missing
  - if folder exists with `pyproject.toml`, skip clone
  - always run or verify `uv sync`
- `start_api_foreground(config)`:
  - uses resolved `uv.exe`
  - sets `cwd=config.ace_step_dir`
  - no user-facing `cd`
- `start_api_background(config)`:
  - starts process with hidden/background behavior
  - writes logs under `data/logs/`
- `doctor(config)`:
  - returns structured checks for CLI/UI.

## UI Changes

Runtime panel should have buttons:

- `Install Runtime`
- `Start Runtime API`
- `Refresh`

The UI should not show full-path shell commands as the main guidance. It can keep command details in an advanced expandable/debug area later.

If runtime is not installed:

```text
ACE-Step runtime not installed.
[Install Runtime]
```

If installed but stopped:

```text
ACE-Step runtime installed.
[Start Runtime API]
```

If running:

```text
ACE-Step API running at http://127.0.0.1:8001
```

## Docs Changes

README should say:

```powershell
conda activate autotransition
autotransition runtime setup
autotransition runtime start
```

No long command should be the primary path.

## Tests

Add tests for:

- setup skips clone when runtime folder already exists
- `uv` resolution from `%USERPROFILE%\.local\bin\uv.exe`
- foreground start command args are built without requiring shell `cd`
- background start log paths
- doctor missing/installed/running statuses

Do not run the actual ACE-Step setup in tests.

## Risks

- Running setup by default is more powerful than print-only, but that is what users expect from `setup`.
- Long setup may take time; CLI must print progress clearly.
- Background API process management on Windows needs careful logging and status checks.

## Approval Needed

Implementation should wait until approved.
