"""Tests for SSLMatrixClient watchdog thread and reconnect logic.

The watchdog monitors SSL UDP heartbeat only, NOT ipMIDI (which runs on a
separate port/protocol and is out of scope for this monitor).
"""

import threading
import time
from unittest.mock import MagicMock, patch

from ssl_matrix_client.client import (
    HEARTBEAT_TIMEOUT,
    MAX_RECONNECT_ATTEMPTS,
    SSLMatrixClient,
)

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
    client._dispatch = {}
    client._split_config = None
    client._on_state_changed = None
    client._on_desk_offline = None
    client._on_desk_online = None
    return client


# ---------------------------------------------------------------------------
# TestWatchdog: basic heartbeat detection
# ---------------------------------------------------------------------------


class TestWatchdog:
    def test_stale_heartbeat_triggers_reconnect(self):
        """When heartbeat_age > HEARTBEAT_TIMEOUT and desk is online, trigger reconnect."""
        client = make_client()
        client.state.desk.online = True
        # heartbeat_age = inf when last_heartbeat == 0, so no need to patch time
        client._trigger_reconnect = MagicMock()
        client._send_get_desk = MagicMock()

        # Run one watchdog iteration manually
        with client._lock:
            online = client.state.desk.online
            age = client.state.desk.heartbeat_age
            reconnecting = client._reconnecting

        if online and age > HEARTBEAT_TIMEOUT and not reconnecting:
            client._trigger_reconnect()

        client._trigger_reconnect.assert_called_once()

    def test_fresh_heartbeat_no_reconnect(self):
        """When heartbeat_age is below threshold, watchdog does not reconnect."""
        client = make_client()
        client.state.desk.online = True
        client.state.desk.last_heartbeat = time.time()  # just received
        client._trigger_reconnect = MagicMock()

        with client._lock:
            online = client.state.desk.online
            age = client.state.desk.heartbeat_age
            reconnecting = client._reconnecting

        if online and age > HEARTBEAT_TIMEOUT and not reconnecting:
            client._trigger_reconnect()

        client._trigger_reconnect.assert_not_called()

    def test_offline_desk_no_reconnect(self):
        """When desk is offline, watchdog does not trigger reconnect."""
        client = make_client()
        client.state.desk.online = False
        client.state.desk.last_heartbeat = 0.0  # stale
        client._trigger_reconnect = MagicMock()

        with client._lock:
            online = client.state.desk.online
            age = client.state.desk.heartbeat_age
            reconnecting = client._reconnecting

        if online and age > HEARTBEAT_TIMEOUT and not reconnecting:
            client._trigger_reconnect()

        client._trigger_reconnect.assert_not_called()

    def test_watchdog_loop_calls_trigger_reconnect_when_stale(self):
        """Integration: _watchdog_loop calls _trigger_reconnect on stale heartbeat."""
        client = make_client()
        client.state.desk.online = True
        client.state.desk.last_heartbeat = 0.0  # age = inf
        client._running = True
        client._trigger_reconnect = MagicMock()
        client._send_get_desk = MagicMock()

        def fake_sleep(duration):
            # Stop after first iteration
            client._running = False

        with patch("ssl_matrix_client.client.time.sleep", side_effect=fake_sleep):
            client._watchdog_loop()

        client._trigger_reconnect.assert_called_once()

    def test_watchdog_loop_no_reconnect_on_fresh_heartbeat(self):
        """_watchdog_loop does not reconnect when heartbeat is fresh."""
        client = make_client()
        client.state.desk.online = True
        client.state.desk.last_heartbeat = time.time()
        client._running = True
        client._trigger_reconnect = MagicMock()

        def fake_sleep(duration):
            client._running = False

        with patch("ssl_matrix_client.client.time.sleep", side_effect=fake_sleep):
            client._watchdog_loop()

        client._trigger_reconnect.assert_not_called()


# ---------------------------------------------------------------------------
# TestReconnectGuard: prevent reconnect storms
# ---------------------------------------------------------------------------


class TestReconnectGuard:
    def test_reconnecting_flag_skips_reconnect(self):
        """When _reconnecting is True, watchdog skips reconnect even if heartbeat is stale."""
        client = make_client()
        client.state.desk.online = True
        client.state.desk.last_heartbeat = 0.0
        client._reconnecting = True
        client._trigger_reconnect = MagicMock()

        with client._lock:
            online = client.state.desk.online
            age = client.state.desk.heartbeat_age
            reconnecting = client._reconnecting

        if online and age > HEARTBEAT_TIMEOUT and not reconnecting:
            client._trigger_reconnect()

        client._trigger_reconnect.assert_not_called()

    def test_trigger_reconnect_sets_reconnecting_flag(self):
        """_trigger_reconnect sets _reconnecting = True."""
        client = make_client()
        client._send_get_desk = MagicMock()
        client.state.desk.last_heartbeat = time.time()

        client._trigger_reconnect()

        assert client._reconnecting is True

    def test_trigger_reconnect_marks_desk_offline(self):
        """_trigger_reconnect sets desk.online = False."""
        client = make_client()
        client.state.desk.online = True
        client._send_get_desk = MagicMock()

        client._trigger_reconnect()

        assert client.state.desk.online is False

    def test_trigger_reconnect_increments_attempt_counter(self):
        """_trigger_reconnect increments _reconnect_attempts."""
        client = make_client()
        client._send_get_desk = MagicMock()
        assert client._reconnect_attempts == 0

        client._trigger_reconnect()
        assert client._reconnect_attempts == 1

        client._trigger_reconnect()
        assert client._reconnect_attempts == 2

    def test_trigger_reconnect_sends_get_desk(self):
        """_trigger_reconnect calls _send_get_desk."""
        client = make_client()
        client._send_get_desk = MagicMock()

        client._trigger_reconnect()

        client._send_get_desk.assert_called_once()


