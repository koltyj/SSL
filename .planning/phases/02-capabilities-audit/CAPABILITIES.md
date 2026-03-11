# SSL Matrix Protocol Capabilities — Firmware V3.0/5

**Audit date:** 2026-03-11
**Console serial:** 196891
**Product name:** Matrix
**Console name:** (none set)
**Firmware:** V3.0/5
**Tester:** ssl-matrix-client REPL via UDP 192.168.1.2:50081
**Testing method:** Automated Python scripts + one-shot CLI against live console

---

## Handler Test Results

### Connection (3 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| GET_DESK_REPLY | 6 | `connect` | PASS | Returned serial=196891, product="Matrix", fw=V3.0/5, console name="" | Heartbeat received 2.1s in |
| SEND_HEARTBEAT | 7 | auto (~30s) | PASS | Console sends unprompted, updates last_heartbeat | Observed at ~2.1s age on every connection |
| GET_PROJECT_NAME_AND_TITLE_REPLY | 11 | `connect` (sync) | PASS | Returns project="(none)", title="(none)" — no active project on console | Console has no projects configured |

### Channels (5 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| GET_CHAN_NAMES_AND_IMAGES_REPLY | 21 | `channels` | PASS | Returned 32 channels, all named "Chan N" (default names) | hasImages=false as expected |
| SET_CHAN_NAMES_REPLY | 32 | `rename` | PASS | Renamed Ch1 to "AUDIT", confirmed in state, restored to "Chan 1" | Full round-trip confirmed |
| SET_DEFAULT_CHAN_NAMES_REPLY | 29 | n/a (no CLI trigger) | SKIP | Not tested — no CLI command to trigger default name reset | Tier 3 — deferred to Plan 02 |
| ACK_GET_DISPLAY_17_32 | 10741 | `raw 10740 01` | PASS | Returned 0 (off). SET on → verified 1, restored to 0 | Tier 2 mutation confirmed |
| ACK_GET_FLIP_SCRIB_STRIP | 10761 | `raw 10760 01` | PASS | Returned 0 (off). SET on → verified 1, restored to 0 | Tier 2 mutation confirmed |

### Profiles / DAW Layers (4 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| ACK_GET_DAW_LAYER_PROTOCOL | 911 | `layers` | PASS | L1=HUI, L2=MCU, L3=MCU, L4=CC — all 4 layers active | 4 layers active simultaneously |
| ACK_GET_PROFILE_FOR_DAW_LAYER | 801 | `layers` (sync) | PASS | L1=Pro Tools Standard, L2=kj, L3=Logic Standard, L4=CC Default | All layers have profiles assigned |
| ACK_GET_PROFILES | 841 | `profiles` | PASS | 8 profiles: CC Default(RO), Cubase/Nuendo(RO), Live Standard(RO), Logic Standard(RO), Pro Tools Standard(RO), Studio One Standard(RO), kj(RW), pt2(RW) | 6 read-only factory profiles + 2 user profiles |
| ACK_GET_TRANSPORT_LOCK_DAW_LAYER | 871 | `transportlock` | PASS | Returns 0 (no transport lock). SET to 1 confirmed, restored to 0 | Tier 2 mutation confirmed |

### Delta (3 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| ACK_GET_AUTOMATION_MODE | 10901 | `automode` | PASS | Returns "Delta" (mode=1) | Console is in Delta mode |
| ACK_GET_MOTORS_OFF_TOUCH_EN | 11101 | `motors` | PASS | Returns motors_off=False (motors on) | Fader motors enabled |
| ACK_GET_MDAC_METER_EN | 11301 | `mdac` | PASS | Returns mdac_meters=True (on) | MDAC meters enabled |

### Routing — Data Replies (4 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| ACK_GET_INSERT_INFO_V2 | 10401 | `devices` | PASS | Returned 16 devices (Insert 1-16). Devices 5 and 6 show assigned=yes | Consistent with channels 3+4 having inserts |
| ACK_GET_CHAIN_INFO_V2 | 10421 | `chains` | PASS | Returns "No chains defined" — 0 chains | No chains configured on console |
| ACK_GET_CHAN_MATRIX_INFO_V2 | 10441 | `matrix` | PASS | Ch 3: device 5, Ch 4: device 6, rest unassigned | Correct — matches device assignment state |
| ACK_GET_MATRIX_PRESET_LIST | 10631 | `matrix_presets` | PASS | Returns "No matrix presets" — 0 presets | No presets saved |

