# Phase 2: Capabilities Audit - Research

**Researched:** 2026-03-11
**Domain:** SSL Matrix UDP protocol wire-testing, split board feasibility, softkey/V-pot/SuperCue capability mapping
**Confidence:** HIGH (primary source is the codebase itself — no external library unknowns)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
1. **Audit scope: all 105 dispatch handlers + feature feasibility** — Protocol verification (pass/fail per handler) AND feature feasibility (soft keys, V-pots, SuperCue, split board).
2. **ssl-matrix-client is the sole console control tool** — MatrixRemote is completely broken on macOS Tahoe 26.2. Every protocol feature must work through ssl-matrix-client.
3. **No custom DAW bridge needed** — Pro Tools (HUI) and Ableton Live (MCU) both communicate with the Matrix natively over ipMIDI. DAW switching is hardware buttons.
4. **Split board is a key feasibility question** — Left 8 faders on one DAW, right 8 on another simultaneously. Audit must answer this definitively.
5. **Testing approach: CLI-driven, documented results** — Each handler group tested through ssl-matrix-client CLI commands against live console. Results in a capabilities document.

### Claude's Discretion
- (none specified — scope and approach are fully locked)

### Deferred Ideas (OUT OF SCOPE)
- Routing recall from DAW (Phase 4 — session templates)
- Session-aware router presets (Phase 4)
- Connection health monitoring (Phase 4)
- Native macOS dock app (Phase 5)
- Language choice for GUI app (research during Phase 4/5)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUDIT-01 | All 105 ssl-matrix-client dispatch handlers wire-tested against live console with pass/fail documented | Handler inventory below; 10 handler groups identified; test script architecture defined |
| AUDIT-02 | Soft key, V-pot, and SuperCue protocol capabilities mapped with confirmed working message codes | Softkeys handler has 28 builders; V-pot maps to wheel mode / flip state; SuperCue needs investigation |
| AUDIT-03 | Split board feasibility determined — can two DAW layers run simultaneously on different fader groups? | DAW layer protocol (cmd 910) and profile-per-layer (cmd 800/820) are the key messages; 4 layers exist |
| AUDIT-04 | Capabilities document listing every confirmed feature, limitation, and protocol gap | Structured output format defined; gaps identified (file transfer, lower scrib mode, image lib, RTC, network) |
</phase_requirements>

---

## Summary

Phase 2 is a structured verification exercise, not a development phase. The ssl-matrix-client was implemented from decompiled Java sources (MatrixRemote) and has never been run against the live console in a systematic way. All 105 dispatch entries are structurally sound — they compile, their packet formats match the Java source, and the dispatch table is correct — but they have not been wire-tested. The console at 192.168.1.2 is the only truth.

The audit has two modes of work. For query-type handlers (GET_*), the test is: send the message, observe a reply in state, confirm the state reflects reality on the console. For mutation-type handlers (SET_*/SEND_*), the test is: send the message, observe the ACK, confirm the console surface changed. A handful of handlers carry meaningful risk (project delete, restart console, Total Recall snapshot operations) and require care during testing.

The split board question is the most architecturally significant unknown. The firmware supports 4 DAW layers (layers 1-4), each with independent protocol assignment (HUI, MCU, CC) and profile assignment. Whether the console allows two layers to be active simultaneously with independent fader group assignments is not documented anywhere in the decompiled Java — the Java app always operates on one layer at a time. This must be determined empirically.

**Primary recommendation:** Run the audit in handler-group batches, starting with read-only queries (connection, channels, profiles, delta state), then progressing to mutations, then destructive operations. Document every result in a structured capabilities table as you go.

---

## Handler Inventory

The dispatch table has exactly 105 entries across 10 handler modules. This is the complete test surface for AUDIT-01.

### Handler Group Breakdown

| Group | Handler Module | Dispatch Entries | CLI Commands Available | Risk Level |
|-------|---------------|-----------------|----------------------|------------|
| Connection | `connection.py` | 3 | `connect`, `status` | None |
| Channels | `channels.py` | 5 | `channels`, `rename`, (display/flip via raw) | Low |
| Profiles / DAW layers | `profiles.py` | 4 | `layers`, `profiles`, `setprofile`, `clearlayer`, `transportlock` | Medium |
| Delta | `delta.py` | 3 | `automode`, `motors`, `mdac`, `restart` | High (restart) |
| Routing (insert matrix) | `routing.py` | 18 | `devices`, `chains`, `matrix`, `assign`, `deassign`, `matrix_presets`, `load_preset`, `save_preset` | Medium |
| Projects | `projects.py` | 11 | `project_info`, `projects`, `select_title`, `new_project`, `new_title`, `delete_project`, `delete_title` | High (delete) |
| Total Recall | `total_recall.py` | 3 | `tr_snapshots`, `tr_take`, `tr_select`, `tr_delete`, `tr_enable` | High (delete/enable) |
| Channel Names Presets | `chan_presets.py` | 4 | `chan_presets`, `save_chan_preset`, `load_chan_preset` | Low |
| XPatch | `xpatch.py` | 17 | `xpatch_setup`, `xpatch_routes`, `xpatch_route`, `xpatch_presets`, `xpatch_select` | Medium |
| Softkeys | `softkeys.py` | 37 | (no top-level CLI commands yet — requires `raw` cmd or new CLI) | Medium |

