"""Tests for handlers/delta.py."""

import struct

from conftest import build_rx_packet, payload_byte
from ssl_matrix_client.handlers.delta import (
    build_restart_console,
    build_set_auto_mode,
    handle_auto_mode_reply,
    handle_mdac_meters_reply,
    handle_motors_off_reply,
)
from ssl_matrix_client.protocol import MessageCode


class TestAutoMode:
    def test_handler(self, state):
        rx = build_rx_packet(MessageCode.ACK_GET_AUTOMATION_MODE, payload_byte(1))
        handle_auto_mode_reply(rx, state)
        assert state.automation_mode == 1

    def test_builder(self):
        data = build_set_auto_mode(1000, 99, 1)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_AUTOMATION_MODE
        assert data[16] == 1


class TestMotorsOff:
    def test_handler(self, state):
        rx = build_rx_packet(MessageCode.ACK_GET_MOTORS_OFF_TOUCH_EN, payload_byte(1))
        handle_motors_off_reply(rx, state)
        assert state.motors_off == 1


class TestMdacMeters:
    def test_handler(self, state):
        rx = build_rx_packet(MessageCode.ACK_GET_MDAC_METER_EN, payload_byte(1))
        handle_mdac_meters_reply(rx, state)
        assert state.mdac_meters == 1


class TestRestart:
    def test_builder_cmd_code(self):
        data = build_restart_console(1000, 99)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_RESTART_CONSOLE
        assert cmd == 760