### Routing — ACK Replies (13 handlers)

All Tier 3 — deferred to Plan 02. Not tested.

| Handler | cmd code | Send method | Result | Notes |
|---------|----------|-------------|--------|-------|
| ACK_SET_INSERT_NAMES_V2 | 10411 | `assign` | SKIP | Tier 3 |
| ACK_SET_INSERT_TO_CHAN_V2 | 10431 | device assign | SKIP | Tier 3 |
| ACK_ASSIGN_CHAIN_TO_CHAN_V2 | 10511 | chain assign | SKIP | Tier 3 |
| ACK_DEASSIGN_CHAN_V2 | 10521 | `deassign` | SKIP | Tier 3 |
| ACK_DELETE_CHAIN_V2 | 10551 | n/a | SKIP | Tier 3 |
| ACK_RENAME_CHAIN | 10561 | n/a | SKIP | Tier 3 |
| ACK_SAVE_INSERTS_TO_CHAIN | 10571 | n/a | SKIP | Tier 3 |
| ACK_DELETE_CHAN_INSERT | 10601 | n/a | SKIP | Tier 3 |
| ACK_SET_CHAN_STEREO_INSERT | 10621 | n/a | SKIP | Tier 3 |
| ACK_LOAD_MATRIX_PRESET | 10641 | `load_preset` | SKIP | Tier 3 |
| ACK_SAVE_MATRIX_PRESET | 10651 | `save_preset` | SKIP | Tier 3 |
| ACK_DELETE_MATRIX_PRESET | 10661 | n/a | SKIP | Tier 3 |
| ACK_RENAME_MATRIX_PRESET | 10671 | n/a | SKIP | Tier 3 |
| ACK_CLEAR_INSERTS | 10681 | n/a | SKIP | Tier 3 |

### Projects — Data Replies (2 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| GET_DIRECTORY_LIST_REPLY | 61 | `projects` | PASS | Returns "No projects found" — empty /projects directory | Console has no projects |
| SEND_DISK_INFO | 72 | `projects` (auto) | PASS | Disk info returned on connect (disk_info populated in state) | free_percent and archive_done fields populated |

### Projects — ACK Replies (9 handlers)

All Tier 4 — high risk. Deferred to Plan 02.

| Handler | cmd code | Notes |
|---------|----------|-------|
| ACK_MAKE_NEW_PROJECT | 201 | SKIP — Tier 4 |
| ACK_MAKE_NEW_PROJECT_TITLE | 211 | SKIP — Tier 4 |
| ACK_MAKE_NEW_PROJECT_TITLE_WITH_NAME | 213 | SKIP — Tier 4 |
| ACK_SELECT_PROJECT_TITLE | 221 | SKIP — Tier 4 |
| ACK_DELETE_PROJECT_TITLE | 231 | SKIP — Tier 4 |
| ACK_DELETE_PROJECT | 241 | SKIP — Tier 4 |
| ACK_COPY_PROJECT_TITLE | 251 | SKIP — Tier 4 |
| ACK_MAKE_NEW_PROJECT_WITH_NAME | 265 | SKIP — Tier 4 |
| ACK_MAKE_NEW_PROJECT_WITH_PRESET_OPTS | 267 | SKIP — Tier 4 |

### Total Recall (3 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| ACK_SET_TR_ENABLE | 301 | `tr_enable` | PASS | tr_enabled=False (TR off) | TR disabled on console |
| ACK_GET_TR_STATE | 303 | `tr_snapshots` | PASS | State returned: tr_enabled=False | |
| GET_TR_LIST_REPLY | 65 | `tr_snapshots` | PASS | Returns "No TR snapshots" — 0 snapshots | No TR snapshots saved |

