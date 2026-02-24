# Project Research Summary

**Project:** SSL Matrix Console Control Bridge
**Domain:** macOS hardware control bridge — SSL Matrix console + Pro Tools + Ableton Live via HUI/MCU over ipMIDI
**Researched:** 2026-02-24
**Confidence:** MEDIUM (protocol chain HIGH, stack choices HIGH, macOS Tahoe compatibility LOW)

## Executive Summary

The SSL Matrix console communicates with DAWs exclusively over Ethernet using the ipMIDI protocol (multicast UDP 225.0.0.37) — not USB, which is firmware-only. The console presents as virtual CoreMIDI ports via the nerds.de ipMIDI driver and supports both HUI (for Pro Tools) and MCU/Mackie Control Universal (for Ableton Live) simultaneously on separate ipMIDI port pairs. This is a critical architectural fact: Pro Tools and Ableton require different protocols and cannot share a single connection. Any solution must maintain dual protocol sessions simultaneously — HUI targeting Pro Tools and MCU targeting Ableton — with a single shared state manager arbitrating conflicts when both DAWs send automation simultaneously.

The recommended approach is a native Swift 6 menu bar daemon using MIDIKit 0.11.0 (orchetect/MIDIKit, February 2026) with its MIDIKitControlSurfaces module, which provides the only actively maintained HUI implementation in the Swift ecosystem. This stack eliminates the primary performance risk: Node.js GC jitter and Python GIL overhead are both incompatible with the sub-5ms fader latency requirement. The architecture follows a dual-engine fan-out pattern where a lock-free SPSC queue isolates CoreMIDI real-time callbacks from application logic, and a ConsoleStateManager Swift actor serves as the authoritative source of channel state.

The single largest risk is macOS Tahoe (26.2) compatibility. SSL has not validated MatrixRemote or the ipMIDI driver on Tahoe, and Apple introduced USB audio stack regressions in Tahoe 26.0 (partially addressed in 26.1). This must be the first verification step before any other work begins. If ipMIDI proves non-functional on Tahoe, the entire architecture pivots to a physical DIN MIDI fallback. Additionally, delta-ctrl ($50 plugin from SSL) is required for true automation-driven fader movement — the MCU/HUI path only provides position sync, not actual MDAC audio control. Purchase and Tahoe-compatibility verification of delta-ctrl is a P1 item after baseline connectivity is confirmed.

## Key Findings

### Recommended Stack

The protocol chain is: SSL Matrix → Ethernet (ipMIDI multicast UDP) → nerds.de ipMIDI driver → CoreMIDI virtual ports → HUI (Pro Tools) / MCU (Ableton Live). The ipMIDI driver is a hard prerequisite with no substitutes — Apple's built-in Network MIDI (RTP-MIDI) uses a different protocol and will not receive the Matrix's multicast packets. Custom bridge software, if required beyond what MatrixRemote provides, must be implemented in Swift for real-time latency guarantees.

**Core technologies:**
- **ipMIDI (nerds.de):** Ethernet-to-CoreMIDI bridge — the only macOS driver that implements the Matrix's multicast UDP MIDI protocol. Tahoe compatibility unverified; must test empirically.
- **Swift 6 + Xcode 16:** Bridge application language — native macOS, direct CoreMIDI access, zero GC jitter, Swift 6 concurrency maps cleanly to real-time event handling.
- **MIDIKit 0.11.0 (orchetect/MIDIKit):** CoreMIDI wrapper with HUI protocol implementation in MIDIKitControlSurfaces — the only actively maintained Swift library with HUI support. Released Feb 2, 2026, Swift 6 strict concurrency compliant.
- **MIDIKitControlSurfaces:** HUI surface + host implementation — use `HUISurface` for console-side and `HUIHostBank` for DAW-side. HUI completeness at v0.11.0 needs hands-on validation.
- **SwiftUI + NSStatusItem (MenuBarExtra):** Menu bar daemon UI — LSUIElement=YES, no Dock icon, status popover for configuration.
- **MatrixRemote (Java, SSL):** Separate application for console routing, Total Recall, profile management, soft key programming. Runs alongside the bridge; not replaced by it.
- **delta-ctrl plugin ($50, SSL):** AAX/AU/VST3 plugin required for MDAC-driven automation fader movement. Complements MCU/HUI position sync; does not replace it.

