# Requirements: SSL Matrix Control Bridge

**Defined:** 2026-02-24
**Core Value:** Flying faders that respond to DAW automation playback and capture fader moves back into the DAW — transforming the Matrix from a passive summing box into a fully functional mixing console.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Foundation

- [ ] **FOUN-01**: ipMIDI driver installed and verified working on macOS Tahoe 26.2
- [ ] **FOUN-02**: Ethernet network configured with correct multicast routing for ipMIDI (225.0.0.37)
- [ ] **FOUN-03**: MatrixRemote communicating with SSL Matrix console over Ethernet
- [ ] **FOUN-04**: macOS Local Network permissions and Audio MIDI Setup verified for MIDI port visibility

### Pro Tools

- [ ] **PT-01**: Flying faders respond to Pro Tools automation playback via HUI protocol
- [ ] **PT-02**: Fader touch on console writes automation into Pro Tools (touch-sense triggering)
- [ ] **PT-03**: Transport control from console surface (play, stop, record, fast-forward, rewind)
- [ ] **PT-04**: Mute and solo per channel controllable from console
- [ ] **PT-05**: Record arm per channel from console surface
- [ ] **PT-06**: Track names displayed on console scribble strips
- [ ] **PT-07**: Channel banking to control sessions with more than 16 tracks
- [ ] **PT-08**: delta-ctrl plugin integrated for true MDAC-driven fader automation
- [ ] **PT-09**: Automation mode buttons (Read/Write/Touch/Latch) mapped with LED state feedback

### Ableton Live

- [ ] **ABL-01**: Flying faders respond to Ableton Live automation playback via MCU protocol
- [ ] **ABL-02**: Fader touch on console writes automation into Ableton automation lanes
- [ ] **ABL-03**: Transport control from console surface in Ableton
- [ ] **ABL-04**: Mute and solo per channel from console in Ableton
- [ ] **ABL-05**: Record arm per channel from console in Ableton
- [ ] **ABL-06**: Track names displayed on scribble strips from Ableton
- [ ] **ABL-07**: Channel banking to control Ableton sessions with more than 16 tracks
- [ ] **ABL-08**: Custom Python control surface script for Ableton if stock MCU proves limiting

### Bridge Software

- [ ] **BRDG-01**: Health monitoring detects ipMIDI sync loss and auto-reconnects
- [ ] **BRDG-02**: Seamless DAW-switching between Pro Tools and Ableton without MatrixRemote reconfiguration
- [ ] **BRDG-03**: Native Swift menu bar daemon running on macOS Tahoe with launch-at-login

### Advanced

- [ ] **ADV-01**: Soft key macros programmed for session workflow (Pro Tools and Ableton commands)
- [ ] **ADV-02**: V-pot rotary encoders controlling pan, sends, and plugin parameters
- [ ] **ADV-03**: SuperCue/Auto-Mon integration with DAW punch recording workflow

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
| Replacing ipMIDI with custom MIDI-over-network | ipMIDI is the backbone protocol the Matrix firmware expects; replacing it is a multi-month effort solving the wrong problem |
| Building a full MCU/HUI software emulator from scratch | Complete reimplementation has high correctness burden; use MatrixRemote + MIDIKit for protocol handling |
| Audio routing or mix bus control in bridge software | Analog signal path is MatrixRemote's domain; bridge stays in the control protocol layer |
| Building a DAW plugin to replace delta-ctrl | delta-ctrl exists for $50 and solves MDAC automation; rebuilding it is months of plugin development |
| Universal MIDI learn / arbitrary MIDI mapping UI | Mature tools exist (Bome MIDI Translator Pro); this is scope creep beyond SSL Matrix-specific problems |
| Web-based remote control UI for the console | The Matrix IS the control surface; adding a software remote inverts the purpose |
| USB-based DAW control | The SSL Matrix USB port is firmware-only; DAW control is exclusively Ethernet/ipMIDI |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUN-01 | — | Pending |
| FOUN-02 | — | Pending |
| FOUN-03 | — | Pending |
| FOUN-04 | — | Pending |
| PT-01 | — | Pending |
| PT-02 | — | Pending |
| PT-03 | — | Pending |
| PT-04 | — | Pending |
| PT-05 | — | Pending |
| PT-06 | — | Pending |
| PT-07 | — | Pending |
| PT-08 | — | Pending |
| PT-09 | — | Pending |
| ABL-01 | — | Pending |
| ABL-02 | — | Pending |
| ABL-03 | — | Pending |
| ABL-04 | — | Pending |
| ABL-05 | — | Pending |
| ABL-06 | — | Pending |
| ABL-07 | — | Pending |
| ABL-08 | — | Pending |
| BRDG-01 | — | Pending |
| BRDG-02 | — | Pending |
| BRDG-03 | — | Pending |
| ADV-01 | — | Pending |
| ADV-02 | — | Pending |
| ADV-03 | — | Pending |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 0
- Unmapped: 27

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after initial definition*
