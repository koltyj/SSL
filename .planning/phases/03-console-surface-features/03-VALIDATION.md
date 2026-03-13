---
phase: 3
slug: console-surface-features
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python3 -m pytest tests/ -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/ -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | ADV-01 | unit+integration | `python3 -m pytest tests/ -v -k softkey` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ADV-02 | unit+integration | `python3 -m pytest tests/ -v -k vpot` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ADV-03 | manual | N/A (not in protocol) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_softkeys.py` — stubs for ADV-01 soft key macro tests
- [ ] `tests/test_vpots.py` — stubs for ADV-02 V-pot/wheel mode tests
- [ ] `tests/conftest.py` — shared fixtures (exists, may need extension)

*Existing pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Soft key macros execute in Pro Tools | ADV-01 | Requires live console + DAW | Program keymap via CLI, press soft key, verify DAW action |
| Soft key macros execute in Ableton | ADV-01 | Requires live console + DAW | Program keymap via CLI, press soft key, verify DAW action |
| V-pot controls DAW parameter | ADV-02 | Requires live console + DAW | Set wheel mode, turn encoder, verify parameter change |
| SuperCue/Auto-Mon workflow | ADV-03 | Not in UDP protocol | Document hardware-only status or implement transport helper |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
