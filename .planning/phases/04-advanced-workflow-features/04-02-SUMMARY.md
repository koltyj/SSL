---
phase: 04-advanced-workflow-features
plan: 02
subsystem: client
tags: [watchdog, heartbeat, reconnect, threading, split-board, state-tracking]

# Dependency graph
requires:
  - phase: 03-console-surface-features
    provides: "SSLMatrixClient with handler dispatch, socket lifecycle, request_sync()"
provides:
  - "Watchdog thread monitoring SSL UDP heartbeat with configurable timeout (35s)"
  - "Reconnect guard preventing simultaneous reconnect storms"
  - "_needs_resync flag scheduling request_sync() after reconnect outside lock"
  - "Split board bookkeeping (set_split/get_split/clear_split) — pure software state"
affects: [05-terminal-ui, 06-dock-app]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Watchdog-via-daemon-thread: separate daemon thread polls heartbeat_age and triggers reconnect"
    - "Resync-flag-pattern: _needs_resync flag checked in watchdog loop to call request_sync() outside _lock"
    - "Reconnect-guard: _reconnecting + _reconnect_attempts prevent concurrent reconnect attempts"
    - "Software-bookkeeping-only: set_split/get_split/clear_split store client state; zero UDP side effects"

key-files:
  created:
    - tests/test_watchdog.py
    - tests/test_split.py
  modified:
    - ssl-matrix-client/client.py

key-decisions:
  - "Watchdog monitors SSL UDP heartbeat only — ipMIDI (HUI/MCU) is separate protocol, out of scope"
  - "_needs_resync flag avoids deadlock: _recv_loop holds _lock when dispatching, so request_sync() would deadlock if called inline"
  - "Split board is purely client-side bookkeeping — confirmed in Phase 2 audit that fader group assignment is console hardware surface config, not UDP"

patterns-established:
  - "Reconnect guard pattern: _reconnecting bool + _reconnect_attempts counter prevent watchdog storms"
  - "Post-dispatch hook: _recv_loop calls _on_desk_came_online() after GET_DESK_REPLY to handle reconnect case outside the handler"

requirements-completed: [BRDG-01, SPLIT-01]

# Metrics
duration: 4min
completed: 2026-03-14
---

# Phase 4 Plan 02: Watchdog and Split Board Summary

**SSL UDP heartbeat watchdog with auto-reconnect guard and split board bookkeeping — 28 unit tests, zero external dependencies**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-14T08:51:13Z
- **Completed:** 2026-03-14T08:55:27Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 3

## Accomplishments

- Watchdog daemon thread detects stale heartbeat (>35s) and triggers reconnect via GET_DESK re-discovery
- Reconnect guard (`_reconnecting` + `_reconnect_attempts`) prevents simultaneous reconnect storms and gives up cleanly after MAX_RECONNECT_ATTEMPTS (10)
- `_needs_resync` flag pattern avoids deadlock: schedules `request_sync()` outside `_lock` in the watchdog loop after reconnect succeeds
- Split board state (set_split/get_split/clear_split) tracks fader group assignment with layer-number validation — zero UDP side effects confirmed by tests

## Task Commits

1. **Task 1: Watchdog thread and reconnect logic** - `f6507dc` (feat)
2. **Task 2: Split board state tracking** - `15b9da6` (feat)

## Files Created/Modified

- `/Users/koltonjacobs/DEV/SSL-BOARD/ssl-matrix-client/client.py` - Added HEARTBEAT_TIMEOUT/WATCHDOG_INTERVAL/MAX_RECONNECT_ATTEMPTS constants; _watchdog_loop(); _trigger_reconnect(); _on_desk_came_online(); set_split/get_split/clear_split(); watchdog thread lifecycle in connect()/disconnect()
- `/Users/koltonjacobs/DEV/SSL-BOARD/tests/test_watchdog.py` - 16 tests: TestWatchdog, TestReconnectGuard, TestReconnectAttempts, TestReconnectSync, TestWatchdogLifecycle
- `/Users/koltonjacobs/DEV/SSL-BOARD/tests/test_split.py` - 12 tests: TestSplitState covering lifecycle, no-UDP enforcement, layer validation

## Decisions Made

- Watchdog monitors SSL UDP heartbeat only, not ipMIDI — documented explicitly in `_watchdog_loop` docstring
- Used `_needs_resync` flag pattern instead of spawning a resync thread inline in `_recv_loop` — the recv loop holds `_lock` during dispatch, so calling `request_sync()` (which calls `wait_online()` which acquires `_lock`) would deadlock
- `_on_desk_came_online()` called from `_recv_loop` after the `with self._lock:` block releases, ensuring reconnect state is cleared correctly without re-entering the lock

## Deviations from Plan

None — plan executed exactly as written. The plan explicitly offered two resync approaches and flagged the lock-deadlock concern; the `_needs_resync` flag pattern was chosen as specified.

## Issues Encountered

Pre-commit `ruff-format` reformatted files twice (once per task) — re-staged after each hook run. Standard workflow.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Watchdog and split board complete; ready for Phase 4 Plan 03 (session templates / routing recall) or Phase 5 (Terminal UI)
- No blockers

## Self-Check: PASSED

- ssl-matrix-client/client.py: FOUND
- tests/test_watchdog.py: FOUND
- tests/test_split.py: FOUND
- .planning/phases/04-advanced-workflow-features/04-02-SUMMARY.md: FOUND
- commit f6507dc: FOUND
- commit 15b9da6: FOUND
