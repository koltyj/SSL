"""Total Recall handler: TR snapshot management, enable/state, channel data.

Payload formats reverse-engineered from the SSL MatrixRemote protocol.
"""

import logging

from ..models import TRSnapshot
from ..protocol import MessageCode, TxMessage

log = logging.getLogger(__name__)


# --- Builders (Remote -> Console) ---


def build_set_tr_enable(desk_serial, my_serial, on):
    """Build SEND_SET_TR_ENABLE (cmd=300). Payload: boolean on."""
    msg = TxMessage(MessageCode.SEND_SET_TR_ENABLE, desk_serial, my_serial)
    msg.write_boolean(on)
    return msg.to_bytes()


def build_get_tr_state(desk_serial, my_serial):
    """Build SEND_GET_TR_STATE (cmd=302). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_TR_STATE, desk_serial, my_serial)
    return msg.to_bytes()


def build_take_tr_snap(desk_serial, my_serial):
    """Build SEND_TAKE_TR_SNAP (cmd=310). No payload."""
    msg = TxMessage(MessageCode.SEND_TAKE_TR_SNAP, desk_serial, my_serial)
    return msg.to_bytes()


def build_select_tr_snap(desk_serial, my_serial, index):
    """Build SEND_SELECT_TR_SNAP (cmd=320). Payload: int index."""
    msg = TxMessage(MessageCode.SEND_SELECT_TR_SNAP, desk_serial, my_serial)
    msg.write_int(index)
    return msg.to_bytes()


def build_delete_tr_snap(desk_serial, my_serial, index):
    """Build SEND_DELETE_TR_SNAP (cmd=330). Payload: int index."""
    msg = TxMessage(MessageCode.SEND_DELETE_TR_SNAP, desk_serial, my_serial)
    msg.write_int(index)
    return msg.to_bytes()


def build_get_tr_list(desk_serial, my_serial):
    """Build GET_TR_LIST (cmd=64). No payload."""
    msg = TxMessage(MessageCode.GET_TR_LIST, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_tr_all_chans(desk_serial, my_serial):
    """Build SEND_SET_TR_ALL_CHANS (cmd=360). No payload."""
    msg = TxMessage(MessageCode.SEND_SET_TR_ALL_CHANS, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_tr_chan(desk_serial, my_serial, chan_index):
    """Build SEND_SET_TR_CHAN (cmd=370). Payload: int chanIndex."""
    msg = TxMessage(MessageCode.SEND_SET_TR_CHAN, desk_serial, my_serial)
    msg.write_int(chan_index)
    return msg.to_bytes()


def build_copy_tr_chan_data(desk_serial, my_serial, src, dest):
    """Build SEND_COPY_TR_CHAN_DATA (cmd=340). Payload: int src, int dest."""
    msg = TxMessage(MessageCode.SEND_COPY_TR_CHAN_DATA, desk_serial, my_serial)
    msg.write_int(src)
    msg.write_int(dest)
    return msg.to_bytes()


def build_swap_tr_chan_data(desk_serial, my_serial, src, dest):
    """Build SEND_SWOP_TR_CHAN_DATA (cmd=350). Payload: int src, int dest."""
    msg = TxMessage(MessageCode.SEND_SWOP_TR_CHAN_DATA, desk_serial, my_serial)
    msg.write_int(src)
    msg.write_int(dest)
    return msg.to_bytes()


# --- Handlers (Console -> Remote) ---


def handle_tr_enable_reply(rx, state):
    """Parse ACK_SET_TR_ENABLE (cmd=301) or ACK_GET_TR_STATE (cmd=303).

    Payload: boolean trEnabled
    """
    state.tr_enabled = rx.get_boolean()


def handle_tr_list_reply(rx, state):
    """Parse GET_TR_LIST_REPLY (cmd=65).

    Payload: string dirPath, then loop:
      short fileIndex (0=end), string name, string info,
      boolean isDir, string time, string date, int size,
      [boolean isSelected — if console supports it]
    """
    state.tr_snapshots.clear()
    state.selected_tr_index = -1
    _dir_path = rx.get_string()
    snap_index = 0
    while rx.remaining >= 2:
        file_index = rx.get_short()
        if file_index == 0:
            break
        name = rx.get_string()
        info = rx.get_string()
        _is_dir = rx.get_boolean()
        time_str = rx.get_string()
        date_str = rx.get_string()
        size = rx.get_int()
        # The Matrix console always sends the isSelected boolean per entry.
        # Read it unconditionally — the protocol always includes it.
        is_selected = rx.get_boolean() if rx.remaining >= 1 else False
        if is_selected:
            state.selected_tr_index = snap_index
        # Strip .trs extension from name
        if name.endswith(".trs"):
            name = name[:-4]
        state.tr_snapshots.append(
            TRSnapshot(
                name=name,
                info=info,
                time_str=time_str,
                date_str=date_str,
                size=size,
                is_selected=is_selected,
            )
        )
        snap_index += 1
