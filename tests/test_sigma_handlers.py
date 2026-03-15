"""Tests for SSL Sigma message handlers."""

import struct

import pytest
from ssl_matrix_client.handlers.sigma import (
    build_handshake,
    build_keepalive,
    build_set_connection_mode,
    build_set_dim_level,
    build_set_fader,
    build_set_headphone_source,
    build_set_monitor_source,
    build_set_mute,
    build_set_pan,
    build_set_phase,
    build_set_scribble,
    build_set_solo,
    handle_sigma_message,
)
from ssl_matrix_client.sigma_models import SigmaState
from ssl_matrix_client.sigma_protocol import (
    PayloadType,
    SigmaMessageId,
    SigmaRxMessage,
    uint_to_sigma_float,
)


def _make_rx(payload_type, msg_id, sub_param=0, payload=b""):
    """Build a raw packet and parse it into SigmaRxMessage."""
    from ssl_matrix_client.sigma_protocol import SIGMA_MAGIC, SIGMA_PRODUCT_TYPE

    buf = bytearray(0x14 + len(payload))
    buf[0] = SIGMA_MAGIC
    struct.pack_into(">I", buf, 0x04, SIGMA_PRODUCT_TYPE)
    composite = (payload_type << 24) | (msg_id & 0x00FFFFFF)
    struct.pack_into(">I", buf, 0x08, composite)
    struct.pack_into(">I", buf, 0x0C, sub_param)
    buf[0x14:] = payload
    return SigmaRxMessage(bytes(buf))


@pytest.fixture
def state():
    return SigmaState()


# ---------------------------------------------------------------------------
# Channel handlers
# ---------------------------------------------------------------------------


