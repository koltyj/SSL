"""Tests for handlers/profiles.py."""

import struct

from conftest import (
    build_rx_packet,
    payload_bool,
    payload_byte,
    payload_int,
    payload_string,
)
from ssl_matrix_client.handlers.profiles import (
    build_copy_profile_to_new,
    build_delete_profile,
    build_get_daw_layer_protocol,
    build_get_profiles,
    build_get_transport_lock,
    build_rename_profile,
    build_set_profile_for_daw_layer,
    build_set_transport_lock,
    handle_daw_layer_protocol_reply,
    handle_profile_for_daw_layer_reply,
    handle_profiles_reply,
    handle_transport_lock_reply,
)
from ssl_matrix_client.protocol import MessageCode


class TestDawLayerProtocol:
    def test_handler(self, state):
        payload = payload_byte(2) + payload_byte(1)  # layer=2, protocol=HUI
        rx = build_rx_packet(MessageCode.ACK_GET_DAW_LAYER_PROTOCOL, payload)
        handle_daw_layer_protocol_reply(rx, state)
        assert state.get_daw_layer(2).protocol == 1

    def test_builder(self):
        data = build_get_daw_layer_protocol(1000, 99, 3)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_GET_DAW_LAYER_PROTOCOL
        assert data[16] == 3


class TestProfileForDawLayer:
    def test_handler(self, state):
        payload = payload_byte(1) + payload_string("MyProfile")
        rx = build_rx_packet(MessageCode.ACK_GET_PROFILE_FOR_DAW_LAYER, payload)
        handle_profile_for_daw_layer_reply(rx, state)
        assert state.get_daw_layer(1).profile_name == "MyProfile"

    def test_builder(self):
        data = build_set_profile_for_daw_layer(1000, 99, 2, "TestProf")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_PROFILE_FOR_DAW_LAYER


class TestProfilesReply:
    def test_parse_list(self, state):
        payload = (
            payload_int(2)
            + payload_string("Profile1")
            + payload_byte(1)
            + payload_bool(False)
            + payload_bool(True)
            + payload_string("Profile2")
            + payload_byte(2)
            + payload_bool(True)
            + payload_bool(False)
        )
        rx = build_rx_packet(MessageCode.ACK_GET_PROFILES, payload)
        handle_profiles_reply(rx, state)
        assert len(state.profiles) == 2
        assert state.profiles[0].name == "Profile1"
        assert state.profiles[0].protocol == 1
        assert state.profiles[0].in_use is True
        assert state.profiles[1].name == "Profile2"
        assert state.profiles[1].read_only is True

    def test_empty_list(self, state):
        payload = payload_int(0)
        rx = build_rx_packet(MessageCode.ACK_GET_PROFILES, payload)
        handle_profiles_reply(rx, state)
        assert len(state.profiles) == 0


class TestTransportLock:
    def test_handler(self, state):
        payload = payload_byte(3)
        rx = build_rx_packet(MessageCode.ACK_GET_TRANSPORT_LOCK_DAW_LAYER, payload)
        handle_transport_lock_reply(rx, state)
        assert state.transport_lock_layer == 3


class TestProfileBuilders:
    def test_get_profiles_header_only(self):
        data = build_get_profiles(1000, 99)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_GET_PROFILES
        assert len(data) == 16  # header only

    def test_get_transport_lock_header_only(self):
        data = build_get_transport_lock(1000, 99)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_GET_TRANSPORT_LOCK_DAW_LAYER
        assert len(data) == 16

    def test_set_transport_lock(self):
        data = build_set_transport_lock(1000, 99, 2)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_TRANSPORT_LOCK_DAW_LAYER
        assert data[16] == 2

    def test_copy_profile_to_new(self):
        data = build_copy_profile_to_new(1000, 99, "Source", "Dest")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_COPY_PROFILE_TO_NEW
        payload = data[16:]
        assert b"Source\x00" in payload
        assert b"Dest\x00" in payload

    def test_delete_profile(self):
        data = build_delete_profile(1000, 99, "OldProfile")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_DELETE_PROFILES
        assert b"OldProfile\x00" in data[16:]

    def test_rename_profile(self):
        data = build_rename_profile(1000, 99, "Old", "New")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_RENAME_PROFILES
        payload = data[16:]
        assert b"Old\x00" in payload
        assert b"New\x00" in payload
