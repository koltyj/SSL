---
phase: 05
slug: terminal-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `python3 -m pytest tests/test_tui.py -x -v` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~8 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_tui.py -x -v`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 8 seconds

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|--------|----------|-----------|-------------------|-------------|--------|
| TUI-01 | `tui` subcommand launches app without error | smoke | `pytest tests/test_tui.py::test_app_launches -x` | ❌ W0 | ⬜ pending |
| TUI-02 | Channels tab shows channel names from ConsoleState | unit | `pytest tests/test_tui.py::test_channel_view_renders -x` | ❌ W0 | ⬜ pending |
| TUI-03 | Status bar shows health dot and project name | unit | `pytest tests/test_tui.py::test_status_bar -x` | ❌ W0 | ⬜ pending |
| TUI-04 | Number keys 1-4 switch tabs | unit | `pytest tests/test_tui.py::test_tab_switching -x` | ❌ W0 | ⬜ pending |
| TUI-05 | Command palette opens on `:` keypress | unit | `pytest tests/test_tui.py::test_command_palette_opens -x` | ❌ W0 | ⬜ pending |
| TUI-06 | recv thread state update reaches widget via post_message | unit | `pytest tests/test_tui.py::test_thread_bridge -x` | ❌ W0 | ⬜ pending |
| TUI-07 | Channel name change triggers flash highlight | unit | `pytest tests/test_tui.py::test_flash_highlight -x` | ❌ W0 | ⬜ pending |
| TUI-08 | Disconnect overlay appears when desk goes offline | unit | `pytest tests/test_tui.py::test_disconnect_overlay -x` | ❌ W0 | ⬜ pending |
| TUI-09 | Overlay dismisses when desk comes back online | unit | `pytest tests/test_tui.py::test_reconnect_overlay_dismissed -x` | ❌ W0 | ⬜ pending |
| TUI-10 | SSL theme is applied (custom colors present) | unit | `pytest tests/test_tui.py::test_ssl_theme -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_tui.py` — stubs for TUI-01 through TUI-10
- [ ] `pytest-asyncio` in dev deps
- [ ] conftest.py shim update for tui modules

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SSL theme visually matches console aesthetic | TUI-10 | Color appearance is subjective | Launch TUI, compare visual feel to SSL console |
| Flash highlight is visible and non-distracting | TUI-07 | Timing perception is subjective | Trigger channel name change, observe highlight duration |
| Full-screen overlay is readable during disconnect | TUI-08 | Terminal rendering varies | Disconnect console, verify overlay text is centered and readable |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 8s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
