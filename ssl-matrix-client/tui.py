"""SSL Matrix Console TUI — Textual application shell.

Provides:
- SSLApp(App): tabbed layout with SSL theme, keyboard navigation, thread bridge
- SSLStatusBar(Static): health dot, project info, last loaded template, tab hints
- StateUpdated/ConsoleOnline/ConsoleOffline: message types for recv-thread bridge
- main(argv): entry point for `python3 -m ssl-matrix-client tui`
"""

import argparse
from typing import ClassVar, Optional

from textual.app import App, ComposeResult
from textual.message import Message
from textual.theme import Theme
from textual.widgets import Static, TabbedContent, TabPane

from .client import SSLMatrixClient
from .tui_commands import ConsoleCmdProvider
from .tui_views import RoutingView, SettingsView, TemplatesView
from .tui_widgets import ChannelView, DisconnectOverlay

# SSL-inspired dark theme
SSL_THEME = Theme(
    name="ssl-console",
    dark=True,
    primary="#4CAF50",  # SSL green
    secondary="#8D6E63",  # warm brown
    accent="#FF9800",  # amber
    foreground="#E8E8E8",
    background="#1A1A1A",
    surface="#2D2D2D",
    panel="#3A3A3A",
    success="#4CAF50",
    warning="#FFC107",
    error="#F44336",
)

# Health dot thresholds (seconds)
_HEALTH_GREEN_THRESHOLD = 15.0
_HEALTH_YELLOW_THRESHOLD = 35.0


class SSLStatusBar(Static):
    """Persistent footer bar: health dot, project info, last template, tab hints."""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self._health = "red"
        self._project_info = ""
        self._template_info = ""
        self._hint_text = "1-4:Tabs  /:Commands  q:Quit"

    def render(self) -> str:
        """Render Rich markup with health dot, project, template, and hints."""
        dot_color = {
            "green": "green",
            "yellow": "yellow",
            "red": "red",
        }.get(self._health, "red")

        dot = f"[{dot_color}]●[/{dot_color}]"
        project = f" {self._project_info}" if self._project_info else " —"

        template_part = ""
        if self._template_info:
            template_part = f"  [dim]Template:[/dim] {self._template_info}"

        hints = f"[dim]{self._hint_text}[/dim]"

        left = f"{dot}{project}{template_part}"
        return f"{left}  {hints}"

    def update_from(self, snapshot: dict) -> None:
        """Update status bar from a StateUpdated snapshot dict."""
        age = snapshot.get("heartbeat_age", float("inf"))
        if age < _HEALTH_GREEN_THRESHOLD:
            self._health = "green"
        elif age < _HEALTH_YELLOW_THRESHOLD:
            self._health = "yellow"
        else:
            self._health = "red"

        project = snapshot.get("project_name", "")
        title = snapshot.get("title_name", "")
        if project and title:
            self._project_info = f"{project}/{title}"
        elif project:
            self._project_info = project
        else:
            self._project_info = ""

        self._template_info = snapshot.get("last_template", "")
        self.refresh()

    def set_hints_for_tab(self, tab_id: str) -> None:
        """Update keyboard hint text for the active tab."""
        # All tabs share the same base hints for now; infrastructure is here
        # for per-tab additions (e.g. scroll keys) in later plans.
        tab_hints = {
            "channels": "1-4:Tabs  /:Commands  q:Quit",
            "routing": "1-4:Tabs  /:Commands  q:Quit",
            "templates": "1-4:Tabs  /:Commands  q:Quit",
            "settings": "1-4:Tabs  /:Commands  q:Quit",
        }
        self._hint_text = tab_hints.get(tab_id, "1-4:Tabs  /:Commands  q:Quit")
        self.refresh()


