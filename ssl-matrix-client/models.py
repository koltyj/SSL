"""Data models for SSL Matrix console state."""

import time
from dataclasses import dataclass, field


@dataclass
class DeskInfo:
    """Console identity and status."""

    serial: int = 0
    address: str = ""
    product_name: str = ""
    version: int = 0
    sub: int = 0
    issue: int = 0
    built_str: str = ""
    time_str: str = ""
    console_name: str = ""
    online: bool = False
    last_heartbeat: float = 0.0

    @property
    def firmware(self):
        return f"V{self.version}.{self.sub}/{self.issue}"

    @property
    def heartbeat_age(self):
        if self.last_heartbeat == 0:
            return float("inf")
        return time.time() - self.last_heartbeat


@dataclass
class Channel:
    """A console channel with name."""

    number: int = 0
    name: str = ""


@dataclass
class ProfileItem:
    """A DAW controller profile stored on the console."""

    name: str = ""
    protocol: int = 0  # 0=none, 1=HUI, 2=MCU, 3=CC
    read_only: bool = False
    in_use: bool = False


@dataclass
class DawLayer:
    """A DAW layer (1-4) with its protocol and profile."""

    number: int = 0
    protocol: int = 0  # 0=none, 1=HUI, 2=MCU, 3=CC
    profile_name: str = ""


@dataclass
class InsertDevice:
    """An insert device (1-16) in the matrix routing."""

    number: int = 0
    name: str = ""
    is_assigned: int = 0  # 0=free, 1=assigned
    is_stereo: int = 0  # 0=mono, 1=stereo


@dataclass
class Chain:
    """A chain of insert devices."""

    number: int = 0
    name: str = ""
    is_assigned: int = 0
    elements: list = field(default_factory=list)  # list of (index, name) tuples


@dataclass
class ChannelInserts:
    """Insert routing for a single channel."""

    channel: int = 0
    chain_name: str = ""
    inserts: list = field(default_factory=list)  # list of insert device numbers
    has_stereo: int = 0


@dataclass
class MatrixPreset:
    """A stored matrix routing preset."""

    name: str = ""


@dataclass
class FileEntry:
    """A file or directory entry from the console filesystem."""

    name: str = ""
    info: str = ""
    is_dir: bool = False
    time_str: str = ""
    date_str: str = ""
    size: int = 0


@dataclass
class DiskInfo:
    """Console disk usage information."""

    free_percent: int = 0
    archive_done: bool = False


@dataclass
class TRSnapshot:
    """A Total Recall snapshot entry."""

    name: str = ""
    info: str = ""
    time_str: str = ""
    date_str: str = ""
    size: int = 0
    is_selected: bool = False


@dataclass
class ChanNamesPreset:
    """A stored channel names preset."""

    name: str = ""


@dataclass
class XpatchChannel:
    """XPatch channel setup: device/dest names, levels, mode."""

    number: int = 0
    device_name: str = ""
    dest_name: str = ""
    input_minus_10db: bool = False
    output_minus_10db: bool = False
    mode: int = 0


@dataclass
class XpatchPreset:
    """An XPatch routing preset."""

    index: int = 0
    used: bool = False
    name: str = ""
    srcs: list = field(default_factory=list)  # int per dest channel


@dataclass
class XpatchChain:
    """An XPatch chain definition."""

    index: int = 0
    used: bool = False
    name: str = ""
    links: list = field(default_factory=list)  # int per link slot


@dataclass
class XpatchRoute:
    """XPatch routing for a single destination."""

    dest: int = 0
    display_src: int = 0
    protect: bool = False


@dataclass
class XpatchState:
    """Full XPatch routing state."""

    channels: list = field(default_factory=lambda: [XpatchChannel(i) for i in range(1, 17)])
    presets: list = field(default_factory=list)
    chains: list = field(default_factory=list)
    routes: list = field(default_factory=list)
    selected_preset: int = -1
    preset_edited: bool = False
    midi_enabled: bool = False
    midi_channel: int = 0
    edit_chain: int = -1
    edit_chain_touched: bool = False


@dataclass
class KeyData:
    """A programmable key's current assignment."""

    index: int = 0
    is_top_row: int = 0
    key_type: int = 0  # 0=blank, 1=midi, 2=usb, 3=menu
    keycap_name: str = ""
    data: str = ""


@dataclass
class SoftkeysState:
    """Softkeys/keymap editor state."""

    keymap_name: str = ""
    daw_layer: int = 0
    panel_type: int = 0  # 0=blank, 1=transport(15-key), 2=softkey(8-key)
    unsaved_data: bool = False
    keys: list = field(default_factory=list)  # List[KeyData]
    in_edit: bool = False
    midi_functions: list = field(default_factory=list)  # list of (index, user_name, keycap_name)
    flip_status: bool = False
    handshake: bool = False
    auto_mode_on_scribs: bool = False
    default_wheel_mode: int = 0
    fader_db_readout: int = 0
    cc_names: list = field(default_factory=list)


@dataclass
class ConsoleState:
    """Full state of the connected console."""

    desk: DeskInfo = field(default_factory=DeskInfo)
    channels: list = field(default_factory=lambda: [Channel(i) for i in range(1, 33)])
    profiles: list = field(default_factory=list)
    daw_layers: list = field(default_factory=lambda: [DawLayer(i) for i in range(1, 5)])
    devices: list = field(default_factory=lambda: [InsertDevice(i) for i in range(1, 17)])
    chains: list = field(default_factory=list)
    channel_inserts: list = field(default_factory=list)
    matrix_presets: list = field(default_factory=list)
    directory: list = field(default_factory=list)
    disk_info: DiskInfo = field(default_factory=DiskInfo)
    # Total Recall
    tr_enabled: bool = False
    tr_snapshots: list = field(default_factory=list)
    selected_tr_index: int = -1
    # Channel Names Presets
    chan_names_presets: list = field(default_factory=list)
    # XPatch
    xpatch: XpatchState = field(default_factory=XpatchState)
    # Softkeys
    softkeys: SoftkeysState = field(default_factory=SoftkeysState)
    # Core
    automation_mode: int = 0  # 0=Legacy, 1=Delta
    motors_off: int = 0
    mdac_meters: int = 0
    transport_lock_layer: int = 0
    project_name: str = ""
    title_name: str = ""
    synced: bool = False
    display_17_32: int = 0
    flip_scrib: int = 0

    def get_channel(self, num):
        """Get channel by 1-based number."""
        if 1 <= num <= len(self.channels):
            return self.channels[num - 1]
        return None

    def get_daw_layer(self, num):
        """Get DAW layer by 1-based number (1-4)."""
        if 1 <= num <= 4:
            return self.daw_layers[num - 1]
        return None

    def get_device(self, num):
        """Get insert device by 1-based number (1-16)."""
        if 1 <= num <= 16:
            return self.devices[num - 1]
        return None
