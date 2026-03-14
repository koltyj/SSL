"""Connection handler: discovery, heartbeat, timeout/reconnect."""

import time

from ..protocol import MessageCode, TxMessage


def build_get_desk(my_serial):
    """Build GET_DESK discovery packet (cmd=5, deskSerial=0)."""
    msg = TxMessage(MessageCode.GET_DESK, 0, my_serial)
    return msg.to_bytes()


def handle_get_desk_reply(rx, state):
    """Parse GET_DESK_REPLY (cmd=6) and update state.desk.

    Payload: string prodName, int ver, int sub, int issue, byte skip,
             string built, string time, byte skip, byte skip, string ownName
    """
    desk = state.desk
    desk.serial = rx.desk_serial
    desk.product_name = rx.get_string()
    desk.version = rx.get_int()
    desk.sub = rx.get_int()
    desk.issue = rx.get_int()
    rx.get_unsigned_byte()  # skip
    desk.built_str = rx.get_string()
    desk.time_str = rx.get_string()
    rx.get_unsigned_byte()  # skip
    rx.get_unsigned_byte()  # skip
    desk.console_name = rx.get_string()
    desk.online = True
    desk.last_heartbeat = time.time()


def handle_heartbeat(rx, state):
    """Parse SEND_HEARTBEAT (cmd=7) and update last_heartbeat.

    Payload: string prodName
    """
    rx.get_string()  # prodName — consumed but not stored
    state.desk.last_heartbeat = time.time()
    if not state.desk.online:
        state.desk.online = True


def handle_project_name_and_title_reply(rx, state):
    """Parse GET_PROJECT_NAME_AND_TITLE_REPLY (cmd=11).

    Payload: string projectName, string projectInfo, string titleName, string titleInfo
    """
    state.project_name = rx.get_string()
    _project_info = rx.get_string()
    state.title_name = rx.get_string()
    _title_info = rx.get_string()
