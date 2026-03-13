"""Tests for handlers/softkeys.py."""

import struct

import pytest
from conftest import (
    build_rx_packet,
    payload_bool,
    payload_byte,
    payload_string,
)
from ssl_matrix_client.handlers.softkeys import (
    build_get_default_wheel_mode,
    build_get_flip_status,
    build_set_cc_names_list,
    build_set_default_wheel_mode,
    build_set_edit_keymap_name,
    build_set_key_blank,
    handle_auto_mode_on_scribs_reply,
    handle_cc_names_list_reply,
    handle_default_wheel_mode_reply,
    handle_edit_keymap_data_reply,
    handle_edit_keymap_name_reply,
    handle_edit_keymap_size_reply,
    handle_flip_status_reply,
    handle_handshake_reply,
    handle_midi_function_list_reply,
)
from ssl_matrix_client.protocol import MessageCode


class TestKeymapName:
    def test_handler(self, state):
        payload = payload_string("MyKeymap") + payload_byte(2)
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_NAME, payload)
        handle_edit_keymap_name_reply(rx, state)
        assert state.softkeys.keymap_name == "MyKeymap"
        assert state.softkeys.daw_layer == 2


class TestKeymapData:
    def test_not_in_edit_clears(self, state):
        state.softkeys.keys.append("dummy")
        payload = payload_byte(0) + payload_byte(0)  # in_edit=0
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_DATA, payload)
        handle_edit_keymap_data_reply(rx, state)
        assert state.softkeys.in_edit is False
        assert len(state.softkeys.keys) == 0

    def test_blank_key(self, state):
        payload = (
            payload_byte(1)  # in_edit
            + payload_byte(0)  # show_subs
            + payload_byte(1)
            + payload_byte(1)
            + payload_byte(0)  # idx=1, top=1, type=blank
            + payload_string("KEY1")
            + payload_string("")  # keycap + skip string
            + payload_byte(0)  # terminator
        )
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_DATA, payload)
        handle_edit_keymap_data_reply(rx, state)
        assert len(state.softkeys.keys) == 1
        k = state.softkeys.keys[0]
        assert k.key_type == 0
        assert k.keycap_name == "KEY1"

    def test_midi_key(self, state):
        payload = (
            payload_byte(1)
            + payload_byte(0)  # in_edit, show_subs
            + payload_byte(1)
            + payload_byte(0)
            + payload_byte(1)  # midi
            + payload_string("MIDI1")
            + payload_byte(2)
            + payload_string("Func1")
            + payload_string("Func2")
            + payload_byte(0)  # terminator
        )
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_DATA, payload)
        handle_edit_keymap_data_reply(rx, state)
        k = state.softkeys.keys[0]
        assert k.key_type == 1
        assert "Func1" in k.data

    def test_usb_key(self, state):
        payload = (
            payload_byte(1)
            + payload_byte(0)
            + payload_byte(1)
            + payload_byte(0)
            + payload_byte(2)  # usb
            + payload_string("USB1")
            + payload_string("ctrl+z")
            + payload_byte(0)
        )
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_DATA, payload)
        handle_edit_keymap_data_reply(rx, state)
        k = state.softkeys.keys[0]
        assert k.key_type == 2
        assert k.data == "ctrl+z"

    def test_menu_key(self, state):
        payload = (
            payload_byte(1)
            + payload_byte(0)
            + payload_byte(1)
            + payload_byte(0)
            + payload_byte(3)  # menu
            + payload_string("MENU1")
            + payload_string("skip")
            + payload_byte(0)
        )
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_DATA, payload)
        handle_edit_keymap_data_reply(rx, state)
        k = state.softkeys.keys[0]
        assert k.key_type == 3
        assert k.data == "Menu"


class TestKeymapSize:
    def test_transport(self, state):
        payload = payload_byte(15) + payload_bool(True)
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_SIZE, payload)
        handle_edit_keymap_size_reply(rx, state)
        assert state.softkeys.panel_type == 1
        assert state.softkeys.unsaved_data is True

    def test_softkey(self, state):
        payload = payload_byte(8) + payload_bool(False)
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_SIZE, payload)
        handle_edit_keymap_size_reply(rx, state)
        assert state.softkeys.panel_type == 2

    def test_blank(self, state):
        payload = payload_byte(0) + payload_bool(True)
        rx = build_rx_packet(MessageCode.ACK_GET_EDIT_KEYMAP_SIZE, payload)
        handle_edit_keymap_size_reply(rx, state)
        assert state.softkeys.panel_type == 0
        assert state.softkeys.unsaved_data is False  # cleared for 0-key panel


class TestMidiFunctionList:
    def test_offset_dedup(self, state):
        """Second batch at offset trims entries >= offset."""
        # First batch
        payload1 = (
            payload_byte(2)
            + payload_byte(0)
            + payload_string("A")
            + payload_string("a")
            + payload_string("B")
            + payload_string("b")
        )
        rx1 = build_rx_packet(MessageCode.ACK_GET_MIDI_FUNCTION_LIST, payload1)
        handle_midi_function_list_reply(rx1, state)
        assert len(state.softkeys.midi_functions) == 2

        # Second batch at offset 2
        payload2 = payload_byte(1) + payload_byte(2) + payload_string("C") + payload_string("c")
        rx2 = build_rx_packet(MessageCode.ACK_GET_MIDI_FUNCTION_LIST, payload2)
        handle_midi_function_list_reply(rx2, state)
        assert len(state.softkeys.midi_functions) == 3
        assert state.softkeys.midi_functions[2][1] == "C"

    def test_empty_clears(self, state):
        state.softkeys.midi_functions.append((0, "X", "x"))
        payload = payload_byte(0)
        rx = build_rx_packet(MessageCode.ACK_GET_MIDI_FUNCTION_LIST, payload)
        handle_midi_function_list_reply(rx, state)
        assert len(state.softkeys.midi_functions) == 0