**Total: 105 dispatch entries.**

### Full Dispatch Entry List (AUDIT-01 test surface)

**Connection (3 entries):**
- `GET_DESK_REPLY` (cmd 6) — discovery response
- `SEND_HEARTBEAT` (cmd 7) — console keep-alive
- `GET_PROJECT_NAME_AND_TITLE_REPLY` (cmd 11) — project/title info

**Channels (5 entries):**
- `GET_CHAN_NAMES_AND_IMAGES_REPLY` (cmd 21) — channel name read
- `SET_CHAN_NAMES_REPLY` (cmd 32) — channel name write ack
- `SET_DEFAULT_CHAN_NAMES_REPLY` (cmd 29) — default name set ack
- `ACK_GET_DISPLAY_17_32` (cmd 10741) — channel 17-32 display state
- `ACK_GET_FLIP_SCRIB_STRIP` (cmd 10761) — scribble strip flip state

**Profiles / DAW layers (4 entries):**
- `ACK_GET_DAW_LAYER_PROTOCOL` (cmd 911) — layer protocol read
- `ACK_GET_PROFILE_FOR_DAW_LAYER` (cmd 801) — profile name per layer
- `ACK_GET_PROFILES` (cmd 841) — full profile list
- `ACK_GET_TRANSPORT_LOCK_DAW_LAYER` (cmd 871) — transport lock state

**Delta (3 entries):**
- `ACK_GET_AUTOMATION_MODE` (cmd 10901) — legacy vs delta mode
- `ACK_GET_MOTORS_OFF_TOUCH_EN` (cmd 11101) — motor behavior
- `ACK_GET_MDAC_METER_EN` (cmd 11301) — MDAC meter enable

**Routing — data replies (4 entries):**
- `ACK_GET_INSERT_INFO_V2` (cmd 10401) — insert device names/status
- `ACK_GET_CHAIN_INFO_V2` (cmd 10421) — chain definitions
- `ACK_GET_CHAN_MATRIX_INFO_V2` (cmd 10441) — channel insert routing
- `ACK_GET_MATRIX_PRESET_LIST` (cmd 10631) — preset list

**Routing — ACK replies (13 entries):**
- `ACK_SET_INSERT_NAMES_V2`, `ACK_SET_INSERT_TO_CHAN_V2`, `ACK_ASSIGN_CHAIN_TO_CHAN_V2`,
  `ACK_DEASSIGN_CHAN_V2`, `ACK_DELETE_CHAIN_V2`, `ACK_RENAME_CHAIN`,
  `ACK_SAVE_INSERTS_TO_CHAIN`, `ACK_DELETE_CHAN_INSERT`, `ACK_SET_CHAN_STEREO_INSERT`,
  `ACK_LOAD_MATRIX_PRESET`, `ACK_SAVE_MATRIX_PRESET`, `ACK_DELETE_MATRIX_PRESET`,
  `ACK_RENAME_MATRIX_PRESET`, `ACK_CLEAR_INSERTS`

**Projects — data replies (2 entries):**
- `GET_DIRECTORY_LIST_REPLY` (cmd 61) — filesystem directory
- `SEND_DISK_INFO` (cmd 72) — disk usage

**Projects — ACK replies (9 entries):**
- `ACK_MAKE_NEW_PROJECT`, `ACK_MAKE_NEW_PROJECT_TITLE`, `ACK_MAKE_NEW_PROJECT_TITLE_WITH_NAME`,
  `ACK_SELECT_PROJECT_TITLE`, `ACK_DELETE_PROJECT_TITLE`, `ACK_DELETE_PROJECT`,
  `ACK_COPY_PROJECT_TITLE`, `ACK_MAKE_NEW_PROJECT_WITH_NAME`, `ACK_MAKE_NEW_PROJECT_WITH_PRESET_OPTS`

**Total Recall (3 entries):**
- `ACK_SET_TR_ENABLE` (cmd 301) — TR on/off
- `ACK_GET_TR_STATE` (cmd 303) — TR state read
- `GET_TR_LIST_REPLY` (cmd 65) — snapshot list

