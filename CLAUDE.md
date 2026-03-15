# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python UDP client for controlling SSL mixing consoles (Matrix, Duality, AWS 900, AWS 924/948) over Ethernet. Reverse-engineered from the SSL MatrixRemote protocol and live packet captures. Runtime dependency: Textual (TUI).

## Running

```bash
python3 -m ssl-matrix-client                          # Interactive REPL
python3 -m ssl-matrix-client channels                  # One-shot command
python3 -m ssl-matrix-client --ip 10.0.0.5 layers     # Custom console IP
python3 -m ssl-matrix-client -v channels               # Debug logging
```

Default console IP: `192.168.1.2`, UDP port: `50081`.

No build step. Dev dependencies: `pip install pytest ruff pre-commit`.

## Architecture

**Single-socket UDP client with threaded receive loop and dispatch table.**

```
cli.py (cmd.Cmd REPL + argparse one-shot)
  ├── tui.py (Textual TUI application)
  │     ├── tui_widgets.py (ChannelStrip, ChannelView, DisconnectOverlay)
  │     ├── tui_views.py (RoutingView, TemplatesView, SettingsView)
  │     └── tui_commands.py (command palette provider)
  └── client.py (SSLMatrixClient)
        ├── protocol.py (TxMessage/RxMessage wire format, 197 MessageCodes)
        ├── models.py (ConsoleProfile, ConsoleState dataclass tree)
        ├── templates.py (session template save/load/diff/apply)
        └── handlers/ (10 handler modules, ~105 dispatch entries)
              ├── connection.py   — GET_DESK discovery, heartbeat
              ├── channels.py     — Channel names, scribble strips
              ├── profiles.py     — DAW layers (HUI/MCU/CC), transport lock
              ├── delta.py        — Automation mode, motors, MDAC, restart
              ├── routing.py      — Insert matrix V2, chains, presets
              ├── projects.py     — Project/title CRUD, directory listing
              ├── total_recall.py — TR snapshots
              ├── chan_presets.py  — Channel name presets
              ├── xpatch.py       — XPatch routing, presets, chains, MIDI
              └── softkeys.py     — Programmable keys, keymap editor
```

Each handler module has **builders** (Python → console) and **handlers** (console → Python). The client's `_build_dispatch_table()` maps `MessageCode` → handler function.

## Multi-Console Support

The client auto-detects the console model from `GET_DESK_REPLY` and reconfigures state dimensions and feature availability via `ConsoleProfile`. Features like insert matrix, XPatch, DAW layers, and delta automation are gated per-profile — only Matrix has all features. Duality and AWS boards get channels, projects, Total Recall, and channel name presets.

## Critical Design Constraints

1. **Port 50081 is sacred.** The console only responds to packets arriving on this port. The shared socket must bind to it. Exception: the `restart_console()` method uses an ephemeral socket — the board firmware freezes if restart arrives from port 50081.

2. **Thread safety via `_lock`.** The recv thread runs in a daemon thread and calls handlers that mutate `ConsoleState`. All state reads from the CLI thread must hold `self.client._lock`. All handler writes already run under the lock (dispatched inside `with self._lock:` in `_recv_loop`).

3. **Wire format is shared across all SSL consoles.** The 16-byte header is `[cmdCode:int, destCode:int, deskSerial:int, remoteSerial:int]`, big-endian. Payload serialization uses `TxMessage.write_*` / `RxMessage.get_*`.

4. **Protocol bounds checking.** `RxMessage.get_*` methods raise `BufferError` on truncated packets. `TxMessage.write_*` methods raise `ValueError` on buffer overflow. Handlers must tolerate `BufferError` — the recv loop catches it.

## Supported Consoles

| Console | Channels | Insert Matrix | XPatch | DAW Layers | Delta |
|---------|----------|---------------|--------|------------|-------|
| Matrix | 32 | Yes | Yes (16ch) | Yes (4) | Yes |
| Duality | 96 | No | No | No | No |
| AWS 900 | 48 | No | No | No | No |
| AWS 924/948 | 48 | No | No | No | No |

## Development

```bash
python3 -m pytest tests/ -v              # Run all tests
python3 -m pytest tests/test_protocol.py -v -k test_port  # Single test
ruff check ssl-matrix-client/ tests/     # Lint
ruff format ssl-matrix-client/ tests/    # Format
pre-commit run --all-files               # All hooks
```

Pre-commit hooks run ruff lint+format, trailing whitespace, EOF fixer, and debug statement checks on every commit.

Tests use an import shim in `tests/conftest.py` to work around the hyphenated package directory. Import with underscores: `from ssl_matrix_client.protocol import ...`

Tool config (ruff, pytest) lives in `pyproject.toml`.

## Protocol Reference

The wire format was reverse-engineered from SSL's MatrixRemote protocol. The 16-byte header and payload serialization are documented in `protocol.py`.
