"""SSL Matrix TUI Dashboard — main Textual application."""

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header

from .bridge import StateUpdated, poll_state
from .widgets.status_bar import ConnectionStatus
from .widgets.channels import ChannelGrid
from .widgets.daw_layers import DAWLayersPanel
from .widgets.inserts import InsertMatrixPanel
from .widgets.xpatch import XPatchPanel
from .widgets.project import ProjectInfoPanel
from .widgets.total_recall import TotalRecallPanel


class SSLMatrixApp(App):
    """Full dashboard TUI for SSL Matrix console."""

    CSS_PATH = "matrix.tcss"
    TITLE = "SSL Matrix"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "connect", "Connect"),
        ("d", "disconnect", "Disconnect"),
        ("s", "sync", "Sync"),
    ]

    def __init__(self, console_ip="192.168.1.2", console_port=50081):
        super().__init__()
        self._console_ip = console_ip
        self._console_port = console_port
        self._client = None
        self._poll_task = None

        # Widget references
        self._status_bar = None
        self._channel_grid = None
        self._layers_panel = None
        self._inserts_panel = None
        self._xpatch_panel = None
        self._project_panel = None
        self._tr_panel = None

    def compose(self) -> ComposeResult:
        yield Header()

        self._status_bar = ConnectionStatus()
        yield self._status_bar

        with VerticalScroll(id="main-content"):
            with Horizontal(id="top-row"):
                with Vertical(id="channels-box"):
                    self._channel_grid = ChannelGrid()
                    yield self._channel_grid
                with Vertical(id="layers-box"):
                    self._layers_panel = DAWLayersPanel()
                    yield self._layers_panel

            with Horizontal(id="mid-row"):
                with Vertical(id="inserts-box"):
                    self._inserts_panel = InsertMatrixPanel()
                    yield self._inserts_panel
                with Vertical(id="xpatch-box"):
                    self._xpatch_panel = XPatchPanel()
                    yield self._xpatch_panel

            with Horizontal(id="bottom-row"):
                with Vertical(id="project-box"):
                    self._project_panel = ProjectInfoPanel()
                    yield self._project_panel
                with Vertical(id="tr-box"):
                    self._tr_panel = TotalRecallPanel()
                    yield self._tr_panel

        yield Footer()

    def on_mount(self):
        # Set border titles after mount
        channels_box = self.query_one("#channels-box")
        channels_box.border_title = "Channels (1-32)"
        layers_box = self.query_one("#layers-box")
        layers_box.border_title = "DAW Layers"
        inserts_box = self.query_one("#inserts-box")
        inserts_box.border_title = "Insert Matrix"
        xpatch_box = self.query_one("#xpatch-box")
        xpatch_box.border_title = "XPatch"
        project_box = self.query_one("#project-box")
        project_box.border_title = "Project"
        tr_box = self.query_one("#tr-box")
        tr_box.border_title = "Total Recall"

    def on_state_updated(self, message: StateUpdated):
        """Handle state updates from the bridge poller."""
        snap = message.snapshot
        self._status_bar.update_state(snap)
        self._channel_grid.update_state(snap)
        self._layers_panel.update_state(snap)
        self._inserts_panel.update_state(snap)
        self._xpatch_panel.update_state(snap)
        self._project_panel.update_state(snap)
        self._tr_panel.update_state(snap)

    def action_connect(self):
        """Connect to the console."""
        if self._client:
            self.notify("Already connected", severity="warning")
            return
        self.run_worker(self._do_connect, thread=True)

    def _do_connect(self):
        """Run in worker thread: connect + sync."""
        from ..client import SSLMatrixClient

        client = SSLMatrixClient(console_ip=self._console_ip, port=self._console_port)
        try:
            client.connect()
            if client.wait_online(timeout=5):
                client.request_sync()
                self._client = client
                # Start the poll loop on the main event loop
                self.call_from_thread(self._start_polling)
                self.call_from_thread(self.notify, "Connected and synced")
            else:
                client.disconnect()
                self.call_from_thread(self.notify, "Connection timeout", severity="error")
        except Exception as e:
            try:
                client.disconnect()
            except Exception:
                pass
            self.call_from_thread(self.notify, f"Connection error: {e}", severity="error")

    def _start_polling(self):
        """Start the state polling task (called on main thread)."""
        if self._poll_task:
            self._poll_task.cancel()
        self._poll_task = asyncio.create_task(poll_state(self, self._client))

    def action_disconnect(self):
        """Disconnect from the console."""
        if not self._client:
            self.notify("Not connected", severity="warning")
            return
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        self._client.disconnect()
        self._client = None
        self.notify("Disconnected")

    def action_sync(self):
        """Re-sync all state from console."""
        if not self._client:
            self.notify("Not connected", severity="warning")
            return
        self.run_worker(self._do_sync, thread=True)

    def _do_sync(self):
        """Run in worker thread: request_sync blocks."""
        if self._client:
            self._client.request_sync()
            self.call_from_thread(self.notify, "Sync complete")

    def action_quit(self):
        """Clean shutdown."""
        if self._poll_task:
            self._poll_task.cancel()
        if self._client:
            self._client.disconnect()
        self.exit()