**Channel Names Presets (4 entries):**
- `ACK_GET_CHAN_NAMES_PRESET_LIST` (cmd 10791)
- `ACK_RENAME_CHAN_NAMES_PRESET` (cmd 10771)
- `ACK_DELETE_CHAN_NAMES_PRESET` (cmd 10781)
- `ACK_SAVE_CHAN_NAMES_PRESET` (cmd 10801)
- `ACK_LOAD_CHAN_NAMES_PRESET` (cmd 10811)

**XPatch — setup (9 entries):**
- `GET_XPATCH_CHAN_SETUP_REPLY` (cmd 2061)
- `SET_XPATCH_INPUT_MINUS10DB_REPLY` (cmd 2071)
- `SET_XPATCH_OUTPUT_MINUS10DB_REPLY` (cmd 2081)
- `SET_XPATCH_CHAN_MODE_REPLY` (cmd 2091)
- `SET_XPATCH_DEVICE_NAME_REPLY` (cmd 3001)
- `SET_XPATCH_DEST_NAME_REPLY` (cmd 3011)
- `GET_XPATCH_MIDI_SETUP_REPLY` (cmd 3016)
- `SET_XPATCH_MIDI_ENABLE_REPLY` (cmd 3021)
- `SET_XPATCH_MIDI_CHANNEL_REPLY` (cmd 3041)

**XPatch — routing (1 entry):**
- `GET_XPATCH_ROUTING_DATA_REPLY` (cmd 3051)

**XPatch — presets (3 entries):**
- `GET_XPATCH_PRESETS_LIST_REPLY` (cmd 2001)
- `SET_XPATCH_PRESET_SELECTED_REPLY` (cmd 2012)
- `GET_XPATCH_PRESET_EDITED_REPLY` (cmd 2014)

**XPatch — chains (4 entries):**
- `GET_XPATCH_CHAINS_LIST_REPLY` (cmd 4001)
- `GET_XPATCH_EDIT_CHAIN_REPLY` (cmd 4050)
- `GET_XPATCH_EDIT_CHAIN_TOUCHED_REPLY` (cmd 4071)
- `SET_XPATCH_LINK_REPLACE_MODE_REPLY` (cmd 4091)

**Softkeys — data replies (11 entries):**
- `ACK_GET_EDIT_KEYMAP_NAME` (cmd 601)
- `ACK_GET_EDIT_KEYMAP_DATA` (cmd 621)
- `ACK_GET_EDIT_KEYMAP_SIZE` (cmd 641)
- `ACK_GET_MIDI_FUNCTION_LIST` (cmd 691)
- `ACK_GET_FLIP_STATUS` (cmd 1001)
- `ACK_GET_HANDSHAKING_STATUS` (cmd 1021)
- `ACK_GET_AUTO_MODE_ON_SCRIBS_STATUS` (cmd 1041)
- `ACK_GET_DEFAULT_WHEEL_MODE_STATUS` (cmd 1061)
- `ACK_GET_FADER_DB_READOUT_STATUS` (cmd 1091)
- `ACK_GET_CC_NAMES_LIST` (cmd 951)
- `ACK_GET_PROFILE_PATH` (cmd 941)

**Softkeys — ACK replies (26 entries):**
- All `ACK_SET_*` softkey commands, plus profile ACKs routed through `handle_softkey_ack`

---

## Architecture Patterns

### Test Execution Order (Risk-Ordered)

Test in this sequence. Each tier requires the previous tier to confirm the client can communicate.

**Tier 0: Connection (prerequisite for all else)**
```
connect                   # GET_DESK_REPLY, heartbeat, project name
status                    # verify desk online, serial populated
```

