# Requirements: SSL Matrix Control Bridge

**Defined:** 2026-02-24
**Updated:** 2026-03-11 — Recalibrated after Phase 1 discoveries
**Core Value:** Flying faders that respond to DAW automation playback and capture fader moves back into the DAW — transforming the Matrix from a passive summing box into a fully functional mixing console.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Foundation (Phase 1 — COMPLETE)

- [x] **FOUN-01**: ipMIDI driver installed and verified working on macOS Tahoe 26.2
- [x] **FOUN-02**: Ethernet network configured with correct multicast routing for ipMIDI (225.0.0.37)
- [x] **FOUN-03**: ssl-matrix-client communicating with SSL Matrix console over Ethernet (MatrixRemote broken on Tahoe)
- [x] **FOUN-04**: macOS Local Network permissions and Audio MIDI Setup verified for MIDI port visibility

### DAW Control (Verified natively in Phase 1 — no custom bridge needed)

- [x] **PT-01**: Flying faders respond to Pro Tools automation playback via HUI protocol
- [x] **PT-02**: Fader touch on console writes automation into Pro Tools (touch-sense triggering)
- [x] **PT-03**: Transport control from console surface (play, stop, record, fast-forward, rewind)
- [x] **PT-04**: Mute and solo per channel controllable from console
- [x] **PT-05**: Record arm per channel from console surface
- [x] **PT-06**: Track names displayed on console scribble strips
- [x] **PT-07**: Channel banking to control sessions with more than 16 tracks
- [x] **PT-08**: delta-ctrl plugin integrated for true MDAC-driven fader automation
- [x] **PT-09**: Automation mode buttons (Read/Write/Touch/Latch) mapped with LED state feedback
- [x] **ABL-01**: Flying faders respond to Ableton Live automation playback via MCU protocol
- [x] **ABL-02**: Fader touch on console writes automation into Ableton automation lanes
- [x] **ABL-03**: Transport control from console surface in Ableton
- [x] **ABL-04**: Mute and solo per channel from console in Ableton
- [x] **ABL-05**: Record arm per channel from console in Ableton
- [x] **ABL-06**: Track names displayed on scribble strips from Ableton
- [x] **ABL-07**: Channel banking to control Ableton sessions with more than 16 tracks
- [x] **ABL-08**: delta-ctrl plugin working in Ableton (stock MCU sufficient — no custom script needed)

Note: DAW switching between Pro Tools and Ableton is handled by hardware buttons on the Matrix console — no software switching needed.

### Capabilities Audit

- [x] **AUDIT-01**: All 105 ssl-matrix-client dispatch handlers wire-tested against live console with pass/fail documented
- [x] **AUDIT-02**: Soft key, V-pot, and SuperCue protocol capabilities mapped with confirmed working message codes
- [x] **AUDIT-03**: Split board feasibility determined — can two DAW layers run simultaneously on different fader groups?
- [x] **AUDIT-04**: Capabilities document listing every confirmed feature, limitation, and protocol gap

### Console Surface Features

- [x] **ADV-01**: Soft key macros programmed for session workflow (Pro Tools and Ableton commands)
- [x] **ADV-02**: V-pot rotary encoders controlling pan, sends, and plugin parameters
- [x] **ADV-03**: SuperCue/Auto-Mon integration with DAW punch recording workflow

### Session & Workflow

- [ ] **SESS-01**: Console state templates saveable/loadable, each linked to a specific DAW project file
- [ ] **SESS-02**: Routing recall — insert matrix and XPatch state restored per session template
- [x] **SPLIT-01**: Split board mode — left 8 faders to one DAW, right 8 to another, switchable via single command
- [x] **BRDG-01**: Health monitoring detects ipMIDI sync loss and auto-reconnects

### Native Application

- [ ] **APP-01**: Native macOS dock application (not menu bar) wrapping ssl-matrix-client
- [ ] **APP-02**: All CLI features accessible through GUI
- [ ] **APP-03**: Launch-at-login with auto-connect, persists across DAW restarts

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Extended Integration

- **EXT-01**: Total Recall snapshot integration with DAW session management
- **EXT-02**: Multi-console support (Duality, AWS, or third-party surfaces)
- **EXT-03**: Web-based remote status dashboard

### Plugin Optimization

- **PLUG-01**: Optimized V-pot plugin parameter mapping beyond 4 simultaneous params (HUI limitation)
- **PLUG-02**: Per-plugin V-pot layouts saved and recalled

## Out of Scope

| Feature | Reason |
|---------|--------|
| Replacing ipMIDI with custom MIDI-over-network | ipMIDI is the backbone protocol the Matrix firmware expects |
| Building a full MCU/HUI software emulator from scratch | DAW control works natively — no emulator needed |
| Audio routing or mix bus control in bridge software | Analog signal path is the console's domain |
| Building a DAW plugin to replace delta-ctrl | delta-ctrl works in both DAWs for $50 |
| Universal MIDI learn / arbitrary MIDI mapping UI | Mature tools exist (Bome MIDI Translator Pro) |
| Web-based remote control UI for the console | The Matrix IS the control surface |
| USB-based DAW control | The SSL Matrix USB port is firmware-only |
| Software-based DAW switching | Hardware buttons on the Matrix handle this natively |
| Menu bar app as primary interface | User preference: dock application, not menu bar widget |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUN-01 | Phase 1 | Complete |
| FOUN-02 | Phase 1 | Complete |
| FOUN-03 | Phase 1 | Complete |
| FOUN-04 | Phase 1 | Complete |
| PT-01–09 | Phase 1 | Complete (native) |
| ABL-01–08 | Phase 1 | Complete (native) |
| AUDIT-01 | Phase 2 | Complete |
| AUDIT-02 | Phase 2 | Complete |
| AUDIT-03 | Phase 2 | Complete |
| AUDIT-04 | Phase 2 | Complete |
| ADV-01 | Phase 3 | Complete |
| ADV-02 | Phase 3 | Complete |
| ADV-03 | Phase 3 | Complete |
| SESS-01 | Phase 4 | Pending |
| SESS-02 | Phase 4 | Pending |
| SPLIT-01 | Phase 4 | Complete |
| BRDG-01 | Phase 4 | Complete |
| APP-01 | Phase 5 | Pending |
| APP-02 | Phase 5 | Pending |
| APP-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 31 total
- Mapped to phases: 31
- Unmapped: 0
- Complete: 22 (Phase 1 + native DAW control + AUDIT-04)
- Remaining: 9

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-03-13 — AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04 complete (Phase 2 capabilities audit finished)*
