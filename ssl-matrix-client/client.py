"""Core SSL Matrix client: single socket on port 50081, threaded recv loop, dispatch table."""

import logging
import random
import socket
import threading
import time

from .handlers import (
    chan_presets,
    channels,
    connection,
    delta,
    profiles,
    projects,
    routing,
    softkeys,
    total_recall,
    xpatch,
)
from .models import ConsoleState
from .protocol import (
    BUFFER_SIZE,
    PORT,
    PROTOCOL_NAMES,
    TO_REMOTE,
    MessageCode,
    RxMessage,
    TxMessage,
)

log = logging.getLogger(__name__)


class SSLMatrixClient:
    """UDP client for SSL Matrix console control.

    The critical fix: both send and receive use the SAME socket bound to port 50081.
    The Java app's TxMessage creates ephemeral-port sockets for sending, but the
    console only responds to port 50081. This client uses a single shared socket.
    """

    def __init__(self, console_ip="192.168.1.2", port=PORT):
        self.console_ip = console_ip
        self.port = port
        self.my_serial = random.randint(-(2**31), 2**31 - 1)
        self.state = ConsoleState()
        self._sock = None
        self._recv_thread = None
        self._running = False
        self._lock = threading.Lock()
        self._dispatch = self._build_dispatch_table()

    def _build_dispatch_table(self):
        """Map cmdCode -> handler function(rx, state)."""
        return {
            MessageCode.GET_DESK_REPLY: connection.handle_get_desk_reply,
            MessageCode.SEND_HEARTBEAT: connection.handle_heartbeat,
            MessageCode.GET_PROJECT_NAME_AND_TITLE_REPLY: connection.handle_project_name_and_title_reply,
            # Channel names
            MessageCode.GET_CHAN_NAMES_AND_IMAGES_REPLY: channels.handle_chan_names_reply,
            MessageCode.SET_CHAN_NAMES_REPLY: channels.handle_set_chan_names_reply,
            MessageCode.SET_DEFAULT_CHAN_NAMES_REPLY: channels.handle_set_chan_names_reply,
            MessageCode.ACK_GET_DISPLAY_17_32: channels.handle_get_display_17_32_reply,
            MessageCode.ACK_GET_FLIP_SCRIB_STRIP: channels.handle_get_flip_scrib_strip_reply,
            # Profiles / DAW layers
            MessageCode.ACK_GET_DAW_LAYER_PROTOCOL: profiles.handle_daw_layer_protocol_reply,
            MessageCode.ACK_GET_PROFILE_FOR_DAW_LAYER: profiles.handle_profile_for_daw_layer_reply,
            MessageCode.ACK_GET_PROFILES: profiles.handle_profiles_reply,
            MessageCode.ACK_GET_TRANSPORT_LOCK_DAW_LAYER: profiles.handle_transport_lock_reply,
            # Delta
            MessageCode.ACK_GET_AUTOMATION_MODE: delta.handle_auto_mode_reply,
            MessageCode.ACK_GET_MOTORS_OFF_TOUCH_EN: delta.handle_motors_off_reply,
            MessageCode.ACK_GET_MDAC_METER_EN: delta.handle_mdac_meters_reply,
            # Routing — data replies
            MessageCode.ACK_GET_INSERT_INFO_V2: routing.handle_insert_names_v2_reply,
            MessageCode.ACK_GET_CHAIN_INFO_V2: routing.handle_chain_info_v2_reply,
            MessageCode.ACK_GET_CHAN_MATRIX_INFO_V2: routing.handle_chan_matrix_info_v2_reply,
            MessageCode.ACK_GET_MATRIX_PRESET_LIST: routing.handle_matrix_preset_list_reply,
            # Routing — ACK replies
            MessageCode.ACK_SET_INSERT_NAMES_V2: routing.handle_routing_ack,
            MessageCode.ACK_SET_INSERT_TO_CHAN_V2: routing.handle_routing_ack,
            MessageCode.ACK_ASSIGN_CHAIN_TO_CHAN_V2: routing.handle_routing_ack,
            MessageCode.ACK_DEASSIGN_CHAN_V2: routing.handle_routing_ack,
            MessageCode.ACK_DELETE_CHAIN_V2: routing.handle_routing_ack,
            MessageCode.ACK_RENAME_CHAIN: routing.handle_routing_ack,
            MessageCode.ACK_SAVE_INSERTS_TO_CHAIN: routing.handle_routing_ack,
            MessageCode.ACK_DELETE_CHAN_INSERT: routing.handle_routing_ack,
            MessageCode.ACK_SET_CHAN_STEREO_INSERT: routing.handle_routing_ack,
            MessageCode.ACK_LOAD_MATRIX_PRESET: routing.handle_routing_ack,
            MessageCode.ACK_SAVE_MATRIX_PRESET: routing.handle_routing_ack,
            MessageCode.ACK_DELETE_MATRIX_PRESET: routing.handle_routing_ack,
            MessageCode.ACK_RENAME_MATRIX_PRESET: routing.handle_routing_ack,
            MessageCode.ACK_CLEAR_INSERTS: routing.handle_routing_ack,
            # Projects — data replies
            MessageCode.GET_DIRECTORY_LIST_REPLY: projects.handle_directory_list_reply,
            MessageCode.SEND_DISK_INFO: projects.handle_disk_info,
            # Projects — ACK replies
            MessageCode.ACK_MAKE_NEW_PROJECT: projects.handle_projects_ack,
            MessageCode.ACK_MAKE_NEW_PROJECT_TITLE: projects.handle_projects_ack,
            MessageCode.ACK_MAKE_NEW_PROJECT_TITLE_WITH_NAME: projects.handle_projects_ack,
            MessageCode.ACK_SELECT_PROJECT_TITLE: projects.handle_projects_ack,
            MessageCode.ACK_DELETE_PROJECT_TITLE: projects.handle_projects_ack,
            MessageCode.ACK_DELETE_PROJECT: projects.handle_projects_ack,
            MessageCode.ACK_COPY_PROJECT_TITLE: projects.handle_projects_ack,
            MessageCode.ACK_MAKE_NEW_PROJECT_WITH_NAME: projects.handle_projects_ack,
            MessageCode.ACK_MAKE_NEW_PROJECT_WITH_PRESET_OPTS: projects.handle_projects_ack,
            # Total Recall
            MessageCode.ACK_SET_TR_ENABLE: total_recall.handle_tr_enable_reply,
            MessageCode.ACK_GET_TR_STATE: total_recall.handle_tr_enable_reply,
            MessageCode.GET_TR_LIST_REPLY: total_recall.handle_tr_list_reply,
            # Channel Names Presets
            MessageCode.ACK_GET_CHAN_NAMES_PRESET_LIST: chan_presets.handle_chan_names_preset_list_reply,
            MessageCode.ACK_RENAME_CHAN_NAMES_PRESET: chan_presets.handle_chan_names_preset_ack,
            MessageCode.ACK_DELETE_CHAN_NAMES_PRESET: chan_presets.handle_chan_names_preset_ack,
            MessageCode.ACK_SAVE_CHAN_NAMES_PRESET: chan_presets.handle_chan_names_preset_ack,
            MessageCode.ACK_LOAD_CHAN_NAMES_PRESET: chan_presets.handle_chan_names_preset_ack,
            # XPatch — setup
            MessageCode.GET_XPATCH_CHAN_SETUP_REPLY: xpatch.handle_chan_setup_reply,
            MessageCode.SET_XPATCH_INPUT_MINUS10DB_REPLY: xpatch.handle_input_minus_10db_reply,
            MessageCode.SET_XPATCH_OUTPUT_MINUS10DB_REPLY: xpatch.handle_output_minus_10db_reply,
            MessageCode.SET_XPATCH_CHAN_MODE_REPLY: xpatch.handle_chan_mode_reply,
            MessageCode.SET_XPATCH_DEVICE_NAME_REPLY: xpatch.handle_device_name_reply,
            MessageCode.SET_XPATCH_DEST_NAME_REPLY: xpatch.handle_dest_name_reply,
            MessageCode.GET_XPATCH_MIDI_SETUP_REPLY: xpatch.handle_midi_setup_reply,
            MessageCode.SET_XPATCH_MIDI_ENABLE_REPLY: xpatch.handle_midi_enable_reply,
            MessageCode.SET_XPATCH_MIDI_CHANNEL_REPLY: xpatch.handle_midi_channel_reply,
            # XPatch — routing
            MessageCode.GET_XPATCH_ROUTING_DATA_REPLY: xpatch.handle_routing_data_reply,
            # XPatch — presets
            MessageCode.GET_XPATCH_PRESETS_LIST_REPLY: xpatch.handle_presets_list_reply,
            MessageCode.SET_XPATCH_PRESET_SELECTED_REPLY: xpatch.handle_preset_selected_reply,
            MessageCode.GET_XPATCH_PRESET_EDITED_REPLY: xpatch.handle_preset_edited_reply,
            # XPatch — chains
            MessageCode.GET_XPATCH_CHAINS_LIST_REPLY: xpatch.handle_chains_list_reply,
            MessageCode.GET_XPATCH_EDIT_CHAIN_REPLY: xpatch.handle_edit_chain_reply,
            MessageCode.GET_XPATCH_EDIT_CHAIN_TOUCHED_REPLY: xpatch.handle_edit_chain_touched_reply,
            MessageCode.SET_XPATCH_LINK_REPLACE_MODE_REPLY: xpatch.handle_replace_mode_reply,
            # Softkeys — data replies
            MessageCode.ACK_GET_EDIT_KEYMAP_NAME: softkeys.handle_edit_keymap_name_reply,
            MessageCode.ACK_GET_EDIT_KEYMAP_DATA: softkeys.handle_edit_keymap_data_reply,
            MessageCode.ACK_GET_EDIT_KEYMAP_SIZE: softkeys.handle_edit_keymap_size_reply,
            MessageCode.ACK_GET_MIDI_FUNCTION_LIST: softkeys.handle_midi_function_list_reply,
            MessageCode.ACK_GET_FLIP_STATUS: softkeys.handle_flip_status_reply,
            MessageCode.ACK_GET_HANDSHAKING_STATUS: softkeys.handle_handshake_reply,
            MessageCode.ACK_GET_AUTO_MODE_ON_SCRIBS_STATUS: softkeys.handle_auto_mode_on_scribs_reply,
            MessageCode.ACK_GET_DEFAULT_WHEEL_MODE_STATUS: softkeys.handle_default_wheel_mode_reply,
            MessageCode.ACK_GET_FADER_DB_READOUT_STATUS: softkeys.handle_fader_db_readout_reply,
            MessageCode.ACK_GET_CC_NAMES_LIST: softkeys.handle_cc_names_list_reply,
            MessageCode.ACK_GET_PROFILE_PATH: softkeys.handle_profile_path_reply,
            # Softkeys — ACK replies
            MessageCode.ACK_SET_EDIT_KEYMAP_NAME: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_USB_CMD: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_KEYCAP_NAME: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_KEY_BLANK: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_SAVE_EDIT_KEYMAP: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_MIDI_CMD: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_NEW_MENU_CMD: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_MENU_SUB_KEYCAP_NAME: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_MENU_SUB_MIDI_CMD: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_MENU_SUB_USB_CMD: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_MENU_SUB_BLANK_CMD: softkeys.handle_softkey_ack,
            MessageCode.ACK_FOLLOW_KEY_STATE: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_FLIP_STATUS: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_HANDSHAKING_STATUS: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_AUTO_MODE_ON_SCRIBS_STATUS: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_DEFAULT_WHEEL_MODE_STATUS: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_FADER_DB_READOUT_STATUS: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_CC_NAMES_LIST: softkeys.handle_softkey_ack,
            MessageCode.ACK_COPY_PROFILE_TO_NEW: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_PROFILE_FOR_DAW_LAYER: softkeys.handle_softkey_ack,
            MessageCode.ACK_CLEAR_PROFILE_FOR_DAW_LAYER: softkeys.handle_softkey_ack,
            MessageCode.ACK_RENAME_PROFILES: softkeys.handle_softkey_ack,
            MessageCode.ACK_DELETE_PROFILES: softkeys.handle_softkey_ack,
            MessageCode.ACK_SET_TRANSPORT_LOCK_DAW_LAYER: softkeys.handle_softkey_ack,
            MessageCode.ACK_SAVE_PROFILE_AS: softkeys.handle_softkey_ack,
        }

    def _create_socket(self):
        """Create and bind the shared UDP socket on port 50081."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(("0.0.0.0", self.port))
        sock.settimeout(10.0)
        return sock

    def _recv_loop(self):
        """Receive loop running in daemon thread."""
        while self._running:
            try:
                data, addr = self._sock.recvfrom(BUFFER_SIZE)
                if len(data) < 16:
                    continue
                rx = RxMessage(data)

                # Only process TO_REMOTE messages
                if rx.dest_code != TO_REMOTE:
                    continue

                # For GET_DESK_REPLY, check remoteSerial matches
                if rx.cmd_code == MessageCode.GET_DESK_REPLY:
                    if rx.remote_serial != self.my_serial:
                        continue
                    with self._lock:
                        self.state.desk.address = addr[0]

                # For other messages, verify desk serial (if known) and remote serial
                elif self.state.desk.serial != 0:
                    if rx.desk_serial != self.state.desk.serial:
                        continue
                    if rx.remote_serial != 0 and rx.remote_serial != self.my_serial:
                        continue

                # Dispatch to handler
                handler = self._dispatch.get(rx.cmd_code)
                if handler:
                    with self._lock:
                        try:
                            handler(rx, self.state)
                        except Exception as e:
                            log.warning("Handler error for cmd %d: %s", rx.cmd_code, e)
                else:
                    log.debug("Unhandled cmd: %d (%d bytes)", rx.cmd_code, len(data))

            except socket.timeout:
                if self._running and self.state.desk.online:
                    log.debug("Socket timeout, re-sending GET_DESK")
                    self._send_get_desk()
            except OSError:
                if self._running:
                    log.warning("Socket error in recv loop")
                self._running = False
                break

    def _send_get_desk(self):
        """Send GET_DESK discovery packet."""
        packet = connection.build_get_desk(self.my_serial)
        self.send_raw(packet)

    def send_raw(self, data):
        """Send raw bytes through the shared socket."""
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
        """Create socket, start recv thread, send GET_DESK."""
        if self._running:
            return
        try:
            self._sock = self._create_socket()
            self._running = True
            self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self._recv_thread.start()
            self._send_get_desk()
        except Exception:
            self._running = False
            if self._sock:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
            raise

    def discover(self):
        """Send GET_DESK and return True if console responds."""
        self._send_get_desk()
        return self.wait_online(timeout=5)

    def wait_online(self, timeout=5):
        """Block until state.desk.online or timeout. Returns online status."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if self.state.desk.online:
                    return True
            time.sleep(0.1)
        return False

    def request_sync(self):
        """Send the full sync sequence matching MatrixRemote.requestSync().

        15 messages to fetch all console state.
        """
        with self._lock:
            if not self.state.desk.online:
                log.warning("request_sync called before desk is online")
                return
            ds = self.state.desk.serial
        ms = self.my_serial

        # Channel names
        self.send(channels.build_get_chan_names(ds, ms))
        time.sleep(0.05)

        # DAW layer protocols (1-4)
        for layer in range(1, 5):
            self.send(profiles.build_get_daw_layer_protocol(ds, ms, layer))
            time.sleep(0.05)

        # Transport lock
        self.send(profiles.build_get_transport_lock(ds, ms))
        time.sleep(0.05)

        # Profile list
        self.send(profiles.build_get_profiles(ds, ms))
        time.sleep(0.05)

        # Profile for each DAW layer
        for layer in range(1, 5):
            self.send(profiles.build_get_profile_for_daw_layer(ds, ms, layer))
            time.sleep(0.05)

        # Delta: automation mode, motors, MDAC
        self.send(delta.build_get_auto_mode(ds, ms))
        time.sleep(0.05)
        self.send(delta.build_get_motors_off(ds, ms))
        time.sleep(0.05)
        self.send(delta.build_get_mdac_meters(ds, ms))
        time.sleep(0.05)

        # Display settings
        self.send(channels.build_get_display_17_32(ds, ms))
        time.sleep(0.05)
        self.send(channels.build_get_flip_scrib_strip(ds, ms))
        time.sleep(0.05)

        # Insert matrix
        self.send(routing.build_get_insert_names_v2(ds, ms))
        time.sleep(0.05)
        self.send(routing.build_get_chain_info_v2(ds, ms))
        time.sleep(0.05)
        self.send(routing.build_get_chan_matrix_info_v2(ds, ms))
        time.sleep(0.05)
        self.send(routing.build_get_matrix_preset_list(ds, ms))
        time.sleep(0.05)

        # Projects
        self.send(projects.build_get_directory_list(ds, ms, "/projects", 1))
        time.sleep(0.05)

        # Total Recall
        self.send(total_recall.build_get_tr_state(ds, ms))
        time.sleep(0.05)
        self.send(total_recall.build_get_tr_list(ds, ms))
        time.sleep(0.05)

        # Channel Names Presets
        self.send(chan_presets.build_get_chan_names_preset_list(ds, ms))
        time.sleep(0.05)

        # XPatch
        self.send(xpatch.build_get_chan_setup(ds, ms))
        time.sleep(0.05)
        self.send(xpatch.build_get_routing_data(ds, ms))
        time.sleep(0.05)
        self.send(xpatch.build_get_presets_list(ds, ms))
        time.sleep(0.05)
        self.send(xpatch.build_get_chains_list(ds, ms))
        time.sleep(0.05)
        self.send(xpatch.build_get_midi_setup(ds, ms))

        # Allow time for replies
        time.sleep(0.5)
        with self._lock:
            self.state.synced = True

    def disconnect(self):
        """Stop recv thread and close socket."""
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if self._recv_thread:
            self._recv_thread.join(timeout=2)
            self._recv_thread = None
        with self._lock:
            self.state.desk.online = False

    # --- Convenience methods ---

    def get_channels(self):
        """Return list of (number, name) for channels with names."""
        with self._lock:
            return [(ch.number, ch.name) for ch in self.state.channels if ch.name]

    def rename_channel(self, channel, name):
        """Set a channel name (max 6 chars)."""
        ds = self.state.desk.serial
        self.send(channels.build_set_chan_name(ds, self.my_serial, channel, name[:6]))

    def get_daw_layers(self):
        """Return list of (layer_num, protocol_name, profile_name)."""
        with self._lock:
            return [
                (dl.number, PROTOCOL_NAMES.get(dl.protocol, "?"), dl.profile_name)
                for dl in self.state.daw_layers
            ]

    def set_protocol_for_layer(self, layer, profile_name):
        """Set profile for a DAW layer."""
        ds = self.state.desk.serial
        self.send(profiles.build_set_profile_for_daw_layer(ds, self.my_serial, layer, profile_name))

    def clear_layer(self, layer):
        """Clear profile from a DAW layer."""
        ds = self.state.desk.serial
        self.send(profiles.build_clear_profile_for_daw_layer(ds, self.my_serial, layer))

    def get_profiles(self):
        """Return list of ProfileItem."""
        with self._lock:
            return list(self.state.profiles)

    def set_auto_mode(self, mode):
        """Set automation mode (0=Legacy, 1=Delta)."""
        ds = self.state.desk.serial
        self.send(delta.build_set_auto_mode(ds, self.my_serial, mode))

    def set_motors_off(self, enable):
        """Set motors off (0=off, 1=on)."""
        ds = self.state.desk.serial
        self.send(delta.build_set_motors_off(ds, self.my_serial, enable))

    def set_mdac_meters(self, enable):
        """Set MDAC meters (0=off, 1=on)."""
        ds = self.state.desk.serial
        self.send(delta.build_set_mdac_meters(ds, self.my_serial, enable))

    def restart_console(self):
        """Send restart command to console via ephemeral socket.

        The Java MatrixRemote app creates a new socket (ephemeral source port)
        for every outgoing packet.  Most commands work fine from our shared
        port-50081 socket, but the board firmware's restart handler appears to
        behave differently when the packet arrives from source port 50081 vs an
        ephemeral port — the board freezes instead of rebooting.

        Mirroring Java's TxMessage.tx(): open a fresh socket with port=0,
        send the single restart packet, then close it immediately.
        """
        ds = self.state.desk.serial
        packet = delta.build_restart_console(ds, self.my_serial)
        ephemeral = None
        try:
            ephemeral = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ephemeral.bind(("0.0.0.0", 0))  # OS assigns ephemeral source port
            ephemeral.sendto(packet, (self.console_ip, self.port))
        except OSError as e:
            log.error("Restart send error: %s", e)
        finally:
            if ephemeral:
                try:
                    ephemeral.close()
                except OSError:
                    pass

    # --- Routing convenience methods ---

    def get_devices(self):
        """Return list of InsertDevice."""
        with self._lock:
            return list(self.state.devices)

    def get_chains(self):
        """Return list of Chain."""
        with self._lock:
            return list(self.state.chains)

    def get_channel_inserts(self):
        """Return list of ChannelInserts."""
        with self._lock:
            return list(self.state.channel_inserts)

    def assign_device_to_channel(self, chan, device, slot):
        """Assign an insert device to a channel slot."""
        ds = self.state.desk.serial
        self.send(routing.build_set_insert_to_chan_v2(ds, self.my_serial, chan, device, slot))

    def assign_chain_to_channel(self, chan, chain_name):
        """Assign a chain to a channel."""
        ds = self.state.desk.serial
        self.send(routing.build_assign_chain_to_chan(ds, self.my_serial, chan, chain_name))

    def deassign_channel(self, chan):
        """Remove all inserts from a channel."""
        ds = self.state.desk.serial
        self.send(routing.build_deassign_chan(ds, self.my_serial, chan))

    def get_matrix_presets(self):
        """Return list of MatrixPreset."""
        with self._lock:
            return list(self.state.matrix_presets)

    def load_matrix_preset(self, name):
        """Load a matrix preset by name."""
        ds = self.state.desk.serial
        self.send(routing.build_load_matrix_preset(ds, self.my_serial, name))

    def save_matrix_preset(self, name):
        """Save current matrix routing as a preset."""
        ds = self.state.desk.serial
        self.send(routing.build_save_matrix_preset(ds, self.my_serial, name))

    # --- Projects convenience methods ---

    def get_project_info(self):
        """Return (project_name, title_name)."""
        with self._lock:
            return self.state.project_name, self.state.title_name

    def list_directory(self, path="/projects", mode=1):
        """Request a directory listing from the console."""
        ds = self.state.desk.serial
        self.send(projects.build_get_directory_list(ds, self.my_serial, path, mode))

    def select_title(self, project, title):
        """Select a project title on the console."""
        ds = self.state.desk.serial
        self.send(projects.build_select_title(ds, self.my_serial, project, title))

    def new_project(self, name):
        """Create a new project with the given name."""
        ds = self.state.desk.serial
        self.send(projects.build_make_new_project_with_name(ds, self.my_serial, name))

    def new_title(self, project, title):
        """Create a new title in a project."""
        ds = self.state.desk.serial
        self.send(projects.build_make_new_title_with_name(ds, self.my_serial, project, title))

    def delete_project(self, name):
        """Delete a project."""
        ds = self.state.desk.serial
        self.send(projects.build_delete_project(ds, self.my_serial, name))

    def delete_title(self, project, title):
        """Delete a title from a project."""
        ds = self.state.desk.serial
        self.send(projects.build_delete_project_title(ds, self.my_serial, project, title))

    # --- Total Recall convenience methods ---

    def get_tr_snapshots(self):
        with self._lock:
            return list(self.state.tr_snapshots)

    def take_tr_snapshot(self):
        ds = self.state.desk.serial
        self.send(total_recall.build_take_tr_snap(ds, self.my_serial))

    def select_tr_snapshot(self, index):
        ds = self.state.desk.serial
        self.send(total_recall.build_select_tr_snap(ds, self.my_serial, index))

    def delete_tr_snapshot(self, index):
        ds = self.state.desk.serial
        self.send(total_recall.build_delete_tr_snap(ds, self.my_serial, index))

    def set_tr_enable(self, on):
        ds = self.state.desk.serial
        self.send(total_recall.build_set_tr_enable(ds, self.my_serial, on))

    # --- Channel Names Presets convenience methods ---

    def get_chan_names_presets(self):
        with self._lock:
            return list(self.state.chan_names_presets)

    def save_chan_names_preset(self, name):
        ds = self.state.desk.serial
        self.send(chan_presets.build_save_chan_names_preset(ds, self.my_serial, name))

    def load_chan_names_preset(self, name):
        ds = self.state.desk.serial
        self.send(chan_presets.build_load_chan_names_preset(ds, self.my_serial, name))

    def delete_chan_names_preset(self, name):
        ds = self.state.desk.serial
        self.send(chan_presets.build_delete_chan_names_preset(ds, self.my_serial, name))

    # --- XPatch convenience methods ---

    def get_xpatch_routes(self):
        with self._lock:
            return list(self.state.xpatch.routes)

    def set_xpatch_route(self, dest, src):
        ds = self.state.desk.serial
        self.send(xpatch.build_set_route(ds, self.my_serial, dest, src))

    def get_xpatch_presets(self):
        with self._lock:
            return list(self.state.xpatch.presets)

    def select_xpatch_preset(self, index):
        ds = self.state.desk.serial
        self.send(xpatch.build_set_preset_selected(ds, self.my_serial, index))

    def get_xpatch_channels(self):
        with self._lock:
            return list(self.state.xpatch.channels)

    # --- Softkeys convenience methods ---

    def get_softkeys(self):
        with self._lock:
            return list(self.state.softkeys.keys)

    def send_custom(self, cmd_code, payload_hex=""):
        """Send a raw message with arbitrary cmd code and hex payload."""
        msg = TxMessage(cmd_code, self.state.desk.serial, self.my_serial)
        if payload_hex:
            payload = bytes.fromhex(payload_hex)
            for b in payload:
                msg.write_byte(b)
        self.send(msg.to_bytes())
