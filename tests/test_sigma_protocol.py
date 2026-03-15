"""Tests for the SSL Sigma protocol wire format."""

import math
import struct

import pytest
from ssl_matrix_client.sigma_protocol import (
    SIGMA_FIXED_PACKET_SIZE,
    SIGMA_MAGIC,
    SIGMA_PRODUCT_TYPE,
    PayloadType,
    SigmaMessageId,
    SigmaRxMessage,
    SigmaTxMessage,
    bool_to_sigma_float,
    sigma_float_to_bool,
    sigma_float_to_uint,
    uint_to_sigma_float,
)

# ---------------------------------------------------------------------------
# Value encoding helpers
# ---------------------------------------------------------------------------


class TestBoolEncoding:
    def test_true_encodes_to_1(self):
        assert bool_to_sigma_float(True) == 1.0

    def test_false_encodes_to_0(self):
        assert bool_to_sigma_float(False) == 0.0

    def test_positive_decodes_to_true(self):
        assert sigma_float_to_bool(1.0) is True
        assert sigma_float_to_bool(0.5) is True

    def test_zero_decodes_to_false(self):
        assert sigma_float_to_bool(0.0) is False

    def test_negative_decodes_to_false(self):
        assert sigma_float_to_bool(-1.0) is False


class TestUintFloatReinterpret:
    def test_round_trip(self):
        for val in (0, 1, 42, 255, 0xDEADBEEF, 0xFFFFFFFF):
            f = uint_to_sigma_float(val)
            assert sigma_float_to_uint(f) == val

    def test_zero(self):
        assert uint_to_sigma_float(0) == 0.0
        assert sigma_float_to_uint(0.0) == 0

    def test_known_value(self):
        # 0x3F800000 is IEEE 754 for 1.0
        assert uint_to_sigma_float(0x3F800000) == 1.0
        assert sigma_float_to_uint(1.0) == 0x3F800000


# ---------------------------------------------------------------------------
# SigmaTxMessage — packet construction
# ---------------------------------------------------------------------------


class TestSigmaTxMessageFloat:
    def test_header_fields(self):
        msg = SigmaTxMessage.build_float_message(SigmaMessageId.FADER, sub_param=3, value=0.75)
        data = msg.to_bytes()
        assert data[0] == SIGMA_MAGIC
        assert struct.unpack_from(">I", data, 0x04)[0] == SIGMA_PRODUCT_TYPE
        composite = struct.unpack_from(">I", data, 0x08)[0]
        assert (composite >> 24) == PayloadType.FLOAT
        assert (composite & 0x00FFFFFF) == SigmaMessageId.FADER
        assert struct.unpack_from(">I", data, 0x0C)[0] == 3

    def test_float_payload(self):
        msg = SigmaTxMessage.build_float_message(SigmaMessageId.PAN, sub_param=0, value=-0.5)
        data = msg.to_bytes()
        payload = struct.unpack_from(">f", data, 0x14)[0]
        assert math.isclose(payload, -0.5, abs_tol=1e-7)

    def test_packet_size(self):
        msg = SigmaTxMessage.build_float_message(SigmaMessageId.FADER, sub_param=0, value=1.0)
        assert len(msg.to_bytes()) == SIGMA_FIXED_PACKET_SIZE


class TestSigmaTxMessageBool:
    def test_true_sends_one(self):
        msg = SigmaTxMessage.build_bool_message(SigmaMessageId.SOLO, sub_param=5, value=True)
        data = msg.to_bytes()
        payload = struct.unpack_from(">f", data, 0x14)[0]
        assert payload == 1.0

    def test_false_sends_zero(self):
        msg = SigmaTxMessage.build_bool_message(SigmaMessageId.MUTE, sub_param=0, value=False)
        data = msg.to_bytes()
        payload = struct.unpack_from(">f", data, 0x14)[0]
        assert payload == 0.0


