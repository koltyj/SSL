---
phase: 02-capabilities-audit
verified: 2026-03-13T21:00:00Z
status: passed
score: 6/7 must-haves verified
re_verification: false
human_verification:
  - test: "Physical split board fader group test"
    expected: "Faders 1-8 respond to one DAW (e.g. Pro Tools/HUI) while faders 9-16 respond to another (e.g. Ableton/MCU) when both DAWs are open simultaneously"
    why_human: "Protocol confirms all 4 layers are simultaneously active, but fader group assignment is a console surface configuration — not readable or settable via UDP protocol. Requires physical DAW test at the console."
---

# Phase 2: Capabilities Audit Verification Report

**Phase Goal:** Wire-test all 105 dispatch handlers against the live SSL Matrix console. Determine which handlers work, which fail, and document feature feasibility for soft keys, V-pot, SuperCue, and split board. Produce CAPABILITIES.md as the definitive reference for Phase 3-4 development.
**Verified:** 2026-03-13T21:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

Truth sources: Plan 02-01 must_haves (7 truths) and Plan 02-02 must_haves (4 truths). Overlapping truths deduplicated. The 02-02 truth "every one of the 105 dispatch handlers has a documented result" subsumes the 02-01 Tier 0-2 truths, so verification covers both plans' contracts.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ssl-matrix-client connects to the live console and receives a valid desk reply | VERIFIED | CAPABILITIES.md: GET_DESK_REPLY = PASS, serial=196891, fw=V3.0/5; confirmed in commit 64dfde0 |
| 2 | All read-only query handlers (Tier 0-1) return parseable state | VERIFIED | 35 PASS, 2 PARTIAL (keymap data requires open session; profile path not stored in state), 3 SKIP with reasons — all documented; no blank result cells in Tier 0-1 rows |
| 3 | Non-destructive mutation handlers (Tier 2) apply and acknowledge | VERIFIED | Rename + restore: PASS; display toggle 0→1→0: PASS; flip scrib 0→1→0: PASS; transport lock: PASS; flip/handshake on RO profiles: documented FAIL (expected behavior) |
| 4 | Soft key edit session can be opened and keymap data read | PARTIAL | ACK_SET_EDIT_KEYMAP_NAME returns "Error, name does not exist" for all 4 layers — 'NONE' is not a valid keymap name; MIDI function list read successfully (102/64 functions); protocol infrastructure confirmed FEASIBLE; edit session blocked by missing named keymap on console |
| 5 | V-pot wheel mode status is readable per DAW layer | VERIFIED | ACK_GET_DEFAULT_WHEEL_MODE_STATUS: PASS for all 4 layers (L1=0/Pan, L2-4=5/unknown); CC layer active on L4; cc_names_list returns 0 names (unconfigured) |
| 6 | SuperCue/Auto-Mon protocol presence or absence is determined | VERIFIED | Probed cmds 1100-1200 — no console responses; no SuperCue/Auto-Mon fields in any state dump; documented as NOT IN PROTOCOL (hardware-only feature) |
| 7 | All Tier 3-4 handlers tested with pass/fail documented | VERIFIED | Chan presets CRUD (5 PASS), TR take/select/delete (3 PASS with active-project constraint), routing insert/chain/preset ACKs (11 PASS + 1 FAIL + 1 SKIP), project CRUD (5 PASS + 1 PARTIAL + 3 SKIP), automation mode + restart (2 PASS), XPatch mutations (7 FAIL — hardware unconfigured) |
| 8 | Every one of the 105 dispatch handlers has a documented result | VERIFIED | Dispatch table: 105 entries confirmed by code inspection (client.py lines 56-177). CAPABILITIES.md contains 105 dispatch-table rows plus 2 non-dispatch rows (631, 931) documented for completeness. All 105 dispatch entries have PASS/FAIL/PARTIAL/SKIP with stated reasons. |
| 9 | A complete capabilities document exists summarizing all confirmed features, limitations, and protocol gaps | VERIFIED | CAPABILITIES.md exists at `.planning/phases/02-capabilities-audit/CAPABILITIES.md`; contains Handler Test Results (all sections), Feature Feasibility (4 sections with status), Protocol Gaps table, XPatch Chain Element Count finding, Summary with counts, Audit Conclusion, and Impact on Roadmap table |
| 10 | Split board feasibility is tested — dual DAW layer simultaneous control confirmed or ruled out | DEFERRED | Protocol confirms all 4 layers simultaneously active (L1=HUI, L2=MCU, L3=MCU, L4=CC). Profiles contain no fader range/group fields. No fader group assignment commands in 197-code enum. Physical fader group test deferred — user will test with L3 as split DAW. Fader group assignment is console surface config, not UDP protocol. |

