# Phase 04: Advanced Workflow Features - Research

**Researched:** 2026-03-14
**Domain:** Python stdlib — file serialization, connection monitoring, CLI extension, console state diffing
**Confidence:** HIGH

## Summary

Phase 4 builds four features entirely within the existing ssl-matrix-client architecture: session templates (SESS-01), routing recall (SESS-02), split board (SPLIT-01), and connection health monitoring (BRDG-01). All features use Python stdlib only — no new dependencies.

The foundation is strong: `ConsoleState` already holds every piece of state that templates need to capture. `handlers/connection.py` already has heartbeat tracking and `_recv_loop` already has a socket timeout path that calls `_send_get_desk()`. The template system is a serialization/deserialization layer on top of `ConsoleState`. Connection monitoring is an extension of the existing heartbeat timeout logic. Split board, constrained by Phase 2's finding that fader group assignment is surface-config (not UDP), is implemented as a software bookkeeping layer with CLI guidance output — not protocol mutation.

**Primary recommendation:** Build each feature as a standalone module. Template logic goes in `ssl-matrix-client/templates.py`. Connection monitoring adds a watchdog thread to `client.py`. Split board adds state tracking and CLI commands to `cli.py`. Routing recall is a subcommand of template load.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Connection Monitoring (BRDG-01)**
- Reconnect aggressiveness: Claude's discretion
- Offline UX (logging/callbacks): Claude's discretion
- Scope (UDP only vs UDP+ipMIDI): Claude's discretion
- Auto re-sync after reconnect: Claude's discretion

**Session Template Scope**
- "Everything restorable" — templates capture all confirmed-working console state: routing (insert matrix), channel names, profiles (DAW layer assignments), automation mode, TR enable, display settings (channels 17-32 visibility, flip scribble strips)
- XPatch state stored if present, but skip on restore (SET commands fail silently on this console)

**Session Template Storage and Naming**
- Templates stored at `~/.ssl-matrix/templates/`
- DAW project file absolute path stored in template metadata — informational only, no auto-launch
- Template names auto-generated from console project title + timestamp (no manual naming)
- File format: Claude's discretion (JSON, TOML, or YAML — human-editable preferred)

**Session Template CLI Commands**
- Full CRUD: save, load, list, delete, show (inspect contents)
- All commands accessible from the existing cmd.Cmd REPL and argparse one-shot modes

**Template Load Behavior**
- Diff preview before applying — show what will change (e.g., "Channel 3: KICK -> SNARE")
- Selective apply by category — diff grouped by category (routing, names, profiles, etc.); user picks which groups to apply
- Warn and skip unrestorable items — don't fail the whole load; show warning, apply everything else
- Full report after load — summary of applied changes, skipped items, and unchanged state

**Routing Recall (SESS-02)**
- XPatch gap handling: Claude's discretion (XPatch SET dead on this console)
- Insert matrix recall UX (silent vs diff): Claude's discretion
- Channel names in routing recall: Claude's discretion

**Split Board (SPLIT-01)**
- Skipped discussion — Phase 2 established that fader group assignment is console-surface config, not UDP protocol
- Implementation approach left to research/planning