class TestFlipStatus:
    def test_inverted(self, state):
        """flip==1 means flip enabled."""
        payload = payload_byte(1) + payload_byte(1)  # skip + flip
        rx = build_rx_packet(MessageCode.ACK_GET_FLIP_STATUS, payload)
        handle_flip_status_reply(rx, state)
        assert state.softkeys.flip_status is True

    def test_off(self, state):
        payload = payload_byte(1) + payload_byte(0)
        rx = build_rx_packet(MessageCode.ACK_GET_FLIP_STATUS, payload)
        handle_flip_status_reply(rx, state)
        assert state.softkeys.flip_status is False


class TestHandshake:
    def test_inverted(self, state):
        """handshake==0 means enabled (inverted logic)."""
        payload = payload_byte(1) + payload_byte(0)
        rx = build_rx_packet(MessageCode.ACK_GET_HANDSHAKING_STATUS, payload)
        handle_handshake_reply(rx, state)
        assert state.softkeys.handshake is True

    def test_disabled(self, state):
        payload = payload_byte(1) + payload_byte(1)
        rx = build_rx_packet(MessageCode.ACK_GET_HANDSHAKING_STATUS, payload)
        handle_handshake_reply(rx, state)
        assert state.softkeys.handshake is False


class TestAutoModeOnScribs:
    def test_handler(self, state):
        payload = payload_byte(1) + payload_byte(1)
        rx = build_rx_packet(MessageCode.ACK_GET_AUTO_MODE_ON_SCRIBS_STATUS, payload)
        handle_auto_mode_on_scribs_reply(rx, state)
        assert state.softkeys.auto_mode_on_scribs is True


class TestCcNamesList:
    def test_parse(self, state):
        payload = payload_byte(2) + payload_string("CC1") + payload_string("CC2")
        rx = build_rx_packet(MessageCode.ACK_GET_CC_NAMES_LIST, payload)
        handle_cc_names_list_reply(rx, state)  # parsed but not stored yet


class TestCcNamesStorage:
    def test_names_stored_after_parse(self, state):
        payload = (
            payload_byte(3) + payload_string("Pan") + payload_string("Send") + payload_string("EQ")
        )
        rx = build_rx_packet(MessageCode.ACK_GET_CC_NAMES_LIST, payload)
        handle_cc_names_list_reply(rx, state)
        assert state.softkeys.cc_names == ["Pan", "Send", "EQ"]

    def test_empty_list_clears_cc_names(self, state):
        state.softkeys.cc_names = ["OldName"]
        payload = payload_byte(0)
        rx = build_rx_packet(MessageCode.ACK_GET_CC_NAMES_LIST, payload)
        handle_cc_names_list_reply(rx, state)
        assert state.softkeys.cc_names == []

    def test_second_call_replaces_first(self, state):
        payload1 = payload_byte(2) + payload_string("A") + payload_string("B")
        rx1 = build_rx_packet(MessageCode.ACK_GET_CC_NAMES_LIST, payload1)
        handle_cc_names_list_reply(rx1, state)
        assert state.softkeys.cc_names == ["A", "B"]

        payload2 = payload_byte(1) + payload_string("X")
        rx2 = build_rx_packet(MessageCode.ACK_GET_CC_NAMES_LIST, payload2)
        handle_cc_names_list_reply(rx2, state)
        assert state.softkeys.cc_names == ["X"]


class TestWheelMode:
    def test_mode_stored_after_parse(self, state):
        payload = payload_byte(2) + payload_byte(3)  # daw_layer skip + mode
        rx = build_rx_packet(MessageCode.ACK_GET_DEFAULT_WHEEL_MODE_STATUS, payload)
        handle_default_wheel_mode_reply(rx, state)
        assert state.softkeys.default_wheel_mode == 3


class TestWheelModeBuilder:
    def test_get_default_wheel_mode_cmd_and_layer(self):
        data = build_get_default_wheel_mode(1000, 99, 2)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_GET_DEFAULT_WHEEL_MODE_STATUS
        assert data[16] == 2  # daw_layer

    def test_set_default_wheel_mode_cmd_layer_and_mode(self):
        data = build_set_default_wheel_mode(1000, 99, 3, 1)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_DEFAULT_WHEEL_MODE_STATUS
        assert data[16] == 3  # daw_layer
        assert data[17] == 1  # mode


class TestSoftkeyBuilders:
    def test_set_edit_keymap_name(self):
        data = build_set_edit_keymap_name(1000, 99, 2, "MyKeymap")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_EDIT_KEYMAP_NAME
        assert data[16] == 2  # daw_layer
        assert b"MyKeymap\x00" in data[17:]

    def test_set_key_blank(self):
        data = build_set_key_blank(1000, 99, 3, 1)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_KEY_BLANK
        assert data[16] == 3  # key_index
        assert data[17] == 1  # is_top_row

    def test_get_flip_status(self):
        data = build_get_flip_status(1000, 99, 4)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_GET_FLIP_STATUS
        assert data[16] == 4  # daw_layer

    def test_set_cc_names_list_overflow(self):
        names = [f"CC{i}" for i in range(256)]
        with pytest.raises(ValueError, match="too long"):
            build_set_cc_names_list(1000, 99, 1, 0, names)
