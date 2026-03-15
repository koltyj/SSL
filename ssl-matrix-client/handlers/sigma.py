"""Message handlers for SSL Sigma protocol. EXPERIMENTAL — untested against real hardware.

Dispatches incoming SigmaRxMessage packets to state-update functions and provides
builder functions for sending common commands to the desk.
"""

import time

from ..sigma_models import SigmaState
from ..sigma_protocol import (
    SigmaMessageId,
    SigmaRxMessage,
    SigmaTxMessage,
    bool_to_sigma_float,
    sigma_float_to_bool,
    sigma_float_to_uint,
)

# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------


def handle_sigma_message(rx: SigmaRxMessage, state: SigmaState) -> bool:
    """Dispatch an incoming Sigma message to the appropriate handler.

    Returns True if the message was handled, False if the msg_id is unknown.
    """
    handler = _DISPATCH.get(rx.msg_id)
    if handler is not None:
        handler(rx, state)
        return True
    return False


# ---------------------------------------------------------------------------
# Channel handlers
# ---------------------------------------------------------------------------


def _handle_fader(rx: SigmaRxMessage, state: SigmaState):
    ch = state.get_channel(rx.sub_param)
    if ch and rx.float_value is not None:
        ch.fader = rx.float_value


def _handle_pan(rx: SigmaRxMessage, state: SigmaState):
    ch = state.get_channel(rx.sub_param)
    if ch and rx.float_value is not None:
        ch.pan = rx.float_value


def _handle_solo(rx: SigmaRxMessage, state: SigmaState):
    ch = state.get_channel(rx.sub_param)
    if ch and rx.float_value is not None:
        ch.solo = sigma_float_to_bool(rx.float_value)


def _handle_mute(rx: SigmaRxMessage, state: SigmaState):
    ch = state.get_channel(rx.sub_param)
    if ch and rx.float_value is not None:
        ch.mute = sigma_float_to_bool(rx.float_value)


def _handle_phase(rx: SigmaRxMessage, state: SigmaState):
    ch = state.get_channel(rx.sub_param)
    if ch and rx.float_value is not None:
        ch.phase = sigma_float_to_bool(rx.float_value)


def _handle_solo_safe(rx: SigmaRxMessage, state: SigmaState):
    ch = state.get_channel(rx.sub_param)
    if ch and rx.float_value is not None:
        ch.solo_safe = sigma_float_to_bool(rx.float_value)


def _handle_pan_mode(rx: SigmaRxMessage, state: SigmaState):
    """Pan mode is sent as uint-as-float."""
    ch = state.get_channel(rx.sub_param)
    if ch and rx.float_value is not None:
        # Pan mode is a uint reinterpreted — but for state just track the raw value
        pass  # pan_mode not currently in SigmaChannel model


def _handle_scribble(rx: SigmaRxMessage, state: SigmaState):
    ch = state.get_channel(rx.sub_param)
    if ch and rx.string_value is not None:
        ch.name = rx.string_value


# ---------------------------------------------------------------------------
# Monitor handlers
# ---------------------------------------------------------------------------


def _handle_monitor_source(rx: SigmaRxMessage, state: SigmaState):
    """Handle monitor source 1-7 (0x53-0x59)."""
    idx = rx.msg_id - SigmaMessageId.MON_SRC_1
    if 0 <= idx < len(state.monitor.sources) and rx.float_value is not None:
        state.monitor.sources[idx] = sigma_float_to_bool(rx.float_value)


# ---------------------------------------------------------------------------
# Headphone handlers
# ---------------------------------------------------------------------------


def _handle_headphone_source(rx: SigmaRxMessage, state: SigmaState):
    """Handle headphone source 1-4 (0x5A-0x5D)."""
    idx = rx.msg_id - SigmaMessageId.HP_SRC_1
    if 0 <= idx < len(state.headphone.sources) and rx.float_value is not None:
        state.headphone.sources[idx] = sigma_float_to_bool(rx.float_value)


# ---------------------------------------------------------------------------
# Insert handlers
# ---------------------------------------------------------------------------


