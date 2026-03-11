---
phase: 2
slug: capabilities-audit
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual protocol exercise via ssl-matrix-client REPL + sniff_50081.py |
| **Config file** | None — interactive hardware testing |
| **Quick run command** | `python3 -m ssl_matrix_client --ip 192.168.1.2 channels` |
| **Full suite command** | Full audit session: connect + all 10 handler groups tested |
| **Estimated runtime** | ~60-90 minutes per full audit session |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m ssl_matrix_client --ip 192.168.1.2 channels` (quick connectivity check)
- **After every plan wave:** Run full handler group test for that wave's scope
- **Before `/gsd:verify-work`:** All 105 handlers must have pass/fail results documented
- **Max feedback latency:** N/A — hardware testing is inherently manual

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | AUDIT-01 | manual hardware | `python3 -m ssl_matrix_client --ip 192.168.1.2 state` | ✅ existing | ⬜ pending |
| 02-01-02 | 01 | 1 | AUDIT-01 | manual hardware | REPL: connect + channels + layers + profiles | ✅ existing | ⬜ pending |
| 02-01-03 | 01 | 1 | AUDIT-01 | manual hardware | REPL: Tier 2 mutations (rename, toggle) | ✅ existing | ⬜ pending |
| 02-01-04 | 01 | 2 | AUDIT-01 | manual hardware | REPL: Tier 3 state mutations (presets, TR) | ✅ existing | ⬜ pending |
| 02-01-05 | 01 | 2 | AUDIT-01 | manual hardware | REPL: Tier 4 high-risk (automode, restart, projects) | ✅ existing | ⬜ pending |
| 02-02-01 | 02 | 1 | AUDIT-02 | manual hardware | REPL: raw softkey commands (610, 641, 620, 650, 680) | ✅ existing | ⬜ pending |
| 02-02-02 | 02 | 1 | AUDIT-02 | manual hardware | REPL: raw wheel mode (1060, 1070) + CC names (950) | ✅ existing | ⬜ pending |
| 02-02-03 | 02 | 1 | AUDIT-02 | manual hardware | Physical console: SuperCue button check + protocol probe | N/A manual | ⬜ pending |
| 02-03-01 | 03 | 2 | AUDIT-03 | manual hardware | REPL: layers + profiles + dual-layer assignment | ✅ existing | ⬜ pending |
| 02-04-01 | 04 | 2 | AUDIT-04 | documentation | `test -f CAPABILITIES.md` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `CAPABILITIES.md` template in phase dir — structured output document for AUDIT-04
- [ ] Baseline state capture script/command documented for pre-test snapshots

*No test framework installation needed — testing is interactive/hardware via existing REPL.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| All 105 dispatch handlers respond correctly | AUDIT-01 | Hardware — requires live SSL Matrix console | Execute tiered REPL commands, observe console surface, record pass/fail |
| Softkey edit session opens/saves | AUDIT-02 | Hardware — keymap changes visible on console surface | raw 610/620/650/680 sequence, verify physical button behavior |
| V-pot wheel mode reads correctly | AUDIT-02 | Hardware — V-pot behavior observable only on console | raw 1060 per layer, verify LED ring response |
| SuperCue reachable via protocol | AUDIT-02 | Hardware — no known message code, need physical investigation | Check console surface for SuperCue button, probe HUI transport |
| Split board dual-layer active | AUDIT-03 | Hardware — fader group separation observable only physically | Assign two profiles, observe both DAWs controlling separate fader groups |
| XPatch chain element count | AUDIT-01 | Hardware — chain structure varies by console config | Run sniffer parallel to chains command, compare raw bytes |

---

## Validation Sign-Off

- [ ] All tasks have manual verification instructions defined
- [ ] Sampling continuity: each handler group tested in sequence per tier
- [ ] Wave 0 covers CAPABILITIES.md template creation
- [ ] No watch-mode flags
- [ ] Feedback latency: N/A (manual hardware testing)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
