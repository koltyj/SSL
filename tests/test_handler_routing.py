"""Tests for handlers/routing.py."""

import struct
from unittest.mock import MagicMock, patch

import pytest
from conftest import (
    build_rx_packet,
    payload_byte,
    payload_int,
    payload_string,
)
from ssl_matrix_client.cli import SSLMatrixCLI
from ssl_matrix_client.client import SSLMatrixClient
from ssl_matrix_client.handlers.routing import (
    build_assign_chain_to_chan,
    build_clear_inserts,
    build_deassign_chan,
    build_delete_chain,
    build_delete_chan_insert,
    build_get_insert_names_v2,
    build_rename_chain,
    build_save_inserts_to_chain,
    build_set_chan_stereo_insert,
    build_set_insert_to_chan_v2,
    handle_chain_info_v2_reply,
    handle_chan_matrix_info_v2_reply,
    handle_insert_names_v2_reply,
    handle_matrix_preset_list_reply,
    handle_routing_ack,
)
from ssl_matrix_client.protocol import MessageCode


class TestInsertNamesV2:
    def test_parse_loop(self, state):
        payload = (
            payload_byte(1)
            + payload_byte(1)
            + payload_byte(0)
            + payload_string("Comp1")
            + payload_byte(2)
            + payload_byte(0)
            + payload_byte(1)
            + payload_string("EQ")
            + payload_byte(0)  # terminator
        )
        rx = build_rx_packet(MessageCode.ACK_GET_INSERT_INFO_V2, payload)
        handle_insert_names_v2_reply(rx, state)
        dev1 = state.get_device(1)
        assert dev1.name == "Comp1"
        assert dev1.is_assigned == 1
        assert dev1.is_stereo == 0
        dev2 = state.get_device(2)
        assert dev2.name == "EQ"
        assert dev2.is_stereo == 1


class TestChainInfoV2:
    def test_with_elements(self, state):
        payload = (
            payload_byte(1)
            + payload_byte(1)
            + payload_string("MyChain")
            + payload_byte(2)  # 2 elements
            + payload_byte(1)
            + payload_string("Dev1")
            + payload_byte(2)
            + payload_string("Dev2")
            + payload_byte(0)  # terminator
        )
        rx = build_rx_packet(MessageCode.ACK_GET_CHAIN_INFO_V2, payload)
        handle_chain_info_v2_reply(rx, state)
        assert len(state.chains) == 1
        c = state.chains[0]
        assert c.name == "MyChain"
        assert c.is_assigned == 1
        assert len(c.elements) == 2
        assert c.elements[0] == (1, "Dev1")

    def test_empty(self, state):
        payload = payload_byte(0)
        rx = build_rx_packet(MessageCode.ACK_GET_CHAIN_INFO_V2, payload)
        handle_chain_info_v2_reply(rx, state)
        assert len(state.chains) == 0


class TestChanMatrixInfoV2:
    def test_with_stereo(self, state):
        payload = (
            payload_byte(1)  # chan 1
            + payload_string("ChainA")
            + payload_byte(2)  # 2 inserts
            + payload_byte(3)
            + payload_byte(5)  # insert nums
            + payload_byte(1)  # has stereo
            + payload_byte(0)  # terminator
        )
        rx = build_rx_packet(MessageCode.ACK_GET_CHAN_MATRIX_INFO_V2, payload)
        handle_chan_matrix_info_v2_reply(rx, state)
        assert len(state.channel_inserts) == 1
        ci = state.channel_inserts[0]
        assert ci.channel == 1
        assert ci.chain_name == "ChainA"
        assert ci.inserts == [3, 5]
        assert ci.has_stereo == 1


class TestMatrixPresetList:
    def test_parse(self, state):
        payload = payload_int(2) + payload_string("Preset1") + payload_string("Preset2")
        rx = build_rx_packet(MessageCode.ACK_GET_MATRIX_PRESET_LIST, payload)
        handle_matrix_preset_list_reply(rx, state)
        assert len(state.matrix_presets) == 2
        assert state.matrix_presets[0].name == "Preset1"
        assert state.matrix_presets[1].name == "Preset2"


class TestRoutingAck:
    def test_ok(self, state):
        rx = build_rx_packet(MessageCode.ACK_SET_INSERT_NAMES_V2, payload_string("ok"))
        handle_routing_ack(rx, state)  # no error

    def test_error_logs(self, state):
        rx = build_rx_packet(MessageCode.ACK_SET_INSERT_NAMES_V2, payload_string("error: fail"))
        handle_routing_ack(rx, state)  # logs warning, no exception