**Tier 1: Read-only queries (zero risk)**
```
channels                  # GET_CHAN_NAMES_AND_IMAGES_REPLY
layers                    # ACK_GET_DAW_LAYER_PROTOCOL x4, ACK_GET_TRANSPORT_LOCK_DAW_LAYER
profiles                  # ACK_GET_PROFILES
automode                  # ACK_GET_AUTOMATION_MODE
motors                    # ACK_GET_MOTORS_OFF_TOUCH_EN
mdac                      # ACK_GET_MDAC_METER_EN
devices                   # ACK_GET_INSERT_INFO_V2
chains                    # ACK_GET_CHAIN_INFO_V2
matrix                    # ACK_GET_CHAN_MATRIX_INFO_V2
matrix_presets            # ACK_GET_MATRIX_PRESET_LIST
project_info              # (populated on connect via sync)
projects                  # GET_DIRECTORY_LIST_REPLY, SEND_DISK_INFO
tr_snapshots              # ACK_GET_TR_STATE, GET_TR_LIST_REPLY
chan_presets               # ACK_GET_CHAN_NAMES_PRESET_LIST
xpatch_setup              # GET_XPATCH_CHAN_SETUP_REPLY
xpatch_routes             # GET_XPATCH_ROUTING_DATA_REPLY
xpatch_presets            # GET_XPATCH_PRESETS_LIST_REPLY, GET_XPATCH_CHAINS_LIST_REPLY
raw 601 01                # ACK_GET_EDIT_KEYMAP_NAME (softkey, layer 1)
raw 641                   # ACK_GET_EDIT_KEYMAP_SIZE
raw 691 01                # ACK_GET_MIDI_FUNCTION_LIST (layer 1)
raw 1000 01               # ACK_GET_FLIP_STATUS (layer 1)
raw 1020 01               # ACK_GET_HANDSHAKING_STATUS
raw 1040 01               # ACK_GET_AUTO_MODE_ON_SCRIBS_STATUS
raw 1060 01               # ACK_GET_DEFAULT_WHEEL_MODE_STATUS
raw 1090 01               # ACK_GET_FADER_DB_READOUT_STATUS
raw 950 01 00             # ACK_GET_CC_NAMES_LIST
```

**Tier 2: Non-destructive mutations (low risk)**
```
rename 1 TEST             # SET_CHAN_NAMES_REPLY — rename then restore
rename 1 <original>       # restore
raw 10730 01              # SEND_SET_DISPLAY_17_32 (toggle)
raw 10730 00              # restore
raw 10750 01              # SEND_SET_FLIP_SCRIB_STRIP (toggle and restore)
raw 10750 00
raw 620 00 00 00          # ACK_GET_EDIT_KEYMAP_DATA (keymap data)
raw 1010 01 00            # SEND_SET_FLIP_STATUS (flip off then on)
raw 1010 01 01
raw 1030 01 00            # SEND_SET_HANDSHAKING_STATUS (toggle)
```

**Tier 3: State mutations (medium risk — test on non-critical state)**
```
save_chan_preset AUDIT-TEST   # ACK_SAVE_CHAN_NAMES_PRESET
load_chan_preset AUDIT-TEST   # ACK_LOAD_CHAN_NAMES_PRESET
# clean up: delete preset after test
tr_take                   # ACK_TAKE_TR_SNAP (creates a TR snapshot)
tr_select 0               # ACK_SELECT_TR_SNAP
# document tr_delete separately — destructive
save_preset AUDIT-TEST    # ACK_SAVE_MATRIX_PRESET
load_preset AUDIT-TEST    # ACK_LOAD_MATRIX_PRESET
# delete preset after test
```

**Tier 4: High-risk mutations (require explicit caution)**
```
# Test these only after documenting current state
# Automation mode change requires console restart:
automode delta            # SEND_SET_AUTOMATION_MODE
restart                   # SEND_RESTART_CONSOLE (separate test with timer)
automode legacy
restart

# Project/title operations: test only on a known disposable project
new_project AUDIT-TEMP    # ACK_MAKE_NEW_PROJECT_WITH_NAME
new_title AUDIT-TEMP TESTTITLE  # ACK_MAKE_NEW_PROJECT_TITLE_WITH_NAME
select_title AUDIT-TEMP TESTTITLE  # ACK_SELECT_PROJECT_TITLE
delete_title AUDIT-TEMP TESTTITLE  # ACK_DELETE_PROJECT_TITLE
delete_project AUDIT-TEMP  # ACK_DELETE_PROJECT
```

### Capabilities Document Schema

The output artifact for AUDIT-04 should be structured as:

```markdown
# SSL Matrix Protocol Capabilities — Firmware V3.0/5

## Handler Test Results

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| GET_DESK_REPLY | 6 | auto (connect) | PASS | replied with serial + firmware | - |
| SEND_HEARTBEAT | 7 | auto (every ~30s) | PASS | console sends unprompted | - |
| ...

## Feature Feasibility

### Soft Keys (ADV-01)
...

### V-Pot / Wheel Mode (ADV-02)
...

### SuperCue (ADV-03)
...

### Split Board (SPLIT-01)
...

## Protocol Gaps (Out of Scope or Broken)

| Area | Message codes | Status | Why |
|...
```

### Key Protocol Facts (verified from source)

**Wire format:** All messages share a 16-byte header: `int cmdCode, int destCode (1=desk/2=remote), int deskSerial, int mySerial`. Payload follows. Big-endian throughout.

**Transport:** UDP port 50081, both send and receive on the same bound socket. Console ignores packets from ephemeral ports. This is the Phase 1 critical discovery.