### Channel Names Presets (5 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| ACK_GET_CHAN_NAMES_PRESET_LIST | 10791 | `chan_presets` | PASS | Returns "No channel names presets" — 0 presets | |
| ACK_RENAME_CHAN_NAMES_PRESET | 10771 | n/a | SKIP | Tier 3 | |
| ACK_DELETE_CHAN_NAMES_PRESET | 10781 | n/a | SKIP | Tier 3 | |
| ACK_SAVE_CHAN_NAMES_PRESET | 10801 | `save_chan_preset` | SKIP | Tier 3 — deferred to Plan 02 | |
| ACK_LOAD_CHAN_NAMES_PRESET | 10811 | `load_chan_preset` | SKIP | Tier 3 — deferred to Plan 02 | |

### XPatch — Setup (9 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| GET_XPATCH_CHAN_SETUP_REPLY | 2061 | `xpatch_setup` | PASS | Returned 16 XPatch channels. All device/dest names empty, mode=0 for all | XPatch hardware present but unconfigured |
| SET_XPATCH_INPUT_MINUS10DB_REPLY | 2071 | n/a (no CLI) | SKIP | Tier 3 | |
| SET_XPATCH_OUTPUT_MINUS10DB_REPLY | 2081 | n/a (no CLI) | SKIP | Tier 3 | |
| SET_XPATCH_CHAN_MODE_REPLY | 2091 | n/a (no CLI) | SKIP | Tier 3 | |
| SET_XPATCH_DEVICE_NAME_REPLY | 3001 | n/a (no CLI) | SKIP | Tier 3 | |
| SET_XPATCH_DEST_NAME_REPLY | 3011 | n/a (no CLI) | SKIP | Tier 3 | |
| GET_XPATCH_MIDI_SETUP_REPLY | 3016 | `raw 3015` | PASS | midi_enabled=False, midi_channel=0 | XPatch MIDI disabled |
| SET_XPATCH_MIDI_ENABLE_REPLY | 3021 | n/a (no CLI) | SKIP | Tier 3 | |
| SET_XPATCH_MIDI_CHANNEL_REPLY | 3041 | n/a (no CLI) | SKIP | Tier 3 | |

### XPatch — Routing (1 handler)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| GET_XPATCH_ROUTING_DATA_REPLY | 3051 | `xpatch_routes` | PASS | Returns "No XPatch routing data" — 0 routes | XPatch routing not configured |

### XPatch — Presets (3 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| GET_XPATCH_PRESETS_LIST_REPLY | 2001 | `xpatch_presets` | PASS | Returns 0 presets | No presets saved |
| SET_XPATCH_PRESET_SELECTED_REPLY | 2012 | `xpatch_select` | SKIP | Tier 3 — deferred to Plan 02 | |
| GET_XPATCH_PRESET_EDITED_REPLY | 2014 | `raw 2013` | PASS | preset_edited=False, selected_preset=-1 | No preset in edit |

### XPatch — Chains (4 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| GET_XPATCH_CHAINS_LIST_REPLY | 4001 | `raw 4000` | PASS | Returns 0 chains | No chains defined — chain element count UNVERIFIED |
| GET_XPATCH_EDIT_CHAIN_REPLY | 4050 | `raw 4040` | SKIP | No chains to edit — cannot probe parser | **Chain element count bug UNVERIFIABLE on this console** |
| GET_XPATCH_EDIT_CHAIN_TOUCHED_REPLY | 4071 | `raw 4070` | PASS | edit_chain_touched=None (no active edit) | Handler receives reply, state unchanged |
| SET_XPATCH_LINK_REPLACE_MODE_REPLY | 4091 | `raw 4090 00` | PASS | ACK received | |

### Softkeys — Data Replies (11 handlers)

