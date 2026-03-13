# Phase 3: Console Surface Features — Research

**Researched:** 2026-03-13
**Domain:** SSL Matrix soft key programming, V-pot CC configuration, SuperCue/Auto-Mon re-scoping
**Confidence:** HIGH (grounded in wire-verified audit data from Phase 2 and decompiled Java source)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ADV-01 | Soft key macros programmed for session workflow (Pro Tools and Ableton commands) | Keymap edit flow identified; keymap names are `"keymap1"`–`"keymap4"` (not user strings); full builder/handler infrastructure exists in softkeys.py |
| ADV-02 | V-pot rotary encoders controlling pan, sends, and plugin parameters | Wheel mode per layer confirmed readable/settable (cmd 1060/1070); CC names list write confirmed (cmd 960); Layer 4 uses CC protocol |
| ADV-03 | SuperCue/Auto-Mon integration with DAW punch recording workflow | NOT IN UDP PROTOCOL — must be re-scoped to HUI/MCU-level transport interaction; see section below |
</phase_requirements>

---

## Summary

Phase 2 produced a complete, wire-verified audit of all 105 protocol handlers. The three Phase 3 requirements each have a specific, concrete status that directly constrains what the planner must build.

**ADV-01 (soft keys):** The protocol infrastructure to program soft keys exists and is fully implemented in ssl-matrix-client. The single remaining blocker is a pre-condition: the console firmware requires a named keymap to exist before an edit session can open. In the MatrixRemote Java source, keymaps are always named `"keymap1"` through `"keymap4"` (one per soft-key set slot, buttons 2–5 on the UI), never user-defined strings. The edit flow is: create named keymap via console surface UI (or confirm it already exists with `raw 600 0N`), then `sendSetEditKeyMapName(layer, "keymap1")` to open it, assign USB/MIDI commands per key, then save. This needs one physical prerequisite step (user creates keymap on surface), then can be fully automated via CLI.

**ADV-02 (V-pots):** Wheel mode is configurable per DAW layer via `ACK_GET_DEFAULT_WHEEL_MODE_STATUS` (cmd 1061) and `ACK_SET_DEFAULT_WHEEL_MODE_STATUS` (cmd 1071). Layer 4 is confirmed CC protocol. The CC names list write (cmd 960 `SEND_SET_CC_NAMES_LIST`) sends per-layer, per-type name arrays that populate the V-pot scribble strips. The `handle_cc_names_list_reply` handler currently parses but does not store CC names in ConsoleState — this is a known parser bug that must be fixed. Wheel mode value 5 on MCU/CC layers is undocumented and needs physical investigation.

**ADV-03 (SuperCue/Auto-Mon):** SuperCue is hardware-only on firmware V3.0/5 — no UDP protocol path exists. Probing cmds 1100–1200 returned zero responses in Phase 2. The requirement as written cannot be implemented via ssl-matrix-client. The most honest re-scope is: document the limitation, and if "integration" is still desired, implement it as HUI/MCU transport automation (Pro Tools punch record via HUI RECORD+PLAY command sequence through the DAW transport layer), not through console UDP.

**Primary recommendation:** ADV-01 and ADV-02 are buildable within ssl-matrix-client. ADV-03 must be re-scoped before planning — either accept it cannot be done via UDP and close it, or pivot to HUI/MCU approach as a separate task.

---

## Standard Stack

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Python stdlib only | 3.11+ | UDP messaging, CLI | Project constraint — no external dependencies |
| `ssl-matrix-client` (existing) | HEAD | Console control | Only software path to the Matrix on Tahoe |
| pytest | installed | Testing | Already in pyproject.toml |
| ruff | installed | Lint/format | Already in pre-commit hooks |

### No New Libraries Needed
This phase adds CLI commands and protocol sequences within the existing architecture. No new dependencies required.

---

## Architecture Patterns

### Existing Pattern: Builder + Handler + CLI Command
All features follow this three-part pattern established in the existing codebase:

1. **Builder function** in the relevant handler module — takes args, returns `bytes`
2. **Handler function** registered in `_build_dispatch_table()` — parses console reply, mutates `ConsoleState`
3. **CLI command** in `cli.py` — validates args, calls `self.client.send(builder(...))`, prints result