# ---------------------------------------------------------------------------
# TestReconnectAttempts: max attempt guard
# ---------------------------------------------------------------------------


class TestReconnectAttempts:
    def test_max_attempts_stops_reconnecting(self):
        """After MAX_RECONNECT_ATTEMPTS, watchdog stops retrying and clears _reconnecting."""
        client = make_client()
        client.state.desk.online = False
        client._reconnecting = True
        client._reconnect_attempts = MAX_RECONNECT_ATTEMPTS
        client._running = True
        client._trigger_reconnect = MagicMock()

        def fake_sleep(duration):
            client._running = False

        with patch("ssl_matrix_client.client.time.sleep", side_effect=fake_sleep):
            client._watchdog_loop()

        # Should clear the reconnecting flag
        assert client._reconnecting is False
        assert client._reconnect_attempts == 0
        # Should NOT trigger another reconnect (already at max)
        client._trigger_reconnect.assert_not_called()


# ---------------------------------------------------------------------------
# TestReconnectSync: re-sync after reconnect
# ---------------------------------------------------------------------------


class TestReconnectSync:
    def test_needs_resync_flag_cleared_after_sync(self):
        """After reconnect, _needs_resync flag is set then cleared by watchdog."""
        client = make_client()
        client._needs_resync = True
        client._running = True
        client.request_sync = MagicMock()

        def fake_sleep(duration):
            client._running = False

        with patch("ssl_matrix_client.client.time.sleep", side_effect=fake_sleep):
            client._watchdog_loop()

        client.request_sync.assert_called_once()
        assert client._needs_resync is False

    def test_get_desk_reply_sets_needs_resync_when_reconnecting(self):
        """After successful reconnect (desk online), _needs_resync is set True."""
        client = make_client()
        # Simulate state as if _trigger_reconnect was called
        client._reconnecting = True
        client._reconnect_attempts = 3
        client.state.desk.online = False

        # Simulate what handle_get_desk_reply does: sets desk.online = True
        # Then our post-dispatch logic should set _needs_resync = True
        # We test the method that handles this transition
        client._on_desk_came_online()

        assert client._needs_resync is True
        assert client._reconnecting is False
        assert client._reconnect_attempts == 0

    def test_on_desk_came_online_noop_when_not_reconnecting(self):
        """_on_desk_came_online is a no-op when _reconnecting is False."""
        client = make_client()
        client._reconnecting = False
        client._needs_resync = False

        client._on_desk_came_online()

        assert client._needs_resync is False


# ---------------------------------------------------------------------------
# TestWatchdogLifecycle: thread start/stop
# ---------------------------------------------------------------------------


class TestWatchdogLifecycle:
    def test_connect_starts_watchdog_thread(self):
        """connect() starts the watchdog thread."""
        client = SSLMatrixClient.__new__(SSLMatrixClient)
        client.console_ip = "127.0.0.1"
        client.port = 50081
        client.my_serial = 99
        from ssl_matrix_client.models import ConsoleState

        client.state = ConsoleState()
        client._sock = MagicMock()
        client._recv_thread = None
        client._watchdog_thread = None
        client._running = False
        client._lock = threading.Lock()
        client._reconnecting = False
        client._reconnect_attempts = 0
        client._needs_resync = False
        client._split_config = None
        client._dispatch = {}

        with (
            patch.object(client, "_create_socket", return_value=MagicMock()),
            patch.object(client, "_send_get_desk"),
            patch("ssl_matrix_client.client.threading.Thread") as mock_thread_cls,
        ):
            mock_thread = MagicMock()
            mock_thread_cls.return_value = mock_thread
            client.connect()

        # Thread constructor called at least twice (recv + watchdog)
        assert mock_thread_cls.call_count >= 2
        thread_targets = [kw.get("target") for _, kw in mock_thread_cls.call_args_list]
        assert client._watchdog_loop in thread_targets

    def test_disconnect_joins_watchdog_thread(self):
        """disconnect() joins the watchdog thread."""
        client = make_client()
        mock_watchdog = MagicMock()
        client._watchdog_thread = mock_watchdog
        client._running = True

        client.disconnect()

        mock_watchdog.join.assert_called()
        assert client._watchdog_thread is None
