"""Routing handler: insert matrix V2, chains, presets.

Builders send commands to the console, handlers parse replies and update state.
All payload formats from decompiled MatrixHandler.java.
"""

import logging

from ..protocol import MessageCode, TxMessage
from ..models import InsertDevice, Chain, ChannelInserts, MatrixPreset

log = logging.getLogger(__name__)


# --- Builders (Remote -> Console) ---

def build_get_insert_names_v2(desk_serial, my_serial, first=0, last=0):
    """Build SEND_GET_INSERT_INFO_V2 (cmd=10400). Payload: byte first, byte last."""
    msg = TxMessage(MessageCode.SEND_GET_INSERT_INFO_V2, desk_serial, my_serial)
    msg.write_byte(first)
    msg.write_byte(last)
    return msg.to_bytes()


def build_get_chain_info_v2(desk_serial, my_serial, first=0, last=0):
    """Build SEND_GET_CHAIN_INFO_V2 (cmd=10420). Payload: byte first, byte last."""
    msg = TxMessage(MessageCode.SEND_GET_CHAIN_INFO_V2, desk_serial, my_serial)
    msg.write_byte(first)
    msg.write_byte(last)
    return msg.to_bytes()


def build_get_chan_matrix_info_v2(desk_serial, my_serial, first=0, last=0):
    """Build SEND_GET_CHAN_MATRIX_INFO_V2 (cmd=10440). Payload: byte first, byte last."""
    msg = TxMessage(MessageCode.SEND_GET_CHAN_MATRIX_INFO_V2, desk_serial, my_serial)
    msg.write_byte(first)
    msg.write_byte(last)
    return msg.to_bytes()


def build_set_insert_name_v2(desk_serial, my_serial, index, name):
    """Build SEND_SET_INSERT_NAMES_V2 (cmd=10410). Payload: byte index, string name, byte 0."""
    msg = TxMessage(MessageCode.SEND_SET_INSERT_NAMES_V2, desk_serial, my_serial)
    msg.write_byte(index)
    msg.write_string(name)
    msg.write_byte(0)
    return msg.to_bytes()


def build_set_insert_to_chan_v2(desk_serial, my_serial, chan, insert_num, slot):
    """Build SEND_SET_INSERT_TO_CHAN_V2 (cmd=10430).

    Payload: byte chan, byte insertNum, byte (slot-1), byte 0
    """
    msg = TxMessage(MessageCode.SEND_SET_INSERT_TO_CHAN_V2, desk_serial, my_serial)
    msg.write_byte(chan)
    msg.write_byte(insert_num)
    msg.write_byte(slot - 1)
    msg.write_byte(0)
    return msg.to_bytes()


def build_assign_chain_to_chan(desk_serial, my_serial, chan, chain_name):
    """Build SEND_ASSIGN_CHAIN_TO_CHAN_V2 (cmd=10510). Payload: byte chan, string chainName."""
    msg = TxMessage(MessageCode.SEND_ASSIGN_CHAIN_TO_CHAN_V2, desk_serial, my_serial)
    msg.write_byte(chan)
    msg.write_string(chain_name)
    return msg.to_bytes()


def build_deassign_chan(desk_serial, my_serial, chan):
    """Build SEND_DEASSIGN_CHAN_V2 (cmd=10520). Payload: byte chan."""
    msg = TxMessage(MessageCode.SEND_DEASSIGN_CHAN_V2, desk_serial, my_serial)
    msg.write_byte(chan)
    return msg.to_bytes()


def build_delete_chan_insert(desk_serial, my_serial, chan, slot):
    """Build SEND_DELETE_CHAN_INSERT (cmd=10600). Payload: byte chan, byte (slot-1)."""
    msg = TxMessage(MessageCode.SEND_DELETE_CHAN_INSERT, desk_serial, my_serial)
    msg.write_byte(chan)
    msg.write_byte(slot - 1)
    return msg.to_bytes()


def build_set_chan_stereo_insert(desk_serial, my_serial, first, second, stereo):
    """Build SEND_SET_CHAN_STEREO_INSERT (cmd=10620).

    Payload: byte first, byte second, byte (1 if stereo else 0)
    """
    msg = TxMessage(MessageCode.SEND_SET_CHAN_STEREO_INSERT, desk_serial, my_serial)
    msg.write_byte(first)
    msg.write_byte(second)
    msg.write_byte(1 if stereo else 0)
    return msg.to_bytes()


def build_save_inserts_to_chain(desk_serial, my_serial, chan, name):
    """Build SEND_SAVE_INSERTS_TO_CHAIN (cmd=10570). Payload: byte chan, string name."""
    msg = TxMessage(MessageCode.SEND_SAVE_INSERTS_TO_CHAIN, desk_serial, my_serial)
    msg.write_byte(chan)
    msg.write_string(name)
    return msg.to_bytes()