### Expected Features

**Must have (table stakes):**
- ipMIDI driver verified working on macOS Tahoe 26.2 — gates everything else
- MatrixRemote communicating over Ethernet — required for profile management and console config
- Pro Tools sees Matrix as HUI control surface (ports 1+2, 8 channels each) — core value proposition
- Ableton Live sees Matrix as MCU control surface (separate ipMIDI port) — second primary DAW
- Flying faders respond to DAW playback automation in both DAWs — the console's defining feature
- Fader touch triggers automation write in both DAWs (Touch mode for Pro Tools; automation lane for Ableton)
- Transport controls (play, stop, record, FF, RW) functional in both DAWs
- Scribble strips show track names from both DAWs
- Channel banking across unlimited DAW tracks
- Mute, solo, record arm per channel

**Should have (differentiators over stock MatrixRemote):**
- delta-ctrl plugin integration for true MDAC-driven automation (not just position sync)
- Health monitoring and auto-reconnect for intermittent ipMIDI sync loss
- Seamless DAW-switching without manually reconfiguring MatrixRemote profiles
- Automation mode buttons (Read/Write/Touch/Latch) clearly mapped and state-reflected on LEDs
- Soft key macros programmed for the user's actual session workflow

**Defer (v2+):**
- Custom Ableton Live Python control surface script (if MCU proves limiting)
- SuperCue/Auto-Mon punch recording conflict resolution with Pro Tools record tally
- Total Recall integration with DAW session open/close
- Plugin parameter control optimization (HUI mode restricts to 4 simultaneous params)

### Architecture Approach

The bridge follows a dual-engine fan-out pattern: one HUI session (Pro Tools, ipMIDI ports 1-2) and one MCU session (Ableton Live, ipMIDI port 3) run simultaneously. All console events flow through a lock-free SPSC queue from the CoreMIDI real-time callback to application logic, then through a central MessageRouter, then fan out to both engines. A ConsoleStateManager Swift actor is the single authoritative source of channel state (16 faders, mute, solo, automation modes), preventing the two engines from fighting over console motor commands. Conflict resolution when both DAWs send automation simultaneously uses a configurable "focus DAW" preference plus last-write-wins with per-channel timestamps.

**Major components:**
1. **ipMIDI Driver + MatrixMIDIInterface** — hardware transport layer; registers CoreMIDI ports; no custom code required for the driver itself
2. **MIDIMessageQueue (SPSC ring buffer)** — lock-free bridge from CoreMIDI real-time thread to application thread; prevents callback blocking
3. **MessageRouter** — receives decoded MIDI from console and DAWs; dispatches to correct engine; fans fader moves to both engines
4. **HUIEngine (Pro Tools)** — HUI protocol encode/decode; 1s keepalive timer (HUI goes offline at 2s); 14-bit fader pair collection; zone/port addressing
5. **MCUEngine (Ableton Live)** — MCU protocol encode/decode; pitchbend fader encoding; separate ipMIDI port from HUI
6. **ConsoleStateManager (Swift actor)** — 16-channel state model; serializes concurrent updates from both engines; conflict resolution policy
7. **Bridge App Shell (SwiftUI MenuBarExtra)** — resident daemon; connection status per DAW; focus DAW selector; launch-at-login

### Critical Pitfalls

1. **Flying fader feedback loop** — When the bridge echoes fader position back to the console while the user's hand is touching the fader, the motor fights the incoming DAW position and buzzes/oscillates. Prevention: maintain per-fader `isTouched` boolean; suppress all DAW-to-surface fader updates while touch is active. Never enable the Matrix as a MIDI track input in Pro Tools or Ableton.

