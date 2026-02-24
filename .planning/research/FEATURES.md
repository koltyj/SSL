# Feature Research

**Domain:** Console control bridge software — SSL Matrix + DAW integration
**Researched:** 2026-02-24
**Confidence:** MEDIUM-HIGH (hardware specs HIGH, macOS Tahoe compatibility LOW)

---

## Critical Architecture Clarification

Before categorizing features, one architecture finding changes everything:

**The SSL Matrix does NOT use HUI over USB.** The USB port is for firmware updates only. The Matrix communicates with the DAW via **Ethernet using ipMIDI** (multicast UDP), emulating a multiport MIDI interface. It supports both **MCU (Mackie Control Universal) and HUI protocols** over this Ethernet connection.

For the original Matrix (not Matrix 2), the software required is:
1. **MatrixRemote** — Java app, Ethernet-based, handles routing/configuration/Total Recall/soft key mapping. Does NOT provide DAW automation playback.
2. **ipMIDI driver** — Ethernet-to-MIDI bridge, gives the Matrix a virtual MIDI port the DAW sees as a control surface.
3. **δelta Control plugin** (optional, ~$50) — AAX/AU/VST3 plug-in that routes DAW automation data to drive the Matrix's MDAC volume control, enabling true DAW automation playback on the analog faders.

The PROJECT.md assumption that "HUI protocol communication established between SSL Matrix and DAWs over USB" is incorrect. The correct path is MCU or HUI over Ethernet via ipMIDI.

---

## SSL Matrix Hardware Capabilities (Physical Inventory)

Understanding what the hardware actually has determines what software can expose:

