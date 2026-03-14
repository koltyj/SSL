---
phase: 05-terminal-ui
plan: "01"
subsystem: tui
tags: [textual, tui, thread-bridge, ssl-theme, status-bar]
dependency_graph:
  requires: []
  provides: [SSLApp, SSLStatusBar, TUI-thread-bridge, ssl-theme]
  affects: [ssl-matrix-client/tui.py, ssl-matrix-client/ssl_theme.tcss, ssl-matrix-client/client.py, ssl-matrix-client/__main__.py]
tech_stack:
  added: [textual>=0.80.0, pytest-asyncio]
  patterns: [Textual App/Message bridge, recv-thread post_message pattern, TCSS theming]
key_files:
  created:
    - ssl-matrix-client/tui.py
    - ssl-matrix-client/ssl_theme.tcss
    - tests/test_tui.py
  modified:
    - ssl-matrix-client/client.py
    - ssl-matrix-client/__main__.py
    - tests/conftest.py
    - tests/test_watchdog.py
    - pyproject.toml
decisions:
  - "_on_state_changed fires OUTSIDE the lock in _recv_loop — posting inside would deadlock since the handler on the Textual side acquires the lock to read state"
  - "Snapshot is extracted under lock in _on_state_changed_hook (in SSLApp), then posted outside — lock held as briefly as possible"
  - "BINDINGS annotated with ClassVar to satisfy RUF012 lint rule for Textual subclasses"
  - "test_watchdog.py make_client() fixed to include new callback hook attributes (Rule 1 auto-fix)"
metrics:
  duration: "~15 min"
  tasks_completed: 2
  files_changed: 9
  completed_date: "2026-03-14"
---

# Phase 05 Plan 01: TUI Foundation Summary

Textual app shell with SSL-inspired theme, 4-tab navigation, persistent status bar (health dot, project name, last template, tab-aware hints), and recv-thread → Textual event loop bridge via `post_message`.

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Add Textual dep, client hooks, conftest shim, __main__.py routing, TUI test stubs | 62b58f6 | pyproject.toml, client.py, __main__.py, conftest.py, test_tui.py |
| 2 | Create SSLApp shell with SSL theme, tabs, status bar, thread bridge | 73bd88b | tui.py, ssl_theme.tcss, test_watchdog.py |

## What Was Built

**`ssl-matrix-client/tui.py`**
- `SSLApp(App)` with `CSS_PATH = "ssl_theme.tcss"` and SSL-green/amber/dark theme
- `TabbedContent` with 4 tabs: Channels, Routing, Templates, Settings (placeholder content)
- Number keys 1–4 bound to `action_show_tab` which also updates status bar hints
- Thread bridge: `_on_state_changed_hook` acquires lock, extracts snapshot dict (including `channel_inserts` and `last_template`), releases lock, then calls `post_message` — all outside the recv-thread lock
- `SSLStatusBar` widget: health dot colored green/yellow/red by `heartbeat_age`, project name, last template, tab-aware hints via `set_hints_for_tab()`
- Message classes: `StateUpdated(snapshot)`, `ConsoleOnline()`, `ConsoleOffline(attempt)`
- `main(argv)` parses `--ip` flag and launches app

**`ssl-matrix-client/ssl_theme.tcss`**
- `SSLStatusBar` docked at bottom, 1 line tall, using `$panel` / `$foreground` TCSS variables
- `TabbedContent` fills remaining vertical space
- Tab header styling with `$panel` background and `$primary` for active tab

**`ssl-matrix-client/client.py` hooks**
- `_on_state_changed`: fires after each dispatch, OUTSIDE the `with self._lock:` block
- `_on_desk_offline(attempt)`: fires in `_trigger_reconnect` after lock released
- `_on_desk_online()`: fires in `_on_desk_came_online` after reconnect flags cleared

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_watchdog.py make_client() missing new hook attributes**
- **Found during:** Task 2 verification
- **Issue:** `make_client()` uses `__new__` to construct `SSLMatrixClient` without calling `__init__`, so the three new callback hooks (`_on_desk_offline`, etc.) were missing, causing `AttributeError` in `_trigger_reconnect`
- **Fix:** Added `_on_state_changed = None`, `_on_desk_offline = None`, `_on_desk_online = None` to `make_client()` helper
- **Files modified:** `tests/test_watchdog.py`
- **Commit:** 73bd88b

**2. [Rule 2 - Lint] BINDINGS ClassVar annotation**
- **Found during:** Task 2 pre-commit hook
- **Issue:** Ruff RUF012 requires mutable class attributes on dataclass-like classes to be annotated with `ClassVar`
- **Fix:** Added `ClassVar` import and typed `BINDINGS: ClassVar[list]`
- **Files modified:** `ssl-matrix-client/tui.py`
- **Commit:** 73bd88b

## Test Results

- 264 tests pass, 10 skipped (TUI stubs — all correctly marked with `pytest.mark.skip`)
- No regressions in existing test suite

## Self-Check: PASSED

Files created:
- ssl-matrix-client/tui.py: FOUND
- ssl-matrix-client/ssl_theme.tcss: FOUND
- tests/test_tui.py: FOUND

Commits:
- 62b58f6: FOUND
- 73bd88b: FOUND
