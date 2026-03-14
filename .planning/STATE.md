---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: completed
stopped_at: Completed 04-01-PLAN.md
last_updated: "2026-03-14T08:37:15.718Z"
last_activity: "2026-03-14 — Phase 4 Plan 1 complete: templates.py implemented with full TDD, 42 tests pass."
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 9
  completed_plans: 6
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Flying faders that respond to DAW automation playback and capture fader moves back into the DAW
**Current focus:** Phase 2 — Capabilities Audit

## Current Position

Phase: 4 of 6 (Advanced Workflow Features) — IN PROGRESS
Plan: 1 of N (Phase 4) — COMPLETE
Status: Phase 4 Plan 1 complete — templates.py with save/load/diff/apply/CRUD, 42 unit tests passing
Last activity: 2026-03-14 — Phase 4 Plan 1 complete: templates.py implemented with full TDD, 42 tests pass.

Progress: [█████░░░░░] 50% (2 of 4 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 2 (01-01, 01-02)
- Average duration: ~2 hours
- Total execution time: ~4 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 2/2 | ~4h | ~2h |

**Recent Trend:**
- Last 5 plans: 01-01 ✓, 01-02 ✓
- Trend: —

*Updated after each plan completion*
| Phase 02-capabilities-audit P01 | 3h | 2 tasks | 1 files |
| Phase 02-capabilities-audit P02 | 26min | 1 task | 1 files |
| Phase 03-console-surface-features P01 | 2min | 2 tasks | 4 files |
| Phase 03-console-surface-features P02 | 5min | 1 tasks | 3 files |
| Phase 04-advanced-workflow-features P01 | 4min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [VERIFIED]: All DAW control (HUI for PT, MCU for Ableton) works natively via ipMIDI — no custom bridge needed
- [VERIFIED]: delta-ctrl works in both Pro Tools and Ableton Live
- [VERIFIED]: DAW switching is hardware buttons on the Matrix — no software switching needed
- [DECIDED]: MatrixRemote is completely broken on Tahoe — ssl-matrix-client is the sole replacement
- [DECIDED]: Roadmap recalibrated to 5 phases: Audit → Surface Features → Workflow → Dock App
- [DECIDED]: Native macOS dock app (not menu bar widget) for GUI
- [DECIDED]: Session templates manually linked to project files, not auto-detected
- [DECIDED]: Capabilities audit is a standalone phase — verify before building
- [DECIDED]: Soft keys / V-pots / SuperCue come before split board and session templates
- [Config]: Console IP 192.168.1.2, Mac 192.168.1.50/24 on en11
- [Config]: Matrix firmware V3.0/5
- [Config]: Repo: github.com/koltyj/SSL
- [Phase 02-capabilities-audit]: SuperCue/Auto-Mon is NOT in UDP protocol on V3.0/5 — hardware-only, no UDP path
- [Phase 02-capabilities-audit]: Split board: all 4 DAW layers simultaneously active at protocol level; fader group assignment is console-surface config, not UDP
- [Phase 02-capabilities-audit]: Softkey edit session requires named keymap (not NONE); user must create via console UI before softkey testing
- [Phase 02-capabilities-audit]: XPatch mutations are NOT FEASIBLE on this console — all 7 SET commands silently ignored; hardware unconfigured or absent
- [Phase 02-capabilities-audit]: TR snapshots require active project — critical workflow constraint for any future TR feature implementation
- [Phase 02-capabilities-audit]: Project names are auto-assigned sequential integers by console — build_make_new_project_with_name name param sets display label, not filesystem name
- [Phase 02-capabilities-audit]: Test project artifact (directory '2'/title '1') remains on console — cannot delete active project via protocol alone
- [Phase 03-console-surface-features]: cc_names stored as flat list replaced wholesale on each reply (not keyed by layer/type)
- [Phase 03-console-surface-features]: Wheel mode label mapping 0-3 only (Pan/Linear/Boost-Cut/Off); values 4-5 accepted by set but shown as Unknown on read
- [Phase 03-console-surface-features]: SuperCue/Auto-Mon hardware-only on V3.0/5 — documented via do_supercue, no UDP path needed
- [Phase 03-console-surface-features]: Keymap name whitelist (keymap1-4) enforced in do_softkey_edit; NONE cannot open edit session
- [Phase 04-advanced-workflow-features]: XPatch never applied via SET commands in templates — all 7 XPatch SET commands fail silently on this console; stored in JSON for reference only
- [Phase 04-advanced-workflow-features]: load_template returns raw dict (no dataclass reconstruction) — callers index dict keys directly, avoids schema versioning complexity
- [Phase 04-advanced-workflow-features]: Routing restore order enforced in build_apply_commands: device names before channel slot assignments (Pitfall 3)
- [Phase 04-advanced-workflow-features]: Watchdog monitors SSL UDP heartbeat only — ipMIDI (HUI/MCU) is separate protocol, out of scope
- [Phase 04-advanced-workflow-features]: _needs_resync flag pattern avoids lock deadlock in _recv_loop when scheduling request_sync() after reconnect
- [Phase 04-advanced-workflow-features]: Split board is purely client-side bookkeeping — fader group assignment is console hardware surface config, not UDP

### Pending Todos

- ~~Plan Phase 2 (Capabilities Audit)~~ COMPLETE
- ~~Wire-test all 105 dispatch handlers against live console~~ COMPLETE (63 PASS, 6 PARTIAL, 9 FAIL, 27 SKIP)
- ~~Determine split board feasibility~~ ANSWERED: protocol level confirmed; fader group assignment is surface-config, not UDP
- ~~Map soft key, V-pot, SuperCue protocol capabilities~~ ANSWERED: SuperCue NOT IN PROTOCOL; softkey feasible with keymap; V-pot feasible with CC config
- Begin Phase 3 (Surface Features) planning

### Roadmap Evolution

- Phase 5 (Terminal UI) added before Dock App; former Phase 5 (Dock App) renumbered to Phase 6

### Blockers/Concerns

- ~~**P0:** ipMIDI Tahoe 26.2 compatibility~~ **RESOLVED**
- ~~**P1:** Pro Tools HUI communication error~~ **RESOLVED**
- ~~**P1:** delta-ctrl no effect~~ **RESOLVED — works in both DAWs**
- **P1:** Network topology unclear — ipMIDI works over Wi-Fi (en0) unexpectedly. Functional but not understood.
- **P1:** XPatch chains parse assumes 8 link elements — may be wrong for some console configs
- ~~**P2:** ssl-matrix-client handlers are code-verified but not wire-tested against live console~~ **RESOLVED — all 105 handlers wire-tested**

## Session Continuity

Last session: 2026-03-14T08:37:15.716Z
Stopped at: Completed 04-01-PLAN.md
Resume file: None
