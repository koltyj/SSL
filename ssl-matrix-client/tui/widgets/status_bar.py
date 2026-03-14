"""Connection status bar widget."""

from textual.widgets import Static


PROTOCOL_NAMES = {0: "None", 1: "HUI", 2: "MCU", 3: "CC"}


class ConnectionStatus(Static):
    """Top bar showing console connection status."""

    DEFAULT_CSS = """
    ConnectionStatus {
        height: 3;
        content-align: center middle;
        text-style: bold;
        padding: 0 2;
    }
    ConnectionStatus.online {
        background: #1a5c1a;
        color: #ffffff;
    }
    ConnectionStatus.offline {
        background: #5c1a1a;
        color: #cccccc;
    }
    ConnectionStatus.stale {
        background: #5c4a1a;
        color: #ffffff;
    }
    """

    def __init__(self):
        super().__init__("SSL Matrix Dashboard - Disconnected")
        self.add_class("offline")

    def update_state(self, snapshot):
        desk = snapshot.desk
        if not desk or not desk.online:
            self.update("SSL Matrix Dashboard - Disconnected")
            self.remove_class("online", "stale")
            self.add_class("offline")
            return

        hb = desk.heartbeat_age
        if hb == float("inf"):
            hb_str = "---"
        else:
            hb_str = f"{hb:.1f}s"

        project = snapshot.project_name or "(none)"
        title = snapshot.title_name or "(none)"
        mode = "Delta" if snapshot.automation_mode else "Legacy"

        text = (
            f"{desk.product_name} \"{desk.console_name}\"  |  "
            f"FW {desk.firmware}  |  "
            f"HB {hb_str}  |  "
            f"{mode}  |  "
            f"Project: {project} / {title}"
        )
        self.update(text)

        self.remove_class("offline", "online", "stale")
        if hb != float("inf") and hb > 10:
            self.add_class("stale")
        else:
            self.add_class("online")