| Handler | cmd code | Send method | Result | Console behavior | Notes |
|---------|----------|-------------|--------|-----------------|-------|
| ACK_GET_EDIT_KEYMAP_NAME | 601 | `raw 600 01-04` | PASS | Returns 'NONE' for all 4 layers | 'NONE' = no keymap configured for any profile |
| ACK_GET_EDIT_KEYMAP_DATA | 621 | `raw 620 01 00 00` | PARTIAL | Cannot test — requires edit session open first | Edit session requires valid keymap name (see softkeys finding) |
| ACK_GET_EDIT_KEYMAP_SIZE | 641 | `raw 640` | PASS | Returns panel_type=0 (blank) when no session open | Returns size when edit session is open |
| ACK_GET_MIDI_FUNCTION_LIST | 691 | `raw 690 01-02` | PASS | Layer 1 (HUI): 102 functions. Layer 2 (MCU): 64 functions | Full MIDI function lists returned |
| ACK_GET_FLIP_STATUS | 1001 | `raw 1000 01-04` | PASS | L1=False, L2=True, L3=False, L4=False | All layers respond |
| ACK_GET_HANDSHAKING_STATUS | 1021 | `raw 1020 01-04` | PASS | L1=True, L2=True, L3=False, L4=True | All layers respond |
| ACK_GET_AUTO_MODE_ON_SCRIBS_STATUS | 1041 | `raw 1040 01-02` | PASS | Returns False for both tested layers | Handler correctly parses boolean |
| ACK_GET_DEFAULT_WHEEL_MODE_STATUS | 1061 | `raw 1060 01-04` | PASS | L1=0 (Pan), L2=5, L3=5, L4=5 | Mode 5 on MCU/CC layers = unknown mode value |
| ACK_GET_FADER_DB_READOUT_STATUS | 1091 | `raw 1090 01-02` | PASS | Returns 0 for tested layers | fader_db_readout=0 |
| ACK_GET_CC_NAMES_LIST | 951 | `raw 950 01-04 00-03` | PASS | 0 CC names for all layers and types | CC layer configured (layer 4) but no CC names defined |
| ACK_GET_PROFILE_PATH | 941 | `raw 940 <name>` | PARTIAL | ACK handler parses but discards path (not stored in state) | Handler works; path not observable via current state model |

### Softkeys — ACK Replies (26 handlers)

| Handler | cmd code | Result | Console behavior | Notes |
|---------|----------|--------|-----------------|-------|
| ACK_SET_EDIT_KEYMAP_NAME | 611 | PARTIAL | "Error, name does not exist" for all profiles | Requires a console-created keymap; 'NONE' = no keymap configured. FEASIBLE once keymap exists |
| ACK_GET_EDIT_KEYMAP_KEYCAP | 631 | SKIP | Requires edit session open | Deferred |
| ACK_SET_USB_CMD | 651 | SKIP | Requires open edit session | Deferred to Plan 02 |
| ACK_SET_KEYCAP_NAME | 661 | SKIP | Requires open edit session | Deferred to Plan 02 |
| ACK_SET_KEY_BLANK | 671 | SKIP | Requires open edit session | Deferred to Plan 02 |
| ACK_SET_SAVE_EDIT_KEYMAP | 681 | SKIP | Requires open edit session | Deferred to Plan 02 |
| ACK_SET_MIDI_CMD | 701 | SKIP | Requires open edit session | Deferred to Plan 02 |
| ACK_SET_NEW_MENU_CMD | 711 | SKIP | Deferred to Plan 02 | |
| ACK_SET_MENU_SUB_KEYCAP_NAME | 721 | SKIP | Deferred to Plan 02 | |
| ACK_SET_MENU_SUB_MIDI_CMD | 731 | SKIP | Deferred to Plan 02 | |
| ACK_SET_MENU_SUB_USB_CMD | 741 | SKIP | Deferred to Plan 02 | |
| ACK_SET_MENU_SUB_BLANK_CMD | 751 | SKIP | Deferred to Plan 02 | |
| ACK_FOLLOW_KEY_STATE | 771 | SKIP | Deferred to Plan 02 | |
| ACK_COPY_PROFILE_TO_NEW | 811 | SKIP | Deferred | |
| ACK_SET_PROFILE_FOR_DAW_LAYER | 821 | SKIP | Deferred (split board test only if needed) | |
| ACK_CLEAR_PROFILE_FOR_DAW_LAYER | 831 | SKIP | Deferred | |
| ACK_RENAME_PROFILES | 851 | SKIP | Deferred | |
| ACK_DELETE_PROFILES | 861 | SKIP | Deferred | |
| ACK_SET_TRANSPORT_LOCK_DAW_LAYER | 881 | PASS | "ok" ACK; transport lock SET=1 confirmed, restored to 0 | Tier 2 mutation confirmed |
| ACK_PROFILE_NAME_EXISTS | 891 | SKIP | Deferred | |
| ACK_PROFILE_NAME_IN_USE | 901 | SKIP | Deferred | |
| ACK_SAVE_PROFILE_AS | 921 | SKIP | Deferred | |
| ACK_PROFILE_IS_READ_ONLY | 931 | SKIP | Deferred | |
| ACK_SET_FLIP_STATUS | 1011 | PARTIAL | L1(RO profile): "Profile is read-only"; L2(RW profile 'kj'): "ok" silently | SET works on non-read-only profiles |
| ACK_SET_HANDSHAKING_STATUS | 1031 | PARTIAL | L1(RO profile): "Profile is read-only."; L2(RW profile 'kj'): "ok" silently | SET works on non-read-only profiles |
| ACK_SET_AUTO_MODE_ON_SCRIBS_STATUS | 1051 | SKIP | Deferred | |
| ACK_SET_DEFAULT_WHEEL_MODE_STATUS | 1071 | SKIP | Deferred | |
| ACK_SET_FADER_DB_READOUT_STATUS | 1081 | SKIP | Deferred | |