class SSLApp(App):
    """SSL Matrix Console TUI application."""

    CSS_PATH = "ssl_theme.tcss"
    TITLE = "SSL Matrix Console"
    COMMANDS: ClassVar[set] = App.COMMANDS | {ConsoleCmdProvider}
    BINDINGS: ClassVar[list] = [
        ("1", "show_tab('channels')", "Channels"),
        ("2", "show_tab('routing')", "Routing"),
        ("3", "show_tab('templates')", "Templates"),
        ("4", "show_tab('settings')", "Settings"),
        ("colon", "command_palette", "Commands"),
        ("/", "command_palette", "Commands"),
        ("q", "quit", "Quit"),
    ]

    # --- Message types for the recv-thread → Textual event loop bridge ---

    class StateUpdated(Message):
        """Posted from recv thread (via post_message) when console state changes."""

        def __init__(self, snapshot: dict) -> None:
            super().__init__()
            self.snapshot = snapshot

    class ConsoleOnline(Message):
        """Posted when console comes back online after reconnect."""

    class ConsoleOffline(Message):
        """Posted when console goes offline; includes reconnect attempt count."""

        def __init__(self, attempt: int) -> None:
            super().__init__()
            self.attempt = attempt

    # --- App lifecycle ---

    def __init__(self, console_ip: str = "192.168.1.2", **kwargs):
        super().__init__(**kwargs)
        self.client = SSLMatrixClient(console_ip)
        self._last_template = ""
        self._disconnect_overlay: Optional[DisconnectOverlay] = None

    def compose(self) -> ComposeResult:
        """Build the tabbed layout with status bar docked at bottom."""
        with TabbedContent(initial="channels"):
            with TabPane("1 Channels", id="channels"):
                yield ChannelView()
            with TabPane("2 Routing", id="routing"):
                yield RoutingView()
            with TabPane("3 Templates", id="templates"):
                yield TemplatesView()
            with TabPane("4 Settings", id="settings"):
                yield SettingsView()
        yield SSLStatusBar(id="status-bar")

    def action_show_tab(self, tab: str) -> None:
        """Switch to a named tab and update status bar hints."""
        self.query_one(TabbedContent).active = tab
        self.query_one(SSLStatusBar).set_hints_for_tab(tab)

    def on_mount(self) -> None:
        """Register SSL theme, wire client hooks, connect, and start initial sync."""
        self.register_theme(SSL_THEME)
        self.theme = "ssl-console"

        # Wire thread-bridge callbacks (set here so SSLApp owns the lifecycle)
        self.client._on_state_changed = self._on_state_changed_hook
        self.client._on_desk_offline = self._on_desk_offline_hook
        self.client._on_desk_online = self._on_desk_online_hook

        self.client.connect()
        self.run_worker(self._initial_sync, thread=True)

        # Set initial tab hints
        self.query_one(SSLStatusBar).set_hints_for_tab("channels")

    def _initial_sync(self) -> None:
        """Wait for console to come online then request full state sync."""
        if self.client.wait_online(timeout=10):
            self.client.request_sync()

    # --- Thread bridge: recv thread → Textual event loop ---

    def _on_state_changed_hook(self) -> None:
        """Called from recv thread OUTSIDE the lock. Extract snapshot and post message."""
        with self.client._lock:
            snapshot = {
                "online": self.client.state.desk.online,
                "heartbeat_age": self.client.state.desk.heartbeat_age,
                "project_name": self.client.state.project_name,
                "title_name": self.client.state.title_name,
                "channels": [(ch.number, ch.name) for ch in self.client.state.channels],
                "daw_layers": [
                    (dl.number, dl.protocol, dl.profile_name) for dl in self.client.state.daw_layers
                ],
                "automation_mode": self.client.state.automation_mode,
                "synced": self.client.state.synced,
                "channel_inserts": [
                    (ci.channel, ci.chain_name, list(ci.inserts), ci.has_stereo)
                    for ci in self.client.state.channel_inserts
                ],
                "last_template": self._last_template,
                # Secondary view fields
                "devices": [(d.number, d.name, d.is_assigned) for d in self.client.state.devices],
                "console_name": self.client.state.desk.console_name,
                "firmware": self.client.state.desk.firmware,
                "motors_off": getattr(self.client.state, "motors_off", False),
                "mdac_meters": getattr(self.client.state, "mdac_meters", False),
                "split_config": self.client.get_split(),
            }
        self.post_message(self.StateUpdated(snapshot))

    def _on_desk_offline_hook(self, attempt: int) -> None:
        """Called from watchdog thread when console goes offline."""
        self.post_message(self.ConsoleOffline(attempt))

    def _on_desk_online_hook(self) -> None:
        """Called from recv thread when console comes back online."""
        self.post_message(self.ConsoleOnline())

    # --- Message handlers ---

    def on_ssl_app_state_updated(self, msg: "SSLApp.StateUpdated") -> None:
        """Handle StateUpdated: push snapshot into status bar, channel view, and secondary views."""
        self.query_one(SSLStatusBar).update_from(msg.snapshot)
        for channel_view in self.query(ChannelView):
            channel_view.update_from(msg.snapshot)
        for view_cls in (RoutingView, SettingsView):
            view = self.query_one(view_cls, default=None)
            if view is not None:
                view.update_from(msg.snapshot)

    def on_ssl_app_console_offline(self, msg: "SSLApp.ConsoleOffline") -> None:
        """Handle ConsoleOffline: push disconnect overlay or update attempt count."""
        if self._disconnect_overlay is not None:
            self._disconnect_overlay.update_attempt(msg.attempt)
        else:
            overlay = DisconnectOverlay(attempt=msg.attempt)
            self._disconnect_overlay = overlay
            self.push_screen(overlay)

    def on_ssl_app_console_online(self, _msg: "SSLApp.ConsoleOnline") -> None:
        """Handle ConsoleOnline: dismiss disconnect overlay if showing."""
        if self._disconnect_overlay is not None:
            self.pop_screen()
            self._disconnect_overlay = None

    def on_unmount(self) -> None:
        """Disconnect client on app exit."""
        self.client.disconnect()


def main(argv=None) -> None:
    """Entry point for `python3 -m ssl-matrix-client tui [--ip IP]`."""
    parser = argparse.ArgumentParser(
        prog="ssl-matrix-client tui",
        description="SSL Matrix Console TUI",
    )
    parser.add_argument(
        "--ip",
        default="192.168.1.2",
        help="Console IP address (default: 192.168.1.2)",
    )
    args = parser.parse_args(argv)
    app = SSLApp(console_ip=args.ip)
    app.run()
