"""SSL console TUI — Textual application shell.

Provides:
- SSLApp(App): tabbed layout with SSL theme, keyboard navigation, thread bridge
- SSLStatusBar(Static): health dot, project info, last loaded template, tab hints
- StateUpdated/ConsoleOnline/ConsoleOffline: message types for recv-thread bridge
- main(argv): entry point for `ssl-console tui [--ip IP]`
"""

import argparse
from typing import ClassVar, Optional

from textual.app import App, ComposeResult
from textual.message import Message
from textual.theme import Theme
from textual.widgets import Static, TabbedContent, TabPane

from .client import SSLMatrixClient
from .sigma_client import SSLSigmaClient
from .tui_commands import ConsoleCmdProvider
from .tui_views import (
    RoutingView,
    SettingsView,
    SigmaChannelsView,
    SigmaConsoleView,
    SigmaMonitorView,
    SigmaNotesView,
    TemplatesView,
)
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
        tab_hints = {
            "channels": "1-4:Tabs  /:Commands  q:Quit",
            "routing": "1-4:Tabs  /:Commands  q:Quit",
            "templates": "1-4:Tabs  /:Commands  q:Quit",
            "settings": "1-4:Tabs  /:Commands  q:Quit",
            "monitor": "1-4:Tabs  /:Commands  q:Quit",
            "console": "1-4:Tabs  /:Commands  q:Quit",
            "notes": "1-4:Tabs  /:Commands  q:Quit",
        }
        self._hint_text = tab_hints.get(tab_id, "1-4:Tabs  /:Commands  q:Quit")
        self.refresh()


def _load_css() -> str:
    """Load ssl_theme.tcss from alongside this module file."""
    import pathlib

    css_path = pathlib.Path(__file__).parent / "ssl_theme.tcss"
    return css_path.read_text()