### Claude's Discretion
- All connection monitoring implementation details (timeout values, retry strategy, UX, scope, re-sync)
- XPatch gap handling strategy
- Insert matrix recall UX approach
- Channel names in routing recall behavior
- Template file format choice
- Split board implementation approach (constrained by Phase 2 finding: surface-config, not UDP)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BRDG-01 | Health monitoring detects ipMIDI sync loss and auto-reconnects | Heartbeat tracking already in `DeskInfo.last_heartbeat`; `_recv_loop` timeout already calls `_send_get_desk()`; extend with watchdog thread and re-sync on reconnect |
| SESS-01 | Console state templates saveable/loadable, each linked to a specific DAW project file | `ConsoleState` already holds all capturable state; template = JSON serialization of state subset + metadata; CRUD commands follow existing `do_*` pattern in `cli.py` |
| SESS-02 | Routing recall — insert matrix and XPatch state restored per session template | Insert matrix SET commands confirmed working (Phase 2 PASS); XPatch SET confirmed dead (skip with warning); restore sequence mirrors `request_sync()` pattern |
| SPLIT-01 | Split board mode — left 8 faders to one DAW, right 8 to another, switchable via single command | Protocol level: all 4 DAW layers simultaneously active (Phase 2 confirmed); fader group assignment is hardware surface-config, not UDP; implementation is software bookkeeping + user guidance |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `json` | stdlib | Template file format | Human-readable, no deps, native Python, easy to version-control |
| `dataclasses` | stdlib | `ConsoleState` is already dataclasses; `asdict()` for serialization | Already the project's data layer |
| `pathlib` | stdlib | `~/.ssl-matrix/templates/` path operations | Project already uses pathlib conventions |
| `threading` | stdlib | Watchdog thread for connection monitoring | Already used for `_recv_thread` |
| `time` | stdlib | Heartbeat age calculation | Already used in `DeskInfo.heartbeat_age` |
| `datetime` | stdlib | Template name timestamp generation | Stdlib, no deps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dataclasses.asdict` | stdlib | Convert `ConsoleState` subtree to dict for JSON serialization | Template save path |
| `json.dumps` / `json.loads` | stdlib | Serialize/deserialize template files | With `indent=2` for human-readability |
| `cmd.Cmd` do_* pattern | stdlib | CLI commands (already established) | All new template and split commands |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON | TOML | TOML is more human-editable but requires `tomllib` (Python 3.11+) or `tomli` dep; project targets Python 3.9+; JSON is the correct choice |
| JSON | YAML | YAML requires `pyyaml` dep; out of scope for no-external-deps constraint |
| Watchdog thread | asyncio | asyncio would require rewriting the entire client architecture; threading matches existing pattern |

**Installation:** None — all stdlib. No `pip install` needed.

## Architecture Patterns

### Recommended Project Structure
```
ssl-matrix-client/
├── templates.py          # NEW: Template save/load/diff/apply logic
├── client.py             # EXTEND: Add watchdog thread, reconnect method
├── cli.py                # EXTEND: Add do_template_*, do_split_* commands
├── models.py             # NO CHANGE: ConsoleState already sufficient
└── handlers/
    └── connection.py     # MINOR EXTEND: Expose reconnect callback hook
~/.ssl-matrix/
└── templates/
    └── {title}_{timestamp}.json   # Template files
```

### Pattern 1: Template File Format (JSON)

**What:** A JSON file capturing all restorable console state plus metadata.
**When to use:** Every `template save` command.

```json
{
  "version": 1,
  "saved_at": "2026-03-14T10:30:00",
  "console_project_title": "Session A",
  "daw_project_path": "/Users/koltonjacobs/Documents/ProTools/Session A.ptx",
  "state": {
    "channels": [
      {"number": 1, "name": "KICK"},
      {"number": 2, "name": "SNARE"}
    ],
    "daw_layers": [
      {"number": 1, "protocol": 1, "profile_name": "Pro Tools Standard"},
      {"number": 2, "protocol": 2, "profile_name": "kj"}
    ],
    "devices": [
      {"number": 1, "name": "Insert 1", "is_assigned": 0, "is_stereo": 0}
    ],
    "channel_inserts": [],
    "automation_mode": 1,
    "tr_enabled": false,
    "display_17_32": 0,
    "flip_scrib": 0,
    "xpatch_stored": true,
    "xpatch_note": "XPatch SET commands fail silently on this console — stored for reference only"
  }
}
```

### Pattern 2: Template Serialization via `dataclasses.asdict`

**What:** Convert `ConsoleState` subtrees to dict using stdlib `dataclasses.asdict()`.
**When to use:** Template save — extract only restorable fields.

```python
# Source: Python stdlib docs — dataclasses.asdict()
from dataclasses import asdict

def capture_template_state(state: ConsoleState) -> dict:
    """Extract only confirmed-restorable state from ConsoleState."""
    return {
        "channels": [asdict(ch) for ch in state.channels],
        "daw_layers": [asdict(dl) for dl in state.daw_layers],
        "devices": [asdict(dev) for dev in state.devices],
        "channel_inserts": [asdict(ci) for ci in state.channel_inserts],
        "automation_mode": state.automation_mode,
        "tr_enabled": state.tr_enabled,
        "display_17_32": state.display_17_32,
        "flip_scrib": state.flip_scrib,
        # XPatch: stored for reference, skipped on restore
        "xpatch": asdict(state.xpatch),
    }
