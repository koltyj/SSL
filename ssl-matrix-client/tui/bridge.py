"""State bridge: polls SSLMatrixClient state and posts Textual messages on change."""

import asyncio
import copy
import time
from dataclasses import dataclass, field

from textual.message import Message


@dataclass(frozen=True)
class DeskSnapshot:
    serial: int = 0
    address: str = ""
    product_name: str = ""
    firmware: str = ""
    console_name: str = ""
    online: bool = False
    heartbeat_age: float = float("inf")


@dataclass(frozen=True)
class ChannelSnapshot:
    number: int = 0
    name: str = ""


@dataclass(frozen=True)
class LayerSnapshot:
    number: int = 0
    protocol: int = 0
    profile_name: str = ""


@dataclass(frozen=True)
class DeviceSnapshot:
    number: int = 0
    name: str = ""
    is_assigned: int = 0
    is_stereo: int = 0


@dataclass(frozen=True)
class ChainSnapshot:
    number: int = 0
    name: str = ""
    is_assigned: int = 0
    elements: tuple = ()  # tuple of (index, name)


@dataclass(frozen=True)
class ChanInsertSnapshot:
    channel: int = 0
    chain_name: str = ""
    inserts: tuple = ()
    has_stereo: int = 0


@dataclass(frozen=True)
class RouteSnapshot:
    dest: int = 0
    display_src: int = 0
    protect: bool = False


@dataclass(frozen=True)
class XpatchChanSnapshot:
    number: int = 0
    device_name: str = ""
    dest_name: str = ""
    input_minus_10db: bool = False
    output_minus_10db: bool = False
    mode: int = 0


@dataclass(frozen=True)
class PresetSnapshot:
    index: int = 0
    used: bool = False
    name: str = ""


@dataclass(frozen=True)
class TRSnapshotEntry:
    name: str = ""
    date_str: str = ""
    time_str: str = ""
    size: int = 0
    is_selected: bool = False


@dataclass(frozen=True)
class StateSnapshot:
    """Immutable snapshot of ConsoleState."""

    desk: DeskSnapshot = None
    channels: tuple = ()
    daw_layers: tuple = ()
    devices: tuple = ()
    chains: tuple = ()
    channel_inserts: tuple = ()
    xpatch_routes: tuple = ()
    xpatch_channels: tuple = ()
    xpatch_presets: tuple = ()
    xpatch_selected_preset: int = -1
    xpatch_midi_enabled: bool = False
    xpatch_midi_channel: int = 0
    tr_enabled: bool = False
    tr_snapshots: tuple = ()
    project_name: str = ""
    title_name: str = ""
    automation_mode: int = 0
    motors_off: int = 0
    mdac_meters: int = 0
    transport_lock_layer: int = 0
    matrix_presets: tuple = ()
    chan_names_presets: tuple = ()
    synced: bool = False


def snapshot_from_state(state):
    """Create an immutable StateSnapshot from a mutable ConsoleState.

    Must be called while holding client._lock.
    """
    desk = state.desk
    return StateSnapshot(
        desk=DeskSnapshot(
            serial=desk.serial,
            address=desk.address,
            product_name=desk.product_name,
            firmware=desk.firmware,
            console_name=desk.console_name,
            online=desk.online,
            heartbeat_age=desk.heartbeat_age,
        ),
        channels=tuple(
            ChannelSnapshot(number=ch.number, name=ch.name)
            for ch in state.channels
        ),
        daw_layers=tuple(
            LayerSnapshot(number=dl.number, protocol=dl.protocol, profile_name=dl.profile_name)
            for dl in state.daw_layers
        ),
        devices=tuple(
            DeviceSnapshot(
                number=d.number, name=d.name,
                is_assigned=d.is_assigned, is_stereo=d.is_stereo,
            )
            for d in state.devices
        ),
        chains=tuple(
            ChainSnapshot(
                number=c.number, name=c.name,
                is_assigned=c.is_assigned,
                elements=tuple(c.elements),
            )
            for c in state.chains
        ),
        channel_inserts=tuple(
            ChanInsertSnapshot(
                channel=ci.channel, chain_name=ci.chain_name,
                inserts=tuple(ci.inserts), has_stereo=ci.has_stereo,
            )
            for ci in state.channel_inserts
        ),
        xpatch_routes=tuple(
            RouteSnapshot(dest=r.dest, display_src=r.display_src, protect=r.protect)
            for r in state.xpatch.routes
        ),
        xpatch_channels=tuple(
            XpatchChanSnapshot(
                number=c.number, device_name=c.device_name, dest_name=c.dest_name,
                input_minus_10db=c.input_minus_10db,
                output_minus_10db=c.output_minus_10db, mode=c.mode,
            )
            for c in state.xpatch.channels
        ),
        xpatch_presets=tuple(
            PresetSnapshot(index=p.index, used=p.used, name=p.name)
            for p in state.xpatch.presets
        ),
        xpatch_selected_preset=state.xpatch.selected_preset,
        xpatch_midi_enabled=state.xpatch.midi_enabled,
        xpatch_midi_channel=state.xpatch.midi_channel,
        tr_enabled=state.tr_enabled,
        tr_snapshots=tuple(
            TRSnapshotEntry(
                name=t.name, date_str=t.date_str, time_str=t.time_str,
                size=t.size, is_selected=t.is_selected,
            )
            for t in state.tr_snapshots
        ),
        project_name=state.project_name,
        title_name=state.title_name,
        automation_mode=state.automation_mode,
        motors_off=state.motors_off,
        mdac_meters=state.mdac_meters,
        transport_lock_layer=state.transport_lock_layer,
        matrix_presets=tuple(p.name for p in state.matrix_presets),
        chan_names_presets=tuple(p.name for p in state.chan_names_presets),
        synced=state.synced,
    )


class StateUpdated(Message):
    """Posted when client state changes."""

    def __init__(self, snapshot: StateSnapshot):
        super().__init__()
        self.snapshot = snapshot


async def poll_state(app, client, interval=0.25):
    """Poll client state and post StateUpdated messages when changed."""
    previous = None
    while True:
        with client._lock:
            current = snapshot_from_state(client.state)
        if current != previous:
            app.post_message(StateUpdated(current))
            previous = current
        await asyncio.sleep(interval)