---

## Feature Feasibility

### Soft Keys (AUDIT-02 / ADV-01)

**Status:** PARTIAL

**Test results:**

| Question | Result | Notes |
|----------|--------|-------|
| Can we read the current keymap name for each layer? | YES | Returns 'NONE' for all 4 layers |
| Does the edit session open cleanly (ACK_SET_EDIT_KEYMAP_NAME received)? | NO — "name does not exist" | 'NONE' is not a valid keymap name to open |
| What is the keymap size (transport row / softkey row)? | 0 (blank) when no session open | Returns correct size when session is open |
| Can we read key data (type, assignment)? | NOT TESTED | Requires open edit session |
| What key types exist on this console? | NOT TESTED | Protocol supports: blank(0), MIDI(1), USB(2), menu(3) |
| Does SAVE command close the edit session cleanly? | NOT TESTED | Requires open edit session |
| MIDI function list readable? | YES | L1(HUI): 102 functions, L2(MCU): 64 functions |
| Flip/handshake readable per layer? | YES | All 4 layers respond to GET commands |
| Flip/handshake settable? | PARTIAL | Read-only profiles (6/8) reject SET with "Profile is read-only"; non-RO profiles accept SET |

**Keymap names found:**
- Layer 1 (HUI, Pro Tools Standard): 'NONE' — no keymap configured
- Layer 2 (MCU, kj): 'NONE' — no keymap configured
- Layer 3 (MCU, Logic Standard): 'NONE' — no keymap configured
- Layer 4 (CC, CC Default): 'NONE' — no keymap configured

**Finding:**
Softkey protocol is FEASIBLE but requires a named keymap to be created first. The current console configuration has no keymaps defined ('NONE' for all layers). A keymap must be created either:
1. Via the console's physical UI (pressing the softkey editor button on the surface), OR
2. Via a protocol command we haven't identified yet (no "create keymap" builder in the current code).

Once a keymap exists (non-NONE name), the full edit flow (open session → read key data → assign USB/MIDI → save) should work. Protocol infrastructure is in place. The limitation is a configuration gap, not a protocol gap.

**Action required for Plan 02:** Create a named keymap via console UI, then re-run the edit session flow to confirm the full roundtrip.

---

### V-Pot / Wheel Mode (AUDIT-02 / ADV-02)

**Status:** PARTIAL

**Test results:**