No deviation from this pattern. New commands follow it exactly.

### Recommended Project Structure (Phase 3 additions)
```
ssl-matrix-client/
  handlers/
    softkeys.py     — add: build_set_default_wheel_mode wrapper, cc_names store fix
  models.py         — add: cc_names to SoftkeysState
  cli.py            — add: do_softkey_*, do_vpot_*, do_wheel_mode commands
tests/
  test_handler_softkeys.py  — extend with CC names storage and wheel mode tests
```

---

## ADV-01: Soft Key Programming

### Protocol Flow (from decompiled Java + wire tests)

The correct keymap name format is established by the Java source:
```
SoftKeysPanel.java lines 366, 545, 2794:
  keySetName = "keymap" + (softkeySetButtonVal - 1)
  // softkeySetButtonVal is 2-5 (buttons on the panel)
  // so keymap names are "keymap1" through "keymap4"
  // "NONE" means no keymap is configured for that layer
```

**Keymap existence check flow:**
```
1. raw 600 0<layer>      → ACK_GET_EDIT_KEYMAP_NAME returns current name
   if name == "NONE":
     → user must press softkey editor button on surface to create a keymap
     → console creates "keymap1" (or "keymap2" etc per set selected)
   if name == "keymap1" (or "keymap2"–"keymap4"):
     → proceed to edit session
```

**Edit session flow:**
```
1. SEND_SET_EDIT_KEYMAP_NAME (cmd=610)   → opens edit session for named keymap on layer N
   ACK: "ok" or error string
2. SEND_GET_EDIT_KEYMAP_SIZE (cmd=640)   → returns panel_type: 1=transport(15 keys), 2=softkey(8 keys)
3. SEND_GET_EDIT_KEYMAP_DATA (cmd=620)   → returns all key assignments
   ACK: loop of (index, isTopRow, keyType, keycapName, type-specific data)
4. [assign keys as needed]:
   SEND_SET_USB_CMD (cmd=650)    → assign USB HID keycode to a key
   SEND_SET_MIDI_CMD (cmd=700)   → assign MIDI function to a key (by function index from MIDI list)
   SEND_SET_KEYCAP_NAME (cmd=660) → set label displayed on key
   SEND_SET_KEY_BLANK (cmd=670)  → clear a key assignment
5. SEND_SET_SAVE_EDIT_KEYMAP (cmd=680)  → save and close edit session
6. SEND_SET_EDIT_KEYMAP_NAME(layer, "NONE") (cmd=610) → close without saving (optional)
```

**Key type values (from Java constants):**
- `TP181_BLANK = 0` — unassigned
- `TP181_MIDI = 1` — MIDI function (indexed from MIDI function list)
- `TP181_USB = 2` — USB HID keycode string
- `TP181_MENU = 3` — submenu

**MIDI function list:**
- Layer 1 (HUI, Pro Tools): 102 functions — confirmed via wire test
- Layer 2 (MCU, Ableton): 64 functions — confirmed via wire test
- Retrieved via `SEND_GET_MIDI_FUNCTION_LIST (cmd=690)`, stored in `state.softkeys.midi_functions`

**USB command string format:**
The USB command string is the string the console sends over USB HID when the key is pressed. In the Java source this is treated as a raw USB keycode/modifier string. Exact format needs physical testing — but the builder `build_set_usb_cmd` is already implemented and takes a plain string.

### Pre-condition Required Before Testing
The user must press the softkey editor button on the console surface to create at least one named keymap (e.g., "keymap1") for a layer. Until this is done, `ACK_GET_EDIT_KEYMAP_NAME` returns "NONE" and the edit session rejects with "Error, name does not exist". Phase 3 Plan 1 must include a checkpoint requiring this console-side action.

