---
phase: 04-advanced-workflow-features
plan: 01
subsystem: templates
tags: [json, dataclasses, pathlib, udp, serialization, session-templates]

requires:
  - phase: 03-console-surface-features
    provides: builder functions (build_set_chan_name, build_set_insert_name_v2, build_set_insert_to_chan_v2, build_set_profile_for_daw_layer, build_set_auto_mode, etc.)
  - phase: 01-foundation
    provides: ConsoleState dataclass tree in models.py

provides:
  - templates.py with save/load/diff/apply/CRUD API for JSON session snapshots
  - 42 unit tests covering all public functions
  - Import shim in conftest.py updated to include templates module

affects:
  - 04-02 (template REPL/CLI commands will call these functions directly)
  - 04-03 (routing recall plan uses build_apply_commands)

tech-stack:
  added: []
  patterns:
    - "dataclasses.asdict for ConsoleState serialization to plain dict"
    - "Optional[Path] = None pattern for template_dir overrides (enables test isolation via tmp_path)"
    - "Envelope JSON: {version, saved_at, console_project_title, daw_project_path, state}"
    - "Routing restore order: insert names before channel assignments (Pitfall 3)"
    - "XPatch always in skipped list, never in apply commands"

key-files:
  created:
    - ssl-matrix-client/templates.py
    - tests/test_templates.py
  modified:
    - tests/conftest.py

key-decisions:
  - "XPatch stored in template JSON for reference but apply_template/build_apply_commands never emit XPatch SET packets — all silently fail on this console"
  - "No dataclass deserialization on load — callers consume raw dicts directly (simpler, avoids version mismatch issues)"
  - "template_dir parameter on all I/O functions for test isolation via pytest tmp_path"
  - "Routing restore order enforced in code: device names first, then channel slot assignments"

patterns-established:
  - "TDD: write failing tests, then implement to green, fix lint before commit"
  - "capture_template_state uses explicit field whitelist (not full asdict) to exclude runtime fields"

requirements-completed: [SESS-01, SESS-02]

duration: 4min
completed: 2026-03-14
---

# Phase 4 Plan 1: Template Core Module Summary

**ConsoleState JSON snapshot system with save/load/diff/apply CRUD, routing-order-aware restore, and XPatch skip guarantee — 42 tests, zero external dependencies**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-14T08:31:28Z
- **Completed:** 2026-03-14T08:35:47Z
- **Tasks:** 2 (Task 1: serialization/CRUD/naming, Task 2: diff/apply)
- **Files modified:** 3

## Accomplishments

- `templates.py` with full save/load/diff/apply/CRUD API plus `make_template_name` and `capture_template_state`
- `diff_template` groups changes into 5 categories (channels, profiles, routing, display, skipped) with human-readable strings
- `build_apply_commands` enforces routing order: insert device names sent before channel slot assignments (Pitfall 3 from research)
- XPatch data preserved in JSON snapshot but hardcoded out of all apply/send paths
- 42 unit tests pass, 264 total suite passes with zero regressions

## Task Commits

1. **Tasks 1 + 2: Template core module (save/load/diff/apply/CRUD + naming)** - `a146b57` (feat)

## Files Created/Modified

- `ssl-matrix-client/templates.py` — Template save/load/diff/apply core logic; exports 9 public functions + TEMPLATE_DIR constant
- `tests/test_templates.py` — 42 unit tests across 7 test classes
- `tests/conftest.py` — Added "templates" to import shim loop

## Decisions Made

- XPatch never applied via SET commands: all 7 XPatch SET commands fail silently on this console (V3.0/5, unconfigured hardware). Stored in template for forward compatibility only.
- Raw dict returned from `load_template` — no dataclass reconstruction. Callers index dict keys directly. Avoids schema versioning complexity.
- `template_dir` optional param on all I/O functions: tests pass `tmp_path`, production uses `TEMPLATE_DIR = ~/.ssl-matrix/templates/`.
- Tasks 1 and 2 committed together: both were tightly coupled (diff/apply are part of the same module as save/load); separating would have been artificial.

## Deviations from Plan

None - plan executed exactly as written. Both TDD phases (RED → GREEN → lint) completed as specified. The `apply_template` convenience wrapper was added alongside `build_apply_commands` as a thin alias (zero-impact addition).

## Issues Encountered

- ruff-format reformatted two files on first commit attempt; pre-commit hook auto-fixed and commit succeeded on second attempt. Standard workflow, not a blocker.

## Next Phase Readiness

- `templates.py` API is complete and stable; Plan 02 REPL/CLI commands can import and call these functions directly
- `build_apply_commands` returns `(bytes, str)` tuples — CLI can iterate and call `client.send(pkt)` per tuple
- Thread safety note for CLI implementation: caller must hold `client._lock` while reading `current_state` for diff, then release before sending commands

---
*Phase: 04-advanced-workflow-features*
*Completed: 2026-03-14*
