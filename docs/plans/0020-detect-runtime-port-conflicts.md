# Detect Runtime Port Conflicts Plan

## Problem

ACE-Step can fail at startup with:

```text
[Errno 98] error while attempting to bind on address ('127.0.0.1', 8001): address already in use
```

Autotransition currently discovers existing ACE-Step processes by command line, but it does not explicitly detect when the configured API port is already occupied by a stale process or another service. That leads to launching ACE-Step, watching it fail, and leaving the user to infer that the port is the real problem.

## Approach

- Add lightweight port listener discovery for Windows and POSIX.
- Before starting ACE-Step, if health is not good and the port is already occupied, return a clear startup failure with the listener PID/command when available.
- Keep existing ACE-Step process discovery for stale runtime handling.
- Add regression coverage for the port-conflict path.

## Affected Files

- `src/autotransition/runtime/ace_step.py`
- `tests/test_runtime.py`

## Tradeoffs and Risks

- Process command details depend on platform tools (`Get-NetTCPConnection`, `ss`, `lsof`, `netstat`) and may not always be available. The fallback should still report the port conflict even if it cannot identify the command.
- This does not kill unknown port owners automatically. Autotransition should not terminate unrelated processes without explicit user action.
