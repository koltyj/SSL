"""UDP client for SSL Sigma console control. EXPERIMENTAL — untested against real hardware.

Same threading model as SSLMatrixClient: single UDP socket, recv thread, watchdog.
Uses the Sigma wire format (24-byte header, magic 0x53, ProductType 4) instead of
the Matrix protocol.
"""

import logging
import socket
import struct
import threading
import time

from .handlers.sigma import (
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
from .sigma_models import SigmaState
from .sigma_protocol import (
    SIGMA_BUFFER_SIZE,
    SIGMA_HANDSHAKE_MASTER_PORT,
    SIGMA_MAGIC,
    SIGMA_MULTICAST_1,
    SIGMA_MULTICAST_2,
    SIGMA_PORT,
    SIGMA_PRODUCT_TYPE,
    SigmaRxMessage,
)

log = logging.getLogger(__name__)

# Watchdog / reconnect constants
HEARTBEAT_TIMEOUT = 35.0
WATCHDOG_INTERVAL = 5.0
KEEPALIVE_INTERVAL = 10.0
RECONNECT_DELAY = 5.0
MAX_RECONNECT_ATTEMPTS = 10


class SSLSigmaClient:
    """UDP client for SSL Sigma console control.

    **EXPERIMENTAL** — reverse-engineered from the Sigma Remote APK v2.1.33
    via Ghidra decompilation of libjuce_jni.so. Not yet tested against real
    hardware. If you have a Sigma, please help us validate.

    The Sigma uses a different wire format from the Matrix:
    - 24-byte fixed header with magic byte 0x53 ('S')
    - ProductType 4
    - Payload type encoded in the top byte of the msg_id composite field
    - Handshake via multicast to 225.0.0.38 on port 29940

    Note: The desk communication port defaults to 50081 (inferred from ELF
    binary analysis, not confirmed from decompiled code paths). If this is
    wrong, pass the correct port to ``__init__``.
    """

    def __init__(self, console_ip="192.168.1.201", port=SIGMA_PORT):
        self.console_ip = console_ip
        self.port = port
        self.state = SigmaState()
        self._sock = None
        self._recv_thread = None
        self._watchdog_thread = None
        self._running = False
        self._lock = threading.Lock()
        # Reconnect guard state
        self._reconnecting = False
        self._reconnect_attempts = 0
        self._needs_resync = False
        # TUI callback hooks (set by TUI to bridge recv thread -> event loop)
        self._on_state_changed = None  # Callable | None
        self._on_desk_offline = None  # Callable(attempt: int) | None
        self._on_desk_online = None  # Callable | None

    def _create_socket(self):
        """Create and bind the shared UDP socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(("0.0.0.0", self.port))
        sock.settimeout(10.0)
        # Join multicast groups
        for group in (SIGMA_MULTICAST_1, SIGMA_MULTICAST_2):
            mreq = struct.pack(
                "4s4s",
                socket.inet_aton(group),
                socket.inet_aton("0.0.0.0"),
            )
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            except OSError as e:
                log.warning("Failed to join multicast group %s: %s", group, e)
        return sock

    def _recv_loop(self):
        """Receive loop running in daemon thread."""
        while self._running:
            try:
                data, addr = self._sock.recvfrom(SIGMA_BUFFER_SIZE)
                if len(data) < 0x14:  # minimum header size
                    continue

                # Quick validation before full parse
                if data[0] != SIGMA_MAGIC:
                    continue
                pt = struct.unpack_from(">I", data, 0x04)[0]
                if pt != SIGMA_PRODUCT_TYPE:
                    continue

                try:
                    rx = SigmaRxMessage(data)
                except ValueError as e:
                    log.debug("Invalid packet from %s: %s", addr, e)
                    continue

                # Dispatch to handler
                with self._lock:
                    try:
                        handled = handle_sigma_message(rx, self.state)
                    except Exception as e:
                        log.warning("Handler error for msg_id 0x%02X: %s", rx.msg_id, e)
                        handled = False
                    if handled:
                        if not self.state.console_ip:
                            self.state.console_ip = addr[0]
                        was_reconnecting = self._reconnecting
                        came_online = self.state.online and was_reconnecting

                if handled:
                    if came_online:
                        self._on_desk_came_online()
                    # Fire state-changed hook OUTSIDE the lock
                    if self._on_state_changed:
                        self._on_state_changed()
                else:
                    log.debug("Unhandled msg_id: 0x%02X (%d bytes)", rx.msg_id, len(data))

            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    log.warning("Socket error in recv loop")
                self._running = False
                break

    def _on_desk_came_online(self):
        """Called when the console transitions to online state.

        Clears reconnect guard flags and schedules a keepalive burst
        outside the recv lock.
        """
        with self._lock:
            reconnecting = self._reconnecting
            if reconnecting:
                self._reconnecting = False
                self._reconnect_attempts = 0
        if reconnecting:
            log.info("Watchdog: reconnected, scheduling keepalive")
            self._needs_resync = True
        if self._on_desk_online:
            self._on_desk_online()

    def _watchdog_loop(self):
        """Background thread: send keepalives and detect stale heartbeat."""
        while self._running:
            time.sleep(WATCHDOG_INTERVAL)

            # Handle resync request (set by _on_desk_came_online outside lock)
            if self._needs_resync:
                self._needs_resync = False
                self.send_raw(build_keepalive())
                continue

            # Send periodic keepalive
            if self.state.online:
                self.send_raw(build_keepalive())

            with self._lock:
                online = self.state.online
                age = self.state.heartbeat_age
                reconnecting = self._reconnecting
                attempts = self._reconnect_attempts

            # Give up after max attempts
            if reconnecting and attempts >= MAX_RECONNECT_ATTEMPTS:
                log.error("Watchdog: gave up reconnecting after %d attempts", attempts)
                with self._lock:
                    self._reconnecting = False
                    self._reconnect_attempts = 0
                continue

            # Trigger reconnect on stale heartbeat
            if online and age > HEARTBEAT_TIMEOUT and not reconnecting:
                log.warning(
                    "Watchdog: heartbeat stale (%.1fs > %.1fs), triggering reconnect",
                    age,
                    HEARTBEAT_TIMEOUT,
                )
                self._trigger_reconnect()

    def _trigger_reconnect(self):
        """Mark desk offline and send handshake to re-discover."""
        with self._lock:
            self._reconnecting = True
            self._reconnect_attempts += 1
            self.state.online = False
        log.warning(
            "Watchdog: reconnect attempt %d/%d",
            self._reconnect_attempts,
            MAX_RECONNECT_ATTEMPTS,
        )
        if self._on_desk_offline:
            self._on_desk_offline(self._reconnect_attempts)
        self._send_handshake()

    def _send_handshake(self):
        """Send handshake (0x9D) to multicast group on master port."""
        packet = build_handshake()
        sock = self._sock
        if sock:
            try:
                sock.sendto(packet, (SIGMA_MULTICAST_2, SIGMA_HANDSHAKE_MASTER_PORT))
            except OSError as e:
                log.error("Handshake send error: %s", e)

    def send_raw(self, data):
        """Send raw bytes through the shared socket to the console."""
        sock = self._sock
        if sock:
            try:
                sock.sendto(data, (self.console_ip, self.port))
            except OSError as e:
                log.error("Send error: %s", e)

    def send(self, data):
        """Send a pre-built message packet."""
        self.send_raw(data)

    def connect(self):
        """Create socket, start recv and watchdog threads, send handshake."""
        if self._running:
            return
        try:
            self._sock = self._create_socket()
            self._running = True
            self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self._recv_thread.start()
            self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            self._watchdog_thread.start()
            self._send_handshake()
        except BaseException:
            self._running = False
            if self._sock:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
            raise

    def wait_online(self, timeout=5):
        """Block until state.online or timeout. Returns online status."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if self.state.online:
                    return True
            time.sleep(0.1)
        return False

    def disconnect(self):
        """Stop threads and close socket."""
        self._running = False
        if self._sock:
            # Leave multicast groups
            for group in (SIGMA_MULTICAST_1, SIGMA_MULTICAST_2):
                mreq = struct.pack(
                    "4s4s",
                    socket.inet_aton(group),
                    socket.inet_aton("0.0.0.0"),
                )
                try:
                    self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
                except OSError:
                    pass
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if self._recv_thread:
            self._recv_thread.join(timeout=2)
            self._recv_thread = None
        if self._watchdog_thread:
            self._watchdog_thread.join(timeout=2)
            self._watchdog_thread = None
        with self._lock:
            self.state.online = False

    # --- Convenience methods ---

    def get_channels(self):
        """Return list of (number, name, fader, pan) for all channels."""
        with self._lock:
            return [(ch.number, ch.name, ch.fader, ch.pan) for ch in self.state.channels]

    def rename_channel(self, channel, name):
        """Set channel scribble strip name."""
        self.send(build_set_scribble(channel, name))

    def set_fader(self, channel, value):
        """Set channel fader level (0.0-1.0)."""
        self.send(build_set_fader(channel, value))

    def set_pan(self, channel, value):
        """Set channel pan position."""
        self.send(build_set_pan(channel, value))

    def set_solo(self, channel, on):
        """Set channel solo on/off."""
        self.send(build_set_solo(channel, on))

    def set_mute(self, channel, on):
        """Set channel mute on/off."""
        self.send(build_set_mute(channel, on))

    def set_phase(self, channel, on):
        """Set channel phase/polarity on/off."""
        self.send(build_set_phase(channel, on))

    def set_channel_name(self, channel, name):
        """Set channel scribble strip name (alias for rename_channel)."""
        self.rename_channel(channel, name)

    def get_monitor(self):
        """Return the current monitor state (SigmaMonitor dataclass)."""
        with self._lock:
            return self.state.monitor

    def set_monitor_source(self, source_index, on):
        """Set monitor source select (source_index 0-6)."""
        self.send(build_set_monitor_source(source_index, on))

    def set_cut(self, on):
        """Set monitor cut. Note: cut msg_id not yet confirmed in protocol."""
        log.warning("set_cut: monitor cut msg_id not confirmed in Sigma protocol")

    def set_dim(self, level):
        """Set dim level."""
        self.send(build_set_dim_level(level))

    def set_headphone_source(self, source_index, on):
        """Set headphone source select (source_index 0-3)."""
        self.send(build_set_headphone_source(source_index, on))

    def set_connection_mode(self, unicast):
        """Switch between multicast and unicast mode."""
        self.send(build_set_connection_mode(unicast))
