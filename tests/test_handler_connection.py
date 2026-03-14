"""Tests for handlers/connection.py."""

import struct
import time

from conftest import build_rx_packet, payload_byte, payload_int, payload_string
from ssl_matrix_client.handlers.connection import (
    build_get_desk,
    handle_get_desk_reply,
    handle_heartbeat,
    handle_project_name_and_title_reply,
)
from ssl_matrix_client.protocol import TO_DESK, MessageCode


class TestBuildGetDesk:
    def test_header(self):
        data = build_get_desk(12345)
        cmd, dest, desk, remote = struct.unpack_from(">iiii", data)
        assert cmd == MessageCode.GET_DESK
        assert dest == TO_DESK
        assert desk == 0
        assert remote == 12345


class TestHandleGetDeskReply:
    def test_full_parse(self, state):
        payload = (
            payload_string("SSL Matrix")
            + payload_int(3)
            + payload_int(0)
            + payload_int(5)
            + payload_byte(0)  # skip
            + payload_string("Jan 01 2024")
            + payload_string("12:00:00")
            + payload_byte(0)
            + payload_byte(0)  # skip
            + payload_string("MyConsole")
        )
        rx = build_rx_packet(MessageCode.GET_DESK_REPLY, payload)
        handle_get_desk_reply(rx, state)
        assert state.desk.product_name == "SSL Matrix"
        assert state.desk.version == 3
        assert state.desk.sub == 0
        assert state.desk.issue == 5
        assert state.desk.built_str == "Jan 01 2024"
        assert state.desk.time_str == "12:00:00"
        assert state.desk.console_name == "MyConsole"
        assert state.desk.online is True
        assert state.desk.serial == 1000  # from build_rx_packet default


class TestHandleHeartbeat:
    def test_online_flip(self, state):
        state.desk.online = False
        rx = build_rx_packet(MessageCode.SEND_HEARTBEAT, payload_string("SSL Matrix"))
        handle_heartbeat(rx, state)
        assert state.desk.online is True
        assert state.desk.last_heartbeat > 0

    def test_updates_timestamp(self, state):
        state.desk.online = True
        before = time.time()
        rx = build_rx_packet(MessageCode.SEND_HEARTBEAT, payload_string("SSL Matrix"))
        handle_heartbeat(rx, state)
        assert state.desk.last_heartbeat >= before


class TestHandleProjectNameAndTitle:
    def test_parse(self, state):
        payload = (
            payload_string("MyProject")
            + payload_string("info1")
            + payload_string("MyTitle")
            + payload_string("info2")
        )
        rx = build_rx_packet(MessageCode.GET_PROJECT_NAME_AND_TITLE_REPLY, payload)
        handle_project_name_and_title_reply(rx, state)
        assert state.project_name == "MyProject"
        assert state.title_name == "MyTitle"