**DAW layers:** The console has 4 DAW layers (1-4). Each has:
- An assigned protocol: 0=none, 1=HUI, 2=MCU, 3=CC
- An assigned profile (named configuration)
- Phase 1 confirmed layers 1 and 2 are active (HUI for Pro Tools, MCU for Ableton)

**Profiles:** Named configurations stored on the console. Each profile carries protocol type (HUI/MCU/CC), is_read_only, in_use. Multiple profiles can exist; one is assigned per layer.

**Softkeys structure:** The softkey panel has a transport row (15 keys) and a softkey row (8 keys). Keys are typed: blank (0), MIDI (1), USB (2), menu (3). Key assignment requires opening an edit session (SEND_SET_EDIT_KEYMAP_NAME), editing, then saving (SEND_SET_SAVE_EDIT_KEYMAP).

---

## Key Feasibility Questions

### Question 1: Split Board (AUDIT-03) — UNKNOWN, requires live test

**What needs to happen:** DAW Layer 1 (HUI, Pro Tools) controls faders 1-8. DAW Layer 2 (MCU, Ableton) controls faders 9-16. Both active simultaneously.

**How to test it:** The `layers` command reads `ACK_GET_DAW_LAYER_PROTOCOL` for all 4 layers. The protocol handlers show both can be set. The unknown is whether the Matrix firmware's fader group assignment is separate from the DAW layer protocol assignment, and whether the console can route MIDI from two layers to physically separated fader groups at the same time.

**The key message codes to probe:**
- `SEND_GET_DAW_LAYER_PROTOCOL` (cmd 910) — reads which protocol each layer uses
- `SEND_SET_PROFILE_FOR_DAW_LAYER` (cmd 820) — assigns a profile (and thus protocol) to a layer
- `SEND_GET_PROFILES` (cmd 840) — lists all available profiles with their protocols

**The gap:** There are no message codes in the 197-code enum related to fader group assignment or split-mode enable. If split board is possible, it is configured through a combination of profile assignment (which profile uses which faders) or through a profile setting we haven't identified yet. The XPatch chains may play a role.

**Test approach:**
1. Use `layers` to document current state of all 4 layers
2. Check `profiles` — are there profiles that reference fader group or channel range?
3. Attempt to assign HUI profile to Layer 1 and MCU profile to Layer 3 simultaneously
4. Observe console behavior — do both DAWs respond to their fader groups?
5. If no progress: probe `raw` commands to test undocumented codes

**Likely outcomes:**
- PASS: Firmware supports dual-layer active mode; both DAWs respond on separate fader groups
- PARTIAL: Layers can be assigned but console uses them in round-robin / one-at-a-time
- FAIL: Console only supports one active DAW layer at a time (hardware limitation)

### Question 2: V-Pot Control (AUDIT-02 / ADV-02)

**What it is:** The V-pots on the SSL Matrix are rotary encoders. In HUI/MCU protocol, the DAW drives V-pot LED rings. But the question for Phase 2 is: can ssl-matrix-client query or set the "default wheel mode" — and does this affect what the V-pots send to the DAW?

**Relevant handlers:**
- `SEND_GET_DEFAULT_WHEEL_MODE_STATUS` (cmd 1060) — reads current wheel mode per layer
- `SEND_SET_DEFAULT_WHEEL_MODE_STATUS` (cmd 1070) — sets wheel mode

**The CC names list** (cmd 950/960) suggests V-pots can be mapped to CC messages (protocol type 3 = CC). This is the mechanism for "V-pot controlling plugin parameters" that requires the CC protocol.

**Test approach:**
1. Read current wheel mode for each layer: `raw 1060 01` through `raw 1060 04`
2. Read CC names list: `raw 950 01 00` (layer 1, type 0)
3. Determine what "CC protocol" means — is it a full protocol type, or a mode within HUI/MCU?
4. Test a CC profile assignment on a layer and verify V-pot sends CCs

### Question 3: Soft Keys (AUDIT-02 / ADV-01)