def build_delete_chain(desk_serial, my_serial, name):
    """Build SEND_DELETE_CHAIN_V2 (cmd=10550). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_DELETE_CHAIN_V2, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_rename_chain(desk_serial, my_serial, old_name, new_name):
    """Build SEND_RENAME_CHAIN (cmd=10560). Payload: string old, string new."""
    msg = TxMessage(MessageCode.SEND_RENAME_CHAIN, desk_serial, my_serial)
    msg.write_string(old_name)
    msg.write_string(new_name)
    return msg.to_bytes()


def build_clear_inserts(desk_serial, my_serial, indices):
    """Build SEND_CLEAR_INSERTS (cmd=10680). Payload: byte count, then count bytes."""
    msg = TxMessage(MessageCode.SEND_CLEAR_INSERTS, desk_serial, my_serial)
    msg.write_byte(len(indices))
    for idx in indices:
        msg.write_byte(idx)
    return msg.to_bytes()


def build_get_matrix_preset_list(desk_serial, my_serial):
    """Build SEND_GET_MATRIX_PRESET_LIST (cmd=10630). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_MATRIX_PRESET_LIST, desk_serial, my_serial)
    return msg.to_bytes()


def build_load_matrix_preset(desk_serial, my_serial, name):
    """Build SEND_LOAD_MATRIX_PRESET (cmd=10640). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_LOAD_MATRIX_PRESET, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_save_matrix_preset(desk_serial, my_serial, name):
    """Build SEND_SAVE_MATRIX_PRESET (cmd=10650). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_SAVE_MATRIX_PRESET, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_delete_matrix_preset(desk_serial, my_serial, name):
    """Build SEND_DELETE_MATRIX_PRESET (cmd=10660). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_DELETE_MATRIX_PRESET, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_rename_matrix_preset(desk_serial, my_serial, old_name, new_name):
    """Build SEND_RENAME_MATRIX_PRESET (cmd=10670). Payload: string old, string new."""
    msg = TxMessage(MessageCode.SEND_RENAME_MATRIX_PRESET, desk_serial, my_serial)
    msg.write_string(old_name)
    msg.write_string(new_name)
    return msg.to_bytes()


# --- Handlers (Console -> Remote) ---

def handle_insert_names_v2_reply(rx, state):
    """Parse ACK_GET_INSERT_INFO_V2 (cmd=10401).

    Payload: Loop of [byte insertNum (0=end), byte isAssigned, byte isStereo, string name]
    """
    while rx.remaining > 0:
        insert_num = rx.get_unsigned_byte()
        if insert_num == 0:
            break
        is_assigned = rx.get_unsigned_byte()
        is_stereo = rx.get_unsigned_byte()
        name = rx.get_string()
        dev = state.get_device(insert_num)
        if dev:
            dev.name = name
            dev.is_assigned = is_assigned
            dev.is_stereo = is_stereo


def handle_chain_info_v2_reply(rx, state):
    """Parse ACK_GET_CHAIN_INFO_V2 (cmd=10421).

    Payload: Loop of [byte chainNum (0=end), byte isAssigned, string name,
             byte numElems (0-6), then numElems x (byte elemIndex, string elemName)]
    """
    state.chains.clear()
    while rx.remaining > 0:
        chain_num = rx.get_unsigned_byte()
        if chain_num == 0:
            break
        is_assigned = rx.get_unsigned_byte()
        name = rx.get_string()
        num_elems = rx.get_unsigned_byte()
        elements = []
        for _ in range(num_elems):
            elem_index = rx.get_unsigned_byte()
            elem_name = rx.get_string()
            elements.append((elem_index, elem_name))
        state.chains.append(Chain(
            number=chain_num,
            name=name,
            is_assigned=is_assigned,
            elements=elements,
        ))


def handle_chan_matrix_info_v2_reply(rx, state):
    """Parse ACK_GET_CHAN_MATRIX_INFO_V2 (cmd=10441).

    Payload: Loop of [byte chanNum (0=end), string chainName,
             byte numElems (0-6), then numElems x byte insertNumber,
             byte hasStereoInserts]
    """
    state.channel_inserts.clear()
    while rx.remaining > 0:
        chan_num = rx.get_unsigned_byte()
        if chan_num == 0:
            break
        chain_name = rx.get_string()
        num_elems = rx.get_unsigned_byte()
        inserts = []
        for _ in range(num_elems):
            inserts.append(rx.get_unsigned_byte())
        has_stereo = rx.get_unsigned_byte()
        state.channel_inserts.append(ChannelInserts(
            channel=chan_num,
            chain_name=chain_name,
            inserts=inserts,
            has_stereo=has_stereo,
        ))


def handle_matrix_preset_list_reply(rx, state):
    """Parse ACK_GET_MATRIX_PRESET_LIST (cmd=10631).

    Payload: int listSize, then listSize x string name
    """
    state.matrix_presets.clear()
    count = rx.get_int()
    for _ in range(count):
        name = rx.get_string()
        state.matrix_presets.append(MatrixPreset(name=name))


def handle_routing_ack(rx, state):
    """Handle generic ACK replies for routing commands.

    Payload: string reply — "ok" or error message.
    Used for cmds: 10411, 10431, 10511, 10521, 10551, 10561, 10571,
                   10601, 10621, 10641, 10651, 10661, 10671, 10681
    """
    reply = rx.get_string()
    if reply.lower() != "ok":
        log.warning("Routing ACK error: %s (cmd=%d)", reply, rx.cmd_code)
