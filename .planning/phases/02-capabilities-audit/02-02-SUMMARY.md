---
phase: 02-capabilities-audit
plan: 02
subsystem: audit
tags: [ssl-matrix, udp, protocol, capabilities, audit, tier3, tier4]

# Dependency graph
requires:
  - phase: 02-capabilities-audit
    plan: 01
    provides: "CAPABILITIES.md with Tier 0-2 results; console confirmed online, all layers active"
provides:
  - "CAPABILITIES.md: Complete 105-handler audit — all Tier 3-4 handlers tested (63 PASS, 6 PARTIAL, 9 FAIL, 27 SKIP)"
  - "Roadmap impact table: XPatch mutations NOT FEASIBLE; TR/routing/chan-presets FEASIBLE; softkey edit blocked by no keymap"
  - "Critical finding: XPatch SET commands return no response — hardware unconfigured on this console"
  - "Critical finding: TR requires active project; fails silently without one"
  - "Critical finding: project names auto-assigned sequentially — name parameter ignored"
affects: [03-surface-features, 04-workflow, split-board, softkeys, vpot, tr-snapshots, projects]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tier 3-4 mutation testing: create test artifact → verify → restore → verify clean"
    - "Console restart round-trip: set mode → disconnect → restart (ephemeral socket) → wait 35-60s → reconnect → verify"
    - "TR workflow: requires active project before take/select/delete operations"
    - "Chain operations: save_inserts_to_chain creates chain; must deassign all channels before delete_chain"

key-files:
  created: []
  modified:
    - .planning/phases/02-capabilities-audit/CAPABILITIES.md

key-decisions:
  - "XPatch mutations are NOT FEASIBLE on this console — all 7 SET commands silently ignored; hardware unconfigured or absent"
  - "TR snapshots require active project — critical workflow constraint for any future TR feature implementation"
  - "Project names are auto-assigned sequential integers by console — build_make_new_project_with_name name param sets display label, not filesystem name"
  - "Softkey edit session remains blocked — no keymap was created on console before Plan 02; 13 handlers stay SKIP; feasible once keymap exists"
  - "ACK_PROFILE_NAME_EXISTS (891), ACK_PROFILE_NAME_IN_USE (901), ACK_GET_EDIT_KEYMAP_KEYCAP (631) are protocol enum entries but NOT in dispatch table — excluded from 105 count"
  - "Test project artifact (directory '2'/title '1') remains on console — cannot delete active project via protocol alone"
  - "Stereo insert (ACK_SET_CHAN_STEREO_INSERT) FAILS — console rejects stereo linking after individual assignment; likely requires pairing at creation"

patterns-established:
  - "Handler count: 63 PASS, 6 PARTIAL, 9 FAIL, 27 SKIP = 105 total (dispatch table exact count verified)"
  - "FAIL pattern for XPatch: console sends no reply to SET commands when hardware unconfigured — not a code error"
  - "SKIP pattern for softkeys: requires named keymap, not 'NONE' — must create via console UI first"

requirements-completed: [AUDIT-01, AUDIT-04]

# Metrics
duration: ~26min (automated testing session) + console restart wait times (~70s)
completed: 2026-03-13
---

# Phase 2 Plan 02: Tier 3-4 Capabilities Audit Summary

**63 PASS / 6 PARTIAL / 9 FAIL / 27 SKIP across all 105 dispatch handlers; XPatch mutations non-functional; TR requires active project; full routing/chan-preset/project CRUD confirmed working**

## Performance

- **Duration:** ~26 minutes of execution + ~70s console restart wait + human verify
- **Started:** 2026-03-13T19:37:50Z
- **Completed:** 2026-03-13T20:15:00Z
- **Tasks:** 2/2 (Task 2 checkpoint:human-verify approved — user confirmed all findings accurate)
- **Files modified:** 1

## Accomplishments

- Wire-tested all Tier 3 handlers: chan presets CRUD (5/5 PASS), routing insert/chain/preset ACKs (11/14 PASS, 1 FAIL stereo, 1 SKIP, 1 inconclusive), TR take/select/delete (all PASS with active project)
- Wire-tested all Tier 4 handlers: project CRUD (5/9 PASS, 1 PARTIAL, 3 SKIP), automation mode change + restart (PASS)
- XPatch mutation finding: all 7 SET commands (input/output -10dB, chan mode, device name, dest name, MIDI enable, MIDI channel) return no ACK — console doesn't respond when hardware unconfigured
- Completed definitive 105-handler count: confirmed dispatch table has exactly 105 entries; 3 protocol codes (631, 891, 901) are enum entries without dispatch handlers — excluded from count
- Documented critical constraint: TR requires active project (silently produces 0 snapshots without one)

