# Phase 1: Compatibility Verification - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Confirm the entire Ethernet/ipMIDI/MatrixRemote protocol stack functions on macOS Tahoe 26.2. This is a pure configuration and verification phase — no custom code is written. The phase is complete when a DAW can send/receive control data to/from the SSL Matrix. Setting up the full bridge software is Phase 2+.

</domain>

<decisions>
## Implementation Decisions

### Fallback Strategy
- Primary path: Ethernet + ipMIDI (designed protocol path for the SSL Matrix)
- Fallback path: iConnectivity mioXL DIN MIDI interface (already connected to Mac and working, DIN MIDI cables on hand)
- Research must verify whether the Matrix's DIN MIDI ports carry HUI/MCU control data or only auxiliary MIDI — this determines whether the mioXL is a viable fallback for DAW control
- If ipMIDI fails on Tahoe 26.2, switch to mioXL testing the next day
- No OS downgrade considered — one of the two paths WILL work
- The mioXL also has Ethernet/RTP-MIDI capabilities (unused so far) — could be a third path if needed

### Verification Criteria
- Full DAW test required — "ports visible in Audio MIDI Setup" is NOT sufficient
- Pro Tools 2025.x is the first DAW to verify with (canonical HUI target)
- Four behaviors must all pass to mark phase complete:
  1. Playing automation in Pro Tools moves physical faders on the Matrix
  2. Pressing transport buttons on Matrix controls Pro Tools playback
  3. Touching and moving a fader on Matrix writes automation into Pro Tools
  4. Pro Tools track names appear on Matrix scribble strips
- User will create a test session with simple fader automation for verification
- MIDI monitoring tools need to be installed as part of this phase (user doesn't have one)

### Console Inventory
- Console is an original SSL Matrix v1 (not Matrix²)
- Firmware version is unknown — plan must include steps to check firmware via the console display
- No SD card in rear slot (stores MatrixRemote configs/profiles)
- Ethernet cable is connected from Matrix to a USB hub/dock that has a built-in Ethernet port
- Mac connects to Ethernet via a Thunderbolt adapter
- Network topology is unclear — must verify Matrix and Mac Ethernet are on the same network segment during setup
- ipMIDI multicast routing is a known pain point with multiple network adapters — Mac has Wi-Fi + Thunderbolt Ethernet + USB hub Ethernet, all of which could interfere

### Claude's Discretion
- Choice of MIDI monitoring tool (MIDI Monitor by Snoize is the standard macOS choice)
- Exact order of verification steps within the phase
- How to handle partial success (e.g., MIDI ports visible but faders don't move)
- Network troubleshooting approach if ipMIDI multicast doesn't route correctly

</decisions>

<specifics>
## Specific Ideas

- The mioXL is a significant asset — it's already working and connected. If the Ethernet/ipMIDI path has issues, the DIN MIDI fallback can potentially be attempted in the same session.
- Network topology investigation is critical — the USB hub/dock with built-in Ethernet may or may not be on the same segment as the Mac's Thunderbolt Ethernet adapter. This needs to be mapped before any ipMIDI testing.
- MatrixRemote is a Java application — Java runtime compatibility on Tahoe 26.2 is an additional verification point beyond just ipMIDI.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-compatibility-verification*
*Context gathered: 2026-02-24*
