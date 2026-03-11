"""Channel names preset handler: save/load/rename/delete named channel strip configs.

All payload formats from decompiled ChanSettingsHandler.java (preset portion).
"""

import logging

from ..protocol import MessageCode, TxMessage
from ..models import ChanNamesPreset

log = logging.getLogger(__name__)


# --- Builders (Remote -> Console) ---

def build_get_chan_names_preset_list(desk_serial, my_serial):
    """Build SEND_GET_CHAN_NAMES_PRESET_LIST (cmd=10790). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_CHAN_NAMES_PRESET_LIST, desk_serial, my_serial)
    return msg.to_bytes()


def build_save_chan_names_preset(desk_serial, my_serial, name):
    """Build SEND_SAVE_CHAN_NAMES_PRESET (cmd=10800). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_SAVE_CHAN_NAMES_PRESET, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_load_chan_names_preset(desk_serial, my_serial, name):
    """Build SEND_LOAD_CHAN_NAMES_PRESET (cmd=10810). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_LOAD_CHAN_NAMES_PRESET, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_rename_chan_names_preset(desk_serial, my_serial, old_name, new_name):
    """Build SEND_RENAME_CHAN_NAMES_PRESET (cmd=10770). Payload: string old, string new."""
    msg = TxMessage(MessageCode.SEND_RENAME_CHAN_NAMES_PRESET, desk_serial, my_serial)
    msg.write_string(old_name)
    msg.write_string(new_name)
    return msg.to_bytes()


def build_delete_chan_names_preset(desk_serial, my_serial, name):
    """Build SEND_DELETE_CHAN_NAMES_PRESET (cmd=10780). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_DELETE_CHAN_NAMES_PRESET, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


# --- Handlers (Console -> Remote) ---

def handle_chan_names_preset_list_reply(rx, state):
    """Parse ACK_GET_CHAN_NAMES_PRESET_LIST (cmd=10791).

    Payload: int listSize, then listSize x string name
    """
    state.chan_names_presets.clear()
    count = rx.get_int()
    for _ in range(count):
        name = rx.get_string()
        state.chan_names_presets.append(ChanNamesPreset(name=name))


def handle_chan_names_preset_ack(rx, state):
    """Handle generic ACK for channel names preset commands.

    Payload: string reply — "ok" or error.
    Used for: 10771 (rename), 10781 (delete), 10801 (save), 10811 (load)
    """
    reply = rx.get_string()
    if reply.lower() != "ok":
        log.warning("Chan names preset ACK error: %s (cmd=%d)", reply, rx.cmd_code)