| Hardware Element | Count | Technical Notes |
|-----------------|-------|-----------------|
| Touch-sensitive motorized faders | 17 (16 ch + 1 master) | Same as Duality. MDAC controls audio level — no audio through fader. |
| V-Pots (rotary encoders with LED rings) | 16+ | Per-channel, with integral push-switch. LED rings show parameter value. |
| Two-line alphanumeric scribble strips | 16 | Per-channel display for track names, parameter info |
| Lozenge buttons (per channel) | 3 per ch = 48 | Configurable function buttons |
| Five banks of 16 assignable buttons | 80 total | Custom DAW command mapping |
| LED bar-graph meters | 16 ch (dual) | In meter bridge, with Rec/Mix status lamps |
| Transport keys | Full set | Tape-style: play, stop, rec, FF, RW |
| Jog/shuttle wheel (data wheel) | 1 | For timeline navigation |
| Eight programmable soft keys | 8 above + 8 below display | Context-sensitive DAW function access |
| Keyboard modifier buttons | Shift, Option, Control, Escape, Enter | Reduces reliance on external keyboard |
| Artist talkback button | 1 | Near transport controls |
| Monitor section | Full | Main + nearfield + artist outputs, 3 ext inputs, dim, mono |
| SuperCue | 1 | Latency-free zero-latency monitoring for talent |
| Insert Router | 16 devices | Analog outboard routing via MatrixRemote |
| SD card slot (rear) | 1 | Stores MatrixRemote configs/profiles |
| Ethernet (RJ45) | 1 | ipMIDI control + MatrixRemote communication |
| USB (B-type) | 1 | FIRMWARE UPDATES ONLY — not for DAW control |
| 9-pin D-sub | 1 | SSL X-rack Total Recall linking |

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that must work for the console to function as described. Missing any of these means the console is still "broken" in the user's terms.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Flying faders respond to DAW playback (Pro Tools) | Core value proposition of the console. Without this it's a passive summing box. | MEDIUM | Requires: ipMIDI configured, DAW set to MCU or HUI, OR delta-ctrl plugin. MCU/HUI gives bidirectional fader sync; delta-ctrl gives true DAW automation-driven analog fader movement. These are different features. |
| Flying faders respond to DAW playback (Ableton Live) | Same as above for second primary DAW | MEDIUM | Ableton supports MCU, NOT HUI. SSL provides a default Live profile. Fader recall works via MCU. |
| Fader movements write automation into DAW (Pro Tools) | Essential for hybrid mixing workflow — mixing on console, saving into DAW | MEDIUM | Supported via MCU/HUI touch-sensitive faders. Touch detection triggers automation write mode in DAW. |
| Fader movements write automation into DAW (Ableton Live) | Same for Ableton | MEDIUM | MCU fader touch-writes to Ableton automation lanes. Works with default MCU integration. |
| Transport control from console (play, stop, record, FFwd, RWd) | Standard expectation of any DAW controller | LOW | Fully supported via MCU and HUI. Transport keys are mapped in the SSL profile. |
| Mute/solo per channel controllable from console | Standard DAW controller feature | LOW | MCU provides per-channel mute and solo buttons mapped to lozenge buttons. |
| Record arm per channel from console | Essential for tracking sessions | LOW | MCU provides per-channel rec arm. Mapped to lozenge buttons. |
| Track names appear on scribble strips | Without this, fader banking is blind | LOW | MCU protocol sends track names to the two-line display per channel. |
| Channel banking (16 tracks at a time, scrollable) | 16 faders need to control sessions with more than 16 tracks | LOW | MCU provides bank left/right and channel left/right navigation. The SSL Matrix supports banking to control unlimited DAW tracks. |
| Pan control via V-Pots | Standard encoder function | LOW | V-Pots transmit relative CC deltas. Pan is the default encoder assignment. |
| Channel select/focus from console surface | Needed to direct soft key/V-pot actions to a channel | LOW | MCU provides per-channel select button. |
| ipMIDI driver installed and network configured | Foundation — nothing else works without this | LOW-MEDIUM | ipMIDI uses multicast UDP on 225.0.0.37. Multiple network adapters require manual routing table edits. Some routers block multicast. Requires dedicated network segment or direct cable. |
| MatrixRemote configured and communicating | Required for soft key programming, routing, Total Recall, profile management | MEDIUM | Java app — Ethernet based. Known issues with some routers and macOS validation gaps for newer OS versions. |
| Jog/shuttle wheel for timeline scrubbing | Standard DAW controller expectation | LOW | Provided via MCU data wheel messages. |
| Focus Fader mode functional | Master fader independently controls any channel not in current bank — major workflow feature | LOW | Built into Matrix hardware/firmware via MCU. No custom code required. |

### Differentiators (Competitive Advantage Over SSL's Own Software)

