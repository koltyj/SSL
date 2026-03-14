"""Tests for handlers/xpatch.py."""

import struct

from conftest import (
    build_rx_packet,
    payload_bool,
    payload_int,
    payload_string,
)
from ssl_matrix_client.handlers.xpatch import (
    NUM_CHAIN_ELEMENTS,
    NUM_CHANS,
    build_delete_preset,
    build_send_chain_data,
    build_set_device_name,
    build_set_midi_enable,
    build_set_preset_selected,
    build_set_route,
    handle_chains_list_reply,
    handle_chan_mode_reply,
    handle_chan_setup_reply,
    handle_dest_name_reply,
    handle_device_name_reply,
    handle_input_minus_10db_reply,
    handle_midi_setup_reply,
    handle_output_minus_10db_reply,
    handle_preset_edited_reply,
    handle_preset_selected_reply,
    handle_presets_list_reply,
    handle_routing_data_reply,
)
from ssl_matrix_client.protocol import MessageCode


class TestChanSetup:
    def test_parse_16_channels(self, state):
        payload = b""
        for i in range(NUM_CHANS):
            payload += (
                payload_int(0)  # skip
                + payload_bool(i == 0)  # in10 only for chan 1
                + payload_bool(False)  # out10
                + payload_int(i)  # mode
                + payload_string(f"Dev{i + 1}")
                + payload_string(f"Dest{i + 1}")
            )
        rx = build_rx_packet(MessageCode.GET_XPATCH_CHAN_SETUP_REPLY, payload)
        handle_chan_setup_reply(rx, state)
        xp = state.xpatch
        assert xp.channels[0].device_name == "Dev1"
        assert xp.channels[0].dest_name == "Dest1"
        assert xp.channels[0].input_minus_10db is True
        assert xp.channels[15].device_name == "Dev16"
        assert xp.channels[15].mode == 15

    def test_default_names(self, state):
        """Empty device/dest names get defaults."""
        payload = b""
        for _i in range(NUM_CHANS):
            payload += (
                payload_int(0)
                + payload_bool(False)
                + payload_bool(False)
                + payload_int(0)
                + payload_string("")
                + payload_string("")
            )
        rx = build_rx_packet(MessageCode.GET_XPATCH_CHAN_SETUP_REPLY, payload)
        handle_chan_setup_reply(rx, state)
        assert state.xpatch.channels[0].device_name == "Source 1"
        assert state.xpatch.channels[0].dest_name == "Destination 1"
        assert state.xpatch.channels[15].device_name == "Source 16"


class TestInputMinus10db:
    def test_handler(self, state):
        payload = payload_int(3) + payload_bool(True)
        rx = build_rx_packet(MessageCode.SET_XPATCH_INPUT_MINUS10DB_REPLY, payload)
        handle_input_minus_10db_reply(rx, state)
        assert state.xpatch.channels[2].input_minus_10db is True


class TestOutputMinus10db:
    def test_handler(self, state):
        payload = payload_int(5) + payload_bool(True)
        rx = build_rx_packet(MessageCode.SET_XPATCH_OUTPUT_MINUS10DB_REPLY, payload)
        handle_output_minus_10db_reply(rx, state)
        assert state.xpatch.channels[4].output_minus_10db is True


class TestChanMode:
    def test_handler(self, state):
        payload = payload_int(1) + payload_int(2)
        rx = build_rx_packet(MessageCode.SET_XPATCH_CHAN_MODE_REPLY, payload)
        handle_chan_mode_reply(rx, state)
        assert state.xpatch.channels[0].mode == 2


class TestDeviceName:
    def test_handler(self, state):
        payload = payload_int(2) + payload_string("Reverb")
        rx = build_rx_packet(MessageCode.SET_XPATCH_DEVICE_NAME_REPLY, payload)
        handle_device_name_reply(rx, state)
        assert state.xpatch.channels[1].device_name == "Reverb"

    def test_empty_default(self, state):
        payload = payload_int(3) + payload_string("")
        rx = build_rx_packet(MessageCode.SET_XPATCH_DEVICE_NAME_REPLY, payload)
        handle_device_name_reply(rx, state)
        assert state.xpatch.channels[2].device_name == "Source 3"


class TestDestName:
    def test_empty_default(self, state):
        payload = payload_int(4) + payload_string("")
        rx = build_rx_packet(MessageCode.SET_XPATCH_DEST_NAME_REPLY, payload)
        handle_dest_name_reply(rx, state)
        assert state.xpatch.channels[3].dest_name == "Destination 4"


class TestMidiSetup:
    def test_handler(self, state):
        payload = payload_bool(True) + payload_int(5)
        rx = build_rx_packet(MessageCode.GET_XPATCH_MIDI_SETUP_REPLY, payload)
        handle_midi_setup_reply(rx, state)
        assert state.xpatch.midi_enabled is True
        assert state.xpatch.midi_channel == 5


