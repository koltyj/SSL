---
phase: 03-console-surface-features
plan: "01"
subsystem: softkeys
tags: [udp, protocol, cli, softkeys, vpot, cc-names, wheel-mode]

requires:
  - phase: 02-capabilities-audit
    provides: audited handler inventory confirming cc_names and wheel mode are feasible on V3.0/5

provides:
  - cc_names field on SoftkeysState (persists CC parameter names from UDP reply)
  - Fixed handle_cc_names_list_reply stores parsed names instead of discarding them
  - do_wheel_mode CLI command reads/sets V-pot wheel mode per DAW layer
  - do_cc_names CLI command fetches and displays CC parameter names per layer/type
  - do_cc_names_set CLI command sends CC parameter names list to console
  - TestCcNamesStorage, TestWheelMode, TestWheelModeBuilder test classes

affects:
  - 03-02 and later plans that depend on softkeys state being fully populated

tech-stack:
  added: []
  patterns:
    - "TDD RED/GREEN for handler bug fix: write failing test first, then fix model + handler"
    - "Lazy import inside do_* method body for CLI handler builders"
    - "time.sleep(0.3) + _lock state read pattern for async UDP reply commands"

key-files:
  created:
    - tests/test_handler_softkeys.py
  modified:
    - ssl-matrix-client/models.py
    - ssl-matrix-client/handlers/softkeys.py
    - ssl-matrix-client/cli.py

key-decisions:
  - "cc_names stored as flat list on SoftkeysState (not keyed by layer/type) — console replies with current context, state is replaced on each response"
  - "Wheel mode label mapping covers 0-3 (Pan/Linear/Boost-Cut/Off); values 4-5 accepted by protocol but printed as Unknown"

patterns-established:
  - "Handler bug fix pattern: add cc_names: list field, assign state.softkeys.cc_names = names in handler"
  - "CLI read command pattern: send builder, sleep 0.3s, read state under lock, print with label mapping"

requirements-completed: [ADV-02]

duration: 2min
completed: "2026-03-13"
---

# Phase 3 Plan 01: V-pot Wheel Mode and CC Names Summary

**cc_names storage bug fixed and V-pot wheel mode + CC names exposed via three new CLI commands with full TDD test coverage**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-13T21:00:56Z
- **Completed:** 2026-03-13T21:02:49Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Fixed known cc_names storage bug: `handle_cc_names_list_reply` now assigns parsed names to `state.softkeys.cc_names` instead of silently discarding them after parse
- Added `cc_names: list` field to `SoftkeysState` dataclass in `models.py`
- Added 7 new tests (TestCcNamesStorage x3, TestWheelMode x1, TestWheelModeBuilder x2) covering the bug fix and wheel mode builders
- Added `do_wheel_mode`, `do_cc_names`, `do_cc_names_set` CLI commands following all established patterns

## Task Commits

1. **Task 1 RED: Failing tests** - `9486139` (test)
2. **Task 1 GREEN: cc_names field + handler fix** - `d1ba9c1` (feat)
3. **Task 2: CLI commands** - `e2203d9` (feat)

_Note: Task 1 used TDD — RED commit with failing tests, then GREEN commit with fixes._

## Files Created/Modified

- `tests/test_handler_softkeys.py` — Created; 27 tests covering all softkeys handler behavior including new TestCcNamesStorage, TestWheelMode, TestWheelModeBuilder classes
- `ssl-matrix-client/models.py` — Added `cc_names: list = field(default_factory=list)` to SoftkeysState
- `ssl-matrix-client/handlers/softkeys.py` — Fixed `handle_cc_names_list_reply` to store names in `state.softkeys.cc_names`
- `ssl-matrix-client/cli.py` — Added `do_wheel_mode`, `do_cc_names`, `do_cc_names_set` methods

## Decisions Made

- `cc_names` stored as a flat list replaced wholesale on each reply (not keyed by layer/type) — the console echoes the current context's names in each reply, and state is always overwritten to match, consistent with how other state fields work
- Wheel mode label mapping only covers values 0-3 per decompiled Java enum; values 4-5 are accepted in the set command (per plan spec allowing 0-5) and print as "Unknown (N)" on read

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- ruff-format reformatted the test file on first commit attempt (long line in test payload concatenation); re-staged and recommitted. No functional impact.

## Next Phase Readiness

- `cc_names` and `wheel_mode` state fields are populated; ready for Phase 3 Plan 02 (keymap name builder and further softkeys work)
- All 179 tests pass, ruff lint clean

## Self-Check: PASSED

- FOUND: .planning/phases/03-console-surface-features/03-01-SUMMARY.md
- FOUND: ssl-matrix-client/models.py
- FOUND: ssl-matrix-client/handlers/softkeys.py
- FOUND: tests/test_handler_softkeys.py
- FOUND commit: 9486139 (test RED)
- FOUND commit: d1ba9c1 (feat GREEN)
- FOUND commit: e2203d9 (feat CLI)

---
*Phase: 03-console-surface-features*
*Completed: 2026-03-13*
