"""Channel names grid widget."""

from textual.widgets import Static
from textual.containers import Grid


class ChannelCell(Static):
    """A single channel cell."""

    DEFAULT_CSS = """
    ChannelCell {
        height: 3;
        content-align: center middle;
        border: solid #444444;
        padding: 0 1;
    }
    ChannelCell.has-name {
        background: #1a3a1a;
    }
    ChannelCell.no-name {
        background: #2a2a2a;
        color: #666666;
    }
    """

    def __init__(self, number, name=""):
        self.chan_number = number
        self.chan_name = name
        display = f"{number:2d} {name}" if name else f"{number:2d}"
        super().__init__(display)
        self.add_class("has-name" if name else "no-name")

    def set_name(self, name):
        if name == self.chan_name:
            return
        self.chan_name = name
        display = f"{self.chan_number:2d} {name}" if name else f"{self.chan_number:2d}"
        self.update(display)
        self.remove_class("has-name", "no-name")
        self.add_class("has-name" if name else "no-name")


class ChannelGrid(Static):
    """32-channel grid display."""

    DEFAULT_CSS = """
    ChannelGrid {
        height: auto;
        padding: 0;
    }
    ChannelGrid > Grid {
        grid-size: 8 4;
        grid-gutter: 0;
        height: auto;
    }
    """

    def __init__(self):
        super().__init__()
        self._cells = {}

    def compose(self):
        with Grid():
            for i in range(1, 33):
                cell = ChannelCell(i)
                self._cells[i] = cell
                yield cell

    def update_state(self, snapshot):
        for ch in snapshot.channels:
            cell = self._cells.get(ch.number)
            if cell:
                cell.set_name(ch.name)