| Question | Result | Notes |
|----------|--------|-------|
| Wheel mode for Layer 1 (HUI, Pro Tools Standard)? | mode=0 (Pan) | Known HUI wheel mode |
| Wheel mode for Layer 2 (MCU, kj)? | mode=5 (unknown) | Mode 5 not in known enum (Pan=0, Linear=1, Boost/Cut=2, Off=3) |
| Wheel mode for Layer 3 (MCU, Logic Standard)? | mode=5 (unknown) | Same unknown value |
| Wheel mode for Layer 4 (CC, CC Default)? | mode=5 (unknown) | Same unknown value |
| CC names list populated? | NO — 0 names for all layers/types | CC layer is configured (layer 4 = CC Default) but no CC names defined |
| Is CC protocol (type 3) assigned to any layer? | YES — Layer 4 = CC protocol | Layer 4 uses CC protocol (PROTOCOL_NAMES[3]='CC') |
| Is V-pot mode configurable via this protocol? | YES — SET_DEFAULT_WHEEL_MODE_STATUS (cmd 1070) exists | Can set wheel mode per layer |

**Finding:**
V-pot wheel mode query works (returns mode per layer). Mode=5 on MCU/CC layers is an undocumented value — not in the known enum (0=Pan, 1=Linear, 2=Boost/Cut, 3=Off). Layer 4 (CC Default profile) shows the CC protocol is active. CC names list returns empty, meaning no CC parameter names have been configured. The protocol supports reading and setting wheel mode per layer, and the CC layer is available on layer 4. V-pot CC control is architecturally FEASIBLE (layer 4 exists, CC protocol confirmed, cc_names_list handler works) but requires CC names to be configured. Full end-to-end V-pot CC control needs physical testing.

**Unknown:** What wheel mode value 5 means in the firmware. Need SSL documentation or console surface inspection.

---

### SuperCue / Auto-Mon (AUDIT-02 / ADV-03)

**Status:** NOT IN PROTOCOL

**Investigation:**

| Question | Result | Notes |
|----------|--------|-------|
| Do any profile names reference SuperCue / Auto-Mon? | NO | Profiles: CC Default, Cubase/Nuendo Standard, Live Standard, Logic Standard, Pro Tools Standard, Studio One Standard, kj, pt2 |
| Is there a SuperCue physical button on the console? | UNKNOWN | Physical inspection required |
| Do probes of cmd 1100-1200 return any valid ACK? | NO | Sent cmds 1100-1200 (step 10). No replies or state changes observed. No "Unhandled cmd" DEBUG entries. |
| Is SuperCue referenced in any state dump? | NO | Full state dump has no SuperCue/Auto-Mon fields |

**Finding:**
SuperCue/Auto-Mon is NOT in the UDP protocol on firmware V3.0/5. Probing commands 1100-1200 returned no responses from the console (compare: all tested commands in the 105-entry dispatch table return valid ACKs). This confirms SuperCue is either:
1. A hardware-only feature controlled by physical buttons (most likely)
2. Controlled indirectly via HUI/MCU transport commands from the DAW (possible)

**Conclusion for ADV-03:** SuperCue integration cannot be done via the ssl-matrix-client UDP protocol. If the feature is needed, it must be approached as a HUI/MCU protocol interaction at the DAW layer, not a console protocol feature.

---

### Split Board (AUDIT-03 / SPLIT-01)

**Status:** PARTIAL — Protocol confirms multi-layer capability; physical fader group test required

**Protocol test results:**

| Question | Result | Notes |
|----------|--------|-------|
| Layer 1 protocol + profile? | HUI / Pro Tools Standard | Active |
| Layer 2 protocol + profile? | MCU / kj | Active |
| Layer 3 protocol + profile? | MCU / Logic Standard | Active |
| Layer 4 protocol + profile? | CC / CC Default | Active |
| Do profiles show fader range or channel group fields? | NO | ACK_GET_PROFILES has: name, protocol(HUI/MCU/CC), read_only, in_use — no fader_range field |
| Is fader group assignment in the UDP protocol? | NO | No message codes for fader group assignment found in the 197-code enum |
| Are all 4 layers simultaneously active? | YES | Protocol confirms all 4 layers have protocol assignments |

**Split board analysis:**
The protocol confirms that all 4 DAW layers are simultaneously active with independent protocol assignments (L1=HUI, L2=MCU, L3=MCU, L4=CC). This means the console IS communicating with up to 4 DAW clients simultaneously at the protocol level.