```

### Pattern 3: Diff Before Apply

**What:** Compare template state vs current `ConsoleState`, group changes by category, display before applying.
**When to use:** Every `template load` command.

```python
def diff_template(template_state: dict, current: ConsoleState) -> dict:
    """Return changes grouped by category."""
    changes = {
        "channels": [],
        "profiles": [],
        "routing": [],
        "display": [],
        "skipped": [],  # XPatch and any unrestorable items
    }
    for i, ch_data in enumerate(template_state["channels"]):
        current_name = current.channels[i].name
        if ch_data["name"] != current_name:
            changes["channels"].append(
                f"Ch{i+1}: '{current_name}' -> '{ch_data['name']}'"
            )
    # ... similar for daw_layers, channel_inserts, etc.
    changes["skipped"].append("XPatch: SET commands fail silently — skipped")
    return changes
```

### Pattern 4: Watchdog Thread for Connection Monitoring

**What:** A separate daemon thread that checks heartbeat age and triggers reconnect.
**When to use:** BRDG-01 — always active after `connect`.

```python
import threading
import time

HEARTBEAT_TIMEOUT = 35.0   # seconds — console sends ~every 30s
RECONNECT_DELAY   = 5.0    # seconds between reconnect attempts
MAX_RECONNECT_ATTEMPTS = 10

def _watchdog_loop(self):
    """Monitor heartbeat age and reconnect if stale."""
    while self._running:
        time.sleep(5.0)  # check interval
        with self._lock:
            age = self.state.desk.heartbeat_age
            online = self.state.desk.online
        if online and age > HEARTBEAT_TIMEOUT:
            log.warning("Heartbeat stale (%.1fs) — attempting reconnect", age)
            self._trigger_reconnect()

def _trigger_reconnect(self):
    """Mark offline, send GET_DESK, re-sync on reply."""
    with self._lock:
        self.state.desk.online = False
    self._send_get_desk()
    # GET_DESK_REPLY handler already sets desk.online = True
    # After online, call request_sync() to re-establish state
```

**Key insight:** The existing `_recv_loop` socket timeout (10s) already calls `_send_get_desk()` as a keepalive. The watchdog adds a separate layer that checks *semantic* liveness (heartbeat age) independent of socket-level timeouts. These are complementary — socket timeout handles network-layer loss, watchdog handles console-layer loss (e.g., ipMIDI sync loss where UDP socket stays open).

### Pattern 5: Split Board as Software Bookkeeping

**What:** Track which DAW layers are "assigned" to fader groups in client-side state. Display assignments on command. Provide guidance on how to switch physically.
**When to use:** SPLIT-01.

**Constraint from Phase 2:** Fader group assignment is console surface configuration. There is no UDP command to assign DAW layers to fader groups. The protocol confirms all 4 DAW layers are simultaneously active at the protocol level — the hardware buttons on the console select which layer controls which faders.

**Implementation:** The `split` command stores a local assignment map (not sent to console) and prints the current split configuration with instructions. The command also sets the appropriate DAW layer profiles via UDP to prepare the layers for split use.

```python
# In cli.py — do_split command
def do_split(self, arg):
    """Set up split board: configure DAW layers for dual-DAW use.

    Usage: split <left_protocol> <right_protocol>
    Example: split HUI MCU

    Note: Left 8 faders / Right 8 faders assignment requires
    pressing the DAW layer buttons on the console surface.
    This command configures the protocols; you assign faders on the board.
    """