2. **HUI heartbeat failure causes silent disconnection** — HUI requires a ping (0x90 0x00 0x00) every ~1s; if the surface misses 2 consecutive pongs, Pro Tools marks it offline and stops sending automation. Faders freeze with no visible error. Prevention: implement keepalive on a dedicated high-priority timer thread, never blocked by MIDI processing. Verify with MIDI monitor over 60+ seconds, not just "faders work initially."

3. **ipMIDI multicast routed to wrong network adapter** — On a Mac with multiple active NICs (Wi-Fi + Ethernet), macOS routes multicast 225.0.0.37 to the internet adapter, not the console adapter. MatrixRemote may appear connected while DAW control is completely silent. Prevention: disable all non-console adapters, or add a persistent static multicast route via `networksetup -setadditionalroutes`. Avoid TP-Link TL-SG105/108E switches (documented IGMP issues). Avoid 10G adapters for the console port.

4. **macOS Tahoe USB class-compliant regression** — Tahoe 26.0 broke generic USB Audio Class devices in CoreAudio/CoreMIDI. The Matrix is a ~2010-era device likely using USB Audio Class 1.1. Prevention: verify macOS is on Tahoe 26.1+ before testing. Confirm Matrix appears in Audio MIDI Setup > MIDI Studio before any other configuration. If absent, switch to DIN MIDI fallback.

5. **HUI 14-bit fader position: acting on incomplete messages** — HUI transmits fader position as LSB-then-MSB pairs. Processing the first byte alone produces wildly wrong intermediate positions, causing fader snapping at every automation step. Prevention: buffer fader messages in pairs; only compute and act on position after both bytes are received for the same channel. HUI sends LSB first — account for this ordering.

