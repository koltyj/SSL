"""Total Recall snapshots panel widget."""

from textual.widgets import Static, DataTable


class TotalRecallPanel(Static):
    """TR snapshot list."""

    DEFAULT_CSS = """
    TotalRecallPanel {
        height: auto;
        padding: 0 1;
    }
    TotalRecallPanel > DataTable {
        height: auto;
        max-height: 14;
    }
    TotalRecallPanel > .tr-header {
        height: 1;
        color: #aaaaaa;
        text-style: bold;
    }
    """

    def __init__(self):
        super().__init__()
        self._table = None
        self._header = None

    def compose(self):
        self._header = Static("Total Recall: ---", classes="tr-header")
        yield self._header

        table = DataTable()
        table.add_columns("#", "Name", "Date", "Time", "Sel")
        self._table = table
        yield table

    def update_state(self, snapshot):
        if self._header:
            en = "Enabled" if snapshot.tr_enabled else "Disabled"
            self._header.update(f"Total Recall: {en}")

        if self._table:
            self._table.clear()
            for i, t in enumerate(snapshot.tr_snapshots):
                sel = "*" if t.is_selected else ""
                self._table.add_row(str(i), t.name, t.date_str, t.time_str, sel)
