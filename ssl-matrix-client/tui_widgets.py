"""SSL Matrix Console TUI — reusable widgets.

Provides:
- ChannelStrip(Static): single channel scribble-strip column with reactive attrs
- ChannelView(HorizontalScroll): 16 ChannelStrip widgets in a horizontal row
- DisconnectOverlay(ModalScreen): full-screen modal shown when console goes offline
"""

from typing import ClassVar, Optional

from textual.app import ComposeResult
from textual.containers import HorizontalScroll, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, Static

_PROTOCOL_NAMES: dict[int, str] = {0: "", 1: "HUI", 2: "MCU", 3: "CC"}
_AUTO_MODE_NAMES: dict[int, str] = {0: "Legacy", 1: "Delta"}


class ChannelStrip(Static):
    """A single channel strip — mirrors the physical scribble strip layout."""

    channel_name: reactive[str] = reactive("", init=False)
    channel_num: reactive[int] = reactive(0)
    daw_protocol: reactive[str] = reactive("", init=False)
    auto_mode: reactive[str] = reactive("", init=False)
    insert_routing: reactive[str] = reactive("Ins: --", init=False)
    highlighted: reactive[bool] = reactive(False)

    def __init__(self, num: int, **kwargs) -> None:
        super().__init__("", id=f"ch-{num}", **kwargs)
        self.channel_num = num

    def render(self) -> str:
        """Return Rich markup for the strip (number, name, inserts, protocol/mode)."""
        num = f"[dim]{self.channel_num:>2}[/dim]"
        name = f"[bold $primary]{self.channel_name or '—':^10}[/bold $primary]"
        inserts = f"[dim italic]{self.insert_routing}[/dim italic]"
        proto_mode = ""
        if self.daw_protocol or self.auto_mode:
            parts = []
            if self.daw_protocol:
                parts.append(self.daw_protocol)
            if self.auto_mode:
                parts.append(self.auto_mode)
            proto_mode = f"[dim]{' '.join(parts)}[/dim]"
        else:
            proto_mode = "[dim]—[/dim]"

        return f"{num}\n{name}\n{inserts}\n{proto_mode}"

    # --- Reactive watchers ---

    def watch_channel_name(self, old: str, new: str) -> None:
        if old and old != new:
            self.flash_highlight()
        self.refresh()

    def watch_daw_protocol(self, old: str, new: str) -> None:
        if old and old != new:
            self.flash_highlight()
        self.refresh()

    def watch_auto_mode(self, old: str, new: str) -> None:
        if old and old != new:
            self.flash_highlight()
        self.refresh()

    def watch_insert_routing(self, old: str, new: str) -> None:
        if old and old != new:
            self.flash_highlight()
        self.refresh()

    def watch_highlighted(self, value: bool) -> None:
        if value:
            self.add_class("highlighted")
        else:
            self.remove_class("highlighted")

    # --- Flash helper ---

    def flash_highlight(self) -> None:
        """Temporarily highlight the strip for 1.5 seconds."""
        self.highlighted = True
        self.set_timer(1.5, lambda: setattr(self, "highlighted", False))

    # --- Data binding ---

    def update_from_snapshot(
        self,
        ch_tuple: tuple,
        daw_layer_tuple: Optional[tuple],
        auto_mode_int: int,
        insert_info: Optional[tuple],
    ) -> None:
        """Update reactive attributes from snapshot data.

        Args:
            ch_tuple: (num, name) for this channel
            daw_layer_tuple: (num, protocol_int, profile_name) or None
            auto_mode_int: 0=Legacy, 1=Delta
            insert_info: (channel, chain_name, [insert_nums], has_stereo) or None
        """
        _num, name = ch_tuple
        self.channel_name = name

        if daw_layer_tuple is not None:
            _dl_num, protocol_int, _profile = daw_layer_tuple
            self.daw_protocol = _PROTOCOL_NAMES.get(protocol_int, "")
        else:
            self.daw_protocol = ""

        self.auto_mode = _AUTO_MODE_NAMES.get(auto_mode_int, "")

        if insert_info is not None:
            _ch, chain_name, insert_list, _stereo = insert_info
            if chain_name:
                self.insert_routing = chain_name
            elif insert_list:
                nums = ",".join(str(n) for n in insert_list)
                self.insert_routing = f"Ins: {nums}"
            else:
                self.insert_routing = "Ins: --"
        else:
            self.insert_routing = "Ins: --"


class ChannelView(HorizontalScroll):
    """Horizontal row of 16 ChannelStrip widgets mirroring the physical console."""

    def compose(self) -> ComposeResult:
        for i in range(1, 17):
            yield ChannelStrip(i)

    def update_from(self, snapshot: dict) -> None:
        """Push snapshot data into each of the 16 channel strips.

        Args:
            snapshot: dict with keys channels, daw_layers, automation_mode,
                      channel_inserts (as produced by SSLApp._on_state_changed_hook)
        """
        channels = snapshot.get("channels", [])
        daw_layers = snapshot.get("daw_layers", [])
        auto_mode_int = snapshot.get("automation_mode", 0)

        # Build insert lookup keyed by channel number
        insert_by_channel: dict[int, tuple] = {}
        for ci in snapshot.get("channel_inserts", []):
            insert_by_channel[ci[0]] = ci

        # Use first DAW layer for protocol display (surface-level indicator)
        first_layer = daw_layers[0] if daw_layers else None

        # Build a fast lookup for channels by number
        ch_by_num: dict[int, tuple] = {ch[0]: ch for ch in channels}

        for strip in self.query(ChannelStrip):
            num = strip.channel_num
            ch_tuple = ch_by_num.get(num, (num, ""))
            insert_info = insert_by_channel.get(num)
            strip.update_from_snapshot(ch_tuple, first_layer, auto_mode_int, insert_info)


class DisconnectOverlay(ModalScreen):
    """Full-screen modal shown when the console goes offline."""

    DEFAULT_CSS: ClassVar[str] = """
    DisconnectOverlay {
        align: center middle;
        background: $background 70%;
    }

    DisconnectOverlay > Vertical {
        width: 40;
        height: auto;
        border: tall $error;
        background: $surface;
        padding: 2 4;
        align: center middle;
    }

    DisconnectOverlay Label {
        width: 1fr;
        text-align: center;
    }

    DisconnectOverlay #disconnect-title {
        color: $error;
        text-style: bold;
    }

    DisconnectOverlay #disconnect-attempt {
        color: $warning;
    }

    DisconnectOverlay #disconnect-quit {
        color: $text-muted;
        text-style: dim;
    }
    """

    def __init__(self, attempt: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.attempt = attempt

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("DISCONNECTED", id="disconnect-title")
            yield Label(
                f"Reconnecting... attempt {self.attempt}",
                id="disconnect-attempt",
            )
            yield Label("Press Ctrl+Q to quit", id="disconnect-quit")

    def update_attempt(self, attempt: int) -> None:
        """Update the attempt counter displayed in the overlay."""
        self.attempt = attempt
        self.query_one("#disconnect-attempt", Label).update(f"Reconnecting... attempt {attempt}")
