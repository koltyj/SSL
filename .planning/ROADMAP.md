# Roadmap: SSL Matrix Control Bridge

## Overview

Five phases that move the SSL Matrix from disconnected hardware to the functional center of a hybrid mixing workflow. Phase 1 (complete) verified all compatibility on macOS Tahoe 26.2 — ipMIDI, HUI, MCU, and delta-ctrl all work natively with both Pro Tools and Ableton Live. The project has shifted from "build a DAW bridge" to "replace the broken MatrixRemote Java app and build a modern console control tool." Phase 2 audits every protocol capability against the live console. Phase 3 delivers console surface features (soft keys, V-pots, SuperCue). Phase 4 adds advanced workflow features (split board, session templates, monitoring). Phase 5 wraps everything in a native macOS dock application.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Compatibility Verification** - Confirm ipMIDI, MatrixRemote, and macOS Tahoe 26.2 work before writing any code
- [ ] **Phase 2: Capabilities Audit** - Wire-test every ssl-matrix-client protocol handler against the live console and document what's possible
- [ ] **Phase 3: Console Surface Features** - Soft keys, V-pots, SuperCue integration via ssl-matrix-client
- [ ] **Phase 4: Advanced Workflow Features** - Split board mode, session templates, project linking, connection monitoring
- [ ] **Phase 5: Native macOS Dock App** - GUI application wrapping ssl-matrix-client (language TBD)

## Phase Details

### Phase 1: Compatibility Verification
**Goal**: The SSL Matrix communicates over Ethernet on macOS Tahoe 26.2 and every layer of the protocol stack is confirmed working before any code is written
**Depends on**: Nothing (first phase)
**Requirements**: FOUN-01, FOUN-02, FOUN-03, FOUN-04
**Success Criteria** (what must be TRUE):
  1. ipMIDI driver is installed and SSL Matrix MIDI ports appear in Audio MIDI Setup > MIDI Studio on macOS Tahoe 26.2
  2. MatrixRemote connects to the console over Ethernet and the console responds to MatrixRemote commands
  3. macOS Local Network permissions are granted for ipMIDI, and all Matrix MIDI ports are visible as CoreMIDI ports in Audio MIDI Setup
  4. ipMIDI multicast traffic (225.0.0.37) is confirmed routing to the Ethernet adapter connected to the console, not to Wi-Fi or any other adapter
**Plans**: 2 plans (complete)
Plans:
- [x] 01-01-PLAN.md — Infrastructure setup: firmware ID, software install, permissions, network topology, multicast routing, MIDI port visibility
- [x] 01-02-PLAN.md — Connection and DAW verification: MatrixRemote connection, Pro Tools HUI config, four-behavior pass/fail test

### Phase 2: Capabilities Audit
**Goal**: Every ssl-matrix-client protocol handler is tested against the live SSL Matrix console, confirming what works, what doesn't, and documenting hard limits — so subsequent phases only build features that are verified possible
**Depends on**: Phase 1
**Requirements**: AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04
**Success Criteria** (what must be TRUE):
  1. All 105 dispatch handlers in ssl-matrix-client have been exercised against the live console with pass/fail results documented
  2. Soft key, V-pot, and SuperCue protocol capabilities are mapped with confirmed working message codes
  3. Split board feasibility is determined — can two DAW layers (HUI + MCU) run simultaneously on different fader groups?
  4. A capabilities document exists listing every confirmed feature, every known limitation, and every protocol gap
**Plans**: 2 plans
Plans:
- [x] 02-01-PLAN.md — Tier 0-2 handler audit (connection, read-only, non-destructive mutations) + feature feasibility probes (soft keys, V-pot, SuperCue, split board)
- [x] 02-02-PLAN.md — Tier 3-4 handler audit (state mutations, high-risk ops) + finalize CAPABILITIES.md

### Phase 3: Console Surface Features
**Goal**: Soft keys send DAW commands, V-pot encoders control parameters, and SuperCue/Auto-Mon integrates with the recording workflow — all through ssl-matrix-client
**Depends on**: Phase 2
**Requirements**: ADV-01, ADV-02, ADV-03
**Success Criteria** (what must be TRUE):
  1. At least one set of soft key macros is programmed via ssl-matrix-client and executes correct commands in both Pro Tools and Ableton
  2. V-pot rotary encoders control pan, sends, or plugin parameters in the active DAW
  3. SuperCue/Auto-Mon integration works with DAW punch recording workflow
  4. All surface features are configurable through the CLI
**Plans**: 2 plans
Plans:
- [ ] 03-01-PLAN.md — Fix cc_names storage bug, add V-pot wheel mode and CC names CLI commands (ADV-02)
- [ ] 03-02-PLAN.md — Soft key programming CLI commands + SuperCue documentation (ADV-01, ADV-03)

### Phase 4: Advanced Workflow Features
**Goal**: The ssl-matrix-client is a complete MatrixRemote replacement with session-aware workflow features — split board for dual-DAW, session templates linked to project files, routing recall, and connection monitoring with auto-reconnect
**Depends on**: Phase 3
**Requirements**: BRDG-01, SESS-01, SESS-02, SPLIT-01
**Success Criteria** (what must be TRUE):
  1. Console state templates can be saved and loaded, each linked to a specific Ableton set or Pro Tools session file
  2. Split board mode assigns left 8 faders to one DAW and right 8 to another, switchable with a single command
  3. Connection monitoring detects ipMIDI sync loss and auto-reconnects without user intervention
  4. All MatrixRemote functionality is replicated in ssl-matrix-client (channel names, routing, profiles, Total Recall, XPatch, projects)
**Plans**: TBD

### Phase 5: Native macOS Dock App
**Goal**: A native macOS application (dock app, not menu bar) wraps ssl-matrix-client with a visual interface for console control, status monitoring, and session management — replacing the broken MatrixRemote Java app with a modern, reliable GUI
**Depends on**: Phase 4
**Requirements**: APP-01, APP-02, APP-03
**Success Criteria** (what must be TRUE):
  1. A native macOS dock application launches, connects to the console, and displays real-time console state
  2. All ssl-matrix-client CLI features are accessible through the GUI
  3. The app launches at login and persists across DAW restarts without manual intervention
  4. Language/framework choice is informed by Phase 4 research (Swift, Python+native toolkit, or Electron TBD)
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Compatibility Verification | 2/2 | Complete | 2026-03-11 |
| 2. Capabilities Audit | 2/2 | Complete | 2026-03-13 |
| 3. Console Surface Features | 1/2 | In Progress|  |
| 4. Advanced Workflow Features | 0/TBD | Not started | - |
| 5. Native macOS Dock App | 0/TBD | Not started | - |