class SSLApp(App):
    """SSL console TUI application."""

    CSS = _load_css()
    TITLE = "SSL Console"
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

    def __init__(self, console_ip: str = "192.168.1.2", console_type: str = "matrix", **kwargs):
        super().__init__(**kwargs)
        self.console_type = console_type
        self.client = (
            SSLSigmaClient(console_ip) if console_type == "sigma" else SSLMatrixClient(console_ip)
        )
        self._last_template = ""
        self._disconnect_overlay: Optional[DisconnectOverlay] = None
        self.selected_channel: Optional[int] = None

    def compose(self) -> ComposeResult:
        """Build the tabbed layout with status bar docked at bottom."""
        with TabbedContent(initial="channels"):
            if self.console_type == "sigma":
                with TabPane("1 Channels", id="channels"):
                    yield SigmaChannelsView()
                with TabPane("2 Monitor", id="monitor"):
                    yield SigmaMonitorView()
                with TabPane("3 Console", id="console"):
                    yield SigmaConsoleView()
                with TabPane("4 Notes", id="notes"):
                    yield SigmaNotesView()
            else:
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
        if self.console_type == "sigma":
            tab = {
                "channels": "channels",
                "monitor": "monitor",
                "console": "console",
                "notes": "notes",
                "routing": "monitor",
                "templates": "console",
                "settings": "notes",
            }.get(tab, tab)
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

        self.do_connect()

        # Set initial tab hints
        self.query_one(SSLStatusBar).set_hints_for_tab("channels")

    def do_connect(self) -> None:
        """Connect to console, wire hooks, and start initial sync."""
        if self.client._running:
            self.notify("Already connected", severity="warning")
            return
        self.client._on_state_changed = self._on_state_changed_hook
        self.client._on_desk_offline = self._on_desk_offline_hook
        self.client._on_desk_online = self._on_desk_online_hook
        self.client.connect()
        self.run_worker(self._initial_sync, thread=True)
        self.notify("Connecting...")

    def do_disconnect(self) -> None:
        """Disconnect from console and update UI to reflect offline state."""
        if not self.client._running:
            self.notify("Not connected", severity="warning")
            return
        self.client.disconnect()
        # Force status bar to red/disconnected since recv thread is gone
        status_bar = self.query_one(SSLStatusBar)
        status_bar._health = "red"
        status_bar._project_info = "DISCONNECTED"
        status_bar.refresh()
        self.notify("Disconnected")

    def _initial_sync(self) -> None:
        """Wait for console to come online then request full state sync."""
        if self.client.wait_online(timeout=10) and hasattr(self.client, "request_sync"):
            self.client.request_sync()

    # --- Thread bridge: recv thread → Textual event loop ---

    def _on_state_changed_hook(self) -> None:
        """Called from recv thread OUTSIDE the lock. Extract snapshot and post message."""
        try:
            with self.client._lock:
                if self.console_type == "sigma":
                    snapshot = {
                        "online": self.client.state.online,
                        "heartbeat_age": self.client.state.heartbeat_age,
                        "project_name": "Sigma",
                        "title_name": self.client.state.console_ip or "",
                        "console_ip": self.client.state.console_ip,
                        "channels": [
                            {
                                "number": ch.number,
                                "name": ch.name,
                                "fader": ch.fader,
                                "pan": ch.pan,
                                "solo": ch.solo,
                                "mute": ch.mute,
                                "phase": ch.phase,
                            }
                            for ch in self.client.state.channels
                        ],
                        "monitor": {
                            "sources": list(self.client.state.monitor.sources),
                            "dim_level": self.client.state.monitor.dim_level,
                            "secondary_dim": self.client.state.monitor.secondary_dim,
                        },
                        "headphone": {"sources": list(self.client.state.headphone.sources)},
                        "insert": {
                            "insert_a": self.client.state.insert.insert_a,
                            "insert_b": self.client.state.insert.insert_b,
                            "insert_a_sum": self.client.state.insert.insert_a_sum,
                            "insert_b_sum": self.client.state.insert.insert_b_sum,
                        },
                        "level": {
                            "meter_mode": self.client.state.level.meter_mode,
                            "level_value": self.client.state.level.level_value,
                            "level_fader": self.client.state.level.level_fader,
                        },
                        "misc": {
                            "talkback_mode": self.client.state.misc.talkback_mode,
                            "oscillator": self.client.state.misc.oscillator,
                            "listenback": self.client.state.misc.listenback,
                            "connection_status": self.client.state.misc.connection_status,
                            "daw_control": self.client.state.misc.daw_control,
                        },
                        "network": {
                            "master_slave": self.client.state.network.master_slave,
                            "ip": ".".join(str(o) for o in self.client.state.network.ip_octets),
                            "subnet": ".".join(
                                str(o) for o in self.client.state.network.subnet_octets
                            ),
                        },
                        "last_template": self._last_template,
                    }
                else:
                    snapshot = {
                        "online": self.client.state.desk.online,
                        "heartbeat_age": self.client.state.desk.heartbeat_age,
                        "project_name": getattr(self.client.state, "project_name", ""),
                        "title_name": getattr(self.client.state, "title_name", ""),
                        "channels": [(ch.number, ch.name) for ch in self.client.state.channels],
                        "daw_layers": [
                            (dl.number, dl.protocol, dl.profile_name)
                            for dl in self.client.state.daw_layers
                        ],
                        "automation_mode": getattr(self.client.state, "automation_mode", 0),
                        "synced": getattr(self.client.state, "synced", False),
                        "channel_inserts": [
                            (ci.channel, ci.chain_name, list(ci.inserts), ci.has_stereo)
                            for ci in self.client.state.channel_inserts
                        ],
                        "last_template": self._last_template,
                        "devices": [
                            (d.number, d.name, d.is_assigned)
                            for d in getattr(self.client.state, "devices", [])
                        ],
                        "num_channels": len(self.client.state.channels),
                        "console_name": self.client.state.desk.console_name,
                        "firmware": self.client.state.desk.firmware,
                        "motors_off": getattr(self.client.state, "motors_off", False),
                        "mdac_meters": getattr(self.client.state, "mdac_meters", False),
                        "split_config": self.client.get_split(),
                    }
            self.post_message(self.StateUpdated(snapshot))
        except Exception:
            import logging

            logging.getLogger(__name__).exception("state_changed_hook error")

    def _on_desk_offline_hook(self, attempt: int) -> None:
        """Called from watchdog thread when console goes offline."""
        try:
            self.post_message(self.ConsoleOffline(attempt))
        except Exception:
            pass

    def _on_desk_online_hook(self) -> None:
        """Called from recv thread when console comes back online."""
        try:
            self.post_message(self.ConsoleOnline())
        except Exception:
            pass

    # --- Message handlers ---

    def on_sslapp_state_updated(self, msg: "SSLApp.StateUpdated") -> None:
        """Handle StateUpdated: push snapshot into status bar, channel view, and secondary views."""
        self.query_one(SSLStatusBar).update_from(msg.snapshot)
        if self.console_type == "sigma":
            for view_cls in (SigmaChannelsView, SigmaMonitorView, SigmaConsoleView):
                try:
                    self.query_one(view_cls).update_from(msg.snapshot)
                except Exception:
                    pass
        else:
            for channel_view in self.query(ChannelView):
                num_ch = msg.snapshot.get("num_channels", 0)
                if num_ch:
                    channel_view.set_channel_count(num_ch)
                channel_view.update_from(msg.snapshot)
            for view_cls in (RoutingView, SettingsView):
                try:
                    view = self.query_one(view_cls)
                    view.update_from(msg.snapshot)
                except Exception:
                    pass

    def on_channel_strip_selected(self, msg: "ChannelStrip.Selected") -> None:  # noqa: F821
        """Handle channel strip click — select/deselect."""
        if self.console_type == "sigma":
            return
        from .tui_widgets import ChannelStrip

        # Deselect previous
        if self.selected_channel is not None:
            try:
                old = self.query_one(f"#ch-{self.selected_channel}", ChannelStrip)
                old.selected = False
            except Exception:
                pass

        # Toggle if clicking same channel
        if self.selected_channel == msg.channel_num:
            self.selected_channel = None
            return

        # Select new
        self.selected_channel = msg.channel_num
        try:
            new = self.query_one(f"#ch-{msg.channel_num}", ChannelStrip)
            new.selected = True
        except Exception:
            pass
        self.notify(f"Channel {msg.channel_num} selected", severity="information")

    def on_sslapp_console_offline(self, msg: "SSLApp.ConsoleOffline") -> None:
        """Handle ConsoleOffline: push disconnect overlay or update attempt count."""
        if self._disconnect_overlay is not None:
            self._disconnect_overlay.update_attempt(msg.attempt)
        else:
            overlay = DisconnectOverlay(attempt=msg.attempt)
            self._disconnect_overlay = overlay
            self.push_screen(overlay)

    def on_sslapp_console_online(self, _msg: "SSLApp.ConsoleOnline") -> None:
        """Handle ConsoleOnline: dismiss disconnect overlay if showing."""
        if self._disconnect_overlay is not None:
            self.pop_screen()
            self._disconnect_overlay = None

    def on_unmount(self) -> None:
        """Disconnect client on app exit."""
        self.client.disconnect()


def main(argv=None) -> None:
    """Entry point for `ssl-console tui [--ip IP]`."""
    parser = argparse.ArgumentParser(
        prog="ssl-console tui",
        description="SSL Console TUI",
    )
    parser.add_argument(
        "--ip",
        default="192.168.1.2",
        help="Console IP address (default: 192.168.1.2)",
    )
    parser.add_argument(
        "--console",
        choices=["matrix", "sigma"],
        default="matrix",
        help="Console type: matrix (default), sigma",
    )
    args = parser.parse_args(argv)
    app = SSLApp(console_ip=args.ip, console_type=args.console)
    app.run()
