---
phase: 04
slug: advanced-workflow-features
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x-8.x (from pyproject.toml `pytest>=7,<9`) |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` testpaths = ["tests"] |
| **Quick run command** | `python3 -m pytest tests/test_templates.py tests/test_watchdog.py tests/test_split.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_templates.py tests/test_watchdog.py tests/test_split.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|--------|----------|-----------|-------------------|-------------|--------|
| SESS-01 | Template save serializes ConsoleState to JSON | unit | `pytest tests/test_templates.py::TestTemplateSave -x` | ❌ W0 | ⬜ pending |
| SESS-01 | Template load deserializes JSON back to typed state dict | unit | `pytest tests/test_templates.py::TestTemplateLoad -x` | ❌ W0 | ⬜ pending |
| SESS-01 | Template CRUD: list, delete, show work on `~/.ssl-matrix/templates/` | unit (tmp_path) | `pytest tests/test_templates.py::TestTemplateCRUD -x` | ❌ W0 | ⬜ pending |
| SESS-01 | Template name generated as `{title}_{timestamp}.json` | unit | `pytest tests/test_templates.py::TestTemplateNaming -x` | ❌ W0 | ⬜ pending |
| SESS-02 | Diff shows correct changes between template and current state | unit | `pytest tests/test_templates.py::TestTemplateDiff -x` | ❌ W0 | ⬜ pending |
| SESS-02 | Routing restore sends correct builder calls in correct order | unit (mock send) | `pytest tests/test_templates.py::TestRoutingRestore -x` | ❌ W0 | ⬜ pending |
| SESS-02 | XPatch stored in template but skipped on restore | unit | `pytest tests/test_templates.py::TestXpatchSkip -x` | ❌ W0 | ⬜ pending |
| SPLIT-01 | Split command stores assignment in client state | unit | `pytest tests/test_split.py::TestSplitState -x` | ❌ W0 | ⬜ pending |
| BRDG-01 | Watchdog detects stale heartbeat and calls _trigger_reconnect | unit (mock time) | `pytest tests/test_watchdog.py::TestWatchdog -x` | ❌ W0 | ⬜ pending |
| BRDG-01 | Reconnect flag prevents watchdog storm | unit | `pytest tests/test_watchdog.py::TestReconnectGuard -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_templates.py` — stubs for SESS-01, SESS-02 (template save/load/diff/restore)
- [ ] `tests/test_split.py` — stubs for SPLIT-01 (split state tracking)
- [ ] `tests/test_watchdog.py` — stubs for BRDG-01 (heartbeat watchdog)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Template load restores console state correctly | SESS-01 | Requires live console hardware | Load template, verify channel names/routing match on console surface |
| Split board CLI guidance produces correct button press instructions | SPLIT-01 | Fader group assignment is console surface-config, not UDP | Run split command, follow instructions, verify fader assignment on console |
| Watchdog auto-reconnects after console power cycle | BRDG-01 | Requires physical console restart | Power cycle console, verify client auto-reconnects within timeout |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