### CLI Commands to Add (ADV-01)
```
softkey_keymap <layer>          — show current keymap name for layer (1-4)
softkey_edit <layer> <name>     — open edit session (name = "keymap1"-"keymap4")
softkey_list                    — show all key assignments from open edit session
softkey_usb <layer> <key> <row> <cmd>   — assign USB cmd to key
softkey_midi <layer> <key> <row> <func_index>  — assign MIDI function to key
softkey_name <key> <row> <name>  — set keycap label
softkey_blank <key> <row>        — clear key assignment
softkey_save                     — save and close edit session
softkey_midi_funcs <layer>       — list MIDI functions available for layer
```

---

## ADV-02: V-Pot Encoder Control

### Wheel Mode Per Layer
Wheel mode controls what the V-pot encoders do on each DAW layer.

**Confirmed values (from wire test + Java):**
- `0` = Pan (confirmed Layer 1 HUI = Pan mode)
- `1` = Linear (not tested on this console)
- `2` = Boost/Cut (not tested)
- `3` = Off (not tested)
- `5` = Unknown (Layer 2/3/4 returned mode 5 — NOT in Java enum, possible firmware extension)

**Protocol:**
```python
# Read wheel mode for layer
build_get_default_wheel_mode(desk_serial, my_serial, daw_layer)
# cmd=1060, payload: byte daw_layer
# ACK cmd=1061: byte skip, byte mode → stored in state.softkeys.default_wheel_mode

# Set wheel mode for layer
build_set_default_wheel_mode(desk_serial, my_serial, daw_layer, mode)
# cmd=1070, payload: byte daw_layer, byte mode
# ACK cmd=1071: string "ok" or error
```

Both builders already exist in `handlers/softkeys.py`. No new code needed for the protocol layer.

### CC Names List (V-Pot Parameter Names)
The CC layer (Layer 4) uses CC protocol, and parameter names shown on V-pot scribble strips come from the CC names list.

**Bug to fix:** `handle_cc_names_list_reply` currently parses names but does not store them in `ConsoleState`. `SoftkeysState` has no field for CC names. Fix required:

```python
# In models.py — SoftkeysState needs:
cc_names: list = field(default_factory=list)  # list of str

# In handlers/softkeys.py — handle_cc_names_list_reply must store:
state.softkeys.cc_names = names  # replace the local var with state assignment
```

**CC type values** (from `build_get_cc_names_list` call pattern in Java):
- type 0 through 3 — likely Pan, Send, EQ, Plugin or similar. Exact semantics need physical testing.

**Protocol to set CC names:**
```python
build_set_cc_names_list(desk_serial, my_serial, daw_layer, cc_type, names)
# cmd=960, payload: byte layer, byte type, byte numNames, then N x string
# ACK cmd=961: string "ok" or error — existing handler handle_softkey_ack covers this
```

The `ACK_SET_CC_NAMES_LIST` (cmd=961) handler is currently SKIP (no CLI trigger, CC layer unconfigured). This handler must be tested and confirmed working.

### CLI Commands to Add (ADV-02)
```
wheel_mode <layer>              — show current wheel mode for layer
wheel_mode <layer> <0-5>        — set wheel mode for layer
cc_names <layer> <type>         — show CC parameter names for layer/type
cc_names_set <layer> <type> <name1> [name2...]  — set CC parameter names
```

---

## ADV-03: SuperCue / Auto-Mon

### Finding from Phase 2 (CONFIRMED)
SuperCue/Auto-Mon is **NOT in the UDP protocol** on firmware V3.0/5.

Evidence:
- Probe of cmds 1100–1200 (step 10): zero console responses
- No SuperCue/Auto-Mon fields in any state dump
- No profile names reference SuperCue

### Re-scope Options

| Option | Description | Effort | Notes |
|--------|-------------|--------|-------|
| A: Close as hardware-only | Document as out-of-scope for ssl-matrix-client | Minimal | Most honest — zero code |
| B: HUI punch-in helper | Add CLI commands that send HUI REC+PLAY transport automation to trigger punch recording in Pro Tools | Medium | Operates at ipMIDI/HUI layer, not UDP |
| C: MCU punch helper | Same for Ableton MCU | Medium | ipMIDI layer |

**Recommendation:** Option A (close/document) unless the user explicitly wants a HUI/MCU punch-in helper. The requirement as written ("SuperCue/Auto-Mon integration with DAW punch recording workflow") describes a hardware feature. Implementing B or C is technically possible but is a different feature than what ADV-03 describes.