## Task Commits

1. **Task 1: Run Tier 3 state mutations and Tier 4 high-risk handlers** — `09060eb` (feat)
2. **Task 2: Final audit verification** — checkpoint:human-verify APPROVED (user confirmed 63 PASS / 6 PARTIAL / 9 FAIL / 27 SKIP findings accurate)

## Files Created/Modified

- `.planning/phases/02-capabilities-audit/CAPABILITIES.md` — Updated with all Tier 3-4 results; final summary with 63/6/9/27 counts; roadmap impact table; audit conclusion

## Decisions Made

- XPatch SET mutations classified as FAIL (not SKIP) — the commands were sent and no ACK received; this is a functional failure on this console configuration
- Project test artifacts: project "2"/title "1" remains on console (cannot delete active project via protocol); marked in Outstanding Issues
- Softkey edit session handlers remain SKIP (no named keymap available) — this is the same finding as Plan 01; the pre-condition for Plan 02 (create keymap via console UI) was not met
- Console automation mode restored to Delta after 2 restart cycles; console back online

## Deviations from Plan

### Auto-fixed Issues

None — all tests executed as written, deviations documented below are findings not fixes.

### Notable Deviations from Expected Outcomes

1. **XPatch mutations non-functional (unexpected FAIL):**
   - Expected: XPatch SET commands would return ACKs updating state
   - Found: Console returns no reply to any of the 7 XPatch SET commands
   - Cause: XPatch hardware unconfigured/absent (mode=0 for all 16 channels; device/dest names empty)
   - Impact: XPatch routing control is NOT FEASIBLE via this console

2. **TR take requires active project (unexpected constraint):**
   - Expected: TR take/select/delete would work in any console state
   - Found: SEND_TAKE_TR_SNAP silently produces no snapshot without an active project
   - Cause: TR data is project-scoped in SSL firmware
   - Impact: Any TR workflow implementation must ensure active project first

3. **Project auto-naming (unexpected behavior):**
   - Expected: `build_make_new_project_with_name("AUDIT-TEMP")` creates project named "AUDIT-TEMP"
   - Found: Console creates project with sequential integer name ("1", "2") regardless of name parameter
   - Impact: Project CRUD workflow needs to use console-assigned name, not requested name

4. **Second restart extended boot time:**
   - Expected: Console back online within 35s (same as first restart)
   - Found: Second restart took ~120s to come back online
   - Cause: Unknown — possibly related to rapid consecutive restarts
   - Impact: Document 60-120s restart wait time in any restart workflow

5. **Test project artifact left on console:**
   - Expected: Full cleanup after project CRUD test
   - Found: Cannot delete active project/title via protocol — project "2"/title "1" remains
   - Impact: Console has 1 test project remaining; not blocking but not clean

## Issues Encountered

- ACK_SET_CHAN_STEREO_INSERT consistently returns "Insert in use" — stereo linking appears to be a creation-time operation, not a post-assignment one. FAIL result documented.
- ACK_CLEAR_INSERTS (cmd=10681) result inconclusive — sent with channel indices but returned error when channels already empty; couldn't confirm which index convention the console expects. Marked SKIP.
- Console hang after second restart: took ~2 minutes instead of ~35 seconds. Both ping and UDP were unresponsive. Eventual recovery confirmed Delta mode restored.

## Console State After Testing

- **Automation mode:** Delta (restored — required 2 restart cycles)
- **Active project:** "2"/title "1" (test artifact — cannot delete active project via protocol)
- **TR snapshots:** 0 (all cleaned up)
- **Chan name presets:** 0 (all cleaned up)
- **Matrix presets:** 0 (all cleaned up)
- **Chains:** 0 (all cleaned up)
- **TR enabled:** False (restored)
- **Insert assignments:** All channels clean (no test inserts remaining)

## Next Phase Readiness

- CAPABILITIES.md is committed, complete, and user-verified for all 105 handlers
- Phase 3 (Surface Features) can begin using CAPABILITIES.md as ground truth
- Priority features for Phase 3: TR snapshots, channel name presets, routing matrix — all confirmed FEASIBLE
- Blocker for softkeys: user must create a named keymap on console UI before softkey edit session can be tested/implemented
- Phase 2 is fully complete — both plans (02-01 and 02-02) executed and verified

---
*Phase: 02-capabilities-audit*
*Completed: 2026-03-13*
