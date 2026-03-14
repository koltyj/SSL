"""Insert matrix panel widget."""

from textual.widgets import Static, DataTable
from textual.containers import Vertical


class InsertMatrixPanel(Static):
    """Insert devices, chains, and channel routing."""

    DEFAULT_CSS = """
    InsertMatrixPanel {
        height: auto;
        padding: 0 1;
    }
    InsertMatrixPanel > Vertical > DataTable {
        height: auto;
        max-height: 14;
    }
    InsertMatrixPanel > Vertical > .section-label {
        height: 1;
        color: #aaaaaa;
        text-style: bold;
        margin-top: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._dev_table = None
        self._chan_table = None

    def compose(self):
        with Vertical():
            yield Static("Devices", classes="section-label")
            dev_table = DataTable()
            dev_table.add_columns("#", "Name", "Asgn", "Stereo")
            self._dev_table = dev_table
            yield dev_table

            yield Static("Channel Routing", classes="section-label")
            chan_table = DataTable()
            chan_table.add_columns("Ch", "Chain", "Inserts", "Stereo")
            self._chan_table = chan_table
            yield chan_table

    def update_state(self, snapshot):
        if self._dev_table:
            self._dev_table.clear()
            for d in snapshot.devices:
                if d.name:
                    asgn = "Y" if d.is_assigned else ""
                    stereo = "Y" if d.is_stereo else ""
                    self._dev_table.add_row(str(d.number), d.name, asgn, stereo)

        if self._chan_table:
            self._chan_table.clear()
            for ci in snapshot.channel_inserts:
                chain = ci.chain_name or ""
                inserts = ", ".join(str(i) for i in ci.inserts) if ci.inserts else ""
                stereo = "Y" if ci.has_stereo else ""
                self._chan_table.add_row(str(ci.channel), chain, inserts, stereo)