**The planner must present this choice to the user and get a decision before writing ADV-03 tasks.** If Option A, ADV-03 is satisfied by documentation only.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| USB HID keycode tables | Custom HID enum | Test with known strings on live console | Format verified by wire test, not spec |
| MIDI function name resolution | Custom lookup table | `state.softkeys.midi_functions` (returned by console) | Console owns the canonical list |
| Keymap name generation | User-facing name dialog | Always use `"keymap1"–"keymap4"` | Java source confirms these are the only valid names |
| CC scribble strip rendering | Any display layer | Already handled by HUI/MCU protocol at ipMIDI layer | DAW sends scribble data; CC names configure V-pot only |

---

## Common Pitfalls

### Pitfall 1: Using "NONE" as an Edit Session Keymap Name
**What goes wrong:** `sendSetEditKeyMapName(layer, "NONE")` returns "Error, name does not exist". The edit session never opens.
**Why it happens:** "NONE" is a sentinel value meaning "no keymap configured". The console rejects it as an invalid edit target.
**How to avoid:** Always use `"keymap1"` through `"keymap4"`. Verify the keymap exists first with `raw 600 0<layer>`.
**Warning signs:** ACK returns error string instead of "ok".

### Pitfall 2: Editing a Keymap on a Read-Only Profile
**What goes wrong:** All six factory profiles (Pro Tools Standard, Live Standard, Logic Standard, etc.) are read-only. Any SET operation returns "Profile is read-only."
**Why it happens:** Factory profiles cannot be modified. Phase 2 confirmed flip/handshake SET fails on RO profiles.
**How to avoid:** Keymap edits must target a layer whose profile is read-write. The console has two user profiles: "kj" (RW) and "pt2" (RW). Use `do_profiles` to check read_only status before attempting edit. Layer 1 uses "Pro Tools Standard" (RO) — softkey editing on layer 1 requires copying to a new RW profile first via `sendCopyProfileToNew` + `sendSetProfileForDawLayer`.
**Warning signs:** Any "Profile is read-only" error from ACK.

### Pitfall 3: Setting Wheel Mode and Expecting Immediate Effect
**What goes wrong:** Wheel mode change may require a console restart or DAW reconnect to take effect.
**Why it happens:** The Delta automation mode change (Phase 2) required a restart. Wheel mode may behave similarly — not confirmed.
**How to avoid:** After `set_default_wheel_mode`, immediately read it back (cmd 1060) to confirm the ACK reflects the change. Test physical encoder behavior before assuming effect.
**Warning signs:** Mode reads back as old value after SET ACK says "ok".

### Pitfall 4: CC Names Not Stored in State
**What goes wrong:** `do_cc_names` shows empty list even after `SEND_GET_CC_NAMES_LIST` returns data.
**Why it happens:** `handle_cc_names_list_reply` parses but discards names into a local variable. Known bug from Phase 2.
**How to avoid:** Fix `SoftkeysState` to add `cc_names: list` field and update handler to store before adding CLI commands that read it.
**Warning signs:** State dump shows no cc_names field.

### Pitfall 5: Profile Copy Required Before Soft Key Edit on HUI Layer
**What goes wrong:** Layer 1 (Pro Tools/HUI) uses "Pro Tools Standard" (RO). Cannot assign softkeys to it.
**Why it happens:** Read-only profile constraint.
**How to avoid:** Use `build_copy_profile_to_new` to clone a factory profile to a new RW profile, then `build_set_profile_for_daw_layer` to assign it to layer 1, then edit softkeys. Both builders already exist in `handlers/profiles.py`.
**Warning signs:** All softkey edit attempts on layer 1 return "Profile is read-only."

---

## Code Examples

