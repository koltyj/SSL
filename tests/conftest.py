"""Shared fixtures and import shim for ssl-matrix-client tests.

The package directory uses a hyphen (ssl-matrix-client), which is not a valid
Python identifier. We patch sys.modules so tests can import with underscores.
"""

import importlib
import struct
import sys

import pytest

# --- Import shim: ssl-matrix-client -> ssl_matrix_client ---

pkg = importlib.import_module("ssl-matrix-client")
sys.modules["ssl_matrix_client"] = pkg

for sub in ["protocol", "models", "client", "cli", "templates"]:
    try:
        mod = importlib.import_module(f"ssl-matrix-client.{sub}")
        sys.modules[f"ssl_matrix_client.{sub}"] = mod
    except ModuleNotFoundError:
        pass  # module may not exist yet (e.g. templates during initial shim setup)

handlers = importlib.import_module("ssl-matrix-client.handlers")
sys.modules["ssl_matrix_client.handlers"] = handlers

for h in [
    "connection",
    "channels",
    "profiles",
    "delta",
    "routing",
    "projects",
    "total_recall",
    "chan_presets",
    "xpatch",
    "softkeys",
]:
    mod = importlib.import_module(f"ssl-matrix-client.handlers.{h}")
    sys.modules[f"ssl_matrix_client.handlers.{h}"] = mod


# --- Shared fixtures ---

from ssl_matrix_client.models import ConsoleState  # noqa: E402
from ssl_matrix_client.protocol import TO_REMOTE, RxMessage  # noqa: E402


@pytest.fixture
def state():
    """Fresh ConsoleState for each test."""
    return ConsoleState()


def build_rx_packet(cmd, payload=b"", desk_serial=1000, remote_serial=99):
    """Build a fake RxMessage with the given cmd code and payload bytes."""
    header = struct.pack(">iiii", cmd, TO_REMOTE, desk_serial, remote_serial)
    return RxMessage(header + payload)


def payload_int(value):
    """Encode a big-endian signed int for test payloads."""
    return struct.pack(">i", value)


def payload_short(value):
    """Encode a big-endian signed short for test payloads."""
    return struct.pack(">h", value)


def payload_byte(value):
    """Encode a single byte for test payloads."""
    return bytes([value & 0xFF])


def payload_bool(value):
    """Encode a boolean byte for test payloads."""
    return bytes([1 if value else 0])


def payload_string(s):
    """Encode a null-terminated ASCII string for test payloads."""
    return s.encode("ascii") + b"\x00"