class TestChannelHandlers:
    def test_fader(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.FADER, 1, struct.pack(">f", 0.75))
        assert handle_sigma_message(rx, state) is True
        assert state.channels[0].fader == pytest.approx(0.75)

    def test_pan(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.PAN, 3, struct.pack(">f", -0.5))
        handle_sigma_message(rx, state)
        assert state.channels[2].pan == pytest.approx(-0.5)

    def test_solo_on(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.SOLO, 1, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.channels[0].solo is True

    def test_solo_off(self, state):
        state.channels[0].solo = True
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.SOLO, 1, struct.pack(">f", 0.0))
        handle_sigma_message(rx, state)
        assert state.channels[0].solo is False

    def test_mute(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.MUTE, 5, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.channels[4].mute is True

    def test_phase(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.PHASE, 2, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.channels[1].phase is True

    def test_solo_safe(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.SOLO_SAFE, 1, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.channels[0].solo_safe is True

    def test_scribble(self, state):
        payload = bytes(ord(c) & 0x7F for c in "Kick")
        rx = _make_rx(PayloadType.STRING, SigmaMessageId.CHAN_SCRIBBLE, 1, payload)
        handle_sigma_message(rx, state)
        assert state.channels[0].name == "Kick"

    def test_invalid_channel_ignored(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.FADER, 99, struct.pack(">f", 0.5))
        handle_sigma_message(rx, state)
        # No crash — channel 99 doesn't exist


# ---------------------------------------------------------------------------
# Monitor handlers
# ---------------------------------------------------------------------------


class TestMonitorHandlers:
    def test_monitor_source_1(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.MON_SRC_1, 0, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.monitor.sources[0] is True

    def test_monitor_source_7(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.MON_SRC_7, 0, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.monitor.sources[6] is True


# ---------------------------------------------------------------------------
# Headphone handlers
# ---------------------------------------------------------------------------


class TestHeadphoneHandlers:
    def test_hp_source_1(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.HP_SRC_1, 0, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.headphone.sources[0] is True

    def test_hp_source_4(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.HP_SRC_4, 0, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.headphone.sources[3] is True


# ---------------------------------------------------------------------------
# Level handlers
# ---------------------------------------------------------------------------


class TestLevelHandlers:
    def test_level_readout(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.LEVEL_READOUT, 0, struct.pack(">f", -12.5))
        handle_sigma_message(rx, state)
        assert state.level.level_value == pytest.approx(-12.5)

    def test_level_toggle(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.LEVEL_TOGGLE, 0, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.level.level_toggle is True


# ---------------------------------------------------------------------------
# Dim handlers
# ---------------------------------------------------------------------------


class TestDimHandlers:
    def test_dim_level(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.DIM_LEVEL, 0, struct.pack(">f", 0.6))
        handle_sigma_message(rx, state)
        assert state.dim.dim_level == pytest.approx(0.6)
        assert state.monitor.dim_level == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Misc handlers
# ---------------------------------------------------------------------------


class TestMiscHandlers:
    def test_connection_status(self, state):
        rx = _make_rx(
            PayloadType.FLOAT, SigmaMessageId.CONNECTION_STATUS, 0, struct.pack(">f", 1.0)
        )
        handle_sigma_message(rx, state)
        assert state.misc.connection_status is True


# ---------------------------------------------------------------------------
# Network handlers
# ---------------------------------------------------------------------------


class TestNetworkHandlers:
    def test_ip_octets(self, state):
        for i, octet in enumerate([10, 0, 1, 100]):
            msg_id = SigmaMessageId.IP_OCTET_1 + i
            f = uint_to_sigma_float(octet)
            rx = _make_rx(PayloadType.UINT_AS_FLOAT, msg_id, 0, struct.pack(">f", f))
            handle_sigma_message(rx, state)
        assert state.network.ip_octets == [10, 0, 1, 100]


# ---------------------------------------------------------------------------
# Connection handlers
# ---------------------------------------------------------------------------


class TestConnectionHandlers:
    def test_keepalive_sets_online(self, state):
        rx = _make_rx(PayloadType.NONE, SigmaMessageId.KEEPALIVE)
        handle_sigma_message(rx, state)
        assert state.online is True
        assert state.last_heartbeat > 0

    def test_handshake_sets_online(self, state):
        rx = _make_rx(PayloadType.NONE, SigmaMessageId.HANDSHAKE)
        handle_sigma_message(rx, state)
        assert state.online is True


# ---------------------------------------------------------------------------
# Unknown message
# ---------------------------------------------------------------------------


class TestUnknownMessage:
    def test_unknown_returns_false(self, state):
        rx = _make_rx(PayloadType.NONE, 0xFF)
        assert handle_sigma_message(rx, state) is False


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------


class TestBuilders:
    def test_build_handshake(self):
        data = build_handshake()
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.HANDSHAKE

    def test_build_keepalive(self):
        data = build_keepalive()
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.KEEPALIVE

    def test_build_set_fader(self):
        data = build_set_fader(1, 0.5)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.FADER
        assert rx.sub_param == 1
        assert rx.float_value == pytest.approx(0.5)

    def test_build_set_pan(self):
        data = build_set_pan(3, -0.25)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.PAN
        assert rx.float_value == pytest.approx(-0.25)

    def test_build_set_solo(self):
        data = build_set_solo(2, True)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.SOLO
        assert rx.float_value == 1.0

    def test_build_set_mute(self):
        data = build_set_mute(5, False)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.MUTE
        assert rx.float_value == 0.0

    def test_build_set_phase(self):
        data = build_set_phase(1, True)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.PHASE

    def test_build_set_scribble(self):
        data = build_set_scribble(4, "Snare")
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.CHAN_SCRIBBLE
        assert rx.string_value == "Snare"

    def test_build_set_monitor_source(self):
        data = build_set_monitor_source(2, True)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.MON_SRC_3

    def test_build_set_headphone_source(self):
        data = build_set_headphone_source(0, True)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.HP_SRC_1

    def test_build_set_dim_level(self):
        data = build_set_dim_level(0.7)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.DIM_LEVEL
        assert rx.float_value == pytest.approx(0.7)

    def test_build_set_connection_mode_multicast(self):
        data = build_set_connection_mode(False)
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.CONNECTION_MODE
        assert rx.float_value == 0.0

    def test_build_set_connection_mode_unicast(self):
        data = build_set_connection_mode(True)
        rx = SigmaRxMessage(data)
        assert rx.float_value == 1.0


# ---------------------------------------------------------------------------
# Additional handler coverage — edge cases and missing sections
# ---------------------------------------------------------------------------


class TestChannelEdgeCases:
    def test_channel_zero_ignored(self, state):
        """Channel 0 is out of range (1-based) — handler should not crash."""
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.FADER, 0, struct.pack(">f", 0.5))
        handle_sigma_message(rx, state)

    def test_channel_17_ignored(self, state):
        """Channel 17 is out of range (max 16) — handler should not crash."""
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.FADER, 17, struct.pack(">f", 0.5))
        handle_sigma_message(rx, state)

    def test_empty_scribble(self, state):
        """Empty string scribble should set name to empty."""
        state.channels[0].name = "OldName"
        rx = _make_rx(PayloadType.STRING, SigmaMessageId.CHAN_SCRIBBLE, 1, b"")
        handle_sigma_message(rx, state)
        assert state.channels[0].name == ""

    def test_fader_all_16(self, state):
        """Set faders on all 16 channels and verify each."""
        for ch in range(1, 17):
            val = ch / 16.0
            rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.FADER, ch, struct.pack(">f", val))
            handle_sigma_message(rx, state)
        for ch in range(1, 17):
            assert state.channels[ch - 1].fader == pytest.approx(ch / 16.0)


class TestMonitorEdgeCases:
    def test_monitor_source_off(self, state):
        state.monitor.sources[2] = True
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.MON_SRC_3, 0, struct.pack(">f", 0.0))
        handle_sigma_message(rx, state)
        assert state.monitor.sources[2] is False

    def test_all_monitor_sources(self, state):
        for i in range(7):
            msg_id = SigmaMessageId.MON_SRC_1 + i
            rx = _make_rx(PayloadType.FLOAT, msg_id, 0, struct.pack(">f", 1.0))
            handle_sigma_message(rx, state)
        assert all(state.monitor.sources)


class TestHeadphoneEdgeCases:
    def test_headphone_source_off(self, state):
        state.headphone.sources[2] = True
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.HP_SRC_3, 0, struct.pack(">f", 0.0))
        handle_sigma_message(rx, state)
        assert state.headphone.sources[2] is False

    def test_all_headphone_sources(self, state):
        for i in range(4):
            msg_id = SigmaMessageId.HP_SRC_1 + i
            rx = _make_rx(PayloadType.FLOAT, msg_id, 0, struct.pack(">f", 1.0))
            handle_sigma_message(rx, state)
        assert all(state.headphone.sources)


class TestInsertEdgeCases:
    def test_insert_b_sum_off(self, state):
        state.insert.insert_b_sum = True
        f = uint_to_sigma_float(0)
        rx = _make_rx(
            PayloadType.UINT_AS_FLOAT, SigmaMessageId.INSERT_B_SUM, 0, struct.pack(">f", f)
        )
        handle_sigma_message(rx, state)
        assert state.insert.insert_b_sum is False

    def test_insert_a_off(self, state):
        """Value 0 means insert off."""
        f = uint_to_sigma_float(0)
        rx = _make_rx(PayloadType.UINT_AS_FLOAT, SigmaMessageId.INSERT_A, 0, struct.pack(">f", f))
        handle_sigma_message(rx, state)
        assert state.insert.insert_a == 0

    def test_insert_a_on(self, state):
        """Value 2 means insert on."""
        f = uint_to_sigma_float(2)
        rx = _make_rx(PayloadType.UINT_AS_FLOAT, SigmaMessageId.INSERT_A, 0, struct.pack(">f", f))
        handle_sigma_message(rx, state)
        assert state.insert.insert_a == 2

    def test_insert_a_on_plus_sum(self, state):
        """Value 3 means insert on + sum."""
        f = uint_to_sigma_float(3)
        rx = _make_rx(PayloadType.UINT_AS_FLOAT, SigmaMessageId.INSERT_A, 0, struct.pack(">f", f))
        handle_sigma_message(rx, state)
        assert state.insert.insert_a == 3

    def test_insert_a_sum_encoding(self, state):
        """Insert A SUM: value==3 means on, anything else means off."""
        f_on = uint_to_sigma_float(3)
        rx = _make_rx(
            PayloadType.UINT_AS_FLOAT, SigmaMessageId.INSERT_A_SUM, 0, struct.pack(">f", f_on)
        )
        handle_sigma_message(rx, state)
        assert state.insert.insert_a_sum is True

        f_off = uint_to_sigma_float(2)
        rx = _make_rx(
            PayloadType.UINT_AS_FLOAT, SigmaMessageId.INSERT_A_SUM, 0, struct.pack(">f", f_off)
        )
        handle_sigma_message(rx, state)
        assert state.insert.insert_a_sum is False


class TestAdditionalLevelHandlers:
    def test_level_fader(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.LEVEL_FADER, 0, struct.pack(">f", 0.65))
        handle_sigma_message(rx, state)
        assert state.level.level_fader == pytest.approx(0.65)

    def test_meter_mode(self, state):
        f = uint_to_sigma_float(3)
        rx = _make_rx(PayloadType.UINT_AS_FLOAT, SigmaMessageId.METER_MODE, 0, struct.pack(">f", f))
        handle_sigma_message(rx, state)
        assert state.level.meter_mode == 3

    def test_meter_source(self, state):
        f = uint_to_sigma_float(2)
        rx = _make_rx(
            PayloadType.UINT_AS_FLOAT, SigmaMessageId.METER_SOURCE, 0, struct.pack(">f", f)
        )
        handle_sigma_message(rx, state)
        assert state.level.meter_source == 2


class TestAdditionalDimHandlers:
    def test_dim_secondary(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.DIM_SECONDARY, 0, struct.pack(">f", 0.45))
        handle_sigma_message(rx, state)
        assert state.dim.secondary_dim == pytest.approx(0.45)
        assert state.monitor.secondary_dim == pytest.approx(0.45)


class TestAdditionalMiscHandlers:
    def test_talkback_mode(self, state):
        f = uint_to_sigma_float(1)
        rx = _make_rx(
            PayloadType.UINT_AS_FLOAT, SigmaMessageId.TALKBACK_MODE, 0, struct.pack(">f", f)
        )
        handle_sigma_message(rx, state)
        assert state.misc.talkback_mode == 1

    def test_oscillator_on(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.OSCILLATOR, 0, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.misc.oscillator is True

    def test_oscillator_off(self, state):
        state.misc.oscillator = True
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.OSCILLATOR, 0, struct.pack(">f", 0.0))
        handle_sigma_message(rx, state)
        assert state.misc.oscillator is False

    def test_listenback(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.LISTENBACK, 0, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.misc.listenback is True

    def test_daw_control(self, state):
        f = uint_to_sigma_float(2)
        rx = _make_rx(
            PayloadType.UINT_AS_FLOAT, SigmaMessageId.DAW_CONTROL, 0, struct.pack(">f", f)
        )
        handle_sigma_message(rx, state)
        assert state.misc.daw_control == 2


class TestAdditionalNetworkHandlers:
    def test_master_slave_on(self, state):
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.NET_MASTER_SLAVE, 0, struct.pack(">f", 1.0))
        handle_sigma_message(rx, state)
        assert state.network.master_slave is True

    def test_master_slave_off(self, state):
        state.network.master_slave = True
        rx = _make_rx(PayloadType.FLOAT, SigmaMessageId.NET_MASTER_SLAVE, 0, struct.pack(">f", 0.0))
        handle_sigma_message(rx, state)
        assert state.network.master_slave is False

    def test_subnet_octets(self, state):
        for i, val in enumerate([255, 255, 0, 0]):
            msg_id = SigmaMessageId.SUBNET_OCTET_1 + i
            f = uint_to_sigma_float(val)
            rx = _make_rx(PayloadType.UINT_AS_FLOAT, msg_id, 0, struct.pack(">f", f))
            handle_sigma_message(rx, state)
        assert state.network.subnet_octets == [255, 255, 0, 0]


class TestConnectionEdgeCases:
    def test_keepalive_heartbeat_advances(self, state):
        """Two keepalives should advance the heartbeat timestamp."""
        import time

        rx = _make_rx(PayloadType.NONE, SigmaMessageId.KEEPALIVE)
        handle_sigma_message(rx, state)
        first = state.last_heartbeat
        time.sleep(0.01)
        handle_sigma_message(rx, state)
        assert state.last_heartbeat > first


# ---------------------------------------------------------------------------
# Integration: build → parse → dispatch → verify state
# ---------------------------------------------------------------------------


class TestEndToEndIntegration:
    def test_fader_roundtrip(self, state):
        raw = build_set_fader(8, 0.42)
        rx = SigmaRxMessage(raw)
        handle_sigma_message(rx, state)
        assert state.channels[7].fader == pytest.approx(0.42)

    def test_solo_roundtrip(self, state):
        raw = build_set_solo(3, True)
        rx = SigmaRxMessage(raw)
        handle_sigma_message(rx, state)
        assert state.channels[2].solo is True

    def test_mute_roundtrip(self, state):
        raw = build_set_mute(16, True)
        rx = SigmaRxMessage(raw)
        handle_sigma_message(rx, state)
        assert state.channels[15].mute is True

    def test_scribble_roundtrip(self, state):
        raw = build_set_scribble(1, "Vox")
        rx = SigmaRxMessage(raw)
        handle_sigma_message(rx, state)
        assert state.channels[0].name == "Vox"

    def test_monitor_source_roundtrip(self, state):
        raw = build_set_monitor_source(5, True)
        rx = SigmaRxMessage(raw)
        handle_sigma_message(rx, state)
        assert state.monitor.sources[5] is True

    def test_headphone_source_roundtrip(self, state):
        raw = build_set_headphone_source(3, True)
        rx = SigmaRxMessage(raw)
        handle_sigma_message(rx, state)
        assert state.headphone.sources[3] is True

    def test_dim_roundtrip(self, state):
        raw = build_set_dim_level(0.55)
        rx = SigmaRxMessage(raw)
        handle_sigma_message(rx, state)
        assert state.dim.dim_level == pytest.approx(0.55)

    def test_handshake_roundtrip(self, state):
        raw = build_handshake()
        rx = SigmaRxMessage(raw)
        handle_sigma_message(rx, state)
        assert state.online is True
        assert state.last_heartbeat > 0