### Opening a Keymap Edit Session
```python
# Source: decompiled SoftKeysPanel.java lines 365-372 + build_set_edit_keymap_name
# Check current keymap name first
client.send(build_get_edit_keymap_name(desk_serial, my_serial, layer=1))
# state.softkeys.keymap_name will be "NONE" or "keymap1"-"keymap4"

# Open edit session (keymap must exist — create via console surface UI if NONE)
client.send(build_set_edit_keymap_name(desk_serial, my_serial, daw_layer=1, keymap_name="keymap1"))
# ACK (cmd=611): "ok" or error string → handle_softkey_ack logs warnings on error
```

### Assigning a USB Command to Soft Key
```python
# Source: handlers/softkeys.py build_set_usb_cmd
# daw_layer=1, key_index=1, is_top_row=1, usb_cmd="ctrl+shift+p"
client.send(build_set_usb_cmd(desk_serial, my_serial, daw_layer=1, key_index=1, is_top_row=1, usb_cmd="ctrl+shift+p"))
# ACK (cmd=651): "ok" or error → handle_softkey_ack
```

### Assigning a MIDI Function to Soft Key
```python
# Source: handlers/softkeys.py build_set_midi_cmd
# Get MIDI function list first to find function index
client.send(build_get_midi_function_list(desk_serial, my_serial, daw_layer=1))
# state.softkeys.midi_functions = [(0, "Play", "Play"), (1, "Stop", "Stop"), ...]
# Then assign function index 0 (Play) to key 3:
client.send(build_set_midi_cmd(desk_serial, my_serial, daw_layer=1, is_top_row=1, key_index=3, func_index=0))
```

### Saving and Closing Edit Session
```python
# Source: handlers/softkeys.py build_save_edit_keymap
client.send(build_save_edit_keymap(desk_serial, my_serial))
# ACK (cmd=681): "ok" or error → handle_softkey_ack
```

### Reading and Setting Wheel Mode
```python
# Source: handlers/softkeys.py
client.send(build_get_default_wheel_mode(desk_serial, my_serial, daw_layer=2))
# state.softkeys.default_wheel_mode → current mode (0=Pan, 1=Linear, 2=Boost/Cut, 3=Off, 5=unknown)

client.send(build_set_default_wheel_mode(desk_serial, my_serial, daw_layer=2, mode=0))
# ACK (cmd=1071): "ok" or error
```

### Setting CC Names (V-Pot Parameter Labels)
```python
# Source: handlers/softkeys.py build_set_cc_names_list
names = ["Pan", "Send 1", "Send 2", "EQ Gain"]
client.send(build_set_cc_names_list(desk_serial, my_serial, daw_layer=4, cc_type=0, names=names))
# ACK (cmd=961): "ok" or error
```

---

## State of the Art

| Old Understanding | Corrected Understanding | Source | Impact |
|-------------------|------------------------|--------|--------|
| "Keymap names are user strings" | Keymaps are always named "keymap1"–"keymap4" | decompiled SoftKeysPanel.java lines 366, 545, 2794 | CLI args must validate against this set |
| "SuperCue is in UDP protocol" | SuperCue is hardware-only, no UDP path | Phase 2 wire test — zero responses to cmds 1100-1200 | ADV-03 must be re-scoped |
| "CC names not stored in state" | Known bug in handle_cc_names_list_reply | Phase 2 audit + code inspection | Must fix before ADV-02 CLI is useful |
| "Wheel mode 5 is unknown" | Mode 5 on MCU/CC layers — undocumented | Phase 2 audit | Needs physical testing to classify |

---

## Open Questions

1. **What does wheel mode value 5 mean?**
   - What we know: Returned by Layer 2 (MCU), Layer 3 (MCU), Layer 4 (CC) on this console
   - What's unclear: Not in the Java enum (Pan=0, Linear=1, Boost/Cut=2, Off=3). May be a firmware extension or parsing artifact
   - Recommendation: Physical test — set layer 2 to mode 0 (Pan), check V-pot behavior, then restore. Add a `--raw-mode` flag to `wheel_mode` CLI command so undocumented values can be set

2. **What is the USB command string format for soft keys?**
   - What we know: `build_set_usb_cmd` sends a plain null-terminated string. Java passes it as-is.
   - What's unclear: Does the console interpret it as a USB HID key name ("ctrl+shift+p"), a modifier+key code ("0x41"), or something else?
   - Recommendation: Physical test — assign known string to key 1, press it, observe what the console sends to the host computer. Use a USB HID monitor tool.