class TestBuilders:
    def test_slot_validation(self):
        with pytest.raises(ValueError, match="slot must be >= 1"):
            build_set_insert_to_chan_v2(1000, 99, 1, 1, 0)

    def test_valid_slot(self):
        data = build_set_insert_to_chan_v2(1000, 99, 1, 5, 3)
        # slot-1 = 2 should be in payload
        assert data[18] == 2  # slot-1

    def test_clear_inserts_limit(self):
        with pytest.raises(ValueError, match="Too many"):
            build_clear_inserts(1000, 99, list(range(256)))

    def test_get_insert_names_v2(self):
        data = build_get_insert_names_v2(1000, 99, 3, 10)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_GET_INSERT_INFO_V2
        assert data[16] == 3  # first
        assert data[17] == 10  # last

    def test_assign_chain_to_chan(self):
        data = build_assign_chain_to_chan(1000, 99, 5, "MyChain")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_ASSIGN_CHAIN_TO_CHAN_V2
        assert data[16] == 5
        assert b"MyChain\x00" in data[17:]

    def test_deassign_chan(self):
        data = build_deassign_chan(1000, 99, 7)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_DEASSIGN_CHAN_V2
        assert data[16] == 7

    def test_delete_chain(self):
        data = build_delete_chain(1000, 99, "OldChain")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_DELETE_CHAIN_V2
        assert b"OldChain\x00" in data[16:]

    def test_rename_chain(self):
        data = build_rename_chain(1000, 99, "Old", "New")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_RENAME_CHAIN
        payload = data[16:]
        assert b"Old\x00" in payload
        assert b"New\x00" in payload

    def test_save_inserts_to_chain(self):
        data = build_save_inserts_to_chain(1000, 99, 3, "SavedChain")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SAVE_INSERTS_TO_CHAIN
        assert data[16] == 3
        assert b"SavedChain\x00" in data[17:]

    def test_delete_chan_insert_validation(self):
        with pytest.raises(ValueError, match="slot must be >= 1"):
            build_delete_chan_insert(1000, 99, 1, 0)

    def test_delete_chan_insert_valid(self):
        data = build_delete_chan_insert(1000, 99, 2, 3)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_DELETE_CHAN_INSERT
        assert data[16] == 2  # chan
        assert data[17] == 2  # slot-1

    def test_set_chan_stereo_insert(self):
        data = build_set_chan_stereo_insert(1000, 99, 1, 2, True)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_CHAN_STEREO_INSERT
        assert data[16] == 1  # first
        assert data[17] == 2  # second
        assert data[18] == 1  # stereo=True


class TestClientStereoInsert:
    def test_set_stereo_insert_link(self):
        client = SSLMatrixClient.__new__(SSLMatrixClient)
        client.state = MagicMock()
        client.state.desk.serial = 1000
        client.my_serial = 99
        client.send = MagicMock()
        client.set_stereo_insert(1, 2, stereo=True)
        client.send.assert_called_once()
        data = client.send.call_args[0][0]
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SET_CHAN_STEREO_INSERT
        assert data[16] == 1
        assert data[17] == 2
        assert data[18] == 1

    def test_set_stereo_insert_unlink(self):
        client = SSLMatrixClient.__new__(SSLMatrixClient)
        client.state = MagicMock()
        client.state.desk.serial = 1000
        client.my_serial = 99
        client.send = MagicMock()
        client.set_stereo_insert(3, 4, stereo=False)
        client.send.assert_called_once()
        data = client.send.call_args[0][0]
        assert data[16] == 3
        assert data[17] == 4
        assert data[18] == 0  # stereo=False


class TestStereoCliCommand:
    def _make_cli(self):
        cli = SSLMatrixCLI.__new__(SSLMatrixCLI)
        cli._console_type = "matrix"
        cli.client = MagicMock()
        cli.client.state.desk.online = True
        cli._connected = True
        return cli

    def test_stereo_link(self, capsys):
        cli = self._make_cli()
        cli.do_stereo("1 2")
        cli.client.set_stereo_insert.assert_called_once_with(1, 2, True)
        out = capsys.readouterr().out
        assert "Linked" in out

    def test_stereo_unlink(self, capsys):
        cli = self._make_cli()
        cli.do_stereo("3 4 off")
        cli.client.set_stereo_insert.assert_called_once_with(3, 4, False)
        out = capsys.readouterr().out
        assert "Unlinked" in out

    def test_stereo_missing_args(self, capsys):
        cli = self._make_cli()
        cli.do_stereo("1")
        cli.client.set_stereo_insert.assert_not_called()
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_stereo_invalid_args(self, capsys):
        cli = self._make_cli()
        cli.do_stereo("abc def")
        cli.client.set_stereo_insert.assert_not_called()
        out = capsys.readouterr().out
        assert "integers" in out

    def test_stereo_not_connected(self, capsys):
        cli = self._make_cli()
        cli._connected = False
        cli.do_stereo("1 2")
        cli.client.set_stereo_insert.assert_not_called()


class TestSigmaCliGuardrails:
    def test_tui_launches_sigma_app(self):
        cli = SSLMatrixCLI.__new__(SSLMatrixCLI)
        cli._console_type = "sigma"
        cli.client = MagicMock()
        cli.client.console_ip = "192.168.1.201"
        cli._connected = False

        fake_app = MagicMock()

        with patch("ssl_matrix_client.tui.SSLApp", return_value=fake_app) as mock_app_cls:
            result = cli.do_tui("")

        mock_app_cls.assert_called_once_with(console_ip="192.168.1.201", console_type="sigma")
        fake_app.run.assert_called_once()
        assert result is True
