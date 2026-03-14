# Phase 05: Terminal UI - Research

**Researched:** 2026-03-14
**Domain:** Textual TUI framework, thread-to-async bridging, reactive UI patterns
**Confidence:** HIGH (Textual 8.1.1 official docs verified)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Framework:** Textual — first external dependency for the project
- **Layout:** Channel strips as primary area + persistent status bar at bottom
- **Channel strip info:** Channel name + number, DAW layer + protocol, insert device routing, automation mode — full detail per strip
- **Status bar contents:** Connection health (green/yellow/red dot), active project + last loaded template, keyboard shortcut hints for current view
- **Navigation:** Tabbed views switchable with number keys (1-4). Views: Channels, Routing, Templates, Settings (exact tab set at Claude's discretion)
- **Command input:** Command palette triggered by `:` or `/` — type commands, get autocomplete
- **No direct keyboard shortcuts** for actions (beyond tab switching with number keys)
- **Launch mode:** `python3 -m ssl-matrix-client tui` — separate subcommand, REPL stays as default
- **Update strategy:** Immediate reactive — state changes appear as recv thread processes them, not polled
- **Visual feedback:** Changed values briefly highlight (color flash, 1-2 seconds) before returning to normal
- **Disconnect UX:** Full-screen overlay dimming the UI with centered "DISCONNECTED — reconnecting..." banner and attempt counter
- **Heartbeat indicator:** Green/yellow/red health dot in status bar (not a live-ticking counter)
- **Theme:** SSL-inspired custom color scheme (greens, warm tones, accent colors inspired by the console aesthetic)
- **Aesthetic reference:** Mimic the physical SSL console scribble strips — channel strips in a row like the hardware surface
- **Command palette:** Textual's built-in command palette widget (Provider subclass)

### Claude's Discretion
- Exact tab set and tab names (Channels, Routing, Templates, Settings as starting point)
- Command naming strategy (reuse REPL names vs TUI-optimized)
- Highlight animation timing and color choice
- Textual CSS theming details (exact SSL-inspired palette)
- How to bridge recv thread updates to Textual's async event loop
- Whether to add Textual to pyproject.toml as optional or required dependency

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Textual 8.1.1 (released 2026-03-10) is the current stable version. The framework's threading model is well-suited to this project: `post_message()` is explicitly thread-safe and is the correct bridge from the SSL recv thread into Textual's async event loop. Reactive attributes with watch methods handle automatic widget re-renders when state snapshots change. The built-in `ModalScreen` handles the disconnect overlay; `TabbedContent` with number-key bindings handles tab navigation; the `Provider` subclass pattern wires up the command palette.

The central integration challenge is bridging the sync recv thread (which holds `_lock` and mutates `ConsoleState`) into Textual's async event loop. The pattern is: recv thread calls `app.post_message(StateUpdated(snapshot))` immediately after releasing the lock; the app's `on_state_updated` handler diffs the snapshot against current widget state and updates reactive attributes. This is the only safe path — Textual's other APIs are not thread-safe.

The SSL-inspired theme maps naturally to Textual's `Theme` class (primary, background, surface, accent, etc.). Channel strips are best implemented as a horizontal `HorizontalScroll` of custom `Static` subclasses — each strip is a fixed-width column widget styled to resemble a hardware scribble strip.

**Primary recommendation:** One `tui.py` module, one `SSLApp(App)` class, custom `Theme` registered in `on_mount`, `Provider` subclass for command palette, `ModalScreen` for disconnect overlay, `post_message` for recv-thread bridge.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | >=0.80.0 (8.x) | TUI framework: layout, events, CSS, reactivity | Only production-quality Python TUI with command palette, animation, and theme system |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-asyncio | latest | Async test support for `run_test()` | Required for Textual unit tests |
| rich | (bundled with Textual) | Markup rendering inside widgets | Available without separate install |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Textual | urwid / curses | No reactive system, no CSS, no command palette — far more hand-rolling |
| Textual | prompt_toolkit | Good for input-focused apps, weak at dashboard-style layout |

**Installation:**
```bash
pip install "textual>=0.80.0"
# Dev/test:
pip install "textual[dev]>=0.80.0" pytest-asyncio
```

`pyproject.toml` update — add textual as a runtime (not optional) dependency since the `tui` subcommand is a first-class feature:
```toml
[project]
dependencies = ["textual>=0.80.0"]
```

---

## Architecture Patterns

### Recommended Project Structure
```
ssl-matrix-client/
├── tui.py           # SSLApp(App) — the Textual app class
├── tui_widgets.py   # ChannelStrip, StatusBar, DisconnectOverlay custom widgets
├── tui_commands.py  # ConsoleCmdProvider(Provider) — command palette actions
├── ssl_theme.tcss   # SSL-inspired TCSS stylesheet
├── cli.py           # unchanged — REPL stays as default
└── __main__.py      # add `tui` subcommand to argparse
```

### Pattern 1: Thread-to-Textual Bridge via post_message

**What:** recv thread safely posts a message carrying a state snapshot into Textual's event loop. Only `post_message` is thread-safe — do not call reactive setters or `call_from_thread` from within the dispatch handlers.

**When to use:** Every time the recv thread processes a packet that changes visible state.

**Implementation approach:**

The recv thread in `SSLMatrixClient._recv_loop` dispatches handlers inside `with self._lock`. The bridge fires after the lock is released. Two implementation options:

**Option A — Inject a post-dispatch callback into the client** (recommended):
```python
# In SSLMatrixClient, add a hook:
self._on_state_changed: Callable | None = None

# At the end of _recv_loop after each dispatch (outside the lock):
if self._on_state_changed:
    self._on_state_changed()

# In SSLApp.on_mount:
def on_mount(self) -> None:
    self.client._on_state_changed = self._emit_state_update

def _emit_state_update(self) -> None:
    # Called from recv thread — thread-safe:
    with self.client._lock:
        # Take a lightweight snapshot of relevant fields
        snapshot = _extract_snapshot(self.client.state)
    self.post_message(self.StateUpdated(snapshot))
```

**Option B — Subclass SSLMatrixClient** and override `_recv_loop` to call `post_message` after each dispatch. More invasive, less preferred.

**The StateUpdated message:**
```python
class SSLApp(App):
    class StateUpdated(Message):
        def __init__(self, snapshot: dict) -> None:
            self.snapshot = snapshot
            super().__init__()

    def on_ssl_app_state_updated(self, msg: StateUpdated) -> None:
        # Updates reactive attributes on widgets — runs in Textual's async loop
        self.query_one(ChannelView).update_from(msg.snapshot)
        self.query_one(StatusBar).update_from(msg.snapshot)
```

**Source:** [Textual Events Guide](https://textual.textualize.io/guide/events/) — `post_message` is explicitly thread-safe.

### Pattern 2: Reactive Attributes for Widget State

Widgets expose reactive attributes. Setting them triggers automatic re-render via watch methods.

```python
# Source: https://textual.textualize.io/guide/reactivity/
from textual.reactive import reactive

class ChannelStrip(Static):
    channel_name: reactive[str] = reactive("")
    daw_protocol: reactive[str] = reactive("")
    highlighted: reactive[bool] = reactive(False)

    def watch_channel_name(self, new_name: str) -> None:
        self.update(self._render_strip())

    def watch_highlighted(self, value: bool) -> None:
        if value:
            self.add_class("highlighted")
        else:
            self.remove_class("highlighted")
```

### Pattern 3: Flash-Highlight Animation

When a channel name or value changes, flash a highlight color then revert. Uses `animate()` with `delay` for the return animation, OR a `set_timer` to revert a CSS class.

```python
# Source: https://textual.textualize.io/guide/animation/
def flash_highlight(self) -> None:
    """Called when this channel's value changes."""
    self.highlighted = True
    self.set_timer(1.5, self._clear_highlight)

def _clear_highlight(self) -> None:
    self.highlighted = False
```

CSS class approach is more reliable than `styles.animate()` for color changes because terminal color depth varies. The CSS class toggle is instant and deterministic.

### Pattern 4: Tab Navigation with Number Keys

```python
# Source: https://textual.textualize.io/widgets/tabbed_content/
from textual.widgets import TabbedContent, TabPane

class SSLApp(App):
    BINDINGS = [
        ("1", "show_tab('channels')", "Channels"),
        ("2", "show_tab('routing')", "Routing"),
        ("3", "show_tab('templates')", "Templates"),
        ("4", "show_tab('settings')", "Settings"),
    ]

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="channels"):
            with TabPane("1 Channels", id="channels"):
                yield ChannelView()
            with TabPane("2 Routing", id="routing"):
                yield RoutingView()
            with TabPane("3 Templates", id="templates"):
                yield TemplatesView()
            with TabPane("4 Settings", id="settings"):
                yield SettingsView()
        yield SSLStatusBar()

    def action_show_tab(self, tab: str) -> None:
        self.query_one(TabbedContent).active = tab
```

### Pattern 5: Disconnect Overlay (ModalScreen)

```python
# Source: https://textual.textualize.io/guide/screens/
from textual.screen import ModalScreen

class DisconnectOverlay(ModalScreen):
    """Full-screen overlay shown when console connection is lost."""

    DEFAULT_CSS = """
    DisconnectOverlay {
        align: center middle;
    }
    #overlay-box {
        width: 60;
        height: 9;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    """

    def __init__(self, attempt: int = 0) -> None:
        super().__init__()
        self.attempt = attempt

    def compose(self) -> ComposeResult:
        with Vertical(id="overlay-box"):
            yield Label("DISCONNECTED", id="title")
            yield Label(f"Reconnecting... attempt {self.attempt}")
            yield Label("Press Ctrl+Q to quit")

# To show:
self.push_screen(DisconnectOverlay(attempt=n))
# To dismiss when reconnected:
self.pop_screen()
```

The watchdog thread detects disconnect and posts a `ConsoleOffline` message; reconnect posts `ConsoleOnline`. The app handles both to push/pop the overlay.

### Pattern 6: Command Palette Provider

```python
# Source: https://textual.textualize.io/guide/command_palette/
from textual.command import Hit, Hits, Provider

class ConsoleCmdProvider(Provider):
    """Maps console commands to command palette actions."""

    COMMANDS = {
        "channels": ("List channels", _action_channels),
        "layers": ("Show DAW layers", _action_layers),
        "template save": ("Save session template", _action_template_save),
        "template load": ("Load session template", _action_template_load),
        "rename <ch> <name>": ("Rename channel", _action_rename),
        # ... etc
    }

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        for cmd, (description, callback) in self.COMMANDS.items():
            score = matcher.match(cmd)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(cmd),
                    callback,
                    help=description,
                )

class SSLApp(App):
    COMMANDS = App.COMMANDS | {ConsoleCmdProvider}
```

**Note on `:` / `/` triggering the palette:** Textual's default palette opens on `ctrl+p`. To open on `:` or `/`, add key bindings that call `action_command_palette`:
```python
BINDINGS = [
    (":", "command_palette", "Command palette"),
    ("/", "command_palette", "Command palette"),
]
```

### Pattern 7: SSL Custom Theme

```python
# Source: https://textual.textualize.io/guide/design/
from textual.theme import Theme

SSL_THEME = Theme(
    name="ssl-console",
    primary="#4CAF50",       # SSL green (active/healthy)
    secondary="#8D6E63",     # Warm brown (SSL hardware chassis color)
    accent="#FF9800",        # Amber (warning/highlight)
    foreground="#E8E8E8",    # Scribble strip text (near white)
    background="#1A1A1A",    # Dark matte (console surface)
    surface="#2D2D2D",       # Strip background
    panel="#3A3A3A",         # Slightly lighter panel
    success="#4CAF50",       # Green health dot
    warning="#FFC107",       # Yellow health dot
    error="#F44336",         # Red health dot / disconnect
    dark=True,
)

class SSLApp(App):
    def on_mount(self) -> None:
        self.register_theme(SSL_THEME)
        self.theme = "ssl-console"
        self.client.connect()
        # ... request sync
```

### Pattern 8: Channel Strip Layout

The hardware has 16 channels in a horizontal row, each with a name label ("scribble strip"). In Textual:

```tcss
/* ssl_theme.tcss */
ChannelView {
    layout: horizontal;
    overflow-x: auto;
    height: 1fr;
}

ChannelStrip {
    width: 10;
    height: 100%;
    border: tall $surface;
    padding: 0 1;
    background: $surface;
    layout: vertical;
    content-align: center top;
}

ChannelStrip.highlighted {
    background: $accent 30%;
    border: tall $accent;
}

ChannelStrip > .strip-name {
    color: $primary;
    text-style: bold;
    content-align: center middle;
    height: 3;
    background: $panel;
}
```

### Anti-Patterns to Avoid

- **Setting reactive attributes from the recv thread:** Will cause race conditions or silent failures. Always use `post_message`.
- **Calling `call_from_thread` from inside a dispatch handler:** The lock is held at that point. Never schedule `call_from_thread` while holding `_lock`.
- **Polling a timer to read `ConsoleState`:** Creates lock contention and stale reads. Use the push-message pattern instead.
- **Rebuilding widgets on every update:** Mutate reactive attributes, not the widget tree. Widget tree rebuilds via `recompose=True` should be reserved for structural changes.
- **One global `on_state_changed` callback:** The callback fires for every packet. Keep snapshot extraction minimal — only copy fields the TUI actually displays.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Command palette search | Custom fuzzy-match input widget | `Provider` + `self.matcher(query)` | Textual's built-in fuzzy matcher handles scoring and highlight markup |
| Tab switching | Manual show/hide of widgets | `TabbedContent` + `TabPane` | Handles focus, animation, accessibility |
| Disconnect overlay | Manually z-ordering widgets | `ModalScreen` | Handles input blocking and background dimming automatically |
| Flash animation | Background thread with sleep | `set_timer` or `animate()` | Textual's timer runs in the async loop, no threading needed |
| Color theme | Hard-coded ANSI escape codes | `Theme` class + TCSS variables | Textual handles 256-color/true-color fallback automatically |
| CSS file loading | Dynamic string concatenation | `CSS_PATH = "ssl_theme.tcss"` | Textual watches the file in `--dev` mode for live editing |

**Key insight:** The hardest part of this phase is the thread bridge, not the UI. Everything else is standard Textual composition. Invest in getting the `post_message` pattern right and the rest follows.

---

## Common Pitfalls

### Pitfall 1: Lock Held When Posting Message
**What goes wrong:** Code calls `post_message` while still inside `with self._lock:` — the message handler tries to acquire the lock to read state, deadlocking.
**Why it happens:** The dispatch handler holds `_lock` for the entire handler body. `post_message` itself doesn't block (it's a queue enqueue), but the *handler* that fires on the other side will need the lock to read `ConsoleState`.
**How to avoid:** Extract the snapshot before or after releasing the lock. Release the lock, then post the message. Or extract state into a plain dict inside the lock, then call `post_message` outside.
**Warning signs:** App freezes on the first UDP packet received after TUI launches.

### Pitfall 2: Textual API Not Thread-Safe (Except post_message)
**What goes wrong:** Calling `widget.update()`, `self.app.query_one()`, or setting reactive attributes directly from the recv thread causes "RuntimeError: Event loop is closed" or silent corruption.
**Why it happens:** Textual's DOM is single-threaded; only `post_message` is explicitly thread-safe.
**How to avoid:** All widget mutations go through message handlers in the async loop. The recv thread is only a message producer.
**Warning signs:** Intermittent crashes or incorrect widget state that doesn't match console state.

### Pitfall 3: Command Palette `:` / `/` Binding Conflicts
**What goes wrong:** `:` and `/` are not bound by default in Textual. If a focused widget (like an input) intercepts those keys first, the palette never opens.
**Why it happens:** Key events are dispatched to the focused widget before bubbling to the app.
**How to avoid:** Use `priority=True` on the binding or ensure the command palette bindings are placed at the app level, not on any input widget. Test with no widget focused (click on background).
**Warning signs:** Pressing `:` in the channel view types a colon somewhere instead of opening the palette.

### Pitfall 4: Snapshot Extraction Creates Lock Contention
**What goes wrong:** The `_on_state_changed` callback is called after every UDP packet. If snapshot extraction is slow (deep-copies large state), it holds the lock too long and blocks the recv thread.
**Why it happens:** The recv thread processes ~30s heartbeats plus bursts of sync packets. Each packet triggers a snapshot.
**How to avoid:** Extract only the fields the TUI renders. Use shallow copies. For channel names (32 entries), a single list comprehension is fine. Don't deep-copy `XpatchState` unless the XPatch tab is visible.
**Warning signs:** UDP packet loss or console connection instability immediately after launching TUI.

### Pitfall 5: Module Import with Hyphenated Package
**What goes wrong:** `from ssl-matrix-client.tui import SSLApp` fails with `SyntaxError: invalid syntax` because of the hyphen.
**Why it happens:** Python identifiers cannot contain hyphens. The existing code uses the conftest import shim for tests.
**How to avoid:** The new `tui.py` module is inside the `ssl-matrix-client/` package directory, so it imports other modules using relative imports: `from .client import SSLMatrixClient`. It is launched via `python3 -m ssl-matrix-client tui` which goes through `__main__.py` → argparse → `from .tui import SSLApp; SSLApp(...).run()`. Tests add `ssl_matrix_client.tui` to conftest shim.
**Warning signs:** `ModuleNotFoundError` or `SyntaxError` when trying to import `tui.py` in tests.

### Pitfall 6: `__main__.py` Argparse Restructure
**What goes wrong:** Adding `tui` as a subcommand breaks the existing one-shot command syntax (`channels`, `layers`, etc.).
**Why it happens:** `tui` looks like a positional arg to the existing parser, which already takes `command` as `nargs='*'`.
**How to avoid:** Add a simple string check before argparse dispatch, or use subparsers. Simplest: check `sys.argv[1] == 'tui'` before the existing `main()` parse path. No argparse subparsers needed — `tui` takes no sub-arguments.
**Warning signs:** `python3 -m ssl-matrix-client tui` opens the REPL and tries to run "tui" as a REPL command.

---

## Code Examples

Verified patterns from official Textual 8.1.1 documentation:

### Custom Message for Thread Bridge
```python
# Source: https://textual.textualize.io/guide/events/
class SSLApp(App):
    class StateUpdated(Message):
        """Posted by recv thread after each UDP packet dispatch."""
        def __init__(self, snapshot: dict) -> None:
            self.snapshot = snapshot
            super().__init__()

    class ConsoleOnline(Message):
        """Posted when desk comes online or reconnects."""

    class ConsoleOffline(Message):
        """Posted when watchdog detects disconnect."""
        def __init__(self, attempt: int) -> None:
            self.attempt = attempt
            super().__init__()
```

### Registering SSL Theme
```python
# Source: https://textual.textualize.io/guide/design/
from textual.theme import Theme

SSL_THEME = Theme(
    name="ssl-console",
    primary="#4CAF50",
    secondary="#8D6E63",
    accent="#FF9800",
    foreground="#E8E8E8",
    background="#1A1A1A",
    surface="#2D2D2D",
    panel="#3A3A3A",
    success="#4CAF50",
    warning="#FFC107",
    error="#F44336",
    dark=True,
)
```

### TabbedContent with Number Key Switching
```python
# Source: https://textual.textualize.io/widgets/tabbed_content/
BINDINGS = [
    ("1", "show_tab('channels')", "Channels"),
    ("2", "show_tab('routing')", "Routing"),
    ("3", "show_tab('templates')", "Templates"),
    ("4", "show_tab('settings')", "Settings"),
    (":", "command_palette", "Commands"),
    ("/", "command_palette", "Commands"),
]

def action_show_tab(self, tab: str) -> None:
    self.query_one(TabbedContent).active = tab
```

### Command Palette Provider Registration
```python
# Source: https://textual.textualize.io/guide/command_palette/
class SSLApp(App):
    COMMANDS = App.COMMANDS | {ConsoleCmdProvider}
```

### Channel Strip with Flash
```python
# Source: https://textual.textualize.io/guide/reactivity/
class ChannelStrip(Static):
    channel_name: reactive[str] = reactive("", init=False)
    highlighted: reactive[bool] = reactive(False)

    def watch_channel_name(self, old: str, new: str) -> None:
        if old != new and old != "":
            self.flash_highlight()
        self._refresh_content()

    def flash_highlight(self) -> None:
        self.highlighted = True
        self.set_timer(1.5, self._clear_highlight)

    def _clear_highlight(self) -> None:
        self.highlighted = False
```

### ModalScreen Disconnect Overlay
```python
# Source: https://textual.textualize.io/guide/screens/
from textual.screen import ModalScreen

class DisconnectOverlay(ModalScreen):
    DEFAULT_CSS = """
    DisconnectOverlay { align: center middle; background: $background 70%; }
    #box { width: 50; height: 7; border: thick $error; background: $surface; padding: 1 2; }
    """
    def __init__(self, attempt: int = 0) -> None:
        super().__init__()
        self.attempt = attempt

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Label("[bold $error]DISCONNECTED[/]")
            yield Label(f"Reconnecting... attempt {self.attempt}")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `post_message_no_wait` | `post_message` (unified) | Textual 0.14.0 | No `await` needed, simpler threading code |
| `Select.BLANK` | `Select.NULL` | Textual 8.0.0 (Feb 2026) | Avoid using `.BLANK` — use `.NULL` |
| `thread=True` needed on `@work` | Still required | 0.31.0+ | Always set `thread=True` for threaded workers if using `@work` decorator |
| Themes as CSS variables only | `Theme` Python class | ~0.75.0 | Full theme objects with auto-generated shades |

**Deprecated/outdated:**
- `call_from_thread`: Still valid but `post_message` is cleaner for the recv-thread pattern — avoids scheduling complexity. Use `post_message` as primary bridge.
- Old `@on(TabbedContent.TabActivated)` pattern: Still works, but direct `active` reactive assignment is simpler for programmatic control.

---

## Open Questions

1. **How to hook into SSLMatrixClient without modifying its core loop**
   - What we know: `_recv_loop` is a private daemon thread. Adding `_on_state_changed: Callable | None` is a one-liner addition that is backward-compatible.
   - What's unclear: Should the hook fire for every packet (including ACKs with no visible state change) or only after a curated set of message codes?
   - Recommendation: Fire after every dispatch; keep snapshot extraction minimal (only fields the TUI renders). The overhead is a dict construction per packet, which is negligible.

2. **Watchdog integration: how does the TUI know when disconnect/reconnect happens?**
   - What we know: `_watchdog_loop` sets `state.desk.online = False` before reconnect attempts and `_on_desk_came_online` fires after recovery.
   - What's unclear: The same `_on_state_changed` hook will fire when `desk.online` flips — the TUI can detect this from the snapshot. Alternatively, add `_on_desk_offline` and `_on_desk_online` hooks.
   - Recommendation: Use two separate callbacks (`_on_desk_offline`, `_on_desk_online`) rather than inferring from the snapshot — clearer intent, less ambiguity in snapshot diffing.

3. **conftest.py shim for tui.py**
   - What we know: Tests use `importlib.import_module("ssl-matrix-client.tui")` and register as `ssl_matrix_client.tui`.
   - What's unclear: Textual's `run_test()` requires `pytest-asyncio`. Whether existing `pyproject.toml` dev deps include it needs checking.
   - Recommendation: Add `pytest-asyncio` and `pytest-textual-snapshot` (for snapshot tests) to dev deps. Update conftest shim for `tui`, `tui_widgets`, `tui_commands`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `python3 -m pytest tests/test_tui.py -x -v` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements (Proposed)

Since no requirement IDs were assigned yet, the following TUI-01 through TUI-10 IDs are proposed:

| ID | Behavior | Test Type | Automated Command | File Exists? |
|----|----------|-----------|-------------------|-------------|
| TUI-01 | `tui` subcommand launches app without error | smoke | `pytest tests/test_tui.py::test_app_launches -x` | Wave 0 |
| TUI-02 | Channels tab shows channel names from ConsoleState | unit | `pytest tests/test_tui.py::test_channel_view_renders -x` | Wave 0 |
| TUI-03 | Status bar shows health dot and project name | unit | `pytest tests/test_tui.py::test_status_bar -x` | Wave 0 |
| TUI-04 | Number keys 1-4 switch tabs | unit | `pytest tests/test_tui.py::test_tab_switching -x` | Wave 0 |
| TUI-05 | Command palette opens on `:` keypress | unit | `pytest tests/test_tui.py::test_command_palette_opens -x` | Wave 0 |
| TUI-06 | recv thread state update reaches widget via post_message | unit | `pytest tests/test_tui.py::test_thread_bridge -x` | Wave 0 |
| TUI-07 | Channel name change triggers flash highlight | unit | `pytest tests/test_tui.py::test_flash_highlight -x` | Wave 0 |
| TUI-08 | Disconnect overlay appears when desk goes offline | unit | `pytest tests/test_tui.py::test_disconnect_overlay -x` | Wave 0 |
| TUI-09 | Overlay dismisses when desk comes back online | unit | `pytest tests/test_tui.py::test_reconnect_overlay_dismissed -x` | Wave 0 |
| TUI-10 | SSL theme is applied (custom colors present) | unit | `pytest tests/test_tui.py::test_ssl_theme -x` | Wave 0 |

**Note on APP-01/02/03:** The REQUIREMENTS.md maps APP-01 (native macOS dock app), APP-02 (all CLI features via GUI), and APP-03 (launch-at-login) to Phase 5. However, Phase 5 is a terminal UI, not a dock application — those are Phase 6 goals. The TUI directly delivers APP-02 (all CLI features via command palette), partially satisfies APP-01 as a first-class GUI, and does not address APP-03 (launch-at-login is out of scope for TUI).

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_tui.py -x -v`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_tui.py` — all TUI-01 through TUI-10 tests
- [ ] `pytest-asyncio` in dev deps: `pip install pytest-asyncio`
- [ ] conftest.py shim update: register `ssl_matrix_client.tui`, `ssl_matrix_client.tui_widgets`, `ssl_matrix_client.tui_commands`

---

## Sources

### Primary (HIGH confidence)
- [Textual PyPI](https://pypi.org/project/textual/) — confirmed 8.1.1 current as of 2026-03-10
- [Textual Events Guide](https://textual.textualize.io/guide/events/) — custom Message, post_message thread safety
- [Textual Reactivity Guide](https://textual.textualize.io/guide/reactivity/) — reactive descriptor, watch methods
- [Textual Command Palette Guide](https://textual.textualize.io/guide/command_palette/) — Provider, Hit, search(), discover()
- [Textual Screens Guide](https://textual.textualize.io/guide/screens/) — ModalScreen, push_screen, dismiss
- [Textual Animation Guide](https://textual.textualize.io/guide/animation/) — styles.animate(), set_timer pattern
- [Textual TabbedContent Widget](https://textual.textualize.io/widgets/tabbed_content/) — TabbedContent, TabPane, active reactive
- [Textual Design/Themes Guide](https://textual.textualize.io/guide/design/) — Theme class, register_theme, base colors
- [Textual App Guide](https://textual.textualize.io/guide/app/) — App class, on_mount, BINDINGS, CSS_PATH
- [Textual Workers Guide](https://textual.textualize.io/guide/workers/) — call_from_thread, thread=True
- [Textual GitHub Releases](https://github.com/Textualize/textual/releases) — 8.0.0 breaking change (Select.BLANK → Select.NULL)

### Secondary (MEDIUM confidence)
- [Textual Testing Guide](https://textual.textualize.io/guide/testing/) — run_test(), Pilot, pytest-asyncio requirement
- [Textual 0.37.0 Command Palette Blog](https://textual.textualize.io/blog/2023/09/15/textual-0370-adds-a-command-palette/) — original palette introduction

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — version pinned from PyPI, API from official docs
- Architecture: HIGH — threading pattern verified from events/workers guides; ModalScreen from screens guide
- Pitfalls: HIGH for threading (documented); MEDIUM for `:` binding (inferred from key event model)
- Theme colors: MEDIUM — SSL palette is proposed by researcher (not sourced from official SSL documentation)

**Research date:** 2026-03-14
**Valid until:** 2026-06-14 (Textual is actively developed; check for 9.x before planning if > 30 days pass)
