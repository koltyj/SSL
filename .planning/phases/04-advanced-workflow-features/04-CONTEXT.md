# Phase 4: Advanced Workflow Features - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete MatrixRemote replacement with session-aware workflow features: split board for dual-DAW operation, session templates linked to DAW project files, routing recall, and connection monitoring with auto-reconnect. All features operate through the existing ssl-matrix-client CLI.

</domain>

<decisions>
## Implementation Decisions

### Connection Monitoring (BRDG-01)
- Reconnect aggressiveness: Claude's discretion
- Offline UX (logging/callbacks): Claude's discretion
- Scope (UDP only vs UDP+ipMIDI): Claude's discretion
- Auto re-sync after reconnect: Claude's discretion

### Session Template Scope
- **"Everything restorable"** — templates capture all confirmed-working console state: routing (insert matrix), channel names, profiles (DAW layer assignments), automation mode, TR enable, display settings (channels 17-32 visibility, flip scribble strips)
- XPatch state stored if present, but skip on restore (SET commands fail silently on this console)

### Session Template Storage & Naming
- Templates stored at `~/.ssl-matrix/templates/`
- DAW project file absolute path stored in template metadata — informational only, no auto-launch
- Template names auto-generated from console project title + timestamp (no manual naming)
- File format: Claude's discretion (JSON, TOML, or YAML — human-editable preferred)

### Session Template CLI Commands
- Full CRUD: save, load, list, delete, show (inspect contents)
- All commands accessible from the existing cmd.Cmd REPL and argparse one-shot modes

### Template Load Behavior
- **Diff preview before applying** — show what will change (e.g., "Channel 3: KICK → SNARE")
- **Selective apply by category** — diff grouped by category (routing, names, profiles, etc.); user picks which groups to apply
- **Warn and skip unrestorable items** — don't fail the whole load; show warning, apply everything else
- **Full report after load** — summary of applied changes, skipped items, and unchanged state

### Routing Recall (SESS-02)
- XPatch gap handling: Claude's discretion (XPatch SET dead on this console)
- Insert matrix recall UX (silent vs diff): Claude's discretion
- Channel names in routing recall: Claude's discretion

### Split Board (SPLIT-01)
- Skipped discussion — Phase 2 established that fader group assignment is console-surface config, not UDP protocol
- Implementation approach left to research/planning

### Claude's Discretion
- All connection monitoring implementation details (timeout values, retry strategy, UX, scope, re-sync)
- XPatch gap handling strategy
- Insert matrix recall UX approach
- Channel names in routing recall behavior
- Template file format choice
- Split board implementation approach (constrained by Phase 2 finding: surface-config, not UDP)

</decisions>

<specifics>
## Specific Ideas

- Template scope decision was explicit: "Everything restorable" — not just routing, but the full set of confirmed-working state
- DAW project linking is manual (prior decision from project setup) — user associates template with DAW file, no auto-detection
- Diff preview on load was a firm preference — user wants to see what's changing before it happens
- Selective apply was chosen over all-or-nothing — granularity at the category level (routing, names, profiles, etc.)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ConsoleState` dataclass tree in `models.py` — already holds all console state; template save = serialize this
- `handlers/connection.py` — GET_DESK discovery and heartbeat already implemented; monitoring extends this
- `handlers/routing.py` — insert matrix V2, chains, presets handlers exist
- `handlers/profiles.py` — DAW layer assignments, transport lock
- `handlers/projects.py` — project/title CRUD, directory listing
- `handlers/channels.py` — channel names, scribble strips
- `handlers/xpatch.py` — XPatch read works (SET fails silently)

### Established Patterns
- cmd.Cmd REPL with `do_*` methods for CLI commands
- argparse subcommands for one-shot mode
- Builder functions (`build_*`) for Python → console messages
- Handler functions for console → Python state updates
- All state mutations under `self._lock` in recv loop

### Integration Points
- Templates: new handler module or standalone module that serializes/deserializes `ConsoleState`
- Connection monitoring: extends `_recv_loop` and heartbeat logic in `connection.py`
- Split board: may require new CLI commands but limited by surface-config constraint
- Template CLI: new `do_*` methods in `cli.py`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-advanced-workflow-features*
*Context gathered: 2026-03-14*
