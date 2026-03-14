"""Tests for client.py: SSLMatrixClient dispatch, connect/disconnect, send."""

import socket
from unittest.mock import MagicMock, patch

from ssl_matrix_client.client import SSLMatrixClient
from ssl_matrix_client.protocol import MessageCode


class TestDispatchTable:
    def test_entry_count(self):
        client = SSLMatrixClient()
        dispatch = client._dispatch
        # Should have a substantial number of entries (100+)
        assert len(dispatch) >= 100

    def test_known_entries(self):
        client = SSLMatrixClient()
        d = client._dispatch
        assert MessageCode.GET_DESK_REPLY in d
        assert MessageCode.SEND_HEARTBEAT in d
        assert MessageCode.GET_CHAN_NAMES_AND_IMAGES_REPLY in d
        assert MessageCode.ACK_GET_AUTOMATION_MODE in d
        assert MessageCode.GET_XPATCH_CHAN_SETUP_REPLY in d


class TestMySerial:
    def test_randomness(self):
        """Two clients should get different serials (with overwhelming probability)."""
        a = SSLMatrixClient()
        b = SSLMatrixClient()
        assert a.my_serial != b.my_serial

    def test_range(self):
        client = SSLMatrixClient()
        assert -(2**31) <= client.my_serial <= 2**31 - 1


class TestConnectDisconnect:
    @patch.object(SSLMatrixClient, "_create_socket")
    def test_connect_starts_thread(self, mock_create):
        mock_sock = MagicMock()
        mock_sock.recvfrom = MagicMock(side_effect=socket.timeout)
        mock_create.return_value = mock_sock
        client = SSLMatrixClient()
        client.connect()
        assert client._running is True
        assert client._recv_thread is not None
        client.disconnect()
        assert client._running is False

    def test_disconnect_clears_state(self):
        client = SSLMatrixClient()
        client._running = False
        client.state.desk.online = True
        client.disconnect()
        assert client.state.desk.online is False


class TestSendRaw:
    @patch.object(SSLMatrixClient, "_create_socket")
    def test_send_raw_calls_sendto(self, mock_create):
        mock_sock = MagicMock()
        mock_sock.recvfrom = MagicMock(side_effect=socket.timeout)
        mock_create.return_value = mock_sock
        client = SSLMatrixClient(console_ip="10.0.0.1")
        client.connect()
        client.send_raw(b"\x00\x01\x02")
        # sendto called at least once (GET_DESK + our call)
        calls = [c for c in mock_sock.sendto.call_args_list if c[0][0] == b"\x00\x01\x02"]
        assert len(calls) == 1
        assert calls[0][0][1] == ("10.0.0.1", 50081)
        client.disconnect()


class TestRestartConsole:
    @patch("socket.socket")
    def test_ephemeral_socket(self, mock_socket_class):
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        client = SSLMatrixClient(console_ip="10.0.0.1")
        client.state.desk.serial = 999
        client.restart_console()
        # Should bind to ephemeral port
        mock_sock.bind.assert_called_once_with(("0.0.0.0", 0))
        mock_sock.sendto.assert_called_once()
        mock_sock.close.assert_called_once()


class TestEdgeCases:
    def test_send_raw_no_socket(self):
        """send_raw with _sock=None should not crash."""
        client = SSLMatrixClient()
        assert client._sock is None
        client.send_raw(b"\x00\x01")  # no exception

    def test_double_disconnect(self):
        """Calling disconnect twice should not crash."""
        client = SSLMatrixClient()
        client.disconnect()
        client.disconnect()  # second call — no exception

    def test_send_custom_with_payload(self):
        """send_custom with hex payload encodes correctly."""
        client = SSLMatrixClient()
        client.state.desk.serial = 1000
        # Capture what would be sent
        sent = []
        client._sock = MagicMock()
        client._sock.sendto = lambda data, addr: sent.append(data)
        client.send_custom(5, "0102FF")
        assert len(sent) == 1
        data = sent[0]
        # Payload bytes at offset 16, 17, 18
        assert data[16] == 0x01
        assert data[17] == 0x02
        assert data[18] == 0xFF