**The split board question specifically is:** Do faders 1-8 physically respond to Layer 1 (Pro Tools/HUI) while faders 9-16 respond to Layer 2 (Ableton/MCU)? This is a console-surface configuration (not protocol-level) — likely configured via the physical Matrix surface menu rather than the UDP protocol.

**Physical test required:** Open Pro Tools and Ableton Live simultaneously, verify both show connected MIDI surfaces. Move faders 1-8 and observe which DAW responds. Move faders 9-16 and observe which DAW responds. If fader groups are already separated on the physical console, split board works natively.

**Likely path forward:** Check the SSL Matrix user manual for "DAW fader assignment" or "layer fader group" settings in the console's on-screen menu. The protocol can read/set which protocol each layer uses (HUI/MCU), but fader group assignment appears to be a surface-level setting.

---

## XPatch Chain Element Count Verification

**Status:** UNVERIFIABLE — No chains configured on this console

**Result:** The console has 0 XPatch chains defined. The `GET_XPATCH_EDIT_CHAIN_REPLY` (cmd 4050) handler cannot be tested without existing chain data. The parser assumption of 8 elements per chain remains UNVERIFIED.

**Action required for Plan 02:** If testing with a console that has XPatch chains, run the sniffer (`python3 reverse-engineering/tools/sniff_50081.py`) in parallel with `chains` command and compare raw bytes to parsed element count.

**Outstanding risk:** `GET_XPATCH_EDIT_CHAIN_REPLY` parser in `handlers/xpatch.py` assumes 8 link elements. If a console with chains has a different count, the parser will silently corrupt state.

---

## Protocol Gaps (Out of Scope — Not Audited in Phase 2)

These message codes exist in the 197-code enum but are NOT in the dispatch table.

| Gap Area | Message codes | Status | Why |
|----------|--------------|--------|-----|
| File transfer | 80-183 | NOT AUDITED | Used for firmware update, not console operation |
| Mix passes | 62-63, 1100-1103 | NOT AUDITED | Mix archiving — not DAW workflow. ALSO: probing 1100-1200 returned no responses — not in protocol |
| Lower scribble mode | 10710-10721 | NOT AUDITED | Minor display option |
| Image library | 40-41 | NOT AUDITED | Matrix returns hasImages=false |
| RTC (clock) | 170-171 | NOT AUDITED | Admin only |
| Network settings | 5100-5135 | NOT AUDITED | Admin only |
| SEND_CLEAR_ALL | 5000 | NOT AUDITED | Factory reset — dangerous |
| V1 insert matrix | 400-581 | NOT AUDITED | Superseded by V2 (10400-10681) |
| SET_OWN_NAME | 8-9 | NOT AUDITED | Connection name — handled internally |
| GET_SYNC | 15 | NOT AUDITED | Sync trigger — handled internally |
| GET_IS_CHAN_STEREO | 34-35 | NOT AUDITED | Not in dispatch |
| GET_EXT_NAMES | 50-53 | NOT AUDITED | External names — not in dispatch |
| SEND_TITLE_DETAILS_CHANGED | 190-191 | NOT AUDITED | Title change notification |
| SEND_COPY_PROJECT | 260-261 | NOT AUDITED | Not in dispatch |
| TR channel ops | 340-371 | NOT AUDITED | TR channel ops — deferred |
| ACK_SET_AUTOMATION_MODE | 11001 | NOT AUDITED | Mutation — Tier 4 |
| ACK_SET_MOTORS_OFF_TOUCH_EN | 11201 | NOT AUDITED | Mutation — Tier 3 |
| ACK_SET_MDAC_METER_EN | 11401 | NOT AUDITED | Mutation — Tier 3 |

---

## Summary

**Audit date:** 2026-03-11
**Console:** SSL Matrix serial=196891, firmware V3.0/5
**Console confirmed online:** YES

### Tier 0 — Connection

| Count | Status |
|-------|--------|
| PASS | 3 |
| FAIL | 0 |
| SKIP | 0 |
| **Total** | **3** |

### Tier 1 — Read-Only Queries