def _handle_insert_a(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.insert.insert_a = rx.uint_value
    elif rx.float_value is not None:
        state.insert.insert_a = sigma_float_to_uint(rx.float_value)


def _handle_insert_b(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.insert.insert_b = rx.uint_value
    elif rx.float_value is not None:
        state.insert.insert_b = sigma_float_to_uint(rx.float_value)


def _handle_insert_a_sum(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.insert.insert_a_sum = rx.uint_value == 3
    elif rx.float_value is not None:
        state.insert.insert_a_sum = sigma_float_to_uint(rx.float_value) == 3


def _handle_insert_b_sum(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.insert.insert_b_sum = rx.uint_value == 3
    elif rx.float_value is not None:
        state.insert.insert_b_sum = sigma_float_to_uint(rx.float_value) == 3


# ---------------------------------------------------------------------------
# Level / metering handlers
# ---------------------------------------------------------------------------


def _handle_level_readout(rx: SigmaRxMessage, state: SigmaState):
    if rx.float_value is not None:
        state.level.level_value = rx.float_value


def _handle_level_fader(rx: SigmaRxMessage, state: SigmaState):
    if rx.float_value is not None:
        state.level.level_fader = rx.float_value


def _handle_meter_mode(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.level.meter_mode = rx.uint_value
    elif rx.float_value is not None:
        state.level.meter_mode = sigma_float_to_uint(rx.float_value)


def _handle_level_toggle(rx: SigmaRxMessage, state: SigmaState):
    if rx.float_value is not None:
        state.level.level_toggle = sigma_float_to_bool(rx.float_value)


def _handle_meter_source(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.level.meter_source = rx.uint_value
    elif rx.float_value is not None:
        state.level.meter_source = sigma_float_to_uint(rx.float_value)


# ---------------------------------------------------------------------------
# Dim handlers
# ---------------------------------------------------------------------------


def _handle_dim_level(rx: SigmaRxMessage, state: SigmaState):
    if rx.float_value is not None:
        state.dim.dim_level = rx.float_value
        state.monitor.dim_level = rx.float_value


def _handle_dim_secondary(rx: SigmaRxMessage, state: SigmaState):
    if rx.float_value is not None:
        state.dim.secondary_dim = rx.float_value
        state.monitor.secondary_dim = rx.float_value


# ---------------------------------------------------------------------------
# Misc handlers
# ---------------------------------------------------------------------------


def _handle_talkback(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.misc.talkback_mode = rx.uint_value
    elif rx.float_value is not None:
        state.misc.talkback_mode = sigma_float_to_uint(rx.float_value)


def _handle_oscillator(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.misc.oscillator = rx.uint_value != 0
    elif rx.float_value is not None:
        state.misc.oscillator = sigma_float_to_bool(rx.float_value)


def _handle_listenback(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.misc.listenback = rx.uint_value != 0
    elif rx.float_value is not None:
        state.misc.listenback = sigma_float_to_bool(rx.float_value)


def _handle_scene_recall(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.misc.scene_recall = rx.uint_value
    elif rx.float_value is not None:
        state.misc.scene_recall = sigma_float_to_uint(rx.float_value)


def _handle_connection_status(rx: SigmaRxMessage, state: SigmaState):
    if rx.float_value is not None:
        state.misc.connection_status = sigma_float_to_bool(rx.float_value)


def _handle_daw_control(rx: SigmaRxMessage, state: SigmaState):
    if rx.uint_value is not None:
        state.misc.daw_control = rx.uint_value
    elif rx.float_value is not None:
        state.misc.daw_control = sigma_float_to_uint(rx.float_value)


# ---------------------------------------------------------------------------
# Network handlers
# ---------------------------------------------------------------------------


def _handle_net_master_slave(rx: SigmaRxMessage, state: SigmaState):
    if rx.float_value is not None:
        state.network.master_slave = sigma_float_to_bool(rx.float_value)


def _handle_ip_octet(rx: SigmaRxMessage, state: SigmaState):
    """Handle IP octets 1-4 (0x34-0x37)."""
    idx = rx.msg_id - SigmaMessageId.IP_OCTET_1
    if 0 <= idx < 4:
        if rx.uint_value is not None:
            state.network.ip_octets[idx] = rx.uint_value
        elif rx.float_value is not None:
            state.network.ip_octets[idx] = sigma_float_to_uint(rx.float_value)


def _handle_subnet_octet(rx: SigmaRxMessage, state: SigmaState):
    """Handle subnet octets 1-4 (0x38-0x3B)."""
    idx = rx.msg_id - SigmaMessageId.SUBNET_OCTET_1
    if 0 <= idx < 4:
        if rx.uint_value is not None:
            state.network.subnet_octets[idx] = rx.uint_value
        elif rx.float_value is not None:
            state.network.subnet_octets[idx] = sigma_float_to_uint(rx.float_value)


# ---------------------------------------------------------------------------
# Connection / handshake handlers
# ---------------------------------------------------------------------------


def _handle_keepalive(rx: SigmaRxMessage, state: SigmaState):
    state.last_heartbeat = time.time()
    state.online = True


def _handle_handshake(rx: SigmaRxMessage, state: SigmaState):
    state.last_heartbeat = time.time()
    state.online = True


def _handle_connection_mode(rx: SigmaRxMessage, state: SigmaState):
    """0xA0: value=0.0 means multicast, non-zero means unicast."""
    pass  # Mode switching is handled at the transport layer


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_DISPATCH = {
    # Channel controls
    SigmaMessageId.FADER: _handle_fader,
    SigmaMessageId.PAN: _handle_pan,
    SigmaMessageId.SOLO: _handle_solo,
    SigmaMessageId.MUTE: _handle_mute,
    SigmaMessageId.PHASE: _handle_phase,
    SigmaMessageId.SOLO_SAFE: _handle_solo_safe,
    SigmaMessageId.PAN_MODE: _handle_pan_mode,
    SigmaMessageId.CHAN_SCRIBBLE: _handle_scribble,
    # Monitor section (0x53-0x59)
    SigmaMessageId.MON_SRC_1: _handle_monitor_source,
    SigmaMessageId.MON_SRC_2: _handle_monitor_source,
    SigmaMessageId.MON_SRC_3: _handle_monitor_source,
    SigmaMessageId.MON_SRC_4: _handle_monitor_source,
    SigmaMessageId.MON_SRC_5: _handle_monitor_source,
    SigmaMessageId.MON_SRC_6: _handle_monitor_source,
    SigmaMessageId.MON_SRC_7: _handle_monitor_source,
    # Headphone section (0x5A-0x5D)
    SigmaMessageId.HP_SRC_1: _handle_headphone_source,
    SigmaMessageId.HP_SRC_2: _handle_headphone_source,
    SigmaMessageId.HP_SRC_3: _handle_headphone_source,
    SigmaMessageId.HP_SRC_4: _handle_headphone_source,
    # Insert section
    SigmaMessageId.INSERT_A: _handle_insert_a,
    SigmaMessageId.INSERT_B: _handle_insert_b,
    SigmaMessageId.INSERT_A_SUM: _handle_insert_a_sum,
    SigmaMessageId.INSERT_B_SUM: _handle_insert_b_sum,
    # Level / metering
    SigmaMessageId.LEVEL_READOUT: _handle_level_readout,
    SigmaMessageId.LEVEL_FADER: _handle_level_fader,
    SigmaMessageId.METER_MODE: _handle_meter_mode,
    SigmaMessageId.LEVEL_TOGGLE: _handle_level_toggle,
    SigmaMessageId.METER_SOURCE: _handle_meter_source,
    # Dim
    SigmaMessageId.DIM_LEVEL: _handle_dim_level,
    SigmaMessageId.DIM_SECONDARY: _handle_dim_secondary,
    # Misc
    SigmaMessageId.TALKBACK_MODE: _handle_talkback,
    SigmaMessageId.OSCILLATOR: _handle_oscillator,
    SigmaMessageId.LISTENBACK: _handle_listenback,
    SigmaMessageId.SCENE_RECALL: _handle_scene_recall,
    SigmaMessageId.CONNECTION_STATUS: _handle_connection_status,
    SigmaMessageId.DAW_CONTROL: _handle_daw_control,
    # Network
    SigmaMessageId.NET_MASTER_SLAVE: _handle_net_master_slave,
    SigmaMessageId.IP_OCTET_1: _handle_ip_octet,
    SigmaMessageId.IP_OCTET_2: _handle_ip_octet,
    SigmaMessageId.IP_OCTET_3: _handle_ip_octet,
    SigmaMessageId.IP_OCTET_4: _handle_ip_octet,
    SigmaMessageId.SUBNET_OCTET_1: _handle_subnet_octet,
    SigmaMessageId.SUBNET_OCTET_2: _handle_subnet_octet,
    SigmaMessageId.SUBNET_OCTET_3: _handle_subnet_octet,
    SigmaMessageId.SUBNET_OCTET_4: _handle_subnet_octet,
    # Connection
    SigmaMessageId.KEEPALIVE: _handle_keepalive,
    SigmaMessageId.HANDSHAKE: _handle_handshake,
    SigmaMessageId.CONNECTION_MODE: _handle_connection_mode,
}


# ---------------------------------------------------------------------------
# Builder functions — outgoing commands to desk
# ---------------------------------------------------------------------------


def build_handshake() -> bytes:
    """Build a handshake request (0x9D) to initiate connection."""
    return SigmaTxMessage.build_handshake(SigmaMessageId.HANDSHAKE).to_bytes()


def build_keepalive() -> bytes:
    """Build a keepalive/ack (0x99) to maintain connection."""
    return SigmaTxMessage.build_handshake(SigmaMessageId.KEEPALIVE).to_bytes()


def build_set_fader(channel: int, value: float) -> bytes:
    """Build a fader level command (0.0-1.0)."""
    return SigmaTxMessage.build_float_message(SigmaMessageId.FADER, channel, value).to_bytes()


def build_set_pan(channel: int, value: float) -> bytes:
    """Build a pan position command."""
    return SigmaTxMessage.build_float_message(SigmaMessageId.PAN, channel, value).to_bytes()


def build_set_solo(channel: int, state: bool) -> bytes:
    """Build a solo on/off command."""
    return SigmaTxMessage.build_bool_message(SigmaMessageId.SOLO, channel, state).to_bytes()


def build_set_mute(channel: int, state: bool) -> bytes:
    """Build a mute on/off command."""
    return SigmaTxMessage.build_bool_message(SigmaMessageId.MUTE, channel, state).to_bytes()


def build_set_phase(channel: int, state: bool) -> bytes:
    """Build a phase/polarity on/off command."""
    return SigmaTxMessage.build_bool_message(SigmaMessageId.PHASE, channel, state).to_bytes()


def build_set_scribble(channel: int, text: str) -> bytes:
    """Build a channel scribble/name command."""
    return SigmaTxMessage.build_string_message(
        SigmaMessageId.CHAN_SCRIBBLE, channel, text
    ).to_bytes()


def build_set_monitor_source(source_index: int, state: bool) -> bytes:
    """Build a monitor source select command (source_index 0-6)."""
    msg_id = SigmaMessageId.MON_SRC_1 + source_index
    return SigmaTxMessage.build_bool_message(msg_id, 0, state).to_bytes()


def build_set_headphone_source(source_index: int, state: bool) -> bytes:
    """Build a headphone source select command (source_index 0-3)."""
    msg_id = SigmaMessageId.HP_SRC_1 + source_index
    return SigmaTxMessage.build_bool_message(msg_id, 0, state).to_bytes()


def build_set_dim_level(value: float) -> bytes:
    """Build a dim level command."""
    return SigmaTxMessage.build_float_message(SigmaMessageId.DIM_LEVEL, 0, value).to_bytes()


def build_set_connection_mode(unicast: bool) -> bytes:
    """Build a connection mode command (0xA0). 0.0=multicast, 1.0=unicast."""
    return SigmaTxMessage.build_float_message(
        SigmaMessageId.CONNECTION_MODE, 0, bool_to_sigma_float(unicast)
    ).to_bytes()