class TestRoutingData:
    def test_parse_16_routes(self, state):
        payload = b""
        for dest in range(1, NUM_CHANS + 1):
            payload += (
                payload_int(0)  # skip
                + payload_int(dest)  # display_src = dest (1:1 routing)
                + payload_int(0)  # skip
                + payload_bool(dest == 1)  # only dest 1 protected
            )
        rx = build_rx_packet(MessageCode.GET_XPATCH_ROUTING_DATA_REPLY, payload)
        handle_routing_data_reply(rx, state)
        routes = state.xpatch.routes
        assert len(routes) == 16
        assert routes[0].dest == 1
        assert routes[0].display_src == 1
        assert routes[0].protect is True
        assert routes[15].dest == 16
        assert routes[15].protect is False


class TestPresetsList:
    def test_parse(self, state):
        payload = payload_int(0) + payload_bool(True) + payload_string("P1")
        # Add 16 src ints
        for i in range(NUM_CHANS):
            payload += payload_int(i + 1)
        payload += payload_int(-1)  # terminator
        rx = build_rx_packet(MessageCode.GET_XPATCH_PRESETS_LIST_REPLY, payload)
        handle_presets_list_reply(rx, state)
        assert len(state.xpatch.presets) == 1
        p = state.xpatch.presets[0]
        assert p.index == 0
        assert p.used is True
        assert p.name == "P1"
        assert len(p.srcs) == 16
        assert p.srcs[0] == 1


class TestChainsList:
    def test_parse(self, state):
        payload = payload_int(0) + payload_bool(True) + payload_string("Chain1")
        for i in range(NUM_CHAIN_ELEMENTS):
            payload += payload_int(i)
        payload += payload_int(-1)  # terminator
        rx = build_rx_packet(MessageCode.GET_XPATCH_CHAINS_LIST_REPLY, payload)
        handle_chains_list_reply(rx, state)
        assert len(state.xpatch.chains) == 1
        c = state.xpatch.chains[0]
        assert c.name == "Chain1"
        assert len(c.links) == NUM_CHAIN_ELEMENTS


class TestPresetSelected:
    def test_handler(self, state):
        rx = build_rx_packet(MessageCode.SET_XPATCH_PRESET_SELECTED_REPLY, payload_int(3))
        handle_preset_selected_reply(rx, state)
        assert state.xpatch.selected_preset == 3


class TestPresetEdited:
    def test_handler(self, state):
        rx = build_rx_packet(MessageCode.GET_XPATCH_PRESET_EDITED_REPLY, payload_bool(True))
        handle_preset_edited_reply(rx, state)
        assert state.xpatch.preset_edited is True


class TestXpatchBuilders:
    def test_set_route(self):
        data = build_set_route(1000, 99, 3, 7)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SET_XPATCH_ROUTE
        dest = struct.unpack_from(">i", data, 16)[0]
        src = struct.unpack_from(">i", data, 20)[0]
        assert dest == 3
        assert src == 7

    def test_set_preset_selected(self):
        data = build_set_preset_selected(1000, 99, 5)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SET_XPATCH_PRESET_SELECTED
        idx = struct.unpack_from(">i", data, 16)[0]
        assert idx == 5

    def test_delete_preset(self):
        data = build_delete_preset(1000, 99, 2)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.DELETE_XPATCH_PRESET
        idx = struct.unpack_from(">i", data, 16)[0]
        assert idx == 2

    def test_set_device_name(self):
        data = build_set_device_name(1000, 99, 4, "Reverb")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SET_XPATCH_DEVICE_NAME
        chan = struct.unpack_from(">i", data, 16)[0]
        assert chan == 4
        assert b"Reverb\x00" in data[20:]

    def test_set_midi_enable_true(self):
        data = build_set_midi_enable(1000, 99, True)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SET_XPATCH_MIDI_ENABLE
        assert data[16] == 1

    def test_set_midi_enable_false(self):
        data = build_set_midi_enable(1000, 99, False)
        assert data[16] == 0

    def test_send_chain_data(self):
        links = [1, 2, 3, 0, 0, 0, 0, 0]
        data = build_send_chain_data(1000, 99, 0, "TestChain", links)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_CHAIN_DATA
        idx = struct.unpack_from(">i", data, 16)[0]
        assert idx == 0
        assert b"TestChain\x00" in data[20:]


class TestXpatchEdgeCases:
    def test_out_of_range_chan_ignored(self, state):
        """chan=17 in input_minus_10db_reply should not crash."""
        payload = payload_int(17) + payload_bool(True)
        rx = build_rx_packet(MessageCode.SET_XPATCH_INPUT_MINUS10DB_REPLY, payload)
        handle_input_minus_10db_reply(rx, state)
        # No crash, no state change for out-of-range channel
        for ch in state.xpatch.channels:
            assert ch.input_minus_10db is False