Features where custom software can exceed what MatrixRemote + default profiles provide.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| True DAW automation-driven fader movement via delta-ctrl integration | Delta-ctrl plugin ($50) enables analog faders to physically follow DAW automation playback — not just reflect position, but drive the MDAC to actually control audio. This is different from and better than MCU fader sync. | HIGH | Delta-ctrl plugin uses AAX/AU/VST3 to send automation data to the Matrix over the same ipMIDI path. The bridge software may need to facilitate the communication between plugin and console. Confirm delta-ctrl works on original Matrix (SSL announcement says it does). |
| DAW-switching without reconfiguring MatrixRemote | SSL supports up to 4 simultaneous DAW connections. Switching between Pro Tools and Ableton should be seamless — press one button, all faders, transport, and scribble strips remap to the other DAW. | MEDIUM | ipMIDI emulates multiple MIDI ports. The bridge software can manage profile switching without user reconfiguring MatrixRemote manually. |
| Automation mode control buttons clearly mapped (Read/Write/Touch/Latch) | MCU provides automation mode buttons but mapping in SSL's profiles may not surface all modes clearly. Bridge can ensure Pro Tools automation modes (Read, Write, Touch, Latch, Trim, Off) are all accessible and their state reflected on LEDs. | LOW-MEDIUM | HUI supports: Read, Touch, Latch, Write, Trim, Off. MCU also supports these. Pro Tools is the primary target. Ableton has simpler automation model. |
| Soft key macros that aren't DAW-specific | SSL profiles provide per-DAW soft key programming, but switching DAWs loses the other DAW's macro assignments. Bridge could manage layered profiles for both DAWs simultaneously. | MEDIUM | MatrixRemote already handles this partially. Custom bridge can enhance or supplement. |
| Health/status monitoring for ipMIDI connection | ipMIDI sync can drop — users report intermittent loss of DAW control. A bridge that monitors connection state, auto-reconnects, and notifies the user is a significant UX improvement over the stock setup. | MEDIUM | ipMIDI uses periodic polling ("ping" messages). Monitor these for connection health. |
| V-Pot assignment switching (pan / send / plugin params) | MCU provides assignment buttons but the UI for plugin parameter control is limited in HUI mode (4 params) vs MCU mode (wider). Bridge can optimize plugin control for each DAW. | HIGH | In Pro Tools HUI mode, only 4 simultaneous plugin parameters via V-Pots. In MCU mode with Pro Tools or Ableton, broader plugin access. Confirm which protocol maximizes plugin control for each DAW. |
| SuperCue / Auto-Mon integration with punch recording | Matrix's SuperCue provides zero-latency source monitoring during punch-in recording. Bridge can automate the source switching in coordination with DAW record arm state. | HIGH | Known issue: Pro Tools record arm tally mismatch with Matrix's auto-mon causes monitoring dropout. Custom bridge can work around this by monitoring Pro Tools record state differently. |
| Session recall notifications | When Total Recall snapshot is loaded in MatrixRemote, bridge can communicate to DAW or display which TR preset is active. | LOW | Nice coordination between MatrixRemote's TR system and DAW session management. |
| macOS Tahoe compatibility assurance | SSL has not validated Matrix Remote on Tahoe. Bridge software built natively for macOS 26 fills the gap if MatrixRemote has issues. | HIGH | macOS Tahoe (26.2) is the user's OS. SSL's validation status for Tahoe is unknown. ipMIDI 2.0 supports Sequoia (15) — Tahoe (26) compatibility is unverified. This is the single biggest risk in the project. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem valuable but should be deliberately excluded from scope.

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Replacing ipMIDI with a custom MIDI-over-network implementation | If ipMIDI has issues, the temptation is to write a replacement. | ipMIDI is the backbone of how the Matrix communicates. Writing a replacement is a massive undertaking and would need to speak the same multicast UDP protocol the console firmware expects. Any issue is more likely a network config problem. | Configure the network correctly. Use a dedicated switch or direct Ethernet cable. Check routing tables for multiple-adapter setups. |
| Building a full MCU/HUI software emulator from scratch | If profile customization is needed beyond what MatrixRemote offers. | Complete reimplementation of MCU/HUI is a months-long project with high correctness burden. The protocols are complex and partially reverse-engineered. | Use MatrixRemote for profile management. Extend via MIDI remapping (Bome MIDI Translator or similar) to add custom behavior on top of existing protocol. |
| Adding audio routing or mix bus control to the bridge | MatrixRemote handles insert routing; the analog signal path is already working. | This is the analog domain and is properly handled by MatrixRemote and the hardware itself. Software-layer audio routing adds scope without fixing the stated problem. | Keep bridge in the control protocol domain. Audio routing stays in MatrixRemote. |
| Building a DAW plugin from scratch for automation capture | Delta-ctrl already exists and does this for $50. | Reimplementing delta-ctrl is months of plugin development, iLok integration, and format support (AAX, AU, VST3). It's a solved problem. | Purchase the delta-ctrl plugin from SSL. If it has macOS Tahoe compatibility issues, that's the problem to solve — not building a replacement. |
| Universal MIDI learn / arbitrary MIDI mapping UI | Would allow remapping any button to any MIDI message. | This is a general-purpose MIDI mapper — there are mature tools for this (MIDI Monitor, Bome, etc.). Building it is scope creep. | Use Bome MIDI Translator Pro or similar for one-off remapping needs. Focus the bridge on SSL Matrix-specific problems. |
| Web-based remote control UI for the console | Would let you control the Matrix from a tablet/phone. | This inverts the purpose — the Matrix IS the control surface. Adding another remote UI layer creates redundancy and complexity without solving the stated problem. | The Matrix's physical controls are the UX. Fix those, not add a software alternative. |
| Multi-console support | Supporting other SSL consoles (Duality, AWS) or third-party surfaces. | Scope explosion. Each console has different firmware, different protocol variants, different profiles. | Build for SSL Matrix specifically. Generic MCP/HUI support is a future v2 concern if at all. |

