---
phase: 03-console-surface-features
plan: "02"
subsystem: softkeys
tags: [udp, protocol, cli, softkeys, keymap, midi, usb, supercue]

requires:
  - phase: 03-console-surface-features
    plan: "01"
    provides: test infrastructure, SoftkeysState with cc_names, wheel_mode CLI commands

provides:
  - build_get_edit_keymap_name builder (cmd 600) in handlers/softkeys.py
  - do_softkey_keymap, do_softkey_edit, do_softkey_list CLI commands
  - do_softkey_usb, do_softkey_midi, do_softkey_name, do_softkey_blank, do_softkey_save CLI commands
  - do_softkey_midi_funcs for MIDI function list retrieval
  - do_supercue documenting V3.0/5 hardware-only limitation
  - TestGetKeymapNameBuilder, TestUsbCmdBuilder, TestMidiCmdBuilder, TestKeycapNameBuilder test classes

affects:
  - 03-03 and later plans using softkey editing in automated workflows

tech-stack:
  added: []
  patterns:
    - "TDD RED/GREEN: failing tests committed first, then builder + CLI implementation"
    - "Lazy import inside do_* method body for all softkey builders"
    - "time.sleep(0.3-0.5) + _lock state read for async UDP reply commands"
    - "Validate keymap names against whitelist (keymap1-4) before sending"

key-files:
  created: []
  modified:
    - ssl-matrix-client/handlers/softkeys.py
    - ssl-matrix-client/cli.py
    - tests/test_handler_softkeys.py

key-decisions:
  - "SuperCue/Auto-Mon is hardware-only on V3.0/5 — documented via do_supercue informational command, no UDP path"
  - "Keymap name whitelist: only keymap1-keymap4 accepted by do_softkey_edit (NONE cannot open edit session)"
  - "softkey_edit sends set_edit_keymap_name + get_edit_keymap_size + get_edit_keymap_data in sequence with sleeps"

patterns-established:
  - "SuperCue limitation pattern: informational do_* command prints hardware-only notice, no _require_connected guard"
  - "Keymap edit flow: set name (0.5s) -> get size (0.3s) -> get data (0.5s) -> read state under lock"

requirements-completed: [ADV-01, ADV-03]

duration: 5min
completed: "2026-03-13"
---

# Phase 3 Plan 02: Soft Key Programming CLI Summary

**Full soft key keymap editing CLI (9 commands) with USB/MIDI/blank assignment, MIDI function list, and SuperCue hardware limitation documented**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-13T21:04:00Z
- **Completed:** 2026-03-13T21:09:00Z
- **Tasks:** 2 of 2
- **Files modified:** 3

## Accomplishments

- Added `build_get_edit_keymap_name` builder (cmd 600) to complete the softkeys builder set
- Added 4 new test classes (TestGetKeymapNameBuilder x2, TestUsbCmdBuilder x2, TestMidiCmdBuilder x2, TestKeycapNameBuilder x2) bringing softkeys test count to 35
- Added 10 new CLI commands: do_softkey_keymap, do_softkey_edit, do_softkey_list, do_softkey_usb, do_softkey_midi, do_softkey_name, do_softkey_blank, do_softkey_save, do_softkey_midi_funcs, do_supercue
- SuperCue/Auto-Mon documented as hardware-only per Phase 02 audit findings — prints notice, no UDP required

## Task Commits

1. **Task 1 RED: Failing builder tests** - `89994f5` (test)
2. **Task 1 GREEN: build_get_edit_keymap_name + all softkey CLI commands** - `c69fe7b` (feat)

3. **Task 2: Live console verification** — APPROVED (all commands verified working on Matrix V3.0/5)

## Files Created/Modified

- `ssl-matrix-client/handlers/softkeys.py` — Added `build_get_edit_keymap_name` builder (cmd 600)
- `ssl-matrix-client/cli.py` — Added `# --- Soft Keys ---` section with 10 new do_* commands
- `tests/test_handler_softkeys.py` — Added TestGetKeymapNameBuilder, TestUsbCmdBuilder, TestMidiCmdBuilder, TestKeycapNameBuilder (8 new tests, total 35)

## Decisions Made

- SuperCue/Auto-Mon limitation documented via `do_supercue` informational command — no `_require_connected()` guard since it needs no live console
- Keymap names validated against whitelist `(keymap1, keymap2, keymap3, keymap4)` before sending — "NONE" cannot open an edit session per Phase 02 audit
- Edit session flow: send `build_set_edit_keymap_name` then `build_get_edit_keymap_size` then `build_get_edit_keymap_data` in one `do_softkey_edit` call with sleeps between — matches Java client flow

## Deviations from Plan

None — plan executed exactly as written. The implementation was already partially present from a prior session (RED commit 89994f5 existed); GREEN implementation committed in this session.

## Issues Encountered

- ruff-format reformatted on first commit attempt; re-staged and recommitted cleanly. No functional impact.

## Next Phase Readiness

- All 9 softkey programming CLI commands are implemented and lint-clean
- 187 tests pass (35 in test_handler_softkeys.py)
- Task 2 checkpoint VERIFIED: all commands tested on live console — keymap query, wheel mode read/set, 102 MIDI functions listed, edit session opened, SuperCue notice printed

## Self-Check: PASSED

- FOUND: .planning/phases/03-console-surface-features/03-02-SUMMARY.md
- FOUND: ssl-matrix-client/handlers/softkeys.py (build_get_edit_keymap_name present)
- FOUND: ssl-matrix-client/cli.py (do_softkey_edit present)
- FOUND: tests/test_handler_softkeys.py (TestGetKeymapNameBuilder present)
- FOUND commit: 89994f5 (test RED)
- FOUND commit: c69fe7b (feat GREEN)

---
*Phase: 03-console-surface-features*
*Completed: 2026-03-13*
