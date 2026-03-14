"""Channel names handler: read/write channel names, display 17-32, flip scribble."""

from ..protocol import MessageCode, TxMessage


def build_get_chan_names(desk_serial, my_serial, first=0, last=0):
    """Build GET_CHAN_NAMES_AND_IMAGES (cmd=20).

    Payload: byte first, byte last (0,0 = get all)
    """
    msg = TxMessage(MessageCode.GET_CHAN_NAMES_AND_IMAGES, desk_serial, my_serial)
    msg.write_byte(first)
    msg.write_byte(last)
    return msg.to_bytes()


def handle_chan_names_reply(rx, state):
    """Parse GET_CHAN_NAMES_AND_IMAGES_REPLY (cmd=21).

    Payload: repeating [byte chan, string name] terminated by chan=0.
    Matrix has hasImages=false, so no image string.
    """
    while rx.remaining >= 1:
        chan = rx.get_unsigned_byte()
        if chan == 0:
            break
        name = rx.get_string()
        ch = state.get_channel(chan)
        if ch:
            ch.name = name


def handle_set_chan_names_reply(rx, state):
    """Parse SET_CHAN_NAMES_REPLY (cmd=32) or SET_DEFAULT_CHAN_NAMES_REPLY (cmd=29).

    Same format as chan_names_reply: repeating [byte chan, string name] terminated by 0.
    """
    handle_chan_names_reply(rx, state)


def build_set_chan_name(desk_serial, my_serial, channel, name):
    """Build SET_CHAN_NAMES (cmd=30).

    Payload: byte chan, string name, byte 0 (terminator)
    """
    msg = TxMessage(MessageCode.SET_CHAN_NAMES, desk_serial, my_serial)
    msg.write_byte(channel)
    msg.write_string(name)
    msg.write_byte(0)  # terminator
    return msg.to_bytes()


def build_set_default_chan_names(desk_serial, my_serial):
    """Build SET_DEFAULT_CHAN_NAMES (cmd=28). No payload — resets all names."""
    msg = TxMessage(MessageCode.SET_DEFAULT_CHAN_NAMES, desk_serial, my_serial)
    return msg.to_bytes()


def build_get_display_17_32(desk_serial, my_serial):
    """Build SEND_GET_DISPLAY_17_32 (cmd=10740)."""
    msg = TxMessage(MessageCode.SEND_GET_DISPLAY_17_32, desk_serial, my_serial)
    return msg.to_bytes()


def handle_get_display_17_32_reply(rx, state):
    """Parse ACK_GET_DISPLAY_17_32 (cmd=10741). Payload: int state."""
    state.display_17_32 = rx.get_int()


def build_set_display_17_32(desk_serial, my_serial, enable):
    """Build SEND_SET_DISPLAY_17_32 (cmd=10730). Payload: byte enable."""
    msg = TxMessage(MessageCode.SEND_SET_DISPLAY_17_32, desk_serial, my_serial)
    msg.write_byte(1 if enable else 0)
    return msg.to_bytes()


def build_get_flip_scrib_strip(desk_serial, my_serial):
    """Build SEND_GET_FLIP_SCRIB_STRIP (cmd=10760)."""
    msg = TxMessage(MessageCode.SEND_GET_FLIP_SCRIB_STRIP, desk_serial, my_serial)
    return msg.to_bytes()


def handle_get_flip_scrib_strip_reply(rx, state):
    """Parse ACK_GET_FLIP_SCRIB_STRIP (cmd=10761). Payload: int state."""
    state.flip_scrib = rx.get_int()


def build_set_flip_scrib_strip(desk_serial, my_serial, enable):
    """Build SEND_SET_FLIP_SCRIB_STRIP (cmd=10750). Payload: byte enable."""
    msg = TxMessage(MessageCode.SEND_SET_FLIP_SCRIB_STRIP, desk_serial, my_serial)
    msg.write_byte(1 if enable else 0)
    return msg.to_bytes()
