"""Tests for handlers/channels.py."""

import struct

from conftest import build_rx_packet, payload_byte, payload_int, payload_string
from ssl_matrix_client.handlers.channels import (
    build_set_chan_name,
    handle_chan_names_reply,
    handle_get_display_17_32_reply,
    handle_get_flip_scrib_strip_reply,
)
from ssl_matrix_client.protocol import MessageCode


class TestHandleChanNamesReply:
    def test_parse_multiple(self, state):
        payload = (
            payload_byte(1)
            + payload_string("KICK")
            + payload_byte(2)
            + payload_string("SNARE")
            + payload_byte(0)  # terminator
        )
        rx = build_rx_packet(MessageCode.GET_CHAN_NAMES_AND_IMAGES_REPLY, payload)
        handle_chan_names_reply(rx, state)
        assert state.get_channel(1).name == "KICK"
        assert state.get_channel(2).name == "SNARE"

    def test_terminator_stops(self, state):
        payload = (
            payload_byte(1)
            + payload_string("VOX")
            + payload_byte(0)  # terminator — stop here
            + payload_byte(3)
            + payload_string("IGNORED")
        )
        rx = build_rx_packet(MessageCode.GET_CHAN_NAMES_AND_IMAGES_REPLY, payload)
        handle_chan_names_reply(rx, state)
        assert state.get_channel(1).name == "VOX"
        assert state.get_channel(3).name == ""

    def test_empty_packet(self, state):
        rx = build_rx_packet(MessageCode.GET_CHAN_NAMES_AND_IMAGES_REPLY, payload_byte(0))
        handle_chan_names_reply(rx, state)
        assert all(ch.name == "" for ch in state.channels)


class TestBuildSetChanName:
    def test_builder(self):
        data = build_set_chan_name(1000, 99, 5, "BASS")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SET_CHAN_NAMES
        # Payload: byte chan=5, string "BASS\0", byte 0 (terminator)
        assert data[16] == 5
        assert data[17:22] == b"BASS\x00"
        assert data[22] == 0


class TestDisplay1732:
    def test_handler(self, state):
        rx = build_rx_packet(MessageCode.ACK_GET_DISPLAY_17_32, payload_int(1))
        handle_get_display_17_32_reply(rx, state)
        assert state.display_17_32 == 1


class TestFlipScrib:
    def test_handler(self, state):
        rx = build_rx_packet(MessageCode.ACK_GET_FLIP_SCRIB_STRIP, payload_int(1))
        handle_get_flip_scrib_strip_reply(rx, state)
        assert state.flip_scrib == 1


class TestOutOfRangeChannel:
    def test_chan_33_ignored(self, state):
        """Channel 33 is out of range — get_channel returns None, no crash."""
        payload = payload_byte(33) + payload_string("GHOST") + payload_byte(0)
        rx = build_rx_packet(MessageCode.GET_CHAN_NAMES_AND_IMAGES_REPLY, payload)
        handle_chan_names_reply(rx, state)
        # No channel should have been modified
        assert all(ch.name == "" for ch in state.channels)