6. **EUCON conflict disables HUI metering in Pro Tools** — If EUCON (Avid's protocol) is enabled alongside HUI devices, all HUI channel meters stop working. This is a documented but unresolved Pro Tools bug. Prevention: disable EUCON in Setup > Peripherals > Ethernet Controllers before any HUI testing. Verify before spending time debugging metering.

7. **Ableton Live has no native HUI support** — Ableton implements MCU only. Attempting to configure the Matrix as a HUI device in Ableton preferences will produce no results. Prevention: use the Matrix's MCU profile and a separate ipMIDI port for Ableton. Accept that HUI and MCU will have different behavioral characteristics.

## Implications for Roadmap

Based on combined research, a 6-phase build order is recommended. Each phase has a hard gate dependency on the previous one completing successfully.

### Phase 1: Hardware and OS Compatibility Verification
**Rationale:** macOS Tahoe compatibility is the single highest-risk unknown in the project. If ipMIDI doesn't work on Tahoe, the architecture changes completely. Nothing else should proceed until this is resolved. This is a pure verification phase — no software is written.
**Delivers:** Confirmed working state of ipMIDI on Tahoe, Matrix visible in Audio MIDI Setup, MatrixRemote connecting to console, correct MatrixRemote version identified for v1 hardware.
**Addresses features:** ipMIDI driver on Tahoe (P1 gate), MatrixRemote Ethernet config (P1), firmware/software version match
**Avoids pitfalls:** Tahoe USB regression (Pitfall 4), ipMIDI multicast routing (Pitfall 5), macOS Local Network permissions (Pitfall 9), firmware/software mismatch (Pitfall 7)
**Research flag:** HIGH — run this phase before writing any code. If ipMIDI fails, research the DIN MIDI fallback path before proceeding to Phase 2.

### Phase 2: Pro Tools HUI Baseline
**Rationale:** HUI is the harder protocol (keepalive, zone/port addressing, 14-bit fader pairs). Solving the harder problem first means Phase 4 (MCU for Ableton) is straightforward. Pro Tools is also the canonical HUI host, making this the best test environment for HUI correctness.
**Delivers:** SSL Matrix controls Pro Tools: all 16 faders move bidirectionally, transport works, mute/solo/rec arm functional, scribble strips show track names.
**Uses:** Swift 6, MIDIKit 0.11.0 MIDIKitControlSurfaces, CoreMIDI HUI port setup
**Implements:** HUIEngine, HUIKeepalive, MatrixMIDIInterface, MIDIMessageQueue (SPSC)
**Addresses features:** Pro Tools MCU/HUI baseline (P1), flying fader response to automation (P1), fader write automation (P1), transport controls (P1)
**Avoids pitfalls:** Fader feedback loop (Pitfall 1) — implement touch-sense gate from the start; HUI heartbeat failure (Pitfall 2) — build keepalive before testing faders; EUCON conflict (Pitfall 3) — disable before testing; 14-bit fader encoding (Pitfall 6) — buffer pairs, LSB-first
**Research flag:** MEDIUM — MIDIKit HUI completeness at v0.11.0 needs validation. Run against Pro Tools with a MIDI monitor to verify protocol correctness. Issue #136 was partially open in 2022; the v0.11.0 state is claimed-complete but unverified.

### Phase 3: Console State Manager and Message Router
**Rationale:** Must exist before MCU (Ableton) is added. Without a centralized state manager, the two DAW engines will fight over console motor commands when both DAWs send automation simultaneously.
**Delivers:** ConsoleStateManager Swift actor with 16-channel model, MessageRouter with fan-out to both engines, conflict resolution policy (focus DAW preference).
**Implements:** ConsoleStateManager, MessageRouter, ChannelState value types, unit test suite for state logic
**Avoids pitfalls:** Both DAW engines writing state independently (Architecture Anti-Pattern 3)
**Research flag:** LOW — standard Swift actor and SPSC queue patterns; well-documented.

### Phase 4: Ableton Live MCU Baseline
**Rationale:** MCU is a simpler protocol than HUI (no keepalive, pitchbend fader encoding). With ConsoleStateManager in place from Phase 3, MCU engine routes through it cleanly. Ableton requires MCU not HUI — a separate ipMIDI port and separate protocol session.
**Delivers:** SSL Matrix controls Ableton Live: 16 faders bidirectional, transport, mute/solo/rec arm, scribble strips with track names, banking.
**Implements:** MCUEngine, MCUFaderEncoder, separate ipMIDI port configuration
**Addresses features:** Ableton Live MCU baseline (P1), fader write automation to Ableton (P1)
**Avoids pitfalls:** Ableton HUI not supported (Pitfall 8) — use MCU; ipMIDI port enumeration bug (Pitfall 11) — discover ports dynamically, not by hardcoded index
**Research flag:** LOW — MCU is well-documented (TouchMCU spec, MIDIKit implementation). Ableton's MCU behavior is standard.

### Phase 5: Bridge App Shell and UX
**Rationale:** The daemon shell is cosmetic relative to core protocol functionality. It wraps what's already working. Must be resident (launch-at-login) and unobtrusive (menu bar only, no Dock icon).
**Delivers:** SwiftUI MenuBarExtra resident daemon, per-DAW connection status indicators, focus DAW selector, launch-at-login LaunchAgent configuration.
**Implements:** SSLBridgeApp, MenuBarView, LSUIElement=YES Info.plist, LaunchAgent plist
**Addresses features:** macOS Tahoe compatibility as a native app (differentiator over MatrixRemote)
**Research flag:** LOW — MenuBarExtra and LaunchAgent patterns are well-documented.

### Phase 6: Hardening and Differentiators
**Rationale:** Once the baseline works end-to-end, add reliability and workflow features that differentiate from stock MatrixRemote. This phase should not be started until Phase 4 has been validated with real sessions.
**Delivers:** Auto-reconnect on console power cycle or DAW restart; delta-ctrl plugin integration; DAW-switching without MatrixRemote reconfiguration; soft key macro programming; ipMIDI health monitoring; automation mode buttons (Read/Write/Touch/Latch) verified.
**Addresses features:** delta-ctrl integration (P1 after baseline), health monitoring (P2), DAW-switching workflow (P2), soft key macros (P2), automation modes (P1 after baseline)
**Avoids pitfalls:** ipMIDI port enumeration bug during reconnects (Pitfall 11); Local Network permissions after OS updates (Pitfall 9)
**Research flag:** MEDIUM — delta-ctrl Tahoe compatibility is unknown. Verify before purchasing. The delta-ctrl/ipMIDI interaction path under Tahoe is undocumented.

### Phase Ordering Rationale

- **Phase 1 before everything:** ipMIDI on Tahoe is an unknown that can invalidate the entire architecture. No code should be written without this confirmation.
- **Phase 2 before Phase 4:** HUI is harder than MCU. Solving HUI correctness first (keepalive, 14-bit encoding, touch-sense gating) means MCU is a straightforward addition. Also Pro Tools is the primary mixing DAW and should be functional first.
- **Phase 3 between 2 and 4:** ConsoleStateManager is architecturally required before adding the second DAW engine. Building it after Phase 2 means it can be wired in retroactively for HUI before MCU is added.
- **Phase 5 after core protocol:** The shell is ergonomics. Shipping a working bare daemon is preferable to shipping a pretty app that has fader feedback loops.
- **Phase 6 last:** Delta-ctrl and workflow differentiators require a stable foundation to integrate against.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Run empirical Tahoe compatibility testing before planning any code. If ipMIDI fails on Tahoe 26.2, research DIN MIDI fallback path (iConnectivity mio4 or similar) before proceeding.
- **Phase 2:** Validate MIDIKit HUI completeness at v0.11.0 against a live Pro Tools session. The HUI issue (#136) was partially open in 2022; author claims completion in v0.11.0 but this requires hands-on verification.
- **Phase 6:** Verify delta-ctrl Tahoe compatibility before purchasing. Check SSL's compatibility matrix and community reports for Tahoe 26.x support.

Phases with standard patterns (skip additional research):
- **Phase 3:** Swift actor pattern and SPSC queue are well-documented. No novel patterns required.
- **Phase 4:** MCU protocol is thoroughly documented (TouchMCU spec) and MIDIKit has a working implementation.
- **Phase 5:** macOS menu bar daemon patterns with SwiftUI MenuBarExtra are well-established (Xcode 14+).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Protocol chain confirmed via official SSL docs. MIDIKit v0.11.0 confirmed via GitHub. Swift 6 concurrency appropriateness is well-established. Only uncertainty is ipMIDI Tahoe compatibility. |
| Features | MEDIUM-HIGH | Hardware capabilities are HIGH (SSL official docs). Tahoe compatibility of delta-ctrl and MatrixRemote is LOW (unverified by SSL). Feature priorities are solid based on hardware capabilities. |
| Architecture | HIGH | Dual-engine fan-out is architecturally sound and well-supported by the protocol split (HUI=Pro Tools, MCU=Ableton). Lock-free MIDI threading is an established real-time pattern. ConsoleStateManager actor is idiomatic Swift 6. |
| Pitfalls | HIGH | Most pitfalls sourced from official SSL documentation and Avid KB. Fader feedback loop, HUI keepalive, EUCON conflict are all documented production failures with clear prevention strategies. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **ipMIDI on macOS Tahoe 26.2:** No confirmed community or official reports. Must test empirically before any planning proceeds. This is the project's highest-risk unknown. If it fails, the entire transport layer changes.
- **MatrixRemote on macOS Tahoe 26.2:** SSL has not published Tahoe compatibility statements for the original Matrix (v1). The Java-based app may have issues on Tahoe independent of ipMIDI. Verify in Phase 1.
- **delta-ctrl Tahoe compatibility:** SSL's announcement confirmed original Matrix support but not Tahoe 26.x compatibility. Verify before purchase.
- **SSL Matrix firmware version:** Unknown. Determines which MatrixRemote version to install. Identify before any software setup.
- **MIDIKit HUI completeness at v0.11.0:** HUI feature coverage at the current version needs hands-on validation against a live Pro Tools session. The `HUIHostBank` API for two 8-channel banks must be validated.
- **Ableton Live MCU automation write behavior:** Ableton's HUI/automation write behavior from motorized faders differs from Pro Tools. The exact Touch-mode interaction with Ableton automation lanes needs empirical testing.

## Sources

### Primary (HIGH confidence)
- [SSL DAW Control Help — ipMIDI](https://livehelp.solidstatelogic.com/Help/ipMIDI.html) — ipMIDI multicast UDP, route commands, port configuration
- [SSL Live DAW Control docs](https://livehelp.solidstatelogic.com/Help/DAWControl.html) — HUI/MCU protocol confirmation, ipMIDI port count
- [SSL Matrix General FAQ](https://support.solidstatelogic.com/hc/en-gb/articles/4415895478417-Matrix-General-FAQ) — hardware capabilities, feature gaps
- [SSL — Remote app connects but DAW control does not work](https://support.solidstatelogic.com/hc/en-gb/articles/4408131999121) — ipMIDI multicast routing failure documentation
- [SSL — Multiple network adapters, ipMIDI and Delta Control](https://support.solidstatelogic.com/hc/en-gb/articles/4408132028305) — official multicast routing guidance
- [MIDIKit GitHub (orchetect/MIDIKit)](https://github.com/orchetect/MIDIKit) — v0.11.0, Swift 6, MIDIKitControlSurfaces HUI implementation
- [MCU Protocol Specification — TouchMCU](https://github.com/NicoG60/TouchMCU/blob/main/doc/mackie_control_protocol.md) — MCU protocol reference
- [Ableton Forum — Mackie Baby HUI not supported](https://forum.ableton.com/viewtopic.php?t=241657) — Ableton HUI incompatibility confirmed
- [nerds.de ipMIDI for macOS](https://www.nerds.de/en/ipmidi_osx.html) — ARM64 native, Sequoia 15 compatible, Tahoe unconfirmed
- [SSL Matrix Pro Tools Quick Start Guide](https://www.solidstatelogic.com/assets/uploads/downloads/matrix/ProTools-Standard-Matrix-Profile-Setup-Quick-Start-Guide.pdf) — HUI port configuration
- [Delta Control Plug-in Suite — SSL Store](https://store.solidstatelogic.com/plug-ins/delta-control-plug-in-suite) — delta-ctrl for original Matrix confirmed
- [timur.audio — Using locks in real-time audio processing safely](https://timur.audio/using-locks-in-real-time-audio-processing-safely) — lock-free MIDI thread safety
- [Apple CoreMIDI docs](https://developer.apple.com/documentation/coremidi/) — CoreMIDI framework

### Secondary (MEDIUM confidence)
- [HUI Protocol — Wikipedia](https://en.wikipedia.org/wiki/Human_User_Interface_Protocol) — protocol history, MIDI encoding
- [Mackie HUI MIDI Protocol reverse-engineering (htlab.net)](https://htlab.net/computer/protocol/mackie-control/HUI.pdf) — HUI message format details
- [Rogue Amoeba — macOS 26 Tahoe audio bug fixes](https://weblog.rogueamoeba.com/2025/11/04/macos-26-tahoe-includes-important-audio-related-bug-fixes/) — Tahoe 26.1 audio stack fixes
- [SSL Matrix Review — Sound on Sound](https://www.soundonsound.com/reviews/ssl-matrix) — hardware capability details
- [Barry Rudolph SSL Matrix Review](https://www.barryrudolph.com/mix/matrix.html) — hands-on hardware assessment
- [MIDIKit HUI Protocol Support Issue #136](https://github.com/orchetect/MIDIKit/issues/136) — HUI implementation status

### Tertiary (LOW confidence, needs validation)
- [Gearspace — SSL Matrix Ethernet connection](https://gearspace.com/board/high-end/1237723-ssl-matrix-ethernet-connection.html) — community reports of ipMIDI multicast issues
- [Gearspace — SSL Matrix 2 users DAW connection issue](https://gearspace.com/board/music-computers/1362568-ssl-matrix-2-users-do-you-have-daw-connection-issue.html) — intermittent sync loss community reports
- [Apple Community — USB Microphone Tahoe regression](https://discussions.apple.com/thread/256152219) — USB class-compliant regression on Tahoe 26.0

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*
