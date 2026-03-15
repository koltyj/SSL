# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and the project follows Semantic Versioning.

## [Unreleased]

- No unreleased changes yet.

## [0.2.0] - 2026-03-15

### Added

- **SSL Sigma support (experimental)** — reverse-engineered from the Sigma Remote Control Android APK (v2.1.33) via JADX decompilation and Ghidra ARM Thumb2 disassembly, without access to real hardware
- Sigma wire protocol implementation (`sigma_protocol.py`): 24-byte header with magic byte 0x53, ProductType=4, 5 payload types (float, uint pair, string, none, uint-as-float), 50+ message IDs
- Sigma state models (`sigma_models.py`): 16-channel fader/pan/solo/mute/phase, monitor (7 sources), headphone (4 sources), insert A/B, level/metering, dim, talkback, network config
- Sigma message handlers (`handlers/sigma.py`): 40+ incoming message handlers, 14 outgoing command builders
- Sigma UDP client (`sigma_client.py`): threaded recv loop, watchdog, multicast join/leave, handshake on port 29940, keepalive
- `--console sigma` CLI flag to connect to Sigma consoles
- 10 Sigma-specific CLI commands: `sigma_channels`, `sigma_fader`, `sigma_pan`, `sigma_solo`, `sigma_mute`, `sigma_name`, `sigma_monitor`, `sigma_dim`, `sigma_headphone`, `sigma_state`
- Sigma ConsoleProfile (16 channels, delta-ctrl support)
- 160+ Sigma-specific tests across protocol, models, handlers, and client
- Comprehensive reverse-engineering documentation in `reverse-engineering/sigma/`

### Changed

- CLI now accepts `--console` flag (`matrix` default, `sigma` experimental)
- README updated with Sigma support section, dual-protocol architecture diagram, and call for hardware testers
- Package description and keywords updated to include Sigma

## [0.1.0] - 2026-03-15

### Added

- Public Python package metadata and `ssl-console` CLI entry point
- Textual terminal UI with channel, routing, template, and settings views
- Session template save, load, diff, apply, and delete workflows
- Public contributor, support, security, and conduct documentation
- GitHub Actions CI for lint, test, and packaging checks

### Changed

- Tightened README guidance for development and support workflows
- Replaced placeholder TUI test stubs with executable smoke tests

### Fixed

- Channel view resizing in the TUI now expands without duplicate widget IDs