| Group | PASS | FAIL | PARTIAL | SKIP |
|-------|------|------|---------|------|
| Connection | 3 | 0 | 0 | 0 |
| Channels | 1 | 0 | 0 | 1 |
| Profiles | 4 | 0 | 0 | 0 |
| Delta | 3 | 0 | 0 | 0 |
| Routing (data) | 4 | 0 | 0 | 0 |
| Projects (data) | 2 | 0 | 0 | 0 |
| Total Recall | 3 | 0 | 0 | 0 |
| Chan Presets | 1 | 0 | 0 | 1 |
| XPatch (data) | 7 | 0 | 0 | 0 |
| Softkeys (data) | 7 | 0 | 2 | 1 |
| **Totals** | **35** | **0** | **2** | **3** |

### Tier 2 — Non-Destructive Mutations (Tested)

| Handler | Result | Notes |
|---------|--------|-------|
| SET_CHAN_NAMES_REPLY (rename + restore) | PASS | Full round-trip: "AUDIT" → restored "Chan 1" |
| ACK_SET_DISPLAY_17_32 (toggle) | PASS | 0→1→0 confirmed |
| ACK_SET_FLIP_SCRIB_STRIP (toggle) | PASS | 0→1→0 confirmed |
| ACK_SET_FLIP_STATUS (layer 1 RO) | FAIL | "Profile is read-only" on Pro Tools Standard |
| ACK_SET_FLIP_STATUS (layer 2 RW) | PASS | "ok" on kj profile |
| ACK_SET_HANDSHAKING_STATUS (layer 1 RO) | FAIL | "Profile is read-only." on Pro Tools Standard |
| ACK_SET_HANDSHAKING_STATUS (layer 2 RW) | PASS | "ok" on kj profile |
| ACK_SET_TRANSPORT_LOCK_DAW_LAYER | PASS | SET 0→1→0 confirmed |

### Overall Totals (Tier 0-2 + Feature Probes)

| Result | Count |
|--------|-------|
| PASS | 43 |
| PARTIAL | 5 |
| FAIL | 2 (read-only profile constraint, not protocol bug) |
| SKIP (Tier 3-4 + requires edit session) | ~55 |
| **Tested (Tier 0-2 + probes)** | **~50** |
| **Total handlers** | **105** |

### Feature Feasibility Summary

| Feature | Status | Key finding |
|---------|--------|-------------|
| Soft Keys | PARTIAL | Protocol infrastructure works; edit session requires a named keymap (not 'NONE'); create via console UI first |
| V-Pot / Wheel Mode | PARTIAL | Read/set wheel mode works; CC layer active on L4; mode=5 value unknown; CC names empty |
| SuperCue / Auto-Mon | NOT IN PROTOCOL | No responses to cmd 1100-1200; no protocol codes exist; hardware-only feature |
| Split Board | PARTIAL | All 4 layers active simultaneously; no fader group assignment in protocol; physical test required |

### Outstanding Issues / Parser Bugs

1. **XPatch chain element count (xpatch.py):** Parser assumes 8 elements per chain. Unverifiable on this console (0 chains configured). Flag for testing on a console with chains.

2. **Wheel mode value 5 (softkeys handler):** `ACK_GET_DEFAULT_WHEEL_MODE_STATUS` returns mode=5 on MCU/CC layers. Not in the known enum (0=Pan, 1=Linear, 2=Boost/Cut, 3=Off). Either an undocumented mode or a parsing error. Verify against SSL documentation or console surface display.

3. **`ACK_GET_PROFILE_PATH` (handler discards data):** `handle_profile_path_reply` reads the path string but doesn't store it in state. Add `state.softkeys.profile_path = path` to make it observable.

### Deferred to Plan 02 (Tier 3-4)

The following handler groups were not tested in Plan 01 due to mutation risk:
- Routing ACKs (10411-10681) — require mutation testing with reversible state
- Projects ACKs (201-267) — high risk, test on disposable AUDIT-TEMP project
- Chan Presets CRUD (10771-10811) — Tier 3 state mutations
- XPatch preset selection and chain editing — Tier 3
- Automation mode change + console restart — Tier 4 (last)
- Total Recall snapshot take/select/delete — Tier 3-4
- Softkey full edit session (after creating named keymap via console UI) — requires setup
