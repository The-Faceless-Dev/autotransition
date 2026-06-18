# Robust Runtime Startup Plan

## Goal

Make `autotransition run` handle ACE-Step startup reliably on Windows when a previous runtime process is still alive, half-started, or holding the ACE-Step `.venv` lock.

Also make the process lifecycle match the user-facing command model: when `autotransition run` starts ACE-Step, stopping `autotransition run` should stop that managed ACE-Step runtime too.

## Problem

`autotransition run` currently checks API health and starts a new ACE-Step process when `/health` is not reachable. If an earlier ACE-Step process is still running but not serving the API, a second `uv run` can try to sync or touch the same virtual environment and fail with Windows file-lock errors. ACE-Step can also inherit `HF_HUB_ENABLE_HF_TRANSFER=1` even when `hf_transfer` is unavailable, which breaks model initialization/download.

Stopping the UI does not currently stop an ACE-Step runtime that was launched by `autotransition run`, which leaves stale ACE-Step processes behind. The next run can then collide with those stale processes.

## Approach

1. Add lightweight runtime process discovery for the configured ACE-Step command/port.
2. Update runtime startup so it does not launch a duplicate ACE-Step process when one is already present.
3. Add a PID file for Autotransition-started ACE-Step processes so future runs can identify managed runtime state.
4. Set a deterministic ACE-Step subprocess environment:
   - disable `HF_HUB_ENABLE_HF_TRANSFER` by default unless the user explicitly configured it
   - preserve the rest of the parent environment
5. Track whether the current `autotransition run` command started ACE-Step.
6. On normal UI shutdown or `Ctrl+C`, terminate only the ACE-Step process tree started by that same command.
7. Do not stop an API that was already running before `autotransition run`.
8. Improve the failure message so users know whether the API is starting, stale, or failed.
9. Add focused tests for duplicate-process detection, managed shutdown, and subprocess environment construction.

## Affected Files

- `src/autotransition/runtime/ace_step.py`
- `src/autotransition/cli.py`
- `tests/test_runtime.py`
- `README.md` if command behavior or troubleshooting text needs updating

## Tradeoffs

Process discovery without adding `psutil` is intentionally lightweight and platform-aware. It avoids a new dependency, but it is less rich than a full process manager. The PID file gives us a reliable path for processes started by Autotransition while keeping manually started runtimes visible through command-line matching.

Stopping the managed runtime on UI shutdown means `autotransition run` behaves like one app command. Users who want ACE-Step to stay up independently can still start it with the advanced runtime command.

## Risks

The main risk is being too aggressive with existing processes. This plan avoids killing user processes automatically. It reports them clearly and prevents duplicate startup.

Shutdown should only target the process tree started by the current command. If process-tree cleanup fails on Windows, the app should report that clearly instead of pretending the runtime stopped.