---

## Feature Dependencies

```
[ipMIDI driver installed and network configured]
    └──required-by──> [All DAW control features]
                          └──required-by──> [Flying faders, transport, mute/solo, scribble strips]

[MatrixRemote configured]
    └──required-by──> [Soft key macros, Total Recall, Insert Router control]
    └──required-by──> [DAW profile selection (MCU vs HUI, per DAW)]

[MCU protocol active (via ipMIDI)]
    └──enables──> [Flying faders (bidirectional position sync)]
    └──enables──> [Transport control]
    └──enables──> [Scribble strip track names]
    └──enables──> [Mute/solo/rec arm per channel]
    └──enables──> [Banking and channel scrolling]
    └──enables──> [Automation mode buttons (Read/Write/Touch/Latch)]
    └──enables──> [V-pot pan, send, plugin param control]

[Delta-ctrl plugin ($50, iLok)]
    └──required-for──> [True automation-driven fader movement (MDAC control)]
    └──enhances──> [MCU fader sync] (adds actual audio control, not just visual sync)
    └──requires──> [ipMIDI active]
    └──requires──> [Compatible macOS version — VERIFY for Tahoe]

[DAW-switching bridge feature]
    └──requires──> [ipMIDI active]
    └──requires──> [Multiple MIDI port profiles loaded in MatrixRemote]
    └──enhances──> [MCU protocol active]

[SuperCue/Auto-Mon integration]
    └──requires──> [MCU transport/record state read]
    └──enhances──> [Transport control]

[Health monitoring]
    └──requires──> [ipMIDI active]
    └──enhances──> [All DAW control features] (makes them reliable)
```

### Dependency Notes

- **All DAW control requires ipMIDI**: There is no fallback path. USB is firmware-only on this console. MIDI I/O mentioned in PROJECT.md as alternative is not the same — the Matrix's Ethernet ipMIDI is a separate control path from any physical MIDI I/O on the Apollo interface.
- **Delta-ctrl is an enhancement, not a replacement, for MCU**: MCU syncs fader position (control surface behavior). Delta-ctrl drives the analog MDAC via DAW automation data (audio behavior). Both are needed for full hybrid automation.
- **MatrixRemote and ipMIDI are independent layers**: MatrixRemote configures routing and profiles. ipMIDI carries the MCU/HUI messages during live use. Both must work simultaneously.
- **macOS Tahoe compatibility gates everything**: If ipMIDI 2.0 does not function on Tahoe, nothing else matters. This must be the first thing verified in Phase 1.

---

## MVP Definition

### Launch With (v1)

Minimum viable product: the console is functional for sessions.

- [ ] **ipMIDI driver verified working on macOS Tahoe 26.2** — This is the single gating dependency. Everything else is downstream of this. Test before anything else.
- [ ] **MatrixRemote communicating over Ethernet** — Network configured, console visible in MatrixRemote, profiles loadable.
- [ ] **Pro Tools sees Matrix as MCU control surface** — 16 faders move, transport works, scribble strips show track names.
- [ ] **Ableton Live sees Matrix as MCU control surface** — Same baseline capability in second primary DAW.
- [ ] **Flying faders respond to DAW transport/automation** — The core value proposition. MCU provides position sync; confirm faders actually move during Pro Tools and Ableton playback of automated content.
- [ ] **Fader touch triggers automation write in both DAWs** — Touching a fader in Pro Tools should engage Touch mode. In Ableton, it should write to the automation lane.
- [ ] **Transport controls functional in both DAWs** — Play, stop, record, return-to-zero confirmed working.