**What they are:** Programmable buttons on the console (transport row: 15 keys; softkey row: 8 keys). Each key can be assigned a MIDI command (from the console's MIDI function list), a USB command, or act as a menu launcher.

**What "working" means:** A soft key assignment is sent via `SEND_SET_USB_CMD` or `SEND_SET_MIDI_CMD` and saved via `SEND_SET_SAVE_EDIT_KEYMAP`. The key then fires that command when pressed on the console.

**What is NOT in ssl-matrix-client yet:** There is no CLI command to start the softkey edit session end-to-end. The handlers exist but there is no `do_softkeys` or `do_key_assign` command. The audit needs to test:
1. Whether `SEND_SET_EDIT_KEYMAP_NAME` opens an edit session correctly
2. Whether key assignment messages work
3. Whether SAVE commits to the console

**Test approach:** Use `raw` commands to exercise the softkey edit flow:
```
raw 610 01 <keymap_name_string>   # open edit session on layer 1
raw 641                           # check keymap size (transport=15, softkey=8)
raw 620 01 00 00                  # read key 1, top row, no subs
raw 650 01 01 00 <usb_cmd>        # assign USB command to key 1
raw 680                           # save keymap
```

### Question 4: SuperCue / Auto-Mon (AUDIT-02 / ADV-03)

**What it is:** SuperCue is SSL's system for automatically routing cue mixes. Auto-Mon is an automation mode that routes monitor sources based on record/playback state. Both are console-hardware features that the DAW can trigger via HUI transport commands.

**Research finding:** There are NO specific SuperCue/Auto-Mon message codes in the 197-code enum. This is significant — it means SuperCue/Auto-Mon is likely not a protocol-level feature controlled via the remote interface. It may be:
- Purely a hardware feature controlled by physical buttons on the console
- Controlled through HUI/MCU messages from the DAW (transport state changes)
- Absent from this firmware version (V3.0/5)

**Confidence: LOW.** This needs to be verified by checking the console surface for a SuperCue button and reading the Matrix user manual section on Auto-Mon. If it is not a UDP-protocol feature, then ADV-03 (SuperCue integration) would require a different implementation strategy than expected.

---

## Common Pitfalls

### Pitfall 1: Not enough wait time after state-changing messages
**What goes wrong:** Send a mutation command, immediately query state, get stale value.
**Why it happens:** The console takes 50-200ms to apply state and send ACK. The sync sequence already uses `time.sleep(0.05)` between messages.
**How to avoid:** After any SET command in the interactive REPL, wait 0.5s before querying. The `request_sync()` method does this correctly.

### Pitfall 2: XPatch chains hardcoded to 8 elements
**What goes wrong:** `GET_XPATCH_EDIT_CHAIN_REPLY` parser assumes exactly 8 link slots. If the console returns fewer or more, the parser will corrupt state or throw.
**Why it happens:** The constant `NUM_CHANS = 16` is correct for XPatch channels, but the chain parse loop was written to match the decompiled Java's typical-case assumption.
**How to avoid:** During XPatch chain testing, compare raw wire bytes (use sniffer) against parsed state. If chain count is wrong, fix the parser before proceeding.
**Warning sign:** `chains` command shows garbled data or zero chains when the console surface shows chains exist.

### Pitfall 3: Softkey edit session left open
**What goes wrong:** If `SEND_SET_EDIT_KEYMAP_NAME` opens a keymap edit session but `SEND_SET_SAVE_EDIT_KEYMAP` or `CANCEL_EDIT_CHAIN` equivalent is never sent, the console may be left in an edit state that prevents other operations.
**How to avoid:** Always end softkey edit sessions. Have `raw 680` (save) as the cleanup command ready. Test on layer 4 (least-used) first.

### Pitfall 4: Restart console during audit loses connection
**What goes wrong:** `SEND_RESTART_CONSOLE` (cmd 760) causes the console to reboot. The UDP socket on port 50081 closes from the console side. The client's receive loop will timeout and keep retrying GET_DESK.
**How to avoid:** After sending restart, disconnect the Python client (`do_disconnect`) and wait ~30s for console to come back, then reconnect. Do not test restart in the middle of an audit session — do it as the last item in delta testing.

### Pitfall 5: Automation mode change requires restart to take effect
**What goes wrong:** Set automation mode to Delta, expect delta-ctrl behavior to change immediately. It doesn't.
**Why it happens:** The Matrix firmware applies automation mode changes only on boot. The ACK says "ok" but nothing changes until restart.
**How to avoid:** Document this as a confirmed limitation. The `automode` command note already says "Restart console to apply."

### Pitfall 6: Project operations on active project
**What goes wrong:** Deleting or selecting a different title while a DAW is recording can lose the current mix session state.
**How to avoid:** Test project CRUD operations only when DAWs are stopped and idle. Test on a new disposable project (AUDIT-TEMP) — never on the production project.

### Pitfall 7: Console IP / port reuse conflict
**What goes wrong:** If another ssl-matrix-client instance is running (previous REPL session left open), both will be bound to port 50081 (`SO_REUSEPORT`). Both will receive all replies but only one will handle them. State can diverge.
**How to avoid:** Before starting each audit session, confirm no other client instances are running (`lsof -i :50081`).

---

## Protocol Gaps (Not in ssl-matrix-client)

These message codes exist in the 197-code enum but are NOT in the dispatch table. They are out of scope for Phase 2 (AUDIT-01 requires testing the 105 dispatch entries, not implementing new ones):

| Gap Area | Message codes | Why out of scope |
|----------|--------------|-----------------|
| File transfer | 80-183 (request/write file blocks, zip/unzip, move/copy/delete) | Niche — used for firmware update, not console operation |
| Mix passes | 62-63, 1100-1103 | Used for mix archiving — not DAW workflow |
| Lower scribble mode | 10710-10721 | Minor display option not needed for core features |
| Image library | 40-41 | Matrix returns `hasImages=false` — not used |
| RTC (clock) | 170-171 | Setting console clock — not workflow-relevant |
| Network settings | 5100-5135 | DHCP, static IP, Dante, CPU version — admin only |
| SEND_CLEAR_ALL | 5000 | Factory reset equivalent — dangerous |
| V1 insert matrix | 400-581 | Superseded by V2 (10400-10681) |

These should be documented in the capabilities document as "not audited — out of scope for Phase 2."

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Protocol sniffing for unknown replies | Custom pcap parser | `reverse-engineering/sniff_50081.py` | Already exists; captures raw UDP on port 50081 |
| Probing undocumented message codes | Manual packet construction | `raw <cmdcode> [hex]` in the REPL | `send_custom()` is already in the client |
| Tallying pass/fail results | Spreadsheet or complex tool | A markdown table filled in as you test | Simple, portable, version-controllable |
| Recreating test state | Elaborate fixtures | `request_sync()` + `state` JSON dump before each session | Already implemented |

---

## Code Examples

### Starting the REPL for audit testing
```bash
# Verify no other clients running
lsof -i :50081

# Start interactive REPL
python3 -m ssl_matrix_client --ip 192.168.1.2 -v

# In REPL:
ssl> connect
ssl> state    # dump full state as baseline JSON (redirect to file)
ssl> channels
ssl> layers
ssl> profiles
```

### Capturing pre-test baseline
```bash
python3 -m ssl_matrix_client --ip 192.168.1.2 channels > /tmp/baseline-channels.txt
python3 -m ssl_matrix_client --ip 192.168.1.2 layers   > /tmp/baseline-layers.txt
```

### Testing a softkey edit session (raw commands)
```python
# In REPL after connect:
# 1. Open edit session on layer 1 with keymap "ProTools" (as null-terminated ASCII hex)
ssl> raw 610 01 50726f546f6f6c7300   # layer=1, "ProTools\0"
# 2. Read keymap size
ssl> raw 641
# 3. Read key 1, top row
ssl> raw 620 01 00 00
# 4. Check state.softkeys in dump
ssl> state
```

### Reading split board feasibility
```python
# In REPL:
ssl> layers        # shows all 4 DAW layers with protocol + profile
ssl> profiles      # shows all profiles — look for fader range fields
# Attempt to observe two layers active simultaneously:
ssl> raw 910 01    # get protocol for layer 1
ssl> raw 910 02    # get protocol for layer 2
ssl> raw 910 03    # get protocol for layer 3
ssl> raw 910 04    # get protocol for layer 4
```

---

## Validation Architecture

> `workflow.nyquist_validation` is not set to `false` in `.planning/config.json`, so this section is included. However, Phase 2 is primarily an empirical audit — the "test suite" IS the live console test protocol. Automated testing of hardware responses is not applicable. The following maps requirements to verifiable outcomes.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Manual protocol exercise via ssl-matrix-client REPL + sniff_50081.py |
| Config file | None — this is interactive hardware testing |
| Quick run command | `python3 -m ssl_matrix_client --ip 192.168.1.2 channels` |
| Full suite command | Full audit session: connect + all 10 handler groups tested |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUDIT-01 | All 105 dispatch handlers return valid responses | manual hardware | `python3 -m ssl_matrix_client --ip 192.168.1.2 state` (baseline) | ✅ existing |
| AUDIT-01 | Query handlers populate state | manual hardware | `python3 -m ssl_matrix_client --ip 192.168.1.2 channels` | ✅ existing |
| AUDIT-02 | Softkey edit session opens and closes | manual hardware | raw REPL commands (see examples above) | ✅ existing |
| AUDIT-02 | Wheel mode reads correctly per layer | manual hardware | `python3 -m ssl_matrix_client --ip 192.168.1.2 layers` | ✅ existing |
| AUDIT-03 | DAW layer protocol queries return for all 4 layers | manual hardware | `python3 -m ssl_matrix_client --ip 192.168.1.2 layers` | ✅ existing |
| AUDIT-04 | Capabilities document exists and covers all 105 handlers | documentation | file existence check | ❌ Wave 0 — create `CAPABILITIES.md` |

### Wave 0 Gaps

- [ ] `CAPABILITIES.md` in phase dir — the output document for AUDIT-04; create template before testing begins

*(No test infrastructure gaps — testing is interactive/hardware, no pytest suite needed)*

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MatrixRemote Java app | ssl-matrix-client Python | Phase 1 | MatrixRemote broken on Tahoe; ssl-matrix-client is the only option |
| Ephemeral port UDP sends | Bound port 50081 socket | Phase 1 reverse engineering | Console ignores ephemeral-port packets |
| V1 insert matrix (cmd 400-581) | V2 insert matrix (cmd 10400-10681) | Firmware V3.0/5 | V2 is what the live console uses; V1 codes not tested |
| MatrixRemote single-layer view | 4-layer DAW protocol model | Code analysis | Multiple simultaneous DAW connections are at least configured, if not active |

**Not yet known:**
- Whether V3.0/5 firmware supports split board (two active DAW layers simultaneously)
- Whether SuperCue/Auto-Mon is reachable via UDP protocol at all
- Whether XPatch chains always have 8 elements or variable count

---

## Open Questions

1. **Split board support**
   - What we know: 4 DAW layers exist with independent protocol assignments; two are currently active (HUI+MCU)
   - What's unclear: Whether firmware allows BOTH to be "controlling" simultaneously on different physical fader groups, or whether "active" means one-at-a-time
   - Recommendation: Test by querying all 4 layers, then attempting to assign two profiles simultaneously and observing both DAWs

2. **SuperCue/Auto-Mon protocol presence**
   - What we know: No dedicated message codes for SuperCue/Auto-Mon in the 197-code enum
   - What's unclear: Whether it's a hardware-only feature, a console menu item, or triggered via HUI/MCU transport commands from the DAW
   - Recommendation: Check the Matrix physical surface for a SuperCue button; read the V3.0/5 manual section on Auto-Mon; if no protocol codes exist, document as "hardware-controlled only"

3. **XPatch chain element count**
   - What we know: Parser assumes 8 elements; this was flagged in Phase 1 as possibly wrong
   - What's unclear: How many link slots the live console's XPatch chains have
   - Recommendation: During XPatch audit, run the sniffer (`sniff_50081.py`) in parallel and compare raw bytes to parsed output

4. **Softkey keymap name for each layer**
   - What we know: `SEND_SET_EDIT_KEYMAP_NAME` takes a DAW layer byte and a keymap name string
   - What's unclear: What the valid keymap names are for each layer, and whether there's a "get keymap name" flow needed first
   - Recommendation: `raw 600 <layer>` (SEND_GET_EDIT_KEYMAP_NAME) first to read the current name, then use that name when opening the edit session

5. **CC protocol (type 3) and V-pot CC mapping**
   - What we know: The protocol enum includes CC (type 3) alongside HUI and MCU; CC names list handler exists
   - What's unclear: Whether CC protocol gives ssl-matrix-client control over what V-pot movements send; or if it's purely a Mackie CC passthrough
   - Recommendation: Query `raw 910 <layer>` for all layers to see if any are currently in CC mode; check the console profiles list for any CC-type profiles

---

## Sources

### Primary (HIGH confidence)
- `ssl-matrix-client/client.py` — 105-entry dispatch table; exact message codes
- `ssl-matrix-client/protocol.py` — 197 MessageCode enum; TxMessage/RxMessage wire format
- `ssl-matrix-client/handlers/*.py` — all payload formats (from decompiled Java)
- `.planning/phases/02-capabilities-audit/02-CONTEXT.md` — locked decisions and constraints
- `.planning/phases/01-compatibility-verification/.continue-here.md` — Phase 1 implementation summary and known gaps
- `.planning/REQUIREMENTS.md` — AUDIT-01 through AUDIT-04 definitions

### Secondary (MEDIUM confidence)
- Phase 1 research notes — confirmed: UDP port 50081, bound socket required, firmware V3.0/5, 4 DAW layers

### Tertiary (LOW confidence, requires live console verification)
- Split board feasibility — no evidence either way in the source code
- SuperCue/Auto-Mon protocol presence — assumed absent based on message code enumeration, but not confirmed
- XPatch chain element count — assumed 8 based on Java typical case, flagged as potentially wrong

---

## Metadata

**Confidence breakdown:**
- Handler inventory (AUDIT-01 surface): HIGH — derived directly from dispatch table in client.py
- Test sequence / risk ordering: HIGH — based on command semantics in source
- Split board feasibility: LOW — unknown; no protocol evidence either way
- SuperCue protocol: LOW — not in message codes, but mechanism could be indirect
- XPatch chain count: LOW — flagged as a known risk in Phase 1

**Research date:** 2026-03-11
**Valid until:** Permanent — this is an internal codebase audit, not a fast-moving external library. Changes only when ssl-matrix-client code changes.
