"""Delta handler: automation mode, motors off, MDAC meters, restart."""

from ..protocol import MessageCode, TxMessage


def build_get_auto_mode(desk_serial, my_serial):
    """Build SEND_GET_AUTOMATION_MODE (cmd=10900). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_AUTOMATION_MODE, desk_serial, my_serial)
    return msg.to_bytes()


def handle_auto_mode_reply(rx, state):
    """Parse ACK_GET_AUTOMATION_MODE (cmd=10901). Payload: byte mode (0=Legacy, 1=Delta)."""
    state.automation_mode = rx.get_unsigned_byte()


def build_set_auto_mode(desk_serial, my_serial, mode):
    """Build SEND_SET_AUTOMATION_MODE (cmd=11000). Payload: byte mode."""
    msg = TxMessage(MessageCode.SEND_SET_AUTOMATION_MODE, desk_serial, my_serial)
    msg.write_byte(mode)
    return msg.to_bytes()


def build_get_motors_off(desk_serial, my_serial):
    """Build SEND_GET_MOTORS_OFF_TOUCH_EN (cmd=11100). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_MOTORS_OFF_TOUCH_EN, desk_serial, my_serial)
    return msg.to_bytes()


def handle_motors_off_reply(rx, state):
    """Parse ACK_GET_MOTORS_OFF_TOUCH_EN (cmd=11101). Payload: byte enable."""
    state.motors_off = rx.get_unsigned_byte()


def build_set_motors_off(desk_serial, my_serial, enable):
    """Build SEND_SET_MOTORS_OFF_TOUCH_EN (cmd=11200). Payload: byte enable."""
    msg = TxMessage(MessageCode.SEND_SET_MOTORS_OFF_TOUCH_EN, desk_serial, my_serial)
    msg.write_byte(enable)
    return msg.to_bytes()


def build_get_mdac_meters(desk_serial, my_serial):
    """Build SEND_GET_MDAC_METER_EN (cmd=11300). No payload."""
    msg = TxMessage(MessageCode.SEND_GET_MDAC_METER_EN, desk_serial, my_serial)
    return msg.to_bytes()


def handle_mdac_meters_reply(rx, state):
    """Parse ACK_GET_MDAC_METER_EN (cmd=11301). Payload: byte enable."""
    state.mdac_meters = rx.get_unsigned_byte()


def build_set_mdac_meters(desk_serial, my_serial, enable):
    """Build SEND_SET_MDAC_METER_EN (cmd=11400). Payload: byte enable."""
    msg = TxMessage(MessageCode.SEND_SET_MDAC_METER_EN, desk_serial, my_serial)
    msg.write_byte(enable)
    return msg.to_bytes()


def build_restart_console(desk_serial, my_serial):
    """Build SEND_RESTART_CONSOLE (cmd=760). No payload."""
    msg = TxMessage(MessageCode.SEND_RESTART_CONSOLE, desk_serial, my_serial)
    return msg.to_bytes()
