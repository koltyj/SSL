# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Flying faders that respond to DAW automation playback and capture fader moves back into the DAW
**Current focus:** Phase 1 — Compatibility Verification

## Current Position

Phase: 1 of 4 (Compatibility Verification)
Plan: 01-02 in progress (DAW behavior verification)
Status: Ableton VERIFIED — Pro Tools HUI next
Last activity: 2026-02-25 — Ableton MCU fully working; Plan 01-01 complete

Progress: [████░░░░░░] 40%

## Performance Metrics

**Velocity:**
- Total plans completed: 1 (01-01)
- Average duration: ~2 hours (hands-on, includes network troubleshooting)
- Total execution time: ~2 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 1/2 | ~2h | ~2h |

**Recent Trend:**
- Last 5 plans: 01-01 ✓
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Research]: ipMIDI over Ethernet is the only transport — USB is firmware-only, NOT for DAW control
- [Research]: Pro Tools requires HUI protocol; Ableton requires MCU — they cannot share a port or protocol
- [Research]: Phase 1 is a hard gate — no code until Tahoe 26.2 compatibility confirmed empirically
- [Research]: delta-ctrl plugin ($50, SSL) is required for true MDAC-driven automation; verify Tahoe compat before purchasing
- [Research]: Disable EUCON in Pro Tools before any HUI testing to avoid metering bug
- [VERIFIED]: ipMIDI 2.0 works on macOS Tahoe 26.2 — P0 blocker resolved
- [VERIFIED]: MatrixRemote connects to SSL Matrix on Tahoe 26.2 over Ethernet
- [VERIFIED]: Ableton Live MCU control surface works via ipMIDI Port 3 — full transport, faders, scribble strips confirmed
- [Discovery]: CalDigit TS4 2.5GbE Ethernet does NOT get link with Matrix 100Mbps port — Anker USB Ethernet adapter works
- [Discovery]: Matrix static IP is 192.168.1.2; Mac Ethernet set to 192.168.1.50/24 on en11
- [Discovery]: ipMIDI multicast appears to work over en0 (Wi-Fi) even with Ethernet disconnected — network topology needs clarification
- [Config]: Persistent multicast routes set: 225.0.0.37 + 225.0.0.38 → "USB 10/100/1G/2.5G LAN" service
- [Config]: Matrix firmware is V3.0/5
- [Config]: JDK 21.0.10 (Temurin) installed at ~/Library/Java/JavaVirtualMachines/, JAVA_HOME in .zshrc

### Pending Todos

- Verify Pro Tools HUI on ipMIDI (which port? likely Port 1 or 2)
- Clarify network topology — how is Matrix reachable via Wi-Fi/en0?
- Test Local Network permission persistence after reboot (Tahoe bug)

### Blockers/Concerns

- ~~**P0:** ipMIDI Tahoe 26.2 compatibility is unverified~~ **RESOLVED — works**
- **P1:** delta-ctrl Tahoe compatibility unknown — verify before purchasing ($50).
- **P1:** MIDIKit HUI completeness at v0.11.0 needs hands-on validation against a live Pro Tools session before Phase 2 planning is complete.
- ~~**P1:** SSL Matrix firmware version unknown~~ **RESOLVED — V3.0/5**
- **P1:** Network path unclear — Anker adapter (en11) dropped but ipMIDI still works on en0. Need to understand topology for reliability.

## Session Continuity

Last session: 2026-02-25
Stopped at: Ableton MCU verified; Pro Tools HUI verification next
Resume file: .planning/phases/01-compatibility-verification/.continue-here.md