### Add After Validation (v1.x)

Features to add once core ipMIDI + MCU baseline is confirmed working:

- [ ] **Delta-ctrl plugin purchased and integrated** — Once MCU baseline works, add delta-ctrl for true MDAC-driven automation. Verify Tahoe compatibility before purchase.
- [ ] **Automation mode buttons verified (Read/Write/Touch/Latch)** — Confirm Pro Tools automation mode buttons on console surface work correctly with current Pro Tools version.
- [ ] **DAW-switching workflow optimized** — Seamless transition between Pro Tools and Ableton without MatrixRemote reconfiguration.
- [ ] **Soft key macros programmed for session workflow** — Program the 80 assignable buttons for the user's actual workflow (common Pro Tools and Ableton commands).
- [ ] **Health monitoring for ipMIDI connection** — Auto-detect and recover from the intermittent sync loss that users report with MCU/ipMIDI.

### Future Consideration (v2+)

Features to defer until v1 is stable:

- [ ] **SuperCue/Auto-Mon punch recording integration** — The Auto-Mon/record arm tally conflict with Pro Tools is a known issue. Workaround first; custom fix later.
- [ ] **Custom Ableton Live control surface script** — If MCU proves too limiting for Ableton (banking constraints, limited plugin access), a custom Python script extends capabilities significantly. Complex to implement, defer unless MCU is insufficient.
- [ ] **Total Recall integration with DAW session management** — Coordinating MatrixRemote TR snapshots with DAW session open/close is useful but not essential.
- [ ] **Plugin parameter control optimization** — V-pot plugin control is limited in HUI mode (4 params). Optimizing this for specific plugin formats is high-effort.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| ipMIDI verified on Tahoe | HIGH | LOW (verify only) | P1 |
| MatrixRemote Ethernet config | HIGH | LOW | P1 |
| Pro Tools MCU baseline (faders, transport, mutes) | HIGH | LOW-MEDIUM | P1 |
| Ableton Live MCU baseline | HIGH | LOW-MEDIUM | P1 |
| Flying fader response to automation | HIGH | MEDIUM | P1 |
| Fader write automation to DAW | HIGH | MEDIUM | P1 |
| Delta-ctrl plugin integration | HIGH | LOW (purchase + configure) | P1 after baseline |
| Automation modes (Read/Write/Touch/Latch) | HIGH | LOW | P1 after baseline |
| Soft key macro programming | MEDIUM | MEDIUM | P2 |
| DAW-switching workflow | MEDIUM | MEDIUM | P2 |
| Health monitoring/auto-reconnect | MEDIUM | MEDIUM | P2 |
| Scribble strip optimization | LOW | LOW | P2 |
| SuperCue/Auto-Mon conflict fix | MEDIUM | HIGH | P3 |
| Custom Ableton Python script | MEDIUM | HIGH | P3 |
| Plugin param control optimization | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | SSL MatrixRemote (stock) | Delta-ctrl Plugin | Custom Bridge |
|---------|--------------------------|-------------------|---------------|
| Insert router / outboard management | Full support | Not applicable | Not applicable |
| DAW profile management | Full support | Not applicable | Can supplement |
| Total Recall snapshots | Full support | Not applicable | Integration possible |
| Soft key macros | Supported in UI | Not applicable | Can enhance |
| Flying fader DAW position sync | Via MCU/HUI | Enhances (MDAC) | Not required |
| True automation-driven fader (MDAC) | NOT PROVIDED | Full support | Not required |
| DAW automation read (fader follows) | Partial via MCU | Full via MDAC | Not required |
| DAW automation write (fader touch) | Via MCU touch | Via MDAC | Not required |
| Transport control | Via MCU | Not applicable | Not required |
| Scribble strip track names | Via MCU | Not applicable | Not required |
| macOS Tahoe support | UNKNOWN/UNVALIDATED | Unknown (verify) | Can provide if native |
| Multi-DAW session switching | Manual in MatrixRemote | Not applicable | Can automate |
| Connection health monitoring | None | None | Can provide |
| Auto-Mon conflict workaround | Not addressed | Not addressed | Can address |

