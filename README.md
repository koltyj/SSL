# SSL Console Control

**A reverse-engineered Python client for controlling SSL mixing consoles over Ethernet.**

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![CI](https://github.com/koltyj/SSL/actions/workflows/ci.yml/badge.svg)

![TUI Screenshot](https://raw.githubusercontent.com/koltyj/SSL/main/docs/screenshots/tui-channels.svg)

## What is this

SSL's analog consoles and summing mixers (Matrix, Duality, AWS 900, AWS 924/948, Sigma) have digital control capabilities -- flying faders, DAW integration, insert routing, and session recall. SSL's official control software (MatrixRemote for consoles, Sigma Remote for the Sigma) hasn't been maintained for modern macOS.

This project is a from-scratch Python replacement. The Matrix/Duality/AWS protocol was reverse-engineered from the SSL MatrixRemote Java app and live packet captures. The Sigma protocol was reverse-engineered from the Sigma Remote Android APK via JADX decompilation and Ghidra ARM Thumb2 analysis. The client speaks each console's native UDP protocol and exposes available features through a terminal UI, interactive REPL, and scriptable CLI.

This is an independent community project and is not affiliated with or endorsed by Solid State Logic.

## Features

- **Real-time TUI dashboard** with SSL-inspired dark theme, tabbed layout, and command palette
- **Channel strip monitoring** -- names, DAW layer assignments, insert routing, automation modes
- **60+ CLI commands** covering channels, routing, profiles, projects, Total Recall, XPatch, softkeys
- **Experimental Sigma CLI support** for reverse-engineered channel and monitor control
- **Session templates** -- save, load, diff, and apply full console state snapshots
- **Connection health monitoring** with auto-reconnect and heartbeat tracking
- **Interactive REPL** and one-shot CLI mode for scripting
- **CI-validated lint, build, protocol, CLI, template, and TUI smoke checks**
- **Minimal dependencies** -- Python stdlib + [Textual](https://github.com/Textualize/textual) for the TUI

## Quick Start

```bash
pip install ssl-console-client

# Launch the Matrix REPL
ssl-console

# Launch the Matrix TUI
ssl-console tui

# Launch the Sigma REPL
ssl-console --console sigma

# Launch the Sigma TUI
ssl-console --console sigma tui

# One-shot commands
ssl-console channels
ssl-console --ip 10.0.0.50 layers
ssl-console --console sigma sigma_channels
ssl-console -v status
```

Or install from source (in a virtual environment):

```bash
git clone https://github.com/koltyj/SSL.git
cd SSL
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

Matrix defaults to IP `192.168.1.2` on UDP port `50081`. Sigma defaults to IP `192.168.1.201` and currently defaults to port `50081` in this client, but that Sigma port remains inferred rather than hardware-validated. Pass `--ip` and/or `--port` to override.

The client assumes the console is reachable on a trusted local network. See [SECURITY.md](SECURITY.md) before exposing any control host outside a studio LAN.

## Terminal UI

The TUI provides a full-screen dashboard built on Textual. The tab set depends on the selected console family.

Matrix-family tabs:

- **Channels** -- live channel strip display with names, DAW layer info, and flash highlights on state changes
- **Routing** -- insert matrix and XPatch configuration
- **Templates** -- session template management (save/load/diff)
- **Settings** -- console configuration, profiles, automation modes

Sigma tabs:

- **Channels** -- 16-channel overview with name, fader, pan, solo, mute, and phase state
- **Monitor** -- monitor source status, dim values, and headphone source status
- **Console** -- insert, level, talkback, oscillator, and network overview
- **Notes** -- operational caveats and validation guidance for the experimental Sigma path

The Sigma command palette uses Sigma-native actions like `fader`, `pan`, `solo`, `mute`, `phase`, `monitor source`, `headphones`, and `dim` instead of Matrix routing/template commands.

Key bindings:

| Key | Action |
|-----|--------|
| `1`-`4` | Switch tabs |
| `/` | Open command palette |
| `q` | Quit |

A status bar shows connection health (green/yellow/red dot), active project, and last loaded template. A disconnect overlay appears automatically when the console goes offline.

## CLI Commands

### Connection

| Command | Description |
|---------|-------------|
| `connect` | Connect to the console and sync state |
| `disconnect` | Disconnect |
| `status` | Show console info, firmware, heartbeat age |
| `health` | Detailed connection health report |

### Channels & Profiles

| Command | Description |
|---------|-------------|
| `channels` | List all channel names |
| `rename <ch> <name>` | Rename a channel (6 char max) |
| `profiles` | List available DAW profiles |
| `layers` | Show DAW layer protocol assignments |
| `setprofile <layer> <name>` | Assign a profile to a DAW layer |
| `transportlock <0-4>` | Set transport lock to a specific layer |

### Routing & Inserts

| Command | Description |
|---------|-------------|
| `matrix` | Show insert matrix assignments |
| `assign <ch> <slot> <dev>` | Assign a device to an insert slot |
| `stereo <ch> <on/off>` | Toggle stereo linking |
| `chains` | Show insert chains |
| `devices` | List available insert devices |
| `matrix_presets` | List routing presets |

### XPatch

| Command | Description |
|---------|-------------|
| `xpatch_setup` | Show XPatch configuration |
| `xpatch_routes` | Display current XPatch routing |
| `xpatch_route <ch> <src>` | Set an XPatch route |
| `xpatch_presets` | List XPatch presets |

### Projects & Total Recall

| Command | Description |
|---------|-------------|
| `projects` | List projects and titles on the console |
| `new_project <name>` | Create a new project |
| `select_title <proj> <title>` | Load a project title |
| `tr_snapshots` | List Total Recall snapshots |
| `tr_take` | Take a TR snapshot |
| `tr_select <idx>` | Recall a TR snapshot |

### Softkeys

| Command | Description |
|---------|-------------|
| `softkey_keymap` | Show current keymap |
| `softkey_edit <key>` | Edit a softkey assignment |
| `softkey_midi <key> ...` | Assign MIDI output to a softkey |
| `softkey_usb <key> ...` | Assign USB HID output to a softkey |

### Session Templates

| Command | Description |
|---------|-------------|
| `template save <name>` | Save current console state |
| `template load <name>` | Restore a saved template |
| `template diff <name>` | Compare live state to a template |
| `template list` | List saved templates |
| `split <mode>` | Split board between two DAW layers |

### Automation & Control

| Command | Description |
|---------|-------------|
| `automode <mode>` | Set automation mode (read/write/touch/latch) |
| `motors <on/off>` | Enable/disable flying faders |
| `mdac <on/off>` | Enable/disable MDAC mode |
| `restart` | Restart the console firmware |

## Architecture

Single-socket UDP client with a threaded receive loop and dispatch table.

```
cli.py (cmd.Cmd REPL + argparse one-shot)
  ├── tui.py (Textual TUI application)
  ├── client.py (SSLMatrixClient — Matrix/Duality/AWS)
  │     ├── protocol.py (TxMessage/RxMessage, 197 MessageCodes)
  │     ├── models.py (ConsoleState dataclass tree)
  │     └── handlers/ (10 handler modules, ~105 dispatch entries)
  │           ├── connection.py, channels.py, profiles.py, delta.py
  │           ├── routing.py, projects.py, total_recall.py, chan_presets.py
  │           ├── xpatch.py, softkeys.py
  │           └── sigma.py          — Sigma message handlers
  └── sigma_client.py (SSLSigmaClient — Sigma)
        ├── sigma_protocol.py (SigmaTxMessage/SigmaRxMessage, 50+ message IDs)
        └── sigma_models.py (SigmaState dataclass tree)
```

The Matrix and Sigma consoles use **different wire protocols**. The Matrix protocol has a 16-byte big-endian header (cmdCode, destCode, deskSerial, remoteSerial). The Sigma protocol has a 20+ byte header with magic byte `'S'`, ProductType=4, and typed payloads (float, uint, string). Matrix uses UDP port `50081`; Sigma currently defaults to `50081` in this client, but that port is still inferred from reverse engineering rather than hardware-validated.

## Supported Consoles

The client auto-detects the console model on connection and enables the appropriate feature set.

| Console | Channels | Insert Matrix | XPatch | DAW Layers | Delta | Status |
|---------|----------|---------------|--------|------------|-------|--------|
| SSL Matrix | 32 | Yes | Yes (16ch) | Yes (4) | Yes | Tested |
| SSL Duality | 96 | -- | -- | -- | -- | Untested |
| SSL AWS 900 | 48 | -- | -- | -- | -- | Untested |
| SSL AWS 924/948 | 48 | -- | -- | -- | -- | Untested |
| SSL Sigma | 16 | A/B inserts | -- | -- | Yes | **Experimental** |

Matrix/Duality/AWS share: channel names, projects, Total Recall, channel name presets, UDP on port 50081.

Matrix tested with firmware V3.0/5. Other consoles and firmware versions may work but are untested — reports welcome.

### Sigma Support (Experimental)

The SSL Sigma uses a **different wire protocol** from the Matrix-family consoles. Sigma support was reverse-engineered from the Sigma Remote Control Android APK (v2.1.33) via JADX decompilation and Ghidra ARM Thumb2 disassembly — **without access to real hardware**.

Current release position:
- public and usable as an **experimental** feature
- includes an experimental Sigma TUI with `Channels`, `Monitor`, `Console`, and `Notes` tabs
- not hardware-validated, so behavior on real Sigma units may differ from the current implementation

Sigma features implemented:
- 16-channel fader/pan/solo/mute/phase control
- Monitor section (7 sources, cut, dim, alt, mono)
- Headphone section (4 sources)
- Insert A/B with sum controls
- Level/metering control
- Talkback, oscillator, listenback
- Network configuration
- Connection handshake and keepalive

To connect to a Sigma:

```bash
ssl-console --console sigma
ssl-console --console sigma --ip 192.168.1.201
```

**If you own an SSL Sigma**, your help testing and validating is invaluable. Please [open an issue](https://github.com/koltyj/SSL/issues) with packet captures or behavior reports.

## Development

```bash
# Create a dev environment
python3 -m venv .venv
source .venv/bin/activate
pip install ".[dev]"

# Run all tests
python3 -m pytest tests/ -v

# Run a specific test file
python3 -m pytest tests/test_protocol.py -v

# Lint and format
python3 -m ruff check ssl-matrix-client tests
python3 -m ruff format ssl-matrix-client tests

# Build distribution artifacts
python3 -m build

# Pre-commit hooks (ruff, trailing whitespace, EOF fixer, debug statements)
pre-commit run --all-files
```

Tests use an import shim in `tests/conftest.py` to handle the hyphenated package directory. CI runs lint, tests, and packaging checks on Python 3.9 through 3.13. Tool configuration lives in `pyproject.toml`.

## Community

- [CONTRIBUTING.md](CONTRIBUTING.md) -- development setup, PR expectations, and test commands
- [SUPPORT.md](SUPPORT.md) -- how to ask for help or file actionable bug reports
- [SECURITY.md](SECURITY.md) -- security model and private reporting guidance
- [CHANGELOG.md](CHANGELOG.md) -- release history
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) -- expected community behavior

## License

MIT
