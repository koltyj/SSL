"""Tests for SSLMatrixClient split board state tracking.

Split board is software bookkeeping only — no UDP commands are sent.
The physical fader group assignment happens via hardware buttons on the console.
"""

import threading
from unittest.mock import MagicMock

import pytest
from ssl_matrix_client.client import SSLMatrixClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_client():
    """Return an SSLMatrixClient without a real socket."""
    client = SSLMatrixClient.__new__(SSLMatrixClient)
    client.console_ip = "192.168.1.2"
    client.port = 50081
    client.my_serial = 12345
    from ssl_matrix_client.models import ConsoleState

    client.state = ConsoleState()
    client._sock = None
    client._recv_thread = None
    client._watchdog_thread = None
    client._running = False
    client._lock = threading.Lock()
    client._reconnecting = False
    client._reconnect_attempts = 0
    client._needs_resync = False
    client._split_config = None
    client._dispatch = {}
    return client


# ---------------------------------------------------------------------------
# TestSplitState
# ---------------------------------------------------------------------------


class TestSplitState:
    def test_default_split_is_none(self):
        """Default split config is None — split is not active."""
        client = make_client()
        assert client.get_split() is None

    def test_set_split_stores_config(self):
        """set_split() stores left/right layer lists in _split_config."""
        client = make_client()
        result = client.set_split([1, 2], [3, 4])
        assert result == {"left": [1, 2], "right": [3, 4]}
        assert client._split_config == {"left": [1, 2], "right": [3, 4]}

    def test_get_split_returns_config(self):
        """get_split() returns the current split config dict."""
        client = make_client()
        client.set_split([1], [2, 3])
        config = client.get_split()
        assert config == {"left": [1], "right": [2, 3]}

    def test_clear_split_resets_to_none(self):
        """clear_split() resets split config to None."""
        client = make_client()
        client.set_split([1, 2], [3, 4])
        client.clear_split()
        assert client.get_split() is None

    def test_set_split_overwrites_previous(self):
        """set_split() replaces any previous split config."""
        client = make_client()
        client.set_split([1, 2], [3, 4])
        client.set_split([1], [2])
        assert client.get_split() == {"left": [1], "right": [2]}

    def test_set_split_no_udp_sent(self):
        """set_split() does not send any UDP messages."""
        client = make_client()
        client.send = MagicMock()
        client.send_raw = MagicMock()

        client.set_split([1, 2], [3, 4])

        client.send.assert_not_called()
        client.send_raw.assert_not_called()

    def test_get_split_no_udp_sent(self):
        """get_split() does not send any UDP messages."""
        client = make_client()
        client.send = MagicMock()
        client.send_raw = MagicMock()
        client.set_split([1, 2], [3, 4])

        client.get_split()

        client.send.assert_not_called()
        client.send_raw.assert_not_called()

    def test_clear_split_no_udp_sent(self):
        """clear_split() does not send any UDP messages."""
        client = make_client()
        client.send = MagicMock()
        client.send_raw = MagicMock()
        client.set_split([1, 2], [3, 4])

        client.clear_split()

        client.send.assert_not_called()
        client.send_raw.assert_not_called()

    def test_set_split_validates_layer_numbers(self):
        """set_split() raises ValueError for layer numbers outside 1-4."""
        client = make_client()
        with pytest.raises(ValueError):
            client.set_split([0, 1], [2, 3])  # 0 is invalid

    def test_set_split_validates_right_layers(self):
        """set_split() raises ValueError for invalid right layer numbers."""
        client = make_client()
        with pytest.raises(ValueError):
            client.set_split([1, 2], [3, 5])  # 5 is invalid

    def test_set_split_accepts_all_four_layers(self):
        """set_split() accepts layers 1-4."""
        client = make_client()
        result = client.set_split([1, 2], [3, 4])
        assert result == {"left": [1, 2], "right": [3, 4]}

    def test_set_split_accepts_single_layer_each_side(self):
        """set_split() accepts single-layer assignments."""
        client = make_client()
        result = client.set_split([1], [2])
        assert result == {"left": [1], "right": [2]}
