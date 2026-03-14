# Phase 5: Terminal UI - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

A Textual-based terminal UI for real-time SSL Matrix console monitoring and interactive control. Launches as a separate `tui` subcommand alongside the existing cmd.Cmd REPL. Displays live console state with tabbed views, a command palette for issuing commands, and reactive updates from the recv thread.

</domain>

<decisions>
## Implementation Decisions

### Dashboard Layout
- **Main view:** Channel strips as primary area + persistent status bar at bottom
- **Channel strip info:** Channel name + number, DAW layer + protocol, insert device routing, automation mode — full detail per strip
- **Status bar contents:** Connection health (green/yellow/red dot), active project + last loaded template, keyboard shortcut hints for current view
- **Navigation:** Tabbed views switchable with number keys (1-4). Views: Channels, Routing, Templates, Settings (exact tab set at Claude's discretion)

### Interaction Model
- **Command input:** Command palette triggered by `:` or `/` — type commands, get autocomplete
- **No direct keyboard shortcuts** for actions (beyond tab switching with number keys)
- **Launch mode:** `python3 -m ssl-matrix-client tui` — separate subcommand, REPL stays as default
- **Command naming:** Claude's discretion (reuse REPL names or redesign for TUI)
- **Command palette implementation:** Use Textual's built-in command palette widget

### Live Update Behavior
- **Update strategy:** Immediate reactive — state changes appear as recv thread processes them, not polled
- **Visual feedback:** Changed values briefly highlight (color flash, 1-2 seconds) before returning to normal
- **Disconnect UX:** Full-screen overlay dimming the UI with centered "DISCONNECTED — reconnecting..." banner and attempt counter
- **Heartbeat indicator:** Green/yellow/red health dot in status bar (not a live-ticking counter)

### Library Choice
- **Framework:** Textual — first external dependency for the project
- **Theme:** SSL-inspired custom color scheme (greens, warm tones, accent colors inspired by the console aesthetic)
- **Aesthetic reference:** Mimic the physical SSL console scribble strips — channel strips in a row like the hardware surface
- **Command palette:** Textual's built-in command palette widget

### Claude's Discretion
- Exact tab set and tab names (Channels, Routing, Templates, Settings as starting point)
- Command naming strategy (reuse REPL names vs TUI-optimized)
- Highlight animation timing and color choice
- Textual CSS theming details (exact SSL-inspired palette)
- How to bridge recv thread updates to Textual's async event loop
- Whether to add Textual to pyproject.toml as optional or required dependency

</decisions>

<specifics>
## Specific Ideas

- Channel strips should visually mimic the physical SSL console's scribble strip layout — a row of strips, not a table
- SSL-inspired theme: the user wants the TUI to feel like the console hardware, not a generic terminal app
- Full-screen disconnect overlay was a firm preference — connection loss should be unmissable
- Health dot (not counter) for heartbeat — less distracting during mixing sessions
- Command palette (not keyboard shortcuts) for actions — the TUI is a monitoring dashboard first, command interface second

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ConsoleState` dataclass tree in `models.py` — all state already structured and accessible
- `SSLMatrixClient` in `client.py` — connect/disconnect, recv thread, heartbeat, watchdog, split state
- `templates.py` — save/load/diff/apply/CRUD for session templates
- `cli.py` — ~30 `do_*` commands that can be wrapped as command palette actions
- `DeskInfo.heartbeat_age` property — ready-made for health dot thresholds

### Established Patterns
- Recv thread runs under `self._lock` — TUI reads must acquire lock briefly
- `_watchdog_loop` daemon thread — TUI must coexist with watchdog thread
- All state mutations happen in handlers dispatched from `_recv_loop`
- Builder functions (`build_*`) create outbound messages

### Integration Points
- TUI wraps `SSLMatrixClient` — same client instance, new presentation layer
- `__main__.py` needs a `tui` subcommand added to argparse
- Textual app needs a bridge from the sync recv thread to Textual's async event loop (likely `call_from_thread` or message posting)
- Command palette actions map to existing `do_*` logic or direct client method calls

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-terminal-ui*
*Context gathered: 2026-03-14*