class TestSigmaTxMessageUint:
    def test_uint_reinterpret(self):
        msg = SigmaTxMessage.build_uint_message(SigmaMessageId.PAN_MODE, sub_param=1, value=42)
        data = msg.to_bytes()
        composite = struct.unpack_from(">I", data, 0x08)[0]
        assert (composite >> 24) == PayloadType.UINT_AS_FLOAT
        # Payload should be the float reinterpretation of uint32(42)
        raw_bytes = data[0x14 : 0x14 + 4]
        assert struct.unpack(">I", raw_bytes)[0] == 42


class TestSigmaTxMessageString:
    def test_string_payload(self):
        msg = SigmaTxMessage.build_string_message(
            SigmaMessageId.CHAN_SCRIBBLE, sub_param=2, text="Kick"
        )
        data = msg.to_bytes()
        composite = struct.unpack_from(">I", data, 0x08)[0]
        assert (composite >> 24) == PayloadType.STRING
        payload = data[0x14:]
        assert payload == b"Kick"

    def test_7bit_masking(self):
        # Characters above 0x7F should be masked
        msg = SigmaTxMessage.build_string_message(
            SigmaMessageId.CHAN_SCRIBBLE, sub_param=0, text="\x80\xff"
        )
        data = msg.to_bytes()
        payload = data[0x14:]
        for b in payload:
            assert b <= 0x7F

    def test_variable_length(self):
        short = SigmaTxMessage.build_string_message(
            SigmaMessageId.CHAN_SCRIBBLE, sub_param=0, text="Hi"
        )
        long = SigmaTxMessage.build_string_message(
            SigmaMessageId.CHAN_SCRIBBLE, sub_param=0, text="Hello World"
        )
        assert len(long.to_bytes()) > len(short.to_bytes())

    def test_empty_string(self):
        msg = SigmaTxMessage.build_string_message(
            SigmaMessageId.CHAN_SCRIBBLE, sub_param=1, text=""
        )
        data = msg.to_bytes()
        # Packet should be just the header (0x14) with no payload bytes
        assert len(data) == 0x14

    def test_0xff_masked_to_0x7f(self):
        """Char 0xFF should become 0x7F after 7-bit masking."""
        msg = SigmaTxMessage.build_string_message(
            SigmaMessageId.CHAN_SCRIBBLE, sub_param=0, text="\xff"
        )
        data = msg.to_bytes()
        assert data[0x14] == 0x7F


class TestSigmaTxMessageHandshake:
    def test_no_payload(self):
        msg = SigmaTxMessage.build_handshake(SigmaMessageId.HANDSHAKE)
        data = msg.to_bytes()
        composite = struct.unpack_from(">I", data, 0x08)[0]
        assert (composite >> 24) == PayloadType.NONE
        # Packet is just the header (0x14 bytes), no payload
        assert len(data) == 0x14


# ---------------------------------------------------------------------------
# SigmaRxMessage — packet parsing
# ---------------------------------------------------------------------------


def _build_raw_packet(payload_type, msg_id, sub_param=0, payload=b"", magic=SIGMA_MAGIC):
    """Build a raw packet for testing RxMessage parsing."""
    buf = bytearray(0x14 + len(payload))
    buf[0] = magic
    struct.pack_into(">I", buf, 0x04, SIGMA_PRODUCT_TYPE)
    composite = (payload_type << 24) | (msg_id & 0x00FFFFFF)
    struct.pack_into(">I", buf, 0x08, composite)
    struct.pack_into(">I", buf, 0x0C, sub_param)
    buf[0x14:] = payload
    return bytes(buf)