---

## What Existing Software Does NOT Provide

These are the actual gaps the custom bridge should fill:

1. **macOS Tahoe compatibility** — SSL has not validated Matrix Remote or ipMIDI on Tahoe. The bridge, if written natively in Swift or Python for macOS 26, provides a path forward if MatrixRemote has issues.
2. **Connection health monitoring and auto-recovery** — Intermittent ipMIDI sync loss is a documented community complaint. No SSL tool addresses it.
3. **Seamless dual-DAW profile switching** — MatrixRemote requires manual profile changes. A bridge can intercept and automate this.
4. **Auto-Mon punch conflict resolution** — The Pro Tools record tally mismatch with SSL's SuperCue monitoring is a known bug with no SSL workaround.
5. **Custom Ableton Live scripting** — If the standard MCU integration proves limiting, a custom Python control surface script for Ableton offers deeper integration than SSL's generic MCU profile.

---

## Sources

- [SSL Matrix Review — Sound on Sound](https://www.soundonsound.com/reviews/ssl-matrix) — MEDIUM confidence (review era, but hardware details remain accurate)
- [SSL Matrix² δelta Product Page](https://solidstatelogic.com/products/matrix) — MEDIUM confidence (official, but covers Matrix 2 delta primarily)
- [Matrix General FAQ — SSL Support](https://support.solidstatelogic.com/hc/en-gb/articles/4415895478417-Matrix-General-FAQ) — HIGH confidence (official support doc)
- [Delta Control Plug-in Suite — SSL Store](https://store.solidstatelogic.com/plug-ins/delta-control-plug-in-suite) — HIGH confidence (official, current)
- [SSL Matrix δelta Announcement](https://solidstatelogic.com/media/solid-state-logic-announce-new-matrix-%CE%B4elta-software-upgrade) — HIGH confidence (official announcement, confirms original Matrix support)
- [Barry Rudolph SSL Matrix Review](https://www.barryrudolph.com/mix/matrix.html) — MEDIUM confidence (hands-on, detailed, may be dated)
- [ipMIDI for macOS — nerds.de](https://www.nerds.de/en/ipmidi_osx.html) — HIGH confidence (ipMIDI 2.0 compatible with Sequoia 15; Tahoe 26 unverified)
- [Pro Tools Standard Matrix Profile Quick Start Guide](https://www.solidstatelogic.com/assets/uploads/downloads/matrix/ProTools-Standard-Matrix-Profile-Setup-Quick-Start-Guide.pdf) — HIGH confidence (official SSL setup doc)
- [HUI Protocol Wikipedia](https://en.wikipedia.org/wiki/Human_User_Interface_Protocol) — MEDIUM confidence (technical reference)
- [SSL Gearspace forum threads — DAW connection issues](https://gearspace.com/board/music-computers/1362568-ssl-matrix-2-users-do-you-have-daw-connection-issue.html) — LOW-MEDIUM confidence (community reports, informative for real-world problems)
- [Ableton Live HUI limitations — Ableton Forum](https://forum.ableton.com/viewtopic.php?t=242589) — MEDIUM confidence (confirms Ableton does not support HUI, only MCU)

---

*Feature research for: SSL Matrix console control bridge software*
*Researched: 2026-02-24*
