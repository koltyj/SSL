"""DAW layers panel widget."""

from textual.widgets import Static, DataTable


PROTOCOL_NAMES = {0: "None", 1: "HUI", 2: "MCU", 3: "CC"}


class DAWLayersPanel(Static):
    """Shows 4 DAW layers with protocol and profile."""

    DEFAULT_CSS = """
    DAWLayersPanel {
        height: auto;
        padding: 0 1;
    }
    DAWLayersPanel > DataTable {
        height: auto;
        max-height: 10;
    }
    """

    def __init__(self):
        super().__init__()
        self._table = None

    def compose(self):
        table = DataTable()
        table.add_columns("Layer", "Protocol", "Profile")
        for i in range(1, 5):
            table.add_row(str(i), "---", "---", key=str(i))
        self._table = table
        yield table

    def update_state(self, snapshot):
        if not self._table:
            return
        for dl in snapshot.daw_layers:
            proto = PROTOCOL_NAMES.get(dl.protocol, f"?({dl.protocol})")
            profile = dl.profile_name or "---"
            try:
                self._table.update_cell(str(dl.number), "Protocol", proto)
                self._table.update_cell(str(dl.number), "Profile", profile)
            except Exception:
                pass