class TestSigmaRxMessageFloat:
    def test_parse_float(self):
        payload = struct.pack(">f", 0.75)
        data = _build_raw_packet(PayloadType.FLOAT, SigmaMessageId.FADER, 3, payload)
        rx = SigmaRxMessage(data)
        assert rx.magic == SIGMA_MAGIC
        assert rx.product_type == SIGMA_PRODUCT_TYPE
        assert rx.payload_type == PayloadType.FLOAT
        assert rx.msg_id == SigmaMessageId.FADER
        assert rx.sub_param == 3
        assert math.isclose(rx.float_value, 0.75, abs_tol=1e-7)
        assert rx.uint_value is None
        assert rx.string_value is None


class TestSigmaRxMessageUintPair:
    def test_parse_uint_pair(self):
        payload = struct.pack(">II", 7, 42)
        data = _build_raw_packet(PayloadType.UINT_PAIR, SigmaMessageId.CHAN_BTN_SLOT, 0, payload)
        rx = SigmaRxMessage(data)
        assert rx.payload_type == PayloadType.UINT_PAIR
        assert rx.uint_value == 7
        assert rx.uint_extra == 42
        assert rx.float_value is None


class TestSigmaRxMessageString:
    def test_parse_string(self):
        payload = bytes(ord(c) & 0x7F for c in "Vocal")
        data = _build_raw_packet(PayloadType.STRING, SigmaMessageId.CHAN_SCRIBBLE, 1, payload)
        rx = SigmaRxMessage(data)
        assert rx.payload_type == PayloadType.STRING
        assert rx.string_value == "Vocal"

    def test_7bit_masking(self):
        payload = bytes([0xC8, 0xE9])  # high bits set
        data = _build_raw_packet(PayloadType.STRING, SigmaMessageId.CHAN_SCRIBBLE, 0, payload)
        rx = SigmaRxMessage(data)
        for c in rx.string_value:
            assert ord(c) <= 0x7F


class TestSigmaRxMessageNone:
    def test_parse_no_payload(self):
        data = _build_raw_packet(PayloadType.NONE, SigmaMessageId.KEEPALIVE)
        rx = SigmaRxMessage(data)
        assert rx.payload_type == PayloadType.NONE
        assert rx.float_value is None
        assert rx.uint_value is None
        assert rx.string_value is None


class TestSigmaRxMessageUintAsFloat:
    def test_parse_uint_as_float(self):
        val = 42
        float_repr = uint_to_sigma_float(val)
        payload = struct.pack(">f", float_repr)
        data = _build_raw_packet(PayloadType.UINT_AS_FLOAT, SigmaMessageId.PAN_MODE, 1, payload)
        rx = SigmaRxMessage(data)
        assert rx.payload_type == PayloadType.UINT_AS_FLOAT
        assert rx.uint_value == val
        assert rx.float_value is not None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestSigmaRxValidation:
    def test_bad_magic(self):
        data = _build_raw_packet(PayloadType.NONE, 0x99, magic=0x00)
        # Re-patch magic since _build_raw_packet uses the magic param
        with pytest.raises(ValueError, match="Invalid magic byte"):
            SigmaRxMessage(data)

    def test_bad_product_type(self):
        buf = bytearray(_build_raw_packet(PayloadType.NONE, SigmaMessageId.KEEPALIVE))
        struct.pack_into(">I", buf, 0x04, 99)
        with pytest.raises(ValueError, match="Invalid product type"):
            SigmaRxMessage(bytes(buf))

    def test_too_short(self):
        with pytest.raises(ValueError, match="Packet too short"):
            SigmaRxMessage(b"\x53" * 10)