```

### Anti-Patterns to Avoid

- **Sending XPatch SET commands on restore:** Phase 2 confirmed all 7 XPatch SET commands are silently ignored on this console. Never attempt to restore XPatch routing via UDP. Store for reference, skip on restore with a clear warning.
- **Assuming template load is atomic:** Apply category by category. If channel rename fails (console offline mid-restore), log the failure and continue with remaining categories.
- **Blocking the REPL during routing restore:** Insert matrix restore sends multiple UDP commands. Use the same `time.sleep(0.05)` inter-packet spacing as `request_sync()`. Do not block the recv loop.
- **Hardcoding template path:** Always use `pathlib.Path.home() / ".ssl-matrix" / "templates"`. Create directory with `mkdir(parents=True, exist_ok=True)` on first save.
- **Generating template names with spaces:** Console project title may be "(none)" or contain spaces. Sanitize to `{sanitized_title}_{YYYYMMDD_HHMMSS}.json`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON serialization | Custom binary format | `json.dumps(..., indent=2)` | Human-editable, version-control friendly, stdlib |
| State capture | Manual field-by-field copy | `dataclasses.asdict()` | Already works for the entire dataclass tree |
| Timestamp generation | Custom formatter | `datetime.now().strftime("%Y%m%d_%H%M%S")` | Stdlib, no ambiguity |
| File path operations | `os.path.join()` strings | `pathlib.Path` | Already the convention, cleaner |
| Thread-safe state read | Ad-hoc locking | `with self._lock:` (existing pattern) | Already established, don't invent alternatives |

**Key insight:** The project's no-external-dependency constraint means all solutions must be stdlib. The good news: dataclasses + json cover everything needed for template serialization. The hard part is the diff/apply logic and the routing restore sequence — both are custom business logic, not library problems.

## Common Pitfalls

### Pitfall 1: `dataclasses.asdict()` Recursion on XPatch

**What goes wrong:** `XpatchState` contains nested lists of dataclasses. `asdict()` recurses into them correctly, but the resulting dict is large (~16 channels * multiple fields). On load, reconstructing XpatchState from dict requires careful `XpatchChannel(**d)` reconstruction for each element.

**Why it happens:** `asdict()` converts nested dataclasses to nested dicts, not back to dataclasses. The load path must manually reconstruct the object tree.

**How to avoid:** Write explicit `state_from_dict()` function in `templates.py` that reconstructs each dataclass type. Don't use a generic deserializer.

**Warning signs:** `AttributeError: 'dict' object has no attribute 'number'` when accessing restored state fields.

### Pitfall 2: Template Save With No Active Project

**What goes wrong:** `state.project_name` and `state.title_name` are both `""` or `"(none)"` if no project is active on the console. Template name becomes `"none_20260314_103000.json"`.

**Why it happens:** Phase 2 confirmed `GET_PROJECT_NAME_AND_TITLE_REPLY` returns `"(none)"` when no project is configured.

**How to avoid:** Sanitize template name: strip non-alphanumeric characters, replace spaces with underscores, truncate to reasonable length. Default to `"unnamed"` if project title is empty or `"(none)"`.

**Warning signs:** Template file named `"(none)_20260314_103000.json"` — valid but ugly. No functional breakage.

### Pitfall 3: Routing Restore Order Matters

**What goes wrong:** If you try to assign an insert device to a channel before the device exists (or is named), the console may reject the assignment.

**Why it happens:** Insert matrix has dependency ordering: insert names → channel assignments → chain assignments. Phase 2 testing showed the console enforces that devices must be named/assigned in the right sequence.

**How to avoid:** On template load, restore in this order:
1. Insert device names (`SEND_SET_INSERT_NAMES_V2`)
2. Channel insert assignments (`SEND_SET_INSERT_TO_CHAN_V2`)
3. Wait for ACKs between steps (50ms inter-packet delay, same as `request_sync()`)
4. Re-query state after restore to verify

**Warning signs:** Routing ACK error messages ("Insert operation failed") in logs after restore.

### Pitfall 4: Watchdog Reconnect Storm

**What goes wrong:** Watchdog fires reconnect, watchdog fires again before reconnect completes (heartbeat not yet received), second reconnect attempt collides with first.

**Why it happens:** `_send_get_desk()` is fire-and-forget. If the console is slow to respond, the watchdog's next check interval fires before `online` is set to `True`.

**How to avoid:** Track reconnect state with a flag (`_reconnecting: bool`). Watchdog skips if `_reconnecting` is True. Clear `_reconnecting` when `GET_DESK_REPLY` is received (i.e., in `handle_get_desk_reply`).

**Warning signs:** Log shows repeated "Heartbeat stale" messages at 5-second intervals without a corresponding "Connected" message.

### Pitfall 5: Thread Safety on Template Load

**What goes wrong:** Template load reads current `ConsoleState` fields to build the diff, then sends UDP commands that trigger handler callbacks that mutate `ConsoleState` on the recv thread — concurrent read/write without holding `_lock`.

**Why it happens:** Template load runs on the CLI thread. Handlers run on the recv thread. The diff computation reads state fields without lock, then sends, then reads again to verify.

**How to avoid:** Always acquire `self.client._lock` when reading state for diff computation. Copy the relevant fields out under the lock before doing the comparison. Follow the existing pattern from `cli.py:do_status()`.

**Warning signs:** `RuntimeError: dictionary changed size during iteration` or inconsistent diff output.

## Code Examples

Verified patterns from existing codebase:

### Thread-Safe State Read (from cli.py)
```python
# Source: ssl-matrix-client/cli.py do_status()
with self.client._lock:
    d = self.client.state.desk
    online = d.online
    hb_age = d.heartbeat_age
    proj = self.client.state.project_name
