# Cross Platform UV Setup Plan

## Goal

Make `autotransition setup` work from a fresh Linux/macOS clone as well as Windows.

## Problem

The setup command currently tries to install `uv` with a PowerShell command:

```text
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

That fails in Linux containers because `powershell` is not installed. The `uv` resolver also checks for the Windows `uv.exe` fallback but not the POSIX `~/.local/bin/uv` path.

## Approach

1. Make the generated uv install command platform-specific.
2. Resolve `uv` from:
   - `PATH`
   - `~/.local/bin/uv`
   - `~/.local/bin/uv.exe`
3. Keep `autotransition setup --print-only` useful on each platform.
4. Improve the missing-uv error so it does not tell Linux users to restart PowerShell.
5. Add tests for Linux/macOS command generation and POSIX uv resolution.

## Affected Files

- `src/autotransition/runtime/ace_step.py`
- `tests/test_runtime.py`

## Risk

Low. This changes setup command construction and executable resolution only. Existing Windows behavior remains.
