# SSL Matrix Control Bridge

## What This Is

A software solution to restore full digital control of a 16-channel SSL Matrix mixing console on macOS Tahoe (26.2). The console's analog side works fine — audio path, channel strips, insertions — but all digital control features (flying faders, DAW control, automation, transport) are non-functional with the current Mac. This project combines proper configuration of existing SSL tools (MatrixRemote) with custom bridge software to fill the gaps, making the console the functional center of a hybrid mixing workflow with Pro Tools and Ableton Live.

## Core Value

Flying faders that respond to DAW automation playback and capture fader moves back into the DAW — this is what transforms the Matrix from a passive summing box into a real mixing console.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Flying faders respond to DAW automation playback (Pro Tools and Ableton Live)
- [ ] Fader movements on the console write automation into the DAW
- [ ] Transport control from the console surface (play, stop, record)
- [ ] Mute/solo states controllable and automatable
- [ ] MatrixRemote properly configured and communicating over Ethernet
- [ ] HUI protocol communication established between SSL Matrix and DAWs over USB
- [ ] Full board capabilities researched and documented (what's possible with the Matrix's digital control)
- [ ] Custom software bridge for any control gaps not covered by existing SSL tools
- [ ] Reliable operation on macOS Tahoe 26.2

### Out of Scope

- Hardware modifications to the console — software and configuration only
- Replacing the SSL Matrix with a different controller
- Building a standalone DAW — this integrates with Pro Tools and Ableton Live
- Analog signal path changes — the audio routing through Apollos is already working

## Context

- **Console:** SSL Matrix, 16 channels. Firmware updated at some point (version unknown). Connected via USB and Ethernet.
- **Audio interface:** Multiple Universal Audio Apollos (daisy-chained), providing sufficient I/O for all 16 Matrix channels.
- **MIDI:** MIDI I/O available — potential alternative control path if USB/HUI proves problematic on Tahoe.
- **MatrixRemote:** SSL's Ethernet-based control software is installed but the Mac's network hasn't been configured for it yet. MatrixRemote handles console configuration/routing but does NOT provide DAW control or sync.
- **HUI control:** Has never been working on this console for this user. This is the primary protocol for DAW integration (faders, transport, automation).
- **DAWs:** Pro Tools and Ableton Live — both need to work as automation targets.
- **Mixing style:** Hybrid automation — some moves on the console, some in the DAW. Channel routing varies per session (stems, individual tracks, etc.).
- **Documentation:** No SSL documentation on hand. All technical specs, protocols, and setup guides need to be researched online.
- **Timeline:** Urgent — actively needs this for sessions. Not a someday project.
- **Budget:** Open to hardware purchases if needed (MIDI interface, network switch, etc.) but wants to understand costs before committing.
- **Frustration:** The console represents significant wasted potential — an incredible piece of hardware sitting underutilized because the software layer hasn't kept up with modern macOS.

## Constraints

- **OS:** macOS Tahoe 26.2 — SSL's software may not be officially supported. Compatibility is a primary concern.
- **Existing hardware:** Must work with the SSL Matrix as-is (no hardware mods), multiple Apollos, and existing MIDI I/O.
- **Two DAWs:** Solution must work with both Pro Tools and Ableton Live, not just one.
- **HUI protocol:** The SSL Matrix uses HUI over USB for DAW control — this is a fixed protocol, not something we can change on the console side.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Configure existing tools first, build custom software for gaps | Maximize what already works before writing new code | — Pending |
| Target both Pro Tools and Ableton Live | User actively uses both DAWs for different purposes | — Pending |
| Research full board capabilities during project | User wants to discover everything the Matrix can do digitally, not just faders | — Pending |
| MIDI as fallback control path | If USB/HUI is broken on Tahoe, MIDI I/O is available as alternative | — Pending |

---
*Last updated: 2026-02-24 after initialization*