# ---------------------------------------------------------------------------
# Round-trip: build → parse
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_float_round_trip(self):
        tx = SigmaTxMessage.build_float_message(SigmaMessageId.FADER, 7, 0.333)
        rx = SigmaRxMessage(tx.to_bytes())
        assert rx.msg_id == SigmaMessageId.FADER
        assert rx.sub_param == 7
        assert math.isclose(rx.float_value, 0.333, abs_tol=1e-6)

    def test_bool_round_trip(self):
        tx = SigmaTxMessage.build_bool_message(SigmaMessageId.SOLO, 2, True)
        rx = SigmaRxMessage(tx.to_bytes())
        assert sigma_float_to_bool(rx.float_value) is True

    def test_bool_false_round_trip(self):
        tx = SigmaTxMessage.build_bool_message(SigmaMessageId.MUTE, 0, False)
        rx = SigmaRxMessage(tx.to_bytes())
        assert sigma_float_to_bool(rx.float_value) is False

    def test_uint_round_trip(self):
        tx = SigmaTxMessage.build_uint_message(SigmaMessageId.METER_MODE, 0, 3)
        rx = SigmaRxMessage(tx.to_bytes())
        assert rx.uint_value == 3

    def test_string_round_trip(self):
        tx = SigmaTxMessage.build_string_message(SigmaMessageId.CHAN_SCRIBBLE, 4, "Snare")
        rx = SigmaRxMessage(tx.to_bytes())
        assert rx.string_value == "Snare"

    def test_handshake_round_trip(self):
        tx = SigmaTxMessage.build_handshake(SigmaMessageId.HANDSHAKE)
        rx = SigmaRxMessage(tx.to_bytes())
        assert rx.msg_id == SigmaMessageId.HANDSHAKE
        assert rx.payload_type == PayloadType.NONE


# ---------------------------------------------------------------------------
# SigmaMessageId enum coverage
# ---------------------------------------------------------------------------


class TestSigmaMessageIdEnum:
    def test_all_ids_are_unique(self):
        values = [m.value for m in SigmaMessageId]
        assert len(values) == len(set(values))

    def test_known_ids(self):
        assert SigmaMessageId.FADER == 0x2B
        assert SigmaMessageId.SOLO == 0x26
        assert SigmaMessageId.HANDSHAKE == 0x9D
        assert SigmaMessageId.KEEPALIVE == 0x99


# ---------------------------------------------------------------------------
# Edge cases — truncated / malformed payloads
# ---------------------------------------------------------------------------


class TestRxEdgeCases:
    def test_float_payload_truncated(self):
        """Header is valid but float payload is only 2 bytes instead of 4."""
        data = _build_raw_packet(PayloadType.FLOAT, SigmaMessageId.FADER, 1, b"\x00\x00")
        rx = SigmaRxMessage(data)
        # Packet is 0x16 bytes, < 0x18 required for float — float_value should be None
        assert rx.float_value is None

    def test_uint_pair_truncated(self):
        """UINT_PAIR needs 8 bytes of payload but only 4 provided."""
        data = _build_raw_packet(
            PayloadType.UINT_PAIR,
            SigmaMessageId.CHAN_BTN_SLOT,
            0,
            struct.pack(">I", 7),
        )
        rx = SigmaRxMessage(data)
        # Packet is 0x18 bytes, < 0x1C required — both should be None
        assert rx.uint_value is None
        assert rx.uint_extra is None

    def test_string_empty_payload(self):
        """String payload with zero bytes."""
        data = _build_raw_packet(PayloadType.STRING, SigmaMessageId.CHAN_SCRIBBLE, 1, b"")
        rx = SigmaRxMessage(data)
        assert rx.string_value == ""

    def test_none_type_exactly_header(self):
        """NONE payload type with exactly 0x14 bytes (header only) is valid."""
        data = _build_raw_packet(PayloadType.NONE, SigmaMessageId.KEEPALIVE)
        assert len(data) == 0x14
        rx = SigmaRxMessage(data)
        assert rx.msg_id == SigmaMessageId.KEEPALIVE

    def test_uint_as_float_truncated(self):
        """UINT_AS_FLOAT with only 2 bytes of payload."""
        data = _build_raw_packet(
            PayloadType.UINT_AS_FLOAT, SigmaMessageId.METER_MODE, 0, b"\x00\x00"
        )
        rx = SigmaRxMessage(data)
        assert rx.float_value is None
        assert rx.uint_value is None
