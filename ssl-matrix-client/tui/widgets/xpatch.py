"""XPatch routing panel widget."""

from textual.widgets import Static, DataTable
from textual.containers import Vertical


class XPatchPanel(Static):
    """XPatch routing, channels, and presets."""

    DEFAULT_CSS = """
    XPatchPanel {
        height: auto;
        padding: 0 1;
    }
    XPatchPanel > Vertical > DataTable {
        height: auto;
        max-height: 12;
    }
    XPatchPanel > Vertical > .section-label {
        height: 1;
        color: #aaaaaa;
        text-style: bold;
        margin-top: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._route_table = None
        self._chan_table = None
        self._midi_label = None

    def compose(self):
        with Vertical():
            yield Static("Routing", classes="section-label")
            route_table = DataTable()
            route_table.add_columns("Dest", "Source", "Protected")
            self._route_table = route_table
            yield route_table

            yield Static("Channel Setup", classes="section-label")
            chan_table = DataTable()
            chan_table.add_columns("Ch", "Device", "Dest", "In-10", "Out-10", "Mode")
            self._chan_table = chan_table
            yield chan_table

            self._midi_label = Static("MIDI: ---")
            yield self._midi_label

    def update_state(self, snapshot):
        if self._route_table:
            self._route_table.clear()
            for r in snapshot.xpatch_routes:
                prot = "Y" if r.protect else ""
                self._route_table.add_row(str(r.dest), str(r.display_src), prot)

        if self._chan_table:
            self._chan_table.clear()
            for c in snapshot.xpatch_channels:
                i10 = "Y" if c.input_minus_10db else ""
                o10 = "Y" if c.output_minus_10db else ""
                self._chan_table.add_row(
                    str(c.number), c.device_name, c.dest_name, i10, o10, str(c.mode)
                )

        if self._midi_label:
            en = "On" if snapshot.xpatch_midi_enabled else "Off"
            self._midi_label.update(f"MIDI: {en}  Channel: {snapshot.xpatch_midi_channel}")
