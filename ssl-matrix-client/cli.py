#!/usr/bin/env python3
"""CLI interface for SSL Matrix console control.

Interactive REPL (cmd.Cmd) and one-shot mode (argparse).

Usage:
    python3 -m ssl-matrix-client                  # interactive REPL
    python3 -m ssl-matrix-client channels          # one-shot: list channels
    python3 -m ssl-matrix-client --ip 10.0.0.5 layers  # custom IP
"""

import argparse
import cmd
import json
import logging
import sys
import time

from .client import SSLMatrixClient
from .protocol import PORT, PROTOCOL_NAMES


class SSLMatrixCLI(cmd.Cmd):
    """Interactive CLI for SSL Matrix console."""

    prompt = "ssl> "
    intro = "SSL Matrix Client. Type 'help' for commands, 'connect' to start."

    def __init__(self, ip="192.168.1.2", port=PORT):
        super().__init__()
        self.client = SSLMatrixClient(console_ip=ip, port=port)
        self._connected = False

    def _require_connected(self):
        if not self._connected or not self.client.state.desk.online:
            print("Not connected. Run 'connect' first.")
            return False
        return True

    # --- Connection ---

    def do_connect(self, arg):
        """Connect to the console and sync state."""
        if self._connected:
            print("Already connected.")
            return
        print(f"Connecting to {self.client.console_ip}:{self.client.port}...")
        self.client.connect()
        if self.client.wait_online(timeout=5):
            d = self.client.state.desk
            print(f"Connected to {d.product_name} '{d.console_name}'")
            print(f"  Firmware: {d.firmware}")
            print(f"  Serial:   {d.serial}")
            print(f"  Built:    {d.built_str} {d.time_str}")
            print("Syncing state...")
            try:
                self.client.request_sync()
                self._connected = True
                print("Sync complete.")
            except Exception as e:
                print(f"Sync failed: {e}")
                self.client.disconnect()
        else:
            print("Connection timeout. Is the console on and reachable?")
            self.client.disconnect()

    def do_disconnect(self, arg):
        """Disconnect from the console."""
        if not self._connected:
            print("Not connected.")
            return
        self.client.disconnect()
        self._connected = False
        print("Disconnected.")

    def do_status(self, arg):
        """Show console status."""
        if not self._connected:
            print("Not connected.")
            return
        with self.client._lock:
            d = self.client.state.desk
            product = d.product_name
            name = d.console_name
            fw = d.firmware
            serial = d.serial
            addr = d.address
            online = d.online
            hb_age = d.heartbeat_age
            proj = self.client.state.project_name
            title = self.client.state.title_name
        print(f"Console:    {product} '{name}'")
        print(f"Firmware:   {fw}")
        print(f"Serial:     {serial}")
        print(f"Address:    {addr}")
        print(f"Online:     {online}")
        if hb_age == float("inf"):
            print("Heartbeat:  never")
        else:
            print(f"Heartbeat:  {hb_age:.1f}s ago")
        if proj:
            print(f"Project:    {proj}")
        if title:
            print(f"Title:      {title}")

    # --- Channels ---

    def do_channels(self, arg):
        """List all channel names."""
        if not self._require_connected():
            return
        chans = self.client.get_channels()
        if not chans:
            print("No channel names received.")
            return
        for num, name in chans:
            print(f"  {num:2d}: {name}")

    def do_rename(self, arg):
        """Rename a channel. Usage: rename <channel> <name>"""
        if not self._require_connected():
            return
        parts = arg.split(None, 1)
        if len(parts) < 2:
            print("Usage: rename <channel_number> <name>")
            return
        try:
            ch = int(parts[0])
        except ValueError:
            print("Channel must be a number.")
            return
        raw_name = parts[1]
        name = raw_name[:6]
        if len(raw_name) > 6:
            print(f"Warning: name truncated to 6 chars: '{raw_name}' -> '{name}'")
        self.client.rename_channel(ch, name)
        print(f"Channel {ch} -> '{name}'")

    # --- Profiles ---

    def do_profiles(self, arg):
        """List all profiles on the console."""
        if not self._require_connected():
            return
        profs = self.client.get_profiles()
        if not profs:
            print("No profiles received.")
            return
        print(f"{'Name':32s} {'Protocol':8s} {'RO':4s} {'InUse':5s}")
        print("-" * 52)
        for p in profs:
            proto = PROTOCOL_NAMES.get(p.protocol, "?")
            ro = "yes" if p.read_only else ""
            iu = "yes" if p.in_use else ""
            print(f"{p.name:32s} {proto:8s} {ro:4s} {iu:5s}")

    def do_layers(self, arg):
        """Show DAW layer protocols."""
        if not self._require_connected():
            return
        layers = self.client.get_daw_layers()
        print(f"{'Layer':6s} {'Protocol':8s} {'Profile':32s}")
        print("-" * 48)
        for num, proto, profile in layers:
            print(f"  {num:4d} {proto:8s} {profile}")
        tl = self.client.state.transport_lock_layer
        print(f"\nTransport lock: Layer {tl}" if tl else "\nTransport lock: None")

    def do_setprofile(self, arg):
        """Set profile for a DAW layer. Usage: setprofile <layer> <profile_name>"""
        if not self._require_connected():
            return
        parts = arg.split(None, 1)
        if len(parts) < 2:
            print("Usage: setprofile <layer_1-4> <profile_name>")
            return
        try:
            layer = int(parts[0])
        except ValueError:
            print("Layer must be 1-4.")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        profile_name = parts[1]
        self.client.set_protocol_for_layer(layer, profile_name)
        print(f"Layer {layer} -> profile '{profile_name}'")
        print("Note: a console restart may be required for protocol changes.")

    def do_clearlayer(self, arg):
        """Clear profile from a DAW layer. Usage: clearlayer <layer>"""
        if not self._require_connected():
            return
        try:
            layer = int(arg.strip())
        except ValueError:
            print("Usage: clearlayer <layer_1-4>")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        self.client.clear_layer(layer)
        print(f"Layer {layer} cleared.")

    def do_transportlock(self, arg):
        """Set transport lock layer. Usage: transportlock <0-4> (0=none)"""
        if not self._require_connected():
            return
        if not arg.strip():
            tl = self.client.state.transport_lock_layer
            print(f"Transport lock: Layer {tl}" if tl else "Transport lock: None")
            return
        try:
            layer = int(arg.strip())
        except ValueError:
            print("Usage: transportlock <0-4>")
            return
        if not 0 <= layer <= 4:
            print("Layer must be 0-4 (0=none).")
            return
        from .handlers.profiles import build_set_transport_lock

        self.client.send(
            build_set_transport_lock(self.client.state.desk.serial, self.client.my_serial, layer)
        )
        print(f"Transport lock -> Layer {layer}" if layer else "Transport lock cleared.")

    # --- Delta ---

    def do_automode(self, arg):
        """Get or set automation mode. Usage: automode [legacy|delta]"""
        if not self._require_connected():
            return
        if not arg.strip():
            mode = self.client.state.automation_mode
            print(f"Automation mode: {'Delta' if mode else 'Legacy'}")
            return
        val = arg.strip().lower()
        if val == "legacy":
            self.client.set_auto_mode(0)
            print("Set to Legacy mode. Restart console to apply.")
        elif val == "delta":
            self.client.set_auto_mode(1)
            print("Set to Delta mode. Restart console to apply.")
        else:
            print("Usage: automode [legacy|delta]")

    def do_motors(self, arg):
        """Get or set motors. Usage: motors [on|off]"""
        if not self._require_connected():
            return
        if not arg.strip():
            m = self.client.state.motors_off
            print(f"Motors: {'off' if m else 'on'}")
            return
        val = arg.strip().lower()
        if val == "on":
            self.client.set_motors_off(0)  # motors_off=0 means motors enabled
        elif val == "off":
            self.client.set_motors_off(1)  # motors_off=1 means motors disabled
        else:
            print("Usage: motors [on|off]")

    def do_mdac(self, arg):
        """Get or set MDAC meters. Usage: mdac [on|off]"""
        if not self._require_connected():
            return
        if not arg.strip():
            m = self.client.state.mdac_meters
            print(f"MDAC meters: {'on' if m else 'off'}")
            return
        val = arg.strip().lower()
        if val == "on":
            self.client.set_mdac_meters(1)
        elif val == "off":
            self.client.set_mdac_meters(0)
        else:
            print("Usage: mdac [on|off]")

    def do_restart(self, arg):
        """Restart the console (required after automation mode change)."""
        if not self._require_connected():
            return
        confirm = input("Restart console? [y/N] ")
        if confirm.lower() == "y":
            self.client.restart_console()
            self._connected = False
            with self.client._lock:
                self.client.state.desk.online = False
            print("Restart command sent. Console is rebooting.")
            print("Run 'connect' again once the board is back online (usually 10-20s).")
        else:
            print("Cancelled.")

    # --- Routing ---

    def do_devices(self, arg):
        """List all 16 insert devices with name/assigned/stereo status."""
        if not self._require_connected():
            return
        devices = self.client.get_devices()
        print(f"{'#':>3s}  {'Name':16s} {'Assigned':8s} {'Stereo':6s}")
        print("-" * 36)
        for d in devices:
            assigned = "yes" if d.is_assigned else ""
            stereo = "yes" if d.is_stereo else ""
            print(f"{d.number:3d}  {d.name:16s} {assigned:8s} {stereo:6s}")

    def do_chains(self, arg):
        """List all chains with their elements."""
        if not self._require_connected():
            return
        chains = self.client.get_chains()
        if not chains:
            print("No chains defined.")
            return
        for c in chains:
            assigned = " [assigned]" if c.is_assigned else ""
            print(f"  {c.number}: {c.name}{assigned}")
            for idx, name in c.elements:
                print(f"       [{idx}] {name}")

    def do_matrix(self, arg):
        """Show channel insert routing grid."""
        if not self._require_connected():
            return
        inserts = self.client.get_channel_inserts()
        if not inserts:
            print("No channel insert data.")
            return
        for ci in inserts:
            chain = f" (chain: {ci.chain_name})" if ci.chain_name else ""
            stereo = " [stereo]" if ci.has_stereo else ""
            devs = ", ".join(str(i) for i in ci.inserts) if ci.inserts else "none"
            print(f"  Ch {ci.channel:2d}: {devs}{chain}{stereo}")

    def do_assign(self, arg):
        """Assign insert to channel. Usage: assign <chan> <device> <slot> | assign <chan> chain <name>"""
        if not self._require_connected():
            return
        parts = arg.split()
        if len(parts) < 2:
            print("Usage: assign <chan> <device> <slot>")
            print("       assign <chan> chain <chain_name>")
            return
        try:
            chan = int(parts[0])
        except ValueError:
            print("Channel must be a number.")
            return
        if parts[1].lower() == "chain":
            if len(parts) < 3:
                print("Usage: assign <chan> chain <chain_name>")
                return
            chain_name = " ".join(parts[2:])
            self.client.assign_chain_to_channel(chan, chain_name)
            print(f"Chain '{chain_name}' -> channel {chan}")
        else:
            if len(parts) < 3:
                print("Usage: assign <chan> <device> <slot>")
                return
            try:
                device = int(parts[1])
                slot = int(parts[2])
            except ValueError:
                print("Device and slot must be numbers.")
                return
            self.client.assign_device_to_channel(chan, device, slot)
            print(f"Device {device} -> channel {chan} slot {slot}")

    def do_deassign(self, arg):
        """Remove all inserts from a channel. Usage: deassign <chan>"""
        if not self._require_connected():
            return
        try:
            chan = int(arg.strip())
        except ValueError:
            print("Usage: deassign <channel_number>")
            return
        self.client.deassign_channel(chan)
        print(f"Channel {chan} deassigned.")

    def do_stereo(self, arg):
        """Link or unlink a stereo insert pair. Usage: stereo <chan1> <chan2> [off]"""
        if not self._require_connected():
            return
        parts = arg.split()
        if len(parts) < 2:
            print("Usage: stereo <chan1> <chan2>       (link)")
            print("       stereo <chan1> <chan2> off   (unlink)")
            return
        try:
            first = int(parts[0])
            second = int(parts[1])
        except ValueError:
            print("Channel numbers must be integers.")
            return
        stereo = not (len(parts) >= 3 and parts[2].lower() == "off")
        self.client.set_stereo_insert(first, second, stereo)
        action = "Linked" if stereo else "Unlinked"
        print(f"{action} stereo pair: channels {first} + {second}")

    def do_matrix_presets(self, arg):
        """List matrix routing presets."""
        if not self._require_connected():
            return
        presets = self.client.get_matrix_presets()
        if not presets:
            print("No matrix presets.")
            return
        for p in presets:
            print(f"  {p.name}")

    def do_load_preset(self, arg):
        """Load a matrix preset. Usage: load_preset <name>"""
        if not self._require_connected():
            return
        name = arg.strip()
        if not name:
            print("Usage: load_preset <name>")
            return
        self.client.load_matrix_preset(name)
        print(f"Loading preset '{name}'...")

    def do_save_preset(self, arg):
        """Save current matrix as a preset. Usage: save_preset <name>"""
        if not self._require_connected():
            return
        name = arg.strip()
        if not name:
            print("Usage: save_preset <name>")
            return
        self.client.save_matrix_preset(name)
        print(f"Saved preset '{name}'.")

    # --- Projects ---

    def do_project_info(self, arg):
        """Show current project and title."""
        if not self._require_connected():
            return
        proj, title = self.client.get_project_info()
        print(f"Project: {proj or '(none)'}")
        print(f"Title:   {title or '(none)'}")

    def do_projects(self, arg):
        """List projects on the console."""
        if not self._require_connected():
            return
        self.client.list_directory("/projects", 1)
        time.sleep(0.5)
        with self.client._lock:
            entries = list(self.client.state.directory)
        if not entries:
            print("No projects found.")
            return
        for e in entries:
            kind = "DIR " if e.is_dir else "FILE"
            print(f"  {kind} {e.name:24s} {e.date_str} {e.time_str}")

    def do_select_title(self, arg):
        """Select a project title. Usage: select_title <project> <title>"""
        if not self._require_connected():
            return
        parts = arg.split(None, 1)
        if len(parts) < 2:
            print("Usage: select_title <project> <title>")
            return
        self.client.select_title(parts[0], parts[1])
        print(f"Selecting '{parts[0]}' / '{parts[1]}'...")

    def do_new_project(self, arg):
        """Create a new project. Usage: new_project <name>"""
        if not self._require_connected():
            return
        name = arg.strip()
        if not name:
            print("Usage: new_project <name>")
            return
        self.client.new_project(name)
        print(f"Creating project '{name}'...")

    def do_new_title(self, arg):
        """Create a new title. Usage: new_title <project> <title>"""
        if not self._require_connected():
            return
        parts = arg.split(None, 1)
        if len(parts) < 2:
            print("Usage: new_title <project> <title>")
            return
        self.client.new_title(parts[0], parts[1])
        print(f"Creating title '{parts[1]}' in '{parts[0]}'...")

    def do_delete_project(self, arg):
        """Delete a project. Usage: delete_project <name>"""
        if not self._require_connected():
            return
        name = arg.strip()
        if not name:
            print("Usage: delete_project <name>")
            return
        confirm = input(f"Delete project '{name}'? [y/N] ")
        if confirm.lower() == "y":
            self.client.delete_project(name)
            print(f"Deleting project '{name}'...")
        else:
            print("Cancelled.")

    def do_delete_title(self, arg):
        """Delete a title. Usage: delete_title <project> <title>"""
        if not self._require_connected():
            return
        parts = arg.split(None, 1)
        if len(parts) < 2:
            print("Usage: delete_title <project> <title>")
            return
        confirm = input(f"Delete '{parts[0]}' / '{parts[1]}'? [y/N] ")
        if confirm.lower() == "y":
            self.client.delete_title(parts[0], parts[1])
            print(f"Deleting title '{parts[1]}' from '{parts[0]}'...")
        else:
            print("Cancelled.")

    # --- Total Recall ---

    def do_tr_snapshots(self, arg):
        """List Total Recall snapshots."""
        if not self._require_connected():
            return
        snaps = self.client.get_tr_snapshots()
        if not snaps:
            print("No TR snapshots.")
            return
        tr_en = "enabled" if self.client.state.tr_enabled else "disabled"
        print(f"Total Recall: {tr_en}")
        for i, s in enumerate(snaps):
            sel = " *" if s.is_selected else ""
            print(f"  {i:3d}: {s.name:24s} {s.date_str} {s.time_str}{sel}")

    def do_tr_take(self, arg):
        """Take a new TR snapshot."""
        if not self._require_connected():
            return
        self.client.take_tr_snapshot()
        print("Snapshot taken.")

    def do_tr_select(self, arg):
        """Select a TR snapshot. Usage: tr_select <index>"""
        if not self._require_connected():
            return
        try:
            idx = int(arg.strip())
        except ValueError:
            print("Usage: tr_select <index>")
            return
        self.client.select_tr_snapshot(idx)
        print(f"Selected snapshot {idx}.")

    def do_tr_delete(self, arg):
        """Delete a TR snapshot. Usage: tr_delete <index>"""
        if not self._require_connected():
            return
        try:
            idx = int(arg.strip())
        except ValueError:
            print("Usage: tr_delete <index>")
            return
        confirm = input(f"Delete TR snapshot {idx}? [y/N] ")
        if confirm.lower() == "y":
            self.client.delete_tr_snapshot(idx)
            print(f"Deleted snapshot {idx}.")
        else:
            print("Cancelled.")

    def do_tr_enable(self, arg):
        """Enable/disable Total Recall. Usage: tr_enable [on|off]"""
        if not self._require_connected():
            return
        if not arg.strip():
            print(f"TR: {'enabled' if self.client.state.tr_enabled else 'disabled'}")
            return
        val = arg.strip().lower()
        if val == "on":
            self.client.set_tr_enable(True)
        elif val == "off":
            self.client.set_tr_enable(False)
        else:
            print("Usage: tr_enable [on|off]")

    # --- Channel Names Presets ---

    def do_chan_presets(self, arg):
        """List channel names presets."""
        if not self._require_connected():
            return
        presets = self.client.get_chan_names_presets()
        if not presets:
            print("No channel names presets.")
            return
        for p in presets:
            print(f"  {p.name}")

    def do_save_chan_preset(self, arg):
        """Save current channel names as preset. Usage: save_chan_preset <name>"""
        if not self._require_connected():
            return
        name = arg.strip()
        if not name:
            print("Usage: save_chan_preset <name>")
            return
        self.client.save_chan_names_preset(name)
        print(f"Saved channel names preset '{name}'.")

    def do_load_chan_preset(self, arg):
        """Load a channel names preset. Usage: load_chan_preset <name>"""
        if not self._require_connected():
            return
        name = arg.strip()
        if not name:
            print("Usage: load_chan_preset <name>")
            return
        self.client.load_chan_names_preset(name)
        print(f"Loading channel names preset '{name}'...")

    # --- XPatch ---

    def do_xpatch_setup(self, arg):
        """Show XPatch channel setup (device/dest names, levels, mode)."""
        if not self._require_connected():
            return
        chans = self.client.get_xpatch_channels()
        print(f"{'Ch':>3s}  {'Device':16s} {'Dest':16s} {'In-10':5s} {'Out-10':6s} {'Mode':4s}")
        print("-" * 54)
        for c in chans:
            i10 = "yes" if c.input_minus_10db else ""
            o10 = "yes" if c.output_minus_10db else ""
            print(
                f"{c.number:3d}  {c.device_name:16s} {c.dest_name:16s} {i10:5s} {o10:6s} {c.mode:4d}"
            )

    def do_xpatch_routes(self, arg):
        """Show XPatch routing grid."""
        if not self._require_connected():
            return
        routes = self.client.get_xpatch_routes()
        if not routes:
            print("No XPatch routing data.")
            return
        for r in routes:
            prot = " [protected]" if r.protect else ""
            print(f"  Dest {r.dest:2d} <- Src {r.display_src}{prot}")

    def do_xpatch_route(self, arg):
        """Set an XPatch route. Usage: xpatch_route <dest> <src>"""
        if not self._require_connected():
            return
        parts = arg.split()
        if len(parts) < 2:
            print("Usage: xpatch_route <dest> <src>")
            return
        try:
            dest, src = int(parts[0]), int(parts[1])
        except ValueError:
            print("Dest and src must be numbers.")
            return
        self.client.set_xpatch_route(dest, src)
        print(f"Route: dest {dest} <- src {src}")

    def do_xpatch_presets(self, arg):
        """List XPatch presets."""
        if not self._require_connected():
            return
        presets = self.client.get_xpatch_presets()
        if not presets:
            print("No XPatch presets.")
            return
        sel = self.client.state.xpatch.selected_preset
        for p in presets:
            used = "" if p.used else " (empty)"
            marker = " *" if p.index == sel else ""
            print(f"  {p.index:3d}: {p.name}{used}{marker}")

    def do_xpatch_select(self, arg):
        """Select an XPatch preset. Usage: xpatch_select <index>"""
        if not self._require_connected():
            return
        try:
            idx = int(arg.strip())
        except ValueError:
            print("Usage: xpatch_select <index>")
            return
        self.client.select_xpatch_preset(idx)
        print(f"Selected XPatch preset {idx}.")

    # --- V-pot / CC ---

    def do_wheel_mode(self, arg):
        """Get or set V-pot wheel mode. Usage: wheel_mode <layer> [mode]"""
        if not self._require_connected():
            return
        parts = arg.split()
        if not parts:
            print("Usage: wheel_mode <layer_1-4> [mode_0-5]")
            return
        try:
            layer = int(parts[0])
        except ValueError:
            print("Layer must be a number 1-4.")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        if len(parts) == 1:
            # Read mode
            from .handlers.softkeys import build_get_default_wheel_mode

            self.client.send(
                build_get_default_wheel_mode(
                    self.client.state.desk.serial, self.client.my_serial, layer
                )
            )
            time.sleep(0.3)
            with self.client._lock:
                mode = self.client.state.softkeys.default_wheel_mode
            mode_names = {0: "Pan", 1: "Linear", 2: "Boost/Cut", 3: "Off"}
            label = mode_names.get(mode, f"Unknown ({mode})")
            print(f"Layer {layer} wheel mode: {label} ({mode})")
        else:
            try:
                mode = int(parts[1])
            except ValueError:
                print("Mode must be a number 0-5.")
                return
            if not 0 <= mode <= 5:
                print("Mode must be 0-5.")
                return
            from .handlers.softkeys import build_set_default_wheel_mode

            self.client.send(
                build_set_default_wheel_mode(
                    self.client.state.desk.serial, self.client.my_serial, layer, mode
                )
            )
            print(f"Layer {layer} wheel mode set to {mode}.")

    def do_cc_names(self, arg):
        """Show CC parameter names. Usage: cc_names <layer> <type>"""
        if not self._require_connected():
            return
        parts = arg.split()
        if len(parts) < 2:
            print("Usage: cc_names <layer_1-4> <type_0-3>")
            return
        try:
            layer = int(parts[0])
            cc_type = int(parts[1])
        except ValueError:
            print("Layer and type must be numbers.")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        if not 0 <= cc_type <= 3:
            print("Type must be 0-3.")
            return
        from .handlers.softkeys import build_get_cc_names_list

        self.client.send(
            build_get_cc_names_list(
                self.client.state.desk.serial, self.client.my_serial, layer, cc_type
            )
        )
        time.sleep(0.3)
        with self.client._lock:
            names = list(self.client.state.softkeys.cc_names)
        if not names:
            print("No CC names configured.")
            return
        for i, name in enumerate(names):
            print(f"  {i:3d}: {name}")

    def do_cc_names_set(self, arg):
        """Set CC parameter names. Usage: cc_names_set <layer> <type> <name1> [name2...]"""
        if not self._require_connected():
            return
        parts = arg.split()
        if len(parts) < 3:
            print("Usage: cc_names_set <layer_1-4> <type_0-3> <name1> [name2...]")
            return
        try:
            layer = int(parts[0])
            cc_type = int(parts[1])
        except ValueError:
            print("Layer and type must be numbers.")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        if not 0 <= cc_type <= 3:
            print("Type must be 0-3.")
            return
        names = parts[2:]
        from .handlers.softkeys import build_set_cc_names_list

        self.client.send(
            build_set_cc_names_list(
                self.client.state.desk.serial, self.client.my_serial, layer, cc_type, names
            )
        )
        print(f"CC names set for layer {layer} type {cc_type}: {names}")

    # --- Soft Keys ---

    def do_softkey_keymap(self, arg):
        """Show current keymap name for a layer. Usage: softkey_keymap <layer>"""
        if not self._require_connected():
            return
        try:
            layer = int(arg.strip())
        except ValueError:
            print("Usage: softkey_keymap <layer_1-4>")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        from .handlers.softkeys import build_get_edit_keymap_name

        self.client.send(
            build_get_edit_keymap_name(self.client.state.desk.serial, self.client.my_serial, layer)
        )
        time.sleep(0.3)
        with self.client._lock:
            name = self.client.state.softkeys.keymap_name
        if name == "NONE" or not name:
            print(f"Layer {layer}: NONE (no keymap configured)")
        else:
            print(f"Layer {layer}: {name}")

    def do_softkey_edit(self, arg):
        """Open a keymap edit session. Usage: softkey_edit <layer> <name>"""
        if not self._require_connected():
            return
        parts = arg.split(None, 1)
        if len(parts) < 2:
            print("Usage: softkey_edit <layer_1-4> <name>")
            print("Valid names: keymap1, keymap2, keymap3, keymap4")
            return
        try:
            layer = int(parts[0])
        except ValueError:
            print("Layer must be 1-4.")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        name = parts[1].strip()
        if name not in ("keymap1", "keymap2", "keymap3", "keymap4"):
            print("Name must be one of: keymap1, keymap2, keymap3, keymap4")
            return
        from .handlers.softkeys import (
            build_get_edit_keymap_data,
            build_get_edit_keymap_size,
            build_set_edit_keymap_name,
        )

        self.client.send(
            build_set_edit_keymap_name(
                self.client.state.desk.serial, self.client.my_serial, layer, name
            )
        )
        time.sleep(0.5)
        self.client.send(
            build_get_edit_keymap_size(self.client.state.desk.serial, self.client.my_serial)
        )
        time.sleep(0.3)
        self.client.send(
            build_get_edit_keymap_data(
                self.client.state.desk.serial, self.client.my_serial, 1, 1, 0
            )
        )
        time.sleep(0.5)
        with self.client._lock:
            keys = list(self.client.state.softkeys.keys)
            in_edit = self.client.state.softkeys.in_edit
        if not in_edit:
            print(f"Edit session for '{name}' opened (no keys loaded yet).")
            return
        type_names = {0: "blank", 1: "midi", 2: "usb", 3: "menu"}
        print(f"{'Idx':>4s} {'Row':>3s} {'Type':6s} {'Keycap':12s} {'Data'}")
        print("-" * 60)
        for k in keys:
            t = type_names.get(k.key_type, str(k.key_type))
            print(f"{k.index:4d} {k.is_top_row:3d} {t:6s} {k.keycap_name:12s} {k.data}")

    def do_softkey_list(self, arg):
        """Show all key assignments from current edit session."""
        if not self._require_connected():
            return
        with self.client._lock:
            in_edit = self.client.state.softkeys.in_edit
            keys = list(self.client.state.softkeys.keys)
        if not in_edit:
            print("No edit session open. Use 'softkey_edit' first.")
            return
        type_names = {0: "blank", 1: "midi", 2: "usb", 3: "menu"}
        print(f"{'Idx':>4s} {'Row':>3s} {'Type':6s} {'Keycap':12s} {'Data'}")
        print("-" * 60)
        for k in keys:
            t = type_names.get(k.key_type, str(k.key_type))
            print(f"{k.index:4d} {k.is_top_row:3d} {t:6s} {k.keycap_name:12s} {k.data}")

    def do_softkey_usb(self, arg):
        """Assign USB command to a key. Usage: softkey_usb <layer> <key> <row> <cmd>"""
        if not self._require_connected():
            return
        parts = arg.split(None, 3)
        if len(parts) < 4:
            print("Usage: softkey_usb <layer_1-4> <key> <row_0-1> <cmd>")
            return
        try:
            layer = int(parts[0])
            key = int(parts[1])
            row = int(parts[2])
        except ValueError:
            print("layer, key, and row must be numbers.")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        usb_cmd = parts[3]
        from .handlers.softkeys import build_set_usb_cmd

        self.client.send(
            build_set_usb_cmd(
                self.client.state.desk.serial, self.client.my_serial, layer, key, row, usb_cmd
            )
        )
        print(f"Key {key} row {row} layer {layer} -> USB '{usb_cmd}'")

    def do_softkey_midi(self, arg):
        """Assign MIDI function to a key. Usage: softkey_midi <layer> <key> <row> <func_index>"""
        if not self._require_connected():
            return
        parts = arg.split()
        if len(parts) < 4:
            print("Usage: softkey_midi <layer_1-4> <key> <row_0-1> <func_index>")
            return
        try:
            layer = int(parts[0])
            key = int(parts[1])
            row = int(parts[2])
            func_index = int(parts[3])
        except ValueError:
            print("All arguments must be numbers.")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        from .handlers.softkeys import build_set_midi_cmd

        self.client.send(
            build_set_midi_cmd(
                self.client.state.desk.serial,
                self.client.my_serial,
                layer,
                row,
                key,
                func_index,
            )
        )
        print(f"Key {key} row {row} layer {layer} -> MIDI func {func_index}")
        print("Use 'softkey_midi_funcs' to see available functions.")

    def do_softkey_name(self, arg):
        """Set keycap label. Usage: softkey_name <key> <row> <name>"""
        if not self._require_connected():
            return
        parts = arg.split(None, 2)
        if len(parts) < 3:
            print("Usage: softkey_name <key> <row_0-1> <name>")
            return
        try:
            key = int(parts[0])
            row = int(parts[1])
        except ValueError:
            print("key and row must be numbers.")
            return
        name = parts[2]
        from .handlers.softkeys import build_set_keycap_name

        self.client.send(
            build_set_keycap_name(
                self.client.state.desk.serial, self.client.my_serial, key, row, name
            )
        )
        print(f"Key {key} row {row} keycap -> '{name}'")

    def do_softkey_blank(self, arg):
        """Clear a key assignment. Usage: softkey_blank <key> <row>"""
        if not self._require_connected():
            return
        parts = arg.split()
        if len(parts) < 2:
            print("Usage: softkey_blank <key> <row_0-1>")
            return
        try:
            key = int(parts[0])
            row = int(parts[1])
        except ValueError:
            print("key and row must be numbers.")
            return
        from .handlers.softkeys import build_set_key_blank

        self.client.send(
            build_set_key_blank(self.client.state.desk.serial, self.client.my_serial, key, row)
        )
        print(f"Key {key} row {row} cleared.")

    def do_softkey_save(self, arg):
        """Save and close the current keymap edit session."""
        if not self._require_connected():
            return
        from .handlers.softkeys import build_save_edit_keymap

        self.client.send(
            build_save_edit_keymap(self.client.state.desk.serial, self.client.my_serial)
        )
        print("Keymap saved and edit session closed.")

    def do_softkey_midi_funcs(self, arg):
        """List MIDI functions available for a layer. Usage: softkey_midi_funcs <layer>"""
        if not self._require_connected():
            return
        try:
            layer = int(arg.strip())
        except ValueError:
            print("Usage: softkey_midi_funcs <layer_1-4>")
            return
        if not 1 <= layer <= 4:
            print("Layer must be 1-4.")
            return
        from .handlers.softkeys import build_get_midi_function_list

        self.client.send(
            build_get_midi_function_list(
                self.client.state.desk.serial, self.client.my_serial, layer
            )
        )
        time.sleep(0.5)
        with self.client._lock:
            funcs = list(self.client.state.softkeys.midi_functions)
        if not funcs:
            print("No MIDI functions received.")
            return
        print(f"{'Index':>6s} {'Function':32s} {'Keycap'}")
        print("-" * 60)
        for idx, user_name, keycap_name in funcs:
            print(f"{idx:6d} {user_name:32s} {keycap_name}")

    def do_supercue(self, arg):
        """SuperCue/Auto-Mon status. Note: Not available via UDP protocol on firmware V3.0/5."""
        print(
            "SuperCue/Auto-Mon is a hardware-only feature on this console firmware (V3.0/5).\n"
            "It is NOT accessible via the UDP protocol.\n"
            "Use the console surface buttons directly for SuperCue/Auto-Mon control."
        )

    # --- Debug ---

    def do_raw(self, arg):
        """Send raw command. Usage: raw <cmdcode> [hex_payload]"""
        if not self._require_connected():
            return
        parts = arg.split(None, 1)
        if not parts:
            print("Usage: raw <cmdcode> [hex_payload]")
            return
        try:
            cmd_code = int(parts[0])
        except ValueError:
            print("cmdcode must be an integer.")
            return
        payload_hex = parts[1].replace(" ", "") if len(parts) > 1 else ""
        try:
            self.client.send_custom(cmd_code, payload_hex)
        except ValueError as e:
            print(f"Invalid hex payload: {e}")
            return
        print(f"Sent cmd={cmd_code} payload={payload_hex or '(none)'}")

    def do_state(self, arg):
        """Dump full console state as JSON."""
        if not self._require_connected():
            return
        with self.client._lock:
            s = self.client.state
            hb_age = s.desk.heartbeat_age
            out = {
                "desk": {
                    "serial": s.desk.serial,
                    "address": s.desk.address,
                    "product": s.desk.product_name,
                    "firmware": s.desk.firmware,
                    "name": s.desk.console_name,
                    "online": s.desk.online,
                    "heartbeat_age": None if hb_age == float("inf") else round(hb_age, 1),
                },
                "channels": {ch.number: ch.name for ch in s.channels if ch.name},
                "daw_layers": [
                    {
                        "layer": dl.number,
                        "protocol": PROTOCOL_NAMES.get(dl.protocol, "?"),
                        "profile": dl.profile_name,
                    }
                    for dl in s.daw_layers
                ],
                "profiles": [
                    {
                        "name": p.name,
                        "protocol": PROTOCOL_NAMES.get(p.protocol, "?"),
                        "read_only": p.read_only,
                        "in_use": p.in_use,
                    }
                    for p in s.profiles
                ],
                "devices": [
                    {
                        "num": dev.number,
                        "name": dev.name,
                        "assigned": bool(dev.is_assigned),
                        "stereo": bool(dev.is_stereo),
                    }
                    for dev in s.devices
                    if dev.name
                ],
                "chains": [
                    {
                        "num": c.number,
                        "name": c.name,
                        "assigned": bool(c.is_assigned),
                        "elements": [{"idx": i, "name": n} for i, n in c.elements],
                    }
                    for c in s.chains
                ],
                "channel_inserts": [
                    {
                        "channel": ci.channel,
                        "chain": ci.chain_name,
                        "inserts": list(ci.inserts),
                        "stereo": bool(ci.has_stereo),
                    }
                    for ci in s.channel_inserts
                ],
                "matrix_presets": [p.name for p in s.matrix_presets],
                "tr_enabled": s.tr_enabled,
                "tr_snapshots": [
                    {"name": t.name, "date": t.date_str, "selected": t.is_selected}
                    for t in s.tr_snapshots
                ],
                "chan_names_presets": [p.name for p in s.chan_names_presets],
                "xpatch_routes": [
                    {"dest": r.dest, "src": r.display_src, "protect": r.protect}
                    for r in s.xpatch.routes
                ],
                "xpatch_presets": [
                    {"index": p.index, "name": p.name, "used": p.used} for p in s.xpatch.presets
                ],
                "automation_mode": "Delta" if s.automation_mode else "Legacy",
                "motors_off": bool(s.motors_off),
                "mdac_meters": bool(s.mdac_meters),
                "transport_lock": s.transport_lock_layer,
                "project": s.project_name,
                "title": s.title_name,
                "directory": [
                    {
                        "name": e.name,
                        "is_dir": e.is_dir,
                        "date": e.date_str,
                        "time": e.time_str,
                        "size": e.size,
                    }
                    for e in s.directory
                ],
                "disk_info": {
                    "free_percent": s.disk_info.free_percent,
                    "archive_done": s.disk_info.archive_done,
                },
                "synced": s.synced,
            }
        print(json.dumps(out, indent=2))

    # --- Misc ---

    def do_quit(self, arg):
        """Exit the CLI."""
        self.client.disconnect()
        return True

    do_exit = do_quit
    do_EOF = do_quit

    def emptyline(self):
        pass


def main():
    parser = argparse.ArgumentParser(
        description="SSL Matrix Console Client",
        prog="ssl-matrix-client",
    )
    parser.add_argument(
        "--ip", default="192.168.1.2", help="Console IP address (default: 192.168.1.2)"
    )
    parser.add_argument("--port", type=int, default=PORT, help=f"UDP port (default: {PORT})")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("command", nargs="*", help="One-shot command (e.g. 'channels', 'layers')")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    cli = SSLMatrixCLI(ip=args.ip, port=args.port)

    if args.command:
        # One-shot mode: connect, run command, exit
        cli.client.connect()
        if not cli.client.wait_online(timeout=5):
            print("Connection timeout.", file=sys.stderr)
            sys.exit(1)
        cli._connected = True
        cli.client.request_sync()

        cmd_name = args.command[0]
        cmd_args = " ".join(args.command[1:])

        method = getattr(cli, f"do_{cmd_name}", None)
        if method:
            method(cmd_args)
        else:
            print(f"Unknown command: {cmd_name}", file=sys.stderr)
            sys.exit(1)

        cli.client.disconnect()
    else:
        # Interactive REPL
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nBye.")
            cli.client.disconnect()


if __name__ == "__main__":
    main()
