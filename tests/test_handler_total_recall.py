"""Tests for handlers/total_recall.py."""

import struct

from conftest import (
    build_rx_packet,
    payload_bool,
    payload_int,
    payload_short,
    payload_string,
)
from ssl_matrix_client.handlers.total_recall import (
    build_copy_tr_chan_data,
    build_delete_tr_snap,
    build_get_tr_list,
    build_select_tr_snap,
    build_set_tr_all_chans,
    build_set_tr_enable,
    build_swap_tr_chan_data,
    build_take_tr_snap,
    handle_tr_enable_reply,
    handle_tr_list_reply,
)
from ssl_matrix_client.protocol import MessageCode


class TestTREnable:
    def test_enabled(self, state):
        rx = build_rx_packet(MessageCode.ACK_SET_TR_ENABLE, payload_bool(True))
        handle_tr_enable_reply(rx, state)
        assert state.tr_enabled is True

    def test_disabled(self, state):
        rx = build_rx_packet(MessageCode.ACK_GET_TR_STATE, payload_bool(False))
        handle_tr_enable_reply(rx, state)
        assert state.tr_enabled is False


class TestTRList:
    def test_parse_with_selected(self, state):
        payload = (
            payload_string("/tr")
            + payload_short(1)
            + payload_string("Snap1.trs")
            + payload_string("info")
            + payload_bool(False)
            + payload_string("10:00")
            + payload_string("2024-01-01")
            + payload_int(1024)
            + payload_bool(True)  # selected
            + payload_short(2)
            + payload_string("Snap2.trs")
            + payload_string("info2")
            + payload_bool(False)
            + payload_string("11:00")
            + payload_string("2024-01-02")
            + payload_int(2048)
            + payload_bool(False)
            + payload_short(0)  # terminator
        )
        rx = build_rx_packet(MessageCode.GET_TR_LIST_REPLY, payload)
        handle_tr_list_reply(rx, state)
        assert len(state.tr_snapshots) == 2
        assert state.tr_snapshots[0].name == "Snap1"  # .trs stripped
        assert state.tr_snapshots[0].is_selected is True
        assert state.selected_tr_index == 0
        assert state.tr_snapshots[1].name == "Snap2"
        assert state.tr_snapshots[1].is_selected is False

    def test_empty_list(self, state):
        payload = payload_string("/tr") + payload_short(0)
        rx = build_rx_packet(MessageCode.GET_TR_LIST_REPLY, payload)
        handle_tr_list_reply(rx, state)
        assert len(state.tr_snapshots) == 0
        assert state.selected_tr_index == -1


class TestSelectBuilder:
    def test_select_snap(self):
        data = build_select_tr_snap(1000, 99, 3)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SELECT_TR_SNAP
        idx = struct.unpack_from(">i", data, 16)[0]
        assert idx == 3


class TestTRBuilders:
    def test_set_tr_enable_true(self):
        data = build_set_tr_enable(1000, 99, True)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_TR_ENABLE
        assert data[16] == 1

    def test_set_tr_enable_false(self):
        data = build_set_tr_enable(1000, 99, False)
        assert data[16] == 0

    def test_get_tr_list_header_only(self):
        data = build_get_tr_list(1000, 99)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.GET_TR_LIST
        assert len(data) == 16

    def test_take_tr_snap_header_only(self):
        data = build_take_tr_snap(1000, 99)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_TAKE_TR_SNAP
        assert len(data) == 16

    def test_delete_tr_snap(self):
        data = build_delete_tr_snap(1000, 99, 5)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_DELETE_TR_SNAP
        idx = struct.unpack_from(">i", data, 16)[0]
        assert idx == 5

    def test_set_tr_all_chans_header_only(self):
        data = build_set_tr_all_chans(1000, 99)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_TR_ALL_CHANS
        assert len(data) == 16

    def test_copy_tr_chan_data(self):
        data = build_copy_tr_chan_data(1000, 99, 1, 5)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_COPY_TR_CHAN_DATA
        src = struct.unpack_from(">i", data, 16)[0]
        dest = struct.unpack_from(">i", data, 20)[0]
        assert src == 1
        assert dest == 5

    def test_swap_tr_chan_data(self):
        data = build_swap_tr_chan_data(1000, 99, 3, 7)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SWOP_TR_CHAN_DATA
        src = struct.unpack_from(">i", data, 16)[0]
        dest = struct.unpack_from(">i", data, 20)[0]
        assert src == 3
        assert dest == 7
