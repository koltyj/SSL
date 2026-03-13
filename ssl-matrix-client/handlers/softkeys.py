"""Softkeys handler: keymap editing, MIDI/USB key assignment, profile settings.

All payload formats from decompiled SoftKeysHandler.java.
"""

import logging

from ..models import KeyData
from ..protocol import MessageCode, TxMessage

log = logging.getLogger(__name__)


# =============================================================================
# Keymap editing
# =============================================================================


def build_get_edit_keymap_name(desk_serial, my_serial, daw_layer):
    """Build SEND_GET_EDIT_KEYMAP_NAME (cmd=600). Payload: byte dawLayer."""
    msg = TxMessage(MessageCode.SEND_GET_EDIT_KEYMAP_NAME, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    return msg.to_bytes()


def build_set_edit_keymap_name(desk_serial, my_serial, daw_layer, keymap_name):
    """Build SEND_SET_EDIT_KEYMAP_NAME (cmd=610). Payload: byte dawLayer, string name."""
    msg = TxMessage(MessageCode.SEND_SET_EDIT_KEYMAP_NAME, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_string(keymap_name)
    return msg.to_bytes()


def build_get_edit_keymap_data(desk_serial, my_serial, key_index, is_top_row, show_subs):
    """Build SEND_GET_EDIT_KEYMAP_DATA (cmd=620).

    Payload: byte keyIndex, byte isTopRow, byte showSubs
    """
    msg = TxMessage(MessageCode.SEND_GET_EDIT_KEYMAP_DATA, desk_serial, my_serial)
    msg.write_byte(key_index)
    msg.write_byte(is_top_row)
    msg.write_byte(show_subs)
    return msg.to_bytes()


def build_get_edit_keymap_size(desk_serial, my_serial):
    """Build SEND_GET_EDIT_KEYMAP_SIZE (cmd=640). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_EDIT_KEYMAP_SIZE, desk_serial, my_serial)
    return msg.to_bytes()


def build_save_edit_keymap(desk_serial, my_serial):
    """Build SEND_SET_SAVE_EDIT_KEYMAP (cmd=680). No payload."""
    msg = TxMessage(MessageCode.SEND_SET_SAVE_EDIT_KEYMAP, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_keycap_name(desk_serial, my_serial, key_index, is_top_row, name):
    """Build SEND_SET_KEYCAP_NAME (cmd=660). Payload: byte key, byte row, string name."""
    msg = TxMessage(MessageCode.SEND_SET_KEYCAP_NAME, desk_serial, my_serial)
    msg.write_byte(key_index)
    msg.write_byte(is_top_row)
    msg.write_string(name)
    return msg.to_bytes()


def build_set_key_blank(desk_serial, my_serial, key_index, is_top_row):
    """Build SEND_SET_KEY_BLANK (cmd=670). Payload: byte key, byte row."""
    msg = TxMessage(MessageCode.SEND_SET_KEY_BLANK, desk_serial, my_serial)
    msg.write_byte(key_index)
    msg.write_byte(is_top_row)
    return msg.to_bytes()


# =============================================================================
# USB/MIDI key commands
# =============================================================================


def build_set_usb_cmd(desk_serial, my_serial, daw_layer, key_index, is_top_row, usb_cmd):
    """Build SEND_SET_USB_CMD (cmd=650).

    Payload: byte dawLayer, byte keyIndex, byte isTopRow, string usbCmd
    """
    msg = TxMessage(MessageCode.SEND_SET_USB_CMD, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(key_index)
    msg.write_byte(is_top_row)
    msg.write_string(usb_cmd)
    return msg.to_bytes()


def build_set_midi_cmd(desk_serial, my_serial, daw_layer, is_top_row, key_index, func_index):
    """Build SEND_SET_MIDI_CMD (cmd=700).

    Payload: byte dawLayer, byte isTopRow, byte keyIndex, byte functionIndex
    """
    msg = TxMessage(MessageCode.SEND_SET_MIDI_CMD, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(is_top_row)
    msg.write_byte(key_index)
    msg.write_byte(func_index)
    return msg.to_bytes()


def build_get_midi_function_list(desk_serial, my_serial, daw_layer):
    """Build SEND_GET_MIDI_FUNCTION_LIST (cmd=690). Payload: byte dawLayer."""
    msg = TxMessage(MessageCode.SEND_GET_MIDI_FUNCTION_LIST, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    return msg.to_bytes()


def build_set_new_menu_cmd(desk_serial, my_serial, daw_layer, key_index):
    """Build SEND_SET_NEW_MENU_CMD (cmd=710). Payload: byte dawLayer, byte keyIndex."""
    msg = TxMessage(MessageCode.SEND_SET_NEW_MENU_CMD, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(key_index)
    return msg.to_bytes()


# =============================================================================
# Menu sub-key commands
# =============================================================================


def build_set_menu_sub_keycap_name(desk_serial, my_serial, daw_layer, key_index, sub_index, name):
    """Build SEND_SET_MENU_SUB_KEYCAP_NAME (cmd=720)."""
    msg = TxMessage(MessageCode.SEND_SET_MENU_SUB_KEYCAP_NAME, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(key_index)
    msg.write_byte(sub_index)
    msg.write_string(name)
    return msg.to_bytes()


def build_set_menu_sub_midi_cmd(
    desk_serial, my_serial, daw_layer, key_index, sub_index, func_index
):
    """Build SEND_SET_MENU_SUB_MIDI_CMD (cmd=730)."""
    msg = TxMessage(MessageCode.SEND_SET_MENU_SUB_MIDI_CMD, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(key_index)
    msg.write_byte(sub_index)
    msg.write_byte(func_index)
    return msg.to_bytes()


def build_set_menu_sub_usb_cmd(desk_serial, my_serial, daw_layer, key_index, sub_index, usb_cmd):
    """Build SEND_SET_MENU_SUB_USB_CMD (cmd=740)."""
    msg = TxMessage(MessageCode.SEND_SET_MENU_SUB_USB_CMD, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(key_index)
    msg.write_byte(sub_index)
    msg.write_string(usb_cmd)
    return msg.to_bytes()


def build_set_menu_sub_blank_cmd(desk_serial, my_serial, daw_layer, key_index, sub_index):
    """Build SEND_SET_MENU_SUB_BLANK_CMD (cmd=750)."""
    msg = TxMessage(MessageCode.SEND_SET_MENU_SUB_BLANK_CMD, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(key_index)
    msg.write_byte(sub_index)
    return msg.to_bytes()


def build_follow_key_state(desk_serial, my_serial, daw_layer, key_index, is_top_row, state_val):
    """Build SEND_FOLLOW_KEY_STATE (cmd=770)."""
    msg = TxMessage(MessageCode.SEND_FOLLOW_KEY_STATE, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(key_index)
    msg.write_byte(is_top_row)
    msg.write_byte(state_val)
    return msg.to_bytes()


# =============================================================================
# Profile settings within softkeys context
# =============================================================================


def build_get_flip_status(desk_serial, my_serial, daw_layer):
    """Build SEND_GET_FLIP_STATUS (cmd=1000). Payload: byte dawLayer."""
    msg = TxMessage(MessageCode.SEND_GET_FLIP_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    return msg.to_bytes()


def build_set_flip_status(desk_serial, my_serial, daw_layer, flip):
    """Build SEND_SET_FLIP_STATUS (cmd=1010). Payload: byte dawLayer, byte flip."""
    msg = TxMessage(MessageCode.SEND_SET_FLIP_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(flip)
    return msg.to_bytes()


def build_get_handshake(desk_serial, my_serial, daw_layer):
    """Build SEND_GET_HANDSHAKING_STATUS (cmd=1020). Payload: byte dawLayer."""
    msg = TxMessage(MessageCode.SEND_GET_HANDSHAKING_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    return msg.to_bytes()


def build_set_handshake(desk_serial, my_serial, daw_layer, handshake):
    """Build SEND_SET_HANDSHAKING_STATUS (cmd=1030). Payload: byte dawLayer, byte handshake."""
    msg = TxMessage(MessageCode.SEND_SET_HANDSHAKING_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(handshake)
    return msg.to_bytes()


def build_get_auto_mode_on_scribs(desk_serial, my_serial, daw_layer):
    """Build SEND_GET_AUTO_MODE_ON_SCRIBS_STATUS (cmd=1040). Payload: byte dawLayer."""
    msg = TxMessage(MessageCode.SEND_GET_AUTO_MODE_ON_SCRIBS_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    return msg.to_bytes()


def build_set_auto_mode_on_scribs(desk_serial, my_serial, daw_layer, state_val):
    """Build SEND_SET_AUTO_MODE_ON_SCRIBS_STATUS (cmd=1050). Payload: byte dawLayer, byte state."""
    msg = TxMessage(MessageCode.SEND_SET_AUTO_MODE_ON_SCRIBS_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(state_val)
    return msg.to_bytes()


def build_get_default_wheel_mode(desk_serial, my_serial, daw_layer):
    """Build SEND_GET_DEFAULT_WHEEL_MODE_STATUS (cmd=1060). Payload: byte dawLayer."""
    msg = TxMessage(MessageCode.SEND_GET_DEFAULT_WHEEL_MODE_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    return msg.to_bytes()


def build_set_default_wheel_mode(desk_serial, my_serial, daw_layer, mode):
    """Build SEND_SET_DEFAULT_WHEEL_MODE_STATUS (cmd=1070). Payload: byte dawLayer, byte mode."""
    msg = TxMessage(MessageCode.SEND_SET_DEFAULT_WHEEL_MODE_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(mode)
    return msg.to_bytes()


def build_get_fader_db_readout(desk_serial, my_serial, daw_layer):
    """Build SEND_GET_FADER_DB_READOUT_STATUS (cmd=1090). Payload: byte daw."""
    msg = TxMessage(MessageCode.SEND_GET_FADER_DB_READOUT_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    return msg.to_bytes()


def build_set_fader_db_readout(desk_serial, my_serial, daw_layer, status):
    """Build SEND_SET_FADER_DB_READOUT_STATUS (cmd=1080). Payload: byte dawLayer, byte status."""
    msg = TxMessage(MessageCode.SEND_SET_FADER_DB_READOUT_STATUS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(1 if status else 0)
    return msg.to_bytes()


def build_save_profile_as(desk_serial, my_serial, daw_layer, name):
    """Build SEND_SAVE_PROFILE_AS (cmd=920). Payload: byte dawLayer, string name."""
    msg = TxMessage(MessageCode.SEND_SAVE_PROFILE_AS, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_string(name)
    return msg.to_bytes()


def build_get_profile_path(desk_serial, my_serial, name):
    """Build SEND_GET_PROFILE_PATH (cmd=940). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_GET_PROFILE_PATH, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_profile_name_exists(desk_serial, my_serial, name):
    """Build SEND_PROFILE_NAME_EXISTS (cmd=890). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_PROFILE_NAME_EXISTS, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_get_cc_names_list(desk_serial, my_serial, daw_layer, cc_type):
    """Build SEND_GET_CC_NAMES_LIST (cmd=950). Payload: byte dawLayer, byte type."""
    msg = TxMessage(MessageCode.SEND_GET_CC_NAMES_LIST, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(cc_type)
    return msg.to_bytes()


def build_set_cc_names_list(desk_serial, my_serial, daw_layer, cc_type, names):
    """Build SEND_SET_CC_NAMES_LIST (cmd=960).

    Payload: byte dawLayer, byte type, byte numNames, then numNames x string name
    """
    if len(names) > 255:
        raise ValueError(f"CC names list too long: {len(names)} (max 255)")
    msg = TxMessage(MessageCode.SEND_SET_CC_NAMES_LIST, desk_serial, my_serial)
    msg.write_byte(daw_layer)
    msg.write_byte(cc_type)
    msg.write_byte(len(names))
    for name in names:
        msg.write_string(name)
    return msg.to_bytes()


# =============================================================================
# Handlers (Console -> Remote)
# =============================================================================


def handle_edit_keymap_name_reply(rx, state):
    """Parse ACK_GET_EDIT_KEYMAP_NAME (cmd=601). Payload: string name, byte dawLayer."""
    state.softkeys.keymap_name = rx.get_string()
    state.softkeys.daw_layer = rx.get_unsigned_byte()


def handle_edit_keymap_data_reply(rx, state):
    """Parse ACK_GET_EDIT_KEYMAP_DATA (cmd=621).

    Payload: byte inEdit, byte showSubs, then loop:
      byte keyIndex (0=end), byte isTopRow, byte keyType, string keycapName,
      then type-specific data
    """
    sk = state.softkeys
    in_edit = rx.get_unsigned_byte()
    sk.in_edit = in_edit != 0
    if not sk.in_edit:
        sk.keys.clear()
        return
    rx.get_unsigned_byte()  # show_subs — consumed for cursor alignment
    sk.keys.clear()
    while rx.remaining > 0:
        key_index = rx.get_unsigned_byte()
        if key_index == 0:
            break
        is_top_row = rx.get_unsigned_byte()
        key_type = rx.get_unsigned_byte()
        keycap_name = rx.get_string()
        data = ""
        if key_type == 0:  # blank
            # Always consume the trailing string regardless of show_subs,
            # to keep the parse cursor aligned for subsequent keys.
            rx.get_string()  # skip
            data = ""
        elif key_type == 1:  # midi
            func_count = rx.get_unsigned_byte()
            parts = []
            for _ in range(func_count):
                parts.append(rx.get_string())
            data = "  ".join(parts)
        elif key_type == 2:  # usb
            data = rx.get_string()
        elif key_type == 3:  # menu
            rx.get_string()  # skip
            data = "Menu"
        sk.keys.append(
            KeyData(
                index=key_index,
                is_top_row=is_top_row,
                key_type=key_type,
                keycap_name=keycap_name,
                data=data,
            )
        )


def handle_edit_keymap_size_reply(rx, state):
    """Parse ACK_GET_EDIT_KEYMAP_SIZE (cmd=641).

    Payload: byte numKeysOnRow, boolean unsavedData
    """
    num_keys = rx.get_unsigned_byte()
    if num_keys == 15:
        state.softkeys.panel_type = 1  # transport
    elif num_keys == 8:
        state.softkeys.panel_type = 2  # softkey
    else:
        state.softkeys.panel_type = 0  # blank
    unsaved = rx.get_boolean()
    state.softkeys.unsaved_data = unsaved if num_keys > 0 else False


def handle_midi_function_list_reply(rx, state):
    """Parse ACK_GET_MIDI_FUNCTION_LIST (cmd=691).

    Payload: byte listLength, byte listLengthOffset,
             then listLength x (string userName, string keycapName)
    """
    sk = state.softkeys
    list_length = rx.get_unsigned_byte()
    if list_length == 0:
        sk.midi_functions.clear()
        return
    offset = rx.get_unsigned_byte()
    if offset == 0:
        sk.midi_functions.clear()
    else:
        # Trim any existing entries at or beyond this offset to prevent
        # duplication on retransmits
        sk.midi_functions = [entry for entry in sk.midi_functions if entry[0] < offset]
    for j in range(list_length):
        user_name = rx.get_string()
        keycap_name = rx.get_string()
        sk.midi_functions.append((j + offset, user_name, keycap_name))


def handle_flip_status_reply(rx, state):
    """Parse ACK_GET_FLIP_STATUS (cmd=1001). Payload: byte skip, byte flip."""
    rx.get_unsigned_byte()  # dawLayer skip
    flip = rx.get_unsigned_byte()
    state.softkeys.flip_status = flip == 1


def handle_handshake_reply(rx, state):
    """Parse ACK_GET_HANDSHAKING_STATUS (cmd=1021). Payload: byte skip, byte handshake."""
    rx.get_unsigned_byte()  # dawLayer skip
    handshake = rx.get_unsigned_byte()
    state.softkeys.handshake = handshake == 0  # inverted: 0=enabled


def handle_auto_mode_on_scribs_reply(rx, state):
    """Parse ACK_GET_AUTO_MODE_ON_SCRIBS_STATUS (cmd=1041). Payload: byte skip, byte state."""
    rx.get_unsigned_byte()  # dawLayer skip
    val = rx.get_unsigned_byte()
    state.softkeys.auto_mode_on_scribs = val == 1


def handle_default_wheel_mode_reply(rx, state):
    """Parse ACK_GET_DEFAULT_WHEEL_MODE_STATUS (cmd=1061). Payload: byte skip, byte mode."""
    rx.get_unsigned_byte()  # dawLayer skip
    state.softkeys.default_wheel_mode = rx.get_unsigned_byte()


def handle_fader_db_readout_reply(rx, state):
    """Parse ACK_GET_FADER_DB_READOUT_STATUS (cmd=1091). Payload: byte daw, byte res."""
    _daw = rx.get_unsigned_byte()
    state.softkeys.fader_db_readout = rx.get_unsigned_byte()


def handle_softkey_ack(rx, state):
    """Handle generic ACK for softkey commands. Payload: string reply.

    Used for: 611, 651, 661, 671, 681, 701, 711, 721, 731, 741, 751, 771,
              811, 821, 831, 851, 861, 881, 921, 961, 1011, 1031, 1051, 1071, 1081
    """
    reply = rx.get_string()
    if reply.lower() != "ok":
        log.warning("Softkey ACK error: %s (cmd=%d)", reply, rx.cmd_code)


def handle_cc_names_list_reply(rx, state):
    """Parse ACK_GET_CC_NAMES_LIST (cmd=951).

    Payload: byte numNames, then numNames x string name
    """
    num = rx.get_unsigned_byte()
    names = []
    for _ in range(num):
        names.append(rx.get_string())
    state.softkeys.cc_names = names


def handle_profile_path_reply(rx, state):
    """Parse ACK_GET_PROFILE_PATH (cmd=941). Payload: string path."""
    _path = rx.get_string()
    # Informational — not stored in state
