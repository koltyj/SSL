"""Tests for protocol.py: TxMessage, RxMessage, wire format."""

import struct

import pytest
from ssl_matrix_client.protocol import (
    BUFFER_SIZE,
    PORT,
    TO_DESK,
    TO_REMOTE,
    MessageCode,
    RxMessage,
    TxMessage,
)


class TestTxMessage:
    def test_header_format(self):
        msg = TxMessage(MessageCode.GET_DESK, 0, 12345)
        data = msg.to_bytes()
        cmd, dest, desk, remote = struct.unpack_from(">iiii", data)
        assert cmd == MessageCode.GET_DESK
        assert dest == TO_DESK
        assert desk == 0
        assert remote == 12345

    def test_write_int(self):
        msg = TxMessage(5, 0, 0)
        msg.write_int(42)
        data = msg.to_bytes()
        assert struct.unpack_from(">i", data, 16)[0] == 42

    def test_write_short(self):
        msg = TxMessage(5, 0, 0)
        msg.write_short(300)
        data = msg.to_bytes()
        assert struct.unpack_from(">h", data, 16)[0] == 300

    def test_write_byte(self):
        msg = TxMessage(5, 0, 0)
        msg.write_byte(255)
        data = msg.to_bytes()
        assert data[16] == 255

    def test_write_boolean_true(self):
        msg = TxMessage(5, 0, 0)
        msg.write_boolean(True)
        assert msg.to_bytes()[16] == 1

    def test_write_boolean_false(self):
        msg = TxMessage(5, 0, 0)
        msg.write_boolean(False)
        assert msg.to_bytes()[16] == 0

    def test_write_string(self):
        msg = TxMessage(5, 0, 0)
        msg.write_string("ABC")
        data = msg.to_bytes()
        assert data[16:20] == b"ABC\x00"

    def test_overflow_raises(self):
        msg = TxMessage(5, 0, 0)
        # Fill buffer near end
        msg._index = BUFFER_SIZE - 2
        with pytest.raises(ValueError, match="overflow"):
            msg.write_int(1)

    def test_roundtrip_int(self):
        msg = TxMessage(5, 1000, 2000)
        msg.write_int(-42)
        msg.write_int(0x7FFFFFFF)
        rx = RxMessage(msg.to_bytes())
        assert rx.get_int() == -42
        assert rx.get_int() == 0x7FFFFFFF

    def test_roundtrip_string(self):
        msg = TxMessage(5, 0, 0)
        msg.write_string("Hello")
        rx = RxMessage(msg.to_bytes())
        assert rx.get_string() == "Hello"


class TestRxMessage:
    def _make_rx(self, payload=b""):
        header = struct.pack(">iiii", 6, TO_REMOTE, 1000, 99)
        return RxMessage(header + payload)

    def test_header_properties(self):
        rx = self._make_rx()
        assert rx.cmd_code == 6
        assert rx.dest_code == TO_REMOTE
        assert rx.desk_serial == 1000
        assert rx.remote_serial == 99

    def test_get_int(self):
        rx = self._make_rx(struct.pack(">i", -1))
        assert rx.get_int() == -1

    def test_get_short(self):
        rx = self._make_rx(struct.pack(">h", -500))
        assert rx.get_short() == -500

    def test_get_byte_signed(self):
        """Java's byte is signed: 0xFF -> -1."""
        rx = self._make_rx(bytes([0xFF]))
        assert rx.get_byte() == -1

    def test_get_byte_positive(self):
        rx = self._make_rx(bytes([127]))
        assert rx.get_byte() == 127

    def test_get_unsigned_byte(self):
        rx = self._make_rx(bytes([0xFF]))
        assert rx.get_unsigned_byte() == 255

    def test_get_boolean(self):
        rx = self._make_rx(bytes([1, 0]))
        assert rx.get_boolean() is True
        assert rx.get_boolean() is False

    def test_get_string(self):
        rx = self._make_rx(b"test\x00extra")
        assert rx.get_string() == "test"

    def test_get_string_no_null(self):
        """String without null terminator reads to end of packet."""
        rx = self._make_rx(b"noterm")
        assert rx.get_string() == "noterm"

    def test_underflow_raises(self):
        rx = self._make_rx(b"")
        with pytest.raises(BufferError, match="underflow"):
            rx.get_int()

    def test_remaining(self):
        rx = self._make_rx(b"\x00\x01\x02\x03")
        assert rx.remaining == 4
        rx.get_int()
        assert rx.remaining == 0

    def test_peek_int(self):
        rx = self._make_rx(struct.pack(">i", 42))
        assert rx.peek_int(0) == 42
        # Cursor should not advance
        assert rx.remaining == 4

    def test_peek_int_out_of_bounds(self):
        rx = self._make_rx(b"")
        with pytest.raises(BufferError, match="peek_int"):
            rx.peek_int(0)


class TestEdgeCases:
    def test_write_byte_mask(self):
        """Values > 255 get masked to 0xFF."""
        msg = TxMessage(5, 0, 0)
        msg.write_byte(256)  # should mask to 0
        assert msg.to_bytes()[16] == 0
        msg2 = TxMessage(5, 0, 0)
        msg2.write_byte(0x1FF)  # should mask to 0xFF
        assert msg2.to_bytes()[16] == 0xFF

    def test_get_string_empty(self):
        """Null byte at start returns empty string."""
        header = struct.pack(">iiii", 6, TO_REMOTE, 1000, 99)
        rx = RxMessage(header + b"\x00more")
        assert rx.get_string() == ""

    def test_write_string_non_ascii(self):
        """Non-ASCII chars get replaced."""
        msg = TxMessage(5, 0, 0)
        msg.write_string("caf\u00e9")
        data = msg.to_bytes()
        # \u00e9 replaced with '?' by ascii encode errors='replace'
        assert data[16:21] == b"caf?\x00"


class TestProtocolConstants:
    def test_port(self):
        assert PORT == 50081

    def test_buffer_size(self):
        assert BUFFER_SIZE == 2048

    def test_message_code_values(self):
        assert MessageCode.GET_DESK == 5
        assert MessageCode.SEND_RESTART_CONSOLE == 760
        assert MessageCode.SEND_GET_INSERT_INFO_V2 == 10400
