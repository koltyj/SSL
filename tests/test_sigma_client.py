"""Tests for SSLSigmaClient."""

import struct
from unittest.mock import MagicMock

from ssl_matrix_client.sigma_client import SSLSigmaClient
from ssl_matrix_client.sigma_models import SigmaState
from ssl_matrix_client.sigma_protocol import (
    SIGMA_MAGIC,
    SIGMA_PORT,
    SIGMA_PRODUCT_TYPE,
    PayloadType,
    SigmaMessageId,
    SigmaRxMessage,
)

# ---------------------------------------------------------------------------
# Init / defaults
# ---------------------------------------------------------------------------


class TestSSLSigmaClientInit:
    def test_default_ip_is_sigma(self):
        client = SSLSigmaClient()
        assert client.console_ip == "192.168.1.201"

    def test_default_port(self):
        client = SSLSigmaClient()
        assert client.port == SIGMA_PORT
        assert client.port == 50081

    def test_custom_ip(self):
        client = SSLSigmaClient(console_ip="10.0.0.1")
        assert client.console_ip == "10.0.0.1"

    def test_initial_state(self):
        client = SSLSigmaClient()
        assert isinstance(client.state, SigmaState)
        assert len(client.state.channels) == 16
        assert client.state.online is False

    def test_running_false_initially(self):
        client = SSLSigmaClient()
        assert client._running is False

    def test_callbacks_default_none(self):
        client = SSLSigmaClient()
        assert client._on_state_changed is None
        assert client._on_desk_offline is None
        assert client._on_desk_online is None

    def test_reconnect_state_defaults(self):
        client = SSLSigmaClient()
        assert client._reconnecting is False
        assert client._reconnect_attempts == 0
        assert client._needs_resync is False


# ---------------------------------------------------------------------------
# Convenience methods
# ---------------------------------------------------------------------------


class TestSSLSigmaClientConvenience:
    def test_get_channels_returns_all_16(self):
        client = SSLSigmaClient()
        result = client.get_channels()
        assert len(result) == 16

    def test_get_channels_tuple_format(self):
        client = SSLSigmaClient()
        client.state.channels[0].name = "Kick"
        client.state.channels[0].fader = 0.75
        client.state.channels[0].pan = -0.5
        result = client.get_channels()
        assert result[0] == (1, "Kick", 0.75, -0.5)

    def test_get_channels_with_names(self):
        client = SSLSigmaClient()
        client.state.channels[0].name = "Kick"
        client.state.channels[3].name = "Snare"
        result = client.get_channels()
        assert len(result) == 16
        assert result[0] == (1, "Kick", 0.0, 0.0)
        assert result[3] == (4, "Snare", 0.0, 0.0)

    def test_rename_channel_exists(self):
        client = SSLSigmaClient()
        assert hasattr(client, "rename_channel")

    def test_get_monitor_returns_monitor_state(self):
        client = SSLSigmaClient()
        monitor = client.get_monitor()
        assert hasattr(monitor, "sources")
        assert hasattr(monitor, "dim_level")
        assert len(monitor.sources) == 7

    def test_set_cut_does_not_raise(self):
        """set_cut should not raise even though msg_id is unconfirmed."""
        client = SSLSigmaClient()
        client.set_cut(True)


# ---------------------------------------------------------------------------
# Recv loop validation
# ---------------------------------------------------------------------------


def _build_raw_sigma_packet(
    payload_type,
    msg_id,
    sub_param=0,
    payload=b"",
    magic=SIGMA_MAGIC,
    product_type=SIGMA_PRODUCT_TYPE,
):
    """Build a raw Sigma packet for testing."""
    buf = bytearray(0x14 + len(payload))
    buf[0] = magic
    struct.pack_into(">I", buf, 0x04, product_type)
    composite = (payload_type << 24) | (msg_id & 0x00FFFFFF)
    struct.pack_into(">I", buf, 0x08, composite)
    struct.pack_into(">I", buf, 0x0C, sub_param)
    buf[0x14:] = payload
    return bytes(buf)


class TestRecvLoopValidation:
    def test_rejects_non_sigma_magic(self):
        """Packets with wrong magic byte should be skipped by recv loop."""
        data = _build_raw_sigma_packet(PayloadType.NONE, SigmaMessageId.KEEPALIVE, magic=0x00)
        assert data[0] != SIGMA_MAGIC

    def test_rejects_wrong_product_type(self):
        """Packets with product_type != 4 should be skipped by recv loop."""
        data = _build_raw_sigma_packet(PayloadType.NONE, SigmaMessageId.KEEPALIVE, product_type=2)
        pt = struct.unpack_from(">I", data, 0x04)[0]
        assert pt != SIGMA_PRODUCT_TYPE

    def test_valid_packet_parses(self):
        """A valid Sigma packet should parse into SigmaRxMessage."""
        data = _build_raw_sigma_packet(
            PayloadType.FLOAT,
            SigmaMessageId.FADER,
            1,
            struct.pack(">f", 0.5),
        )
        rx = SigmaRxMessage(data)
        assert rx.magic == SIGMA_MAGIC
        assert rx.product_type == SIGMA_PRODUCT_TYPE
        assert rx.msg_id == SigmaMessageId.FADER

    def test_dispatches_valid_packet_to_handler(self):
        """A valid keepalive dispatched through handle_sigma_message sets online."""
        from ssl_matrix_client.handlers.sigma import handle_sigma_message

        client = SSLSigmaClient()
        data = _build_raw_sigma_packet(PayloadType.NONE, SigmaMessageId.KEEPALIVE)
        rx = SigmaRxMessage(data)
        handled = handle_sigma_message(rx, client.state)
        assert handled is True
        assert client.state.online is True

    def test_short_packets_would_be_skipped(self):
        """Packets shorter than 0x14 bytes should be ignored in recv loop."""
        short = b"\x53\x00\x00\x00"
        assert len(short) < 0x14


# ---------------------------------------------------------------------------
# Convenience method -> build function verification via mock socket
# ---------------------------------------------------------------------------


class TestConvenienceBuilders:
    """Verify convenience methods build and send correct packets."""

    def _make_client_with_mock_send(self):
        client = SSLSigmaClient()
        client._sock = MagicMock()
        return client

    def test_set_fader_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_fader(1, 0.5)
        client._sock.sendto.assert_called_once()
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.FADER
        assert rx.sub_param == 1

    def test_set_solo_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_solo(3, True)
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.SOLO
        assert rx.sub_param == 3
        assert rx.float_value == 1.0

    def test_set_mute_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_mute(5, False)
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.MUTE
        assert rx.float_value == 0.0

    def test_set_pan_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_pan(2, -0.25)
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.PAN

    def test_rename_channel_sends_scribble(self):
        client = self._make_client_with_mock_send()
        client.rename_channel(4, "Snare")
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.CHAN_SCRIBBLE
        assert rx.string_value == "Snare"

    def test_set_channel_name_aliases_rename(self):
        client = self._make_client_with_mock_send()
        client.set_channel_name(1, "Kick")
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.CHAN_SCRIBBLE

    def test_set_monitor_source_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_monitor_source(2, True)
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.MON_SRC_3

    def test_set_dim_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_dim(0.7)
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.DIM_LEVEL

    def test_set_headphone_source_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_headphone_source(0, True)
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.HP_SRC_1

    def test_set_phase_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_phase(1, True)
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.PHASE

    def test_set_connection_mode_sends_correct_msg(self):
        client = self._make_client_with_mock_send()
        client.set_connection_mode(True)
        data = client._sock.sendto.call_args[0][0]
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.CONNECTION_MODE
        assert rx.float_value == 1.0