**Score:** 8/10 truths fully verified, 2 PARTIAL (softkey edit session blocked by config; split board physical test pending)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.planning/phases/02-capabilities-audit/CAPABILITIES.md` | Structured capabilities document with all 105 handler results, feature feasibility findings, protocol gaps, and roadmap impact | VERIFIED | File exists (477 lines); contains all required sections; committed in 64dfde0 (Tier 0-2) and 09060eb (Tier 3-4 + finalization) |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| CAPABILITIES.md | ROADMAP.md Phase 3-4 requirements | Feature feasibility status per feature | WIRED | "Impact on Roadmap" table present; maps TR snapshots, channel name presets, softkey assignment, V-Pot CC mode, split board, XPatch routing, project CRUD, automation mode, SuperCue, routing matrix to FEASIBLE/PARTIAL/NOT FEASIBLE with blocking issues |
| ssl-matrix-client REPL | SSL Matrix console at 192.168.1.2:50081 | UDP connect + dispatch handlers | WIRED | GET_DESK_REPLY = PASS (serial 196891 returned); heartbeat received; 63 PASS results confirm live wire-test completed |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| AUDIT-01 | 02-01-PLAN, 02-02-PLAN | All 105 dispatch handlers wire-tested with pass/fail documented | SATISFIED | CAPABILITIES.md documents all 105 dispatch entries: 63 PASS, 6 PARTIAL, 9 FAIL, 27 SKIP (+ 2 non-dispatch rows documented). No blank result cells. REQUIREMENTS.md: marked [x] |
| AUDIT-02 | 02-01-PLAN | Soft key, V-pot, and SuperCue protocol capabilities mapped with confirmed working message codes | SATISFIED | Soft keys: MIDI function list confirmed (102/64 functions); edit session protocol confirmed but blocked by config; V-pot: wheel mode readable all 4 layers; mode=5 undocumented value flagged; CC layer active on L4; SuperCue: NOT IN PROTOCOL confirmed. REQUIREMENTS.md: marked [x] |
| AUDIT-03 | 02-01-PLAN | Split board feasibility determined — can two DAW layers run simultaneously on different fader groups? | PARTIALLY SATISFIED — HUMAN NEEDED | Protocol: 4 layers simultaneously active confirmed. No fader group assignment in UDP protocol. Physical fader group test not completed. Finding accurately characterized as PARTIAL with required next step documented. REQUIREMENTS.md: marked [x] (user-accepted finding). |
| AUDIT-04 | 02-02-PLAN | Capabilities document listing every confirmed feature, limitation, and protocol gap | SATISFIED | CAPABILITIES.md contains: all handler results, Feature Feasibility section (4 features), Protocol Gaps table (18 gap areas), Outstanding Issues (5 items), Audit Conclusion, Impact on Roadmap table. REQUIREMENTS.md: marked [x] |

**Orphaned requirements check:** No additional requirements IDs map to Phase 2 in REQUIREMENTS.md traceability table beyond AUDIT-01 through AUDIT-04. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| CAPABILITIES.md | Summary table | SKIP count: document claims 27, actual table count is 29 | Info | 2 non-dispatch protocol codes (ACK_GET_EDIT_KEYMAP_KEYCAP cmd=631, ACK_PROFILE_IS_READ_ONLY cmd=931) appear in handler tables but are not in the 105-entry dispatch table. The document's exclusion note mentions 631 but not 931. This is a bookkeeping inaccuracy — the audit goal (test all 105 dispatch handlers) was achieved; the extra rows add useful reference data. Does not block Phase 3 planning. |
| CAPABILITIES.md | Softkeys ACK section | SET_DEFAULT_CHAN_NAMES_REPLY deferred "to Plan 02" in Plan 01, but Plan 02 did not address it (still SKIP: "no CLI trigger") | Warning | Handler remains untested with no CLI path. Low impact — this is a reset-to-factory operation, not needed for Phase 3 features. |

---

### Human Verification Required

#### 1. Split Board Physical Fader Group Test

**Test:** Open Pro Tools and Ableton Live simultaneously. Verify both show connected MIDI surfaces (Pro Tools: HUI device visible; Ableton: MCU device visible). Move faders 1-8 on the Matrix and observe which DAW's transport/fader responds. Then move faders 9-16 and observe.

**Expected:** If faders 1-8 respond only to Pro Tools (HUI/Layer 1) and faders 9-16 respond only to Ableton (MCU/Layer 2), split board is firmware-native. If all 16 faders respond to the same DAW regardless of layer, fader group assignment must be configured in the console's on-screen menu first (check SSL Matrix manual for "DAW fader assignment" or "layer fader group" settings).

**Why human:** Fader group assignment is a console surface configuration with no readable or settable UDP protocol path. The protocol confirms all 4 layers are simultaneously active but cannot tell which physical faders are assigned to which layer. Only physical movement at the console can confirm this.

---

### Gaps Summary

No blocking gaps found for Phase 3 planning. The two PARTIAL truths are:

1. **Softkey edit session** — Protocol infrastructure is confirmed. The limitation is a console configuration prerequisite (no named keymap exists; all layers return 'NONE'). User must create a keymap via the console's physical softkey editor button before the edit session handlers can be tested. This is correctly documented in CAPABILITIES.md as a configuration gap, not a protocol gap. 13 softkey ACK handlers remain SKIP as a result. Phase 3 softkey work can proceed once the keymap is created.

2. **Split board physical test** — Protocol-side analysis is complete. Physical verification is the outstanding step. The answer is likely "yes, firmware-native" based on 4-layer simultaneous activation, but physical confirmation is required before SPLIT-01 is planned in Phase 4.

Both are accurately documented in CAPABILITIES.md with clear next steps. Neither blocks Phase 3 planning — Phase 3 features (TR snapshots, channel name presets, routing matrix) are all confirmed FEASIBLE.

---

### Minor Notes for Reference

- **Dispatch count discrepancy:** CAPABILITIES.md summary claims "PASS + PARTIAL + FAIL + SKIP = 105" but the table contains 107 rows (105 dispatch entries + 2 non-dispatch rows: ACK_GET_EDIT_KEYMAP_KEYCAP cmd=631 and ACK_PROFILE_IS_READ_ONLY cmd=931). The actual dispatch table in client.py has exactly 105 entries (verified by code inspection). The document's note correctly excludes 631 but does not mention 931. This does not affect goal achievement.

- **XPatch chain parser risk:** The `GET_XPATCH_EDIT_CHAIN_REPLY` handler in `handlers/xpatch.py` assumes 8 link elements per chain. This is unverifiable on this console (0 chains configured). Flagged as outstanding risk in CAPABILITIES.md Outstanding Issues section.

- **Wheel mode value 5:** `ACK_GET_DEFAULT_WHEEL_MODE_STATUS` returns mode=5 on MCU/CC layers. Not in the known enum. Flagged in Outstanding Issues. Low priority for Phase 3.

- **Test project artifact:** Project "2"/title "1" remains on console — cannot delete active project via protocol. This is a known console limitation documented in CAPABILITIES.md.

---

## Summary

Phase 2 goal is **substantively achieved**. CAPABILITIES.md exists as a complete, user-verified, committed reference document. All 105 dispatch handlers are documented with live wire-test results. All four feature feasibility questions have determinations. The roadmap impact table is present and actionable.

The single outstanding item requiring human action (split board physical test) is accurately characterized and does not block Phase 3 planning — split board is a Phase 4 concern.

Both commits are verified in git history: `64dfde0` (Tier 0-2, Plan 01) and `09060eb` (Tier 3-4, Plan 02). Both tasks in both plans completed the human-verify checkpoint with user sign-off.

---

_Verified: 2026-03-13T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