# Use captured values outside the lock
print(f"Project: {proj}")
```

### Inter-Packet Delay (from client.py request_sync)
```python
# Source: ssl-matrix-client/client.py request_sync()
self.send(routing.build_get_insert_names_v2(ds, ms))
time.sleep(0.05)
self.send(routing.build_get_chain_info_v2(ds, ms))
time.sleep(0.05)
```

### Template Directory Creation
```python
# stdlib pathlib pattern
from pathlib import Path

TEMPLATE_DIR = Path.home() / ".ssl-matrix" / "templates"

def ensure_template_dir():
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    return TEMPLATE_DIR
```

### Template Name Generation
```python
from datetime import datetime
import re

def make_template_name(project_title: str) -> str:
    safe = re.sub(r"[^\w]", "_", project_title or "unnamed")
    safe = safe.strip("_")[:20] or "unnamed"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe}_{ts}.json"
```

### Heartbeat Age Check (existing DeskInfo property)
```python
# Source: ssl-matrix-client/models.py DeskInfo
@property
def heartbeat_age(self):
    if self.last_heartbeat == 0:
        return float("inf")
    return time.time() - self.last_heartbeat
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| XPatch V1 commands (400-581 range) | V2 insert matrix (10400+ range) | Before Phase 2 | V1 commands not wire-tested; V2 confirmed PASS |
| No heartbeat tracking | `last_heartbeat` + `heartbeat_age` property | Phase 1 | Now possible to detect console loss |
| `request_sync()` as one-time sync | To be extended as re-sync-on-reconnect | Phase 4 | Foundation already in place |

**Deprecated/outdated:**
- XPatch SET mutations: Confirmed non-functional on V3.0/5 (Phase 2). Do not attempt to restore XPatch routing. Store only.
- V1 insert matrix commands (400-581 range): Untested; V2 commands (10400+ range) are confirmed working. Use V2.

## Open Questions

1. **ipMIDI sync loss detection scope**
   - What we know: BRDG-01 requires detecting "ipMIDI sync loss." ipMIDI is MIDI-over-UDP multicast (225.0.0.37). The ssl-matrix-client does not speak ipMIDI directly — it speaks the SSL UDP protocol. ipMIDI is a separate channel between DAW and console.
   - What's unclear: Can the ssl-matrix-client detect ipMIDI sync loss at all? ipMIDI runs on a different port and protocol entirely.
   - Recommendation: Scope BRDG-01 to SSL UDP heartbeat monitoring only (not ipMIDI). The watchdog detects loss of UDP heartbeat from the console — which is the only thing ssl-matrix-client can observe. If the user wants ipMIDI monitoring, that requires a separate process. Document this scope limitation explicitly in the feature.

2. **Selective apply UX implementation**
   - What we know: User wants to pick which categories to apply (routing, names, profiles, etc.) after seeing the diff.
   - What's unclear: In one-shot argparse mode, interactive prompting is awkward (piped input). In REPL mode, `input()` works fine.
   - Recommendation: In REPL mode, show diff then prompt `Apply [all/routing/names/profiles/none]?`. In one-shot mode, add a `--categories` flag (e.g., `template load myfile --categories routing,names`). Default to `all` if not specified.