3. **Does wheel mode change require a console restart?**
   - What we know: Delta automation mode required a restart to take effect (Phase 2 finding)
   - What's unclear: Whether wheel mode takes effect immediately or after restart
   - Recommendation: Test on live console before writing "effective immediately" documentation

4. **ADV-03 re-scope: what does the user actually want?**
   - What we know: SuperCue is not in the UDP protocol
   - What's unclear: Whether the user wants (a) this documented and closed, (b) a HUI punch helper, or (c) something else entirely
   - Recommendation: Planner must get user decision before writing any ADV-03 tasks

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (installed, pyproject.toml) |
| Config file | `pyproject.toml` |
| Quick run command | `python3 -m pytest tests/test_handler_softkeys.py -v` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADV-01 | Keymap name builder sends correct keymap name string | unit | `pytest tests/test_handler_softkeys.py::TestSoftkeyBuilders -x` | Yes |
| ADV-01 | Edit session open/close round-trip (requires live console) | manual | Live REPL test | N/A |
| ADV-01 | MIDI function assignment builder | unit | `pytest tests/test_handler_softkeys.py -x -k "midi"` | Yes (extend) |
| ADV-01 | USB command assignment builder | unit | `pytest tests/test_handler_softkeys.py -x -k "usb"` | Wave 0 |
| ADV-02 | Wheel mode GET/SET builders produce correct payload | unit | `pytest tests/test_handler_softkeys.py -x -k "wheel"` | Wave 0 |
| ADV-02 | CC names stored in state after parse | unit | `pytest tests/test_handler_softkeys.py::TestCcNamesList -x` | Extend existing |
| ADV-02 | CC names SET builder payload structure | unit | `pytest tests/test_handler_softkeys.py -x -k "cc_names"` | Yes (extends existing) |
| ADV-03 | Documentation only (if re-scoped to Option A) | — | — | N/A |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_handler_softkeys.py -v`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_handler_softkeys.py` — add `TestWheelMode` builder tests (builders exist, tests missing)
- [ ] `tests/test_handler_softkeys.py` — add `TestCcNamesStorage` test confirming fix (handler fix needed first)
- [ ] `tests/test_handler_softkeys.py` — add USB command builder test
- [ ] No framework install needed — pytest already configured

---

## Sources

### Primary (HIGH confidence)
- `reverse-engineering/decompiled/sources/com/solidstatelogic/remote/common/handlers/SoftKeysHandler.java` — complete wire format for all softkey protocol messages
- `reverse-engineering/decompiled/sources/com/solidstatelogic/remote/matrix/SoftKeysPanel.java` lines 366, 545, 2794 — keymap naming convention confirmed: "keymap1"–"keymap4"
- `.planning/phases/02-capabilities-audit/CAPABILITIES.md` — Feature Feasibility section (wire-verified on live console)
- `ssl-matrix-client/handlers/softkeys.py` — all existing builder/handler implementations
- `ssl-matrix-client/models.py` — SoftkeysState dataclass (cc_names gap identified)

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` Accumulated Context — Phase 02 findings on SuperCue, softkeys, V-pot
- `.planning/phases/02-capabilities-audit/02-02-SUMMARY.md` — detailed audit findings with exact failure modes

### Tertiary (LOW confidence)
- Wheel mode value 5 interpretation — no authoritative source found; undocumented in Java enum

---

## Metadata

**Confidence breakdown:**
- ADV-01 architecture: HIGH — keymap names confirmed from Java source; all builders/handlers verified in code
- ADV-01 physical flow: MEDIUM — edit session untested on live console (no keymap existed during Phase 2)
- ADV-02 wheel mode: HIGH for read/set protocol; LOW for mode=5 semantics
- ADV-02 CC names: HIGH for protocol; fix needed in handler before functional
- ADV-03: HIGH confidence it is NOT in UDP protocol (wire-verified)

**Research date:** 2026-03-13
**Valid until:** Stable — this console hardware is unchanged; valid until firmware update
