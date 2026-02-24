# Roadmap: SSL Matrix Control Bridge

## Overview

Four phases that move the SSL Matrix from disconnected hardware to the functional center of a hybrid mixing workflow. Phase 1 is a pure verification gate — no code until ipMIDI and macOS Tahoe 26.2 are confirmed compatible. Phase 2 builds the Swift bridge and delivers full Pro Tools HUI control including flying faders, automation write, and the ConsoleStateManager that makes dual-DAW possible. Phase 3 adds Ableton Live MCU and the resident menu bar daemon that manages both DAW sessions simultaneously. Phase 4 hardens the system and adds the workflow differentiators (delta-ctrl, health monitoring, seamless DAW switching, soft keys, V-pots) that make this more than stock MatrixRemote.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Compatibility Verification** - Confirm ipMIDI, MatrixRemote, and macOS Tahoe 26.2 work before writing any code
- [ ] **Phase 2: Pro Tools HUI Bridge** - Build Swift bridge with HUI engine, ConsoleStateManager, and full Pro Tools control surface capability
- [ ] **Phase 3: Ableton Live MCU + Daemon Shell** - Add MCU engine for Ableton and resident menu bar app managing both DAW sessions
- [ ] **Phase 4: Hardening and Differentiators** - Health monitoring, delta-ctrl, seamless DAW switching, soft keys, V-pots, and SuperCue

## Phase Details

### Phase 1: Compatibility Verification
**Goal**: The SSL Matrix communicates over Ethernet on macOS Tahoe 26.2 and every layer of the protocol stack is confirmed working before any code is written
**Depends on**: Nothing (first phase)
**Requirements**: FOUN-01, FOUN-02, FOUN-03, FOUN-04
**Success Criteria** (what must be TRUE):
  1. ipMIDI driver is installed and SSL Matrix MIDI ports appear in Audio MIDI Setup > MIDI Studio on macOS Tahoe 26.2
  2. MatrixRemote connects to the console over Ethernet and the console responds to MatrixRemote commands
  3. macOS Local Network permissions are granted for ipMIDI, and all Matrix MIDI ports are visible as CoreMIDI ports in Audio MIDI Setup
  4. ipMIDI multicast traffic (225.0.0.37) is confirmed routing to the Ethernet adapter connected to the console, not to Wi-Fi or any other adapter
**Plans**: TBD

### Phase 2: Pro Tools HUI Bridge
**Goal**: The SSL Matrix is a fully functional HUI control surface for Pro Tools — flying faders, automation write, transport, mute/solo/rec arm, scribble strips, banking, automation modes — all working, with the ConsoleStateManager actor in place as the foundation for adding Ableton in Phase 3
**Depends on**: Phase 1
**Requirements**: PT-01, PT-02, PT-03, PT-04, PT-05, PT-06, PT-07, PT-08, PT-09
**Success Criteria** (what must be TRUE):
  1. Playing back a Pro Tools session with fader automation moves the physical faders on the Matrix in real time with no perceptible lag or oscillation
  2. Touching and moving a fader on the Matrix while Pro Tools is in Touch or Latch mode writes automation into the Pro Tools session
  3. Transport buttons on the console (play, stop, record, fast-forward, rewind) control Pro Tools playback and recording
  4. Mute, solo, and record arm buttons per channel are functional and reflect DAW state via LEDs
  5. Scribble strips display Pro Tools track names, and the console can bank through sessions with more than 16 tracks
**Plans**: TBD

### Phase 3: Ableton Live MCU + Daemon Shell
**Goal**: The SSL Matrix controls Ableton Live over a separate MCU session simultaneously with Pro Tools, and a resident menu bar daemon manages both sessions with visible connection status and a focus DAW selector
**Depends on**: Phase 2
**Requirements**: ABL-01, ABL-02, ABL-03, ABL-04, ABL-05, ABL-06, ABL-07, ABL-08, BRDG-03
**Success Criteria** (what must be TRUE):
  1. Playing back an Ableton Live set with clip or arrangement automation moves the Matrix faders in real time, independently of the Pro Tools session
  2. Touching and moving a fader writes automation into the active Ableton automation lane
  3. Transport, mute, solo, rec arm, scribble strips, and banking all function in Ableton Live from the console surface
  4. A menu bar icon shows per-DAW connection status (Pro Tools: connected/disconnected, Ableton: connected/disconnected) and a focus DAW selector
  5. The bridge daemon launches at login with no Dock icon and persists across DAW restarts without requiring manual intervention
**Plans**: TBD

### Phase 4: Hardening and Differentiators
**Goal**: The bridge is production-reliable for real sessions — auto-reconnects after interruptions, supports true MDAC-driven automation via delta-ctrl, switches DAW focus without MatrixRemote reconfiguration, and has soft key macros and V-pot routing configured for the actual session workflow
**Depends on**: Phase 3
**Requirements**: BRDG-01, BRDG-02, ADV-01, ADV-02, ADV-03
**Success Criteria** (what must be TRUE):
  1. If the console loses ipMIDI sync or the active DAW restarts, the bridge detects the interruption and auto-reconnects without any user action required
  2. Switching the focus DAW from Pro Tools to Ableton (or back) does not require opening MatrixRemote or changing any console profile
  3. At least one set of soft key macros is programmed and executes the correct DAW commands in both Pro Tools and Ableton
  4. V-pot rotary encoders control pan, sends, or plugin parameters in the active DAW
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Compatibility Verification | 0/TBD | Not started | - |
| 2. Pro Tools HUI Bridge | 0/TBD | Not started | - |
| 3. Ableton Live MCU + Daemon Shell | 0/TBD | Not started | - |
| 4. Hardening and Differentiators | 0/TBD | Not started | - |