3. **Re-sync after reconnect: state drift**
   - What we know: `request_sync()` re-fetches all state. After a reconnect, the console may have different state than when we went offline (e.g., user made changes on console surface).
   - What's unclear: Should the watchdog auto-call `request_sync()` after reconnect, or just re-establish connectivity?
   - Recommendation: Auto-call `request_sync()` after each successful reconnect. The full sync takes ~0.5s total (existing implementation). This is the safest approach — always start from ground truth.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x-8.x (from pyproject.toml `pytest>=7,<9`) |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` testpaths = ["tests"] |
| Quick run command | `python3 -m pytest tests/test_templates.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SESS-01 | Template save serializes ConsoleState to JSON correctly | unit | `pytest tests/test_templates.py::TestTemplateSave -x` | Wave 0 |
| SESS-01 | Template load deserializes JSON back to typed state dict | unit | `pytest tests/test_templates.py::TestTemplateLoad -x` | Wave 0 |
| SESS-01 | Template CRUD: list, delete, show work on `~/.ssl-matrix/templates/` | unit (tmp_path) | `pytest tests/test_templates.py::TestTemplateCRUD -x` | Wave 0 |
| SESS-01 | Template name generated as `{title}_{timestamp}.json` | unit | `pytest tests/test_templates.py::TestTemplateNaming -x` | Wave 0 |
| SESS-02 | Diff shows correct changes between template and current state | unit | `pytest tests/test_templates.py::TestTemplateDiff -x` | Wave 0 |
| SESS-02 | Routing restore sends correct builder calls in correct order | unit (mock send) | `pytest tests/test_templates.py::TestRoutingRestore -x` | Wave 0 |
| SESS-02 | XPatch is stored in template JSON but skipped on restore | unit | `pytest tests/test_templates.py::TestXpatchSkip -x` | Wave 0 |
| SPLIT-01 | Split command stores assignment in client state | unit | `pytest tests/test_split.py::TestSplitState -x` | Wave 0 |
| BRDG-01 | Watchdog detects stale heartbeat and calls _trigger_reconnect | unit (mock time) | `pytest tests/test_watchdog.py::TestWatchdog -x` | Wave 0 |
| BRDG-01 | Reconnect flag prevents watchdog storm | unit | `pytest tests/test_watchdog.py::TestReconnectGuard -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_templates.py tests/test_watchdog.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_templates.py` — covers SESS-01, SESS-02 (template save/load/diff/restore)
- [ ] `tests/test_split.py` — covers SPLIT-01 (split state bookkeeping)
- [ ] `tests/test_watchdog.py` — covers BRDG-01 (heartbeat monitoring, reconnect guard)
- [ ] `ssl-matrix-client/templates.py` — core template module (new file)

Note: existing `conftest.py` import shim must be extended to include `ssl_matrix_client.templates` when that module is created.

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `ssl-matrix-client/models.py`, `client.py`, `cli.py`, `handlers/connection.py`, `handlers/routing.py`, `protocol.py` — all state fields, existing patterns, and extension points verified
- `.planning/phases/02-capabilities-audit/CAPABILITIES.md` — wire-test results; XPatch SET confirmed dead, insert matrix V2 confirmed PASS, heartbeat confirmed
- `.planning/phases/04-advanced-workflow-features/04-CONTEXT.md` — locked decisions verbatim

### Secondary (MEDIUM confidence)
- Python stdlib docs (dataclasses.asdict, json, pathlib, threading, datetime) — all used per documented API; no external libraries needed
- `tests/conftest.py` and existing test files — confirmed test patterns and import shim requirements

### Tertiary (LOW confidence)
- ipMIDI scope question (Open Question 1) — requires live console verification to confirm whether ipMIDI loss is observable from ssl-matrix-client's UDP socket

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pure stdlib, no external deps, all confirmed available in Python 3.9+
- Architecture: HIGH — ConsoleState already holds all needed state; patterns directly from existing codebase
- Pitfalls: HIGH — most derive from confirmed Phase 2 wire-test results (XPatch dead, routing ACK behavior, heartbeat timing)
- Split board: HIGH — Phase 2 definitively answered the protocol question; software-only approach is the only viable path

**Research date:** 2026-03-14
**Valid until:** 2026-06-14 (stable — no external dependencies to go stale)
