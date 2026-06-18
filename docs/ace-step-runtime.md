# ACE-Step Runtime

Autotransition can prepare ACE-Step repaint inputs and manage model downloads. Actual audio generation also requires an ACE-Step runtime package that exposes repaint/inference from Python.

## First-Time Setup

Normal first-time setup:

```powershell
autotransition setup
```

To inspect the commands before running them:

```powershell
autotransition runtime setup --print-only
```

Equivalent manual commands:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
git clone https://github.com/ACE-Step/ACE-Step-1.5.git runtimes\ACE-Step-1.5
cd runtimes\ACE-Step-1.5
uv sync
```

Start the ACE-Step API:

```powershell
autotransition run
```

Advanced separate runtime start:

```powershell
autotransition runtime start --background
```

## Generation Flow

Current generation flow:

1. The UI builds the repaint scaffold internally from the selected source point.
2. The selected ACE-Step model is checked or installed.
3. The ACE-Step runtime adapter is called.

If the runtime is missing or the ACE-Step API is not running, generation fails clearly and keeps the prepared scaffold/metadata paths in the output details. This is intentional; the app should not fake generated audio.

When the ACE-Step API is running, Autotransition submits repaint jobs through `/release_task`, polls `/query_result`, and downloads audio through `/v1/audio`.
