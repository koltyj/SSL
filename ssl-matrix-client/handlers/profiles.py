"""Profile and DAW layer handler: protocol get/set, profile CRUD, transport lock."""

from ..models import ProfileItem
from ..protocol import MessageCode, TxMessage


def build_get_daw_layer_protocol(desk_serial, my_serial, layer):
    """Build SEND_GET_DAW_LAYER_PROTOCOL (cmd=910). Payload: byte layer."""
    msg = TxMessage(MessageCode.SEND_GET_DAW_LAYER_PROTOCOL, desk_serial, my_serial)
    msg.write_byte(layer)
    return msg.to_bytes()


def handle_daw_layer_protocol_reply(rx, state):
    """Parse ACK_GET_DAW_LAYER_PROTOCOL (cmd=911).

    Payload: byte dawLayer, byte protocol
    """
    layer = rx.get_unsigned_byte()
    protocol = rx.get_unsigned_byte()
    dl = state.get_daw_layer(layer)
    if dl:
        dl.protocol = protocol


def build_get_profile_for_daw_layer(desk_serial, my_serial, layer):
    """Build SEND_GET_PROFILE_FOR_DAW_LAYER (cmd=800). Payload: byte layer."""
    msg = TxMessage(MessageCode.SEND_GET_PROFILE_FOR_DAW_LAYER, desk_serial, my_serial)
    msg.write_byte(layer)
    return msg.to_bytes()


def handle_profile_for_daw_layer_reply(rx, state):
    """Parse ACK_GET_PROFILE_FOR_DAW_LAYER (cmd=801).

    Payload: byte dawLayer, string profileName
    """
    layer = rx.get_unsigned_byte()
    profile_name = rx.get_string()
    dl = state.get_daw_layer(layer)
    if dl:
        dl.profile_name = profile_name


def build_set_profile_for_daw_layer(desk_serial, my_serial, layer, profile_name):
    """Build SEND_SET_PROFILE_FOR_DAW_LAYER (cmd=820).

    Payload: byte layer, string profileName
    """
    msg = TxMessage(MessageCode.SEND_SET_PROFILE_FOR_DAW_LAYER, desk_serial, my_serial)
    msg.write_byte(layer)
    msg.write_string(profile_name)
    return msg.to_bytes()


def build_clear_profile_for_daw_layer(desk_serial, my_serial, layer):
    """Build SEND_CLEAR_PROFILE_FOR_DAW_LAYER (cmd=830). Payload: byte layer."""
    msg = TxMessage(MessageCode.SEND_CLEAR_PROFILE_FOR_DAW_LAYER, desk_serial, my_serial)
    msg.write_byte(layer)
    return msg.to_bytes()


def build_get_profiles(desk_serial, my_serial):
    """Build SEND_GET_PROFILES (cmd=840). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_PROFILES, desk_serial, my_serial)
    return msg.to_bytes()


def handle_profiles_reply(rx, state):
    """Parse ACK_GET_PROFILES (cmd=841).

    Payload: int numProfiles, then repeating [string name, byte protocol,
             boolean readOnly, boolean inUse]
    """
    state.profiles.clear()
    num = rx.get_int()
    for _ in range(num):
        name = rx.get_string()
        protocol = rx.get_unsigned_byte()
        read_only = rx.get_boolean()
        in_use = rx.get_boolean()
        state.profiles.append(ProfileItem(name, protocol, read_only, in_use))


def build_get_transport_lock(desk_serial, my_serial):
    """Build SEND_GET_TRANSPORT_LOCK_DAW_LAYER (cmd=870). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_TRANSPORT_LOCK_DAW_LAYER, desk_serial, my_serial)
    return msg.to_bytes()


def handle_transport_lock_reply(rx, state):
    """Parse ACK_GET_TRANSPORT_LOCK_DAW_LAYER (cmd=871). Payload: byte layer."""
    state.transport_lock_layer = rx.get_unsigned_byte()


def build_set_transport_lock(desk_serial, my_serial, layer):
    """Build SEND_SET_TRANSPORT_LOCK_DAW_LAYER (cmd=880). Payload: byte layer."""
    msg = TxMessage(MessageCode.SEND_SET_TRANSPORT_LOCK_DAW_LAYER, desk_serial, my_serial)
    msg.write_byte(layer)
    return msg.to_bytes()


def build_copy_profile_to_new(desk_serial, my_serial, src_name, dest_name):
    """Build SEND_COPY_PROFILE_TO_NEW (cmd=810)."""
    msg = TxMessage(MessageCode.SEND_COPY_PROFILE_TO_NEW, desk_serial, my_serial)
    msg.write_string(src_name)
    msg.write_string(dest_name)
    return msg.to_bytes()


def build_delete_profile(desk_serial, my_serial, name):
    """Build SEND_DELETE_PROFILES (cmd=860)."""
    msg = TxMessage(MessageCode.SEND_DELETE_PROFILES, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_rename_profile(desk_serial, my_serial, old_name, new_name):
    """Build SEND_RENAME_PROFILES (cmd=850)."""
    msg = TxMessage(MessageCode.SEND_RENAME_PROFILES, desk_serial, my_serial)
    msg.write_string(old_name)
    msg.write_string(new_name)
    return msg.to_bytes()
