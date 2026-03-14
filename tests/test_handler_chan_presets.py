"""Tests for handlers/chan_presets.py."""

import struct

from conftest import build_rx_packet, payload_int, payload_string
from ssl_matrix_client.handlers.chan_presets import (
    build_save_chan_names_preset,
    handle_chan_names_preset_ack,
    handle_chan_names_preset_list_reply,
)
from ssl_matrix_client.protocol import MessageCode


class TestPresetList:
    def test_parse(self, state):
        payload = payload_int(2) + payload_string("Drums") + payload_string("Strings")
        rx = build_rx_packet(MessageCode.ACK_GET_CHAN_NAMES_PRESET_LIST, payload)
        handle_chan_names_preset_list_reply(rx, state)
        assert len(state.chan_names_presets) == 2
        assert state.chan_names_presets[0].name == "Drums"
        assert state.chan_names_presets[1].name == "Strings"


class TestPresetAck:
    def test_ok(self, state):
        rx = build_rx_packet(MessageCode.ACK_SAVE_CHAN_NAMES_PRESET, payload_string("ok"))
        handle_chan_names_preset_ack(rx, state)  # no error


class TestSaveBuilder:
    def test_builder(self):
        data = build_save_chan_names_preset(1000, 99, "MyPreset")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SAVE_CHAN_NAMES_PRESET
        assert b"MyPreset\x00" in data[16:]
