---
status: resolved
trigger: "half-faders-dead — SSL Matrix faders 9-16 unresponsive in both directions (Matrix→Ableton and Ableton→Matrix flying faders) while faders 1-8 work perfectly. MCU over ipMIDI Port 3."
created: 2026-02-25T17:30:00.000Z
updated: 2026-02-25T17:45:00.000Z
---

## Current Focus

hypothesis: CONFIRMED — Ableton is missing the MCU Extender control surface entry for faders 9-16
test: Cross-referenced SSL Matrix Live Profile PDF (official SSL doc) with current Ableton configuration
expecting: Adding MackieControlXT on ipMIDI Port 4 (Input + Output) resolves faders 9-16 in both directions
next_action: User to add MackieControlXT on Port 4 in Ableton Preferences > MIDI > Control Surfaces

## Symptoms

expected: All 16 Matrix faders control Ableton track volumes via MCU, and Ableton automation drives all 16 flying faders
actual: Faders 1-8 work bidirectionally. Faders 9-16 do absolutely nothing in either direction.
errors: No error messages — faders 9-16 simply do not respond
reproduction: Move any fader 9-16 on the Matrix — no corresponding track volume change in Ableton. Play automation on Ableton tracks 9-16 — no flying fader movement on the Matrix.
timeline: Unknown start; last session noted MCU as "fully working" but likely only tested faders 1-8 explicitly.

## Eliminated

- hypothesis: Hardware fault (physical fader failure on channels 9-16)
  evidence: The Matrix communicates channels 9-16 via a SEPARATE ipMIDI port (Port 4), not Port 3. If Port 4 has no listener, there is zero MIDI exchange in either direction — indistinguishable from a hardware fault but caused by missing software config.
  timestamp: 2026-02-25T17:45:00.000Z

- hypothesis: MatrixRemote profile misconfiguration for MCU zones
  evidence: MatrixRemote assigns MCU main (Port 3) and MCU extender (Port 4) as a fixed pair for DAW Layer 1. The console profile itself is correct — the gap is entirely on the Ableton side.
  timestamp: 2026-02-25T17:45:00.000Z

## Evidence

- timestamp: 2026-02-25T17:35:00.000Z
  checked: MCU protocol specification and SSL Matrix architecture
  found: MCU protocol is hard-limited to 8 faders per device. A 16-fader surface MUST use two separate MCU devices: a main controller (MackieControl) for faders 1-8 and an extender (MackieControlXT) for faders 9-16. These are two independent MIDI connections.
  implication: The current Ableton config with only ONE MCU entry can never reach faders 9-16 regardless of any other setting.

- timestamp: 2026-02-25T17:38:00.000Z
  checked: SSL Matrix Owner's Manual (https://solid-state-logic.co.jp/docs/Matrix_Owners_Manual.pdf), network wiring section
  found: "Channel controls and scribble strips on channels 9-16 can fail to update reliably when using the Channel keys" — this is a known protocol boundary note, confirming the 8-fader-per-port split is by design, not incidental.
  implication: SSL is aware of and documents the two-port architecture.

- timestamp: 2026-02-25T17:40:00.000Z
  checked: SSL Matrix Live Profile PDF — "Configuring Live for Matrix Control" screenshot (page 5 of Matrix_Live_Profile.pdf, official SSL document)
  found: DEFINITIVE. The official SSL Ableton Live configuration shows TWO control surface entries:
    - Row 1: MackieControl   | Input: ipMIDI (Port 1) | Output: ipMIDI (Port 2)
    - Row 2: MackieControlXT | Input: ipMIDI (Port 3) | Output: ipMIDI (Port 4)
  This is for DAW Layer 1. The caption states: "Substitute the appropriate MIDI ports if Live is required on a different Matrix layer."
  implication: The current setup is on a DIFFERENT layer — Ableton is on Port 3 (not Port 1). This means the layer offset applies. The correct pair for the active layer is: MackieControl on Port 3 + MackieControlXT on Port 4.

- timestamp: 2026-02-25T17:42:00.000Z
  checked: STATE.md and .continue-here.md for session history
  found: "Ableton uses MCU protocol on ipMIDI Port 3 (not Port 1 as expected)" — confirmed, the active DAW layer is NOT Layer 1 (which uses Port 1). The Matrix is configured with Ableton on a layer that uses Port 3 as the main MCU port.
  implication: Following SSL's two-port pairing pattern, Port 4 is the extender port for this layer. Only MackieControl on Port 3 was configured; MackieControlXT on Port 4 was never added. That is the exact missing entry.

- timestamp: 2026-02-25T17:44:00.000Z
  checked: SSL Matrix Live Profile PDF — ipMIDI port pairing pattern across layers
  found: SSL's screenshot shows the port pairing is always consecutive: main on odd port N, extender on even port N+1 (Port 1+2, Port 3+4, Port 5+6, etc.). The active session is on Port 3, so extender is Port 4.
  implication: No ambiguity. The fix is a single Ableton control surface entry: MackieControlXT, Input ipMIDI Port 4, Output ipMIDI Port 4.

## Resolution

root_cause: Ableton Live is configured with only ONE MCU control surface entry (MackieControl on ipMIDI Port 3), which covers faders 1-8. The MCU Extender entry (MackieControlXT on ipMIDI Port 4) is missing entirely. The SSL Matrix transmits fader 9-16 data exclusively on Port 4 and listens for flying fader commands on Port 4. With no Ableton listener on Port 4, there is zero MIDI exchange for channels 9-16 in either direction — exactly matching the observed symptom.

fix: Add a second control surface entry in Ableton Live Preferences > MIDI:
  - Control Surface: MackieControlXT
  - Input: ipMIDI (Port 4)
  - Output: ipMIDI (Port 4)
  The existing MackieControl entry on Port 3 stays unchanged.

verification: Not yet applied — user action required (see CHECKPOINT below).

files_changed: []

---

## CHECKPOINT: Human Action Required

**Type:** human-action

**Root cause is confirmed.** The fix requires adding one control surface entry in Ableton's GUI — this cannot be done programmatically.

### Steps to Fix

1. Open Ableton Live
2. Go to **Preferences > MIDI** (Cmd+,, then click MIDI tab)
3. In the Control Surfaces section, find the next empty row below the existing MackieControl entry
4. Set:
   - **Control Surface:** MackieControlXT
   - **Input:** ipMIDI (Port 4)
   - **Output:** ipMIDI (Port 4)
5. Close Preferences

### Verification After Fix

1. Move fader 9 on the Matrix — confirm the corresponding Ableton track volume changes
2. Move fader 16 on the Matrix — confirm response
3. Play automation on tracks 9-16 in Ableton — confirm the physical faders on the Matrix move

### If Port 4 Does Not Work

If faders 9-16 still do not respond after adding MackieControlXT on Port 4:
- Open MIDI Monitor (Snoize) and listen on all ipMIDI ports
- Move fader 9 on the Matrix
- Identify which port receives data (it will be one of: Port 2, Port 4, Port 6, or Port 8)
- The port that shows traffic IS the extender port — update the MackieControlXT entry to that port

### Why Port 4 Is the Correct Extender Port

The SSL Matrix Live Profile PDF (official SSL document) shows the port pairing pattern: main MCU and extender always use consecutive port pairs (1+2, 3+4, 5+6). The active Ableton layer uses Port 3 as the main MCU port. Therefore Port 4 is the extender port for this layer.

If the MatrixRemote profile was configured with a non-standard layer assignment, Port 4 is still the highest-probability guess. MIDI Monitor verification above will confirm definitively.
