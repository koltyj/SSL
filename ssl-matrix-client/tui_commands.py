"""Command palette provider for the SSL Matrix TUI.

ConsoleCmdProvider exposes console commands as fuzzy-searchable
palette entries triggered by `:` or `/` in SSLApp.

InputScreen provides a reusable modal for commands that need text input.
"""

from __future__ import annotations

import time
from typing import Callable, ClassVar, Optional

from textual.app import ComposeResult
from textual.command import Hit, Hits, Provider
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label


class InputScreen(ModalScreen[Optional[str]]):
    """Modal screen with a text input field. Returns the entered string or None."""

    DEFAULT_CSS: ClassVar[str] = """
    InputScreen {
        align: center middle;
        background: $background 70%;
    }

    InputScreen > Vertical {
        width: 50;
        height: auto;
        border: tall $primary;
        background: $surface;
        padding: 1 2;
    }

    InputScreen Label {
        width: 1fr;
        margin-bottom: 1;
    }

    InputScreen Input {
        width: 1fr;
    }
    """

    def __init__(self, prompt: str, placeholder: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._prompt = prompt
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._prompt)
            yield Input(placeholder=self._placeholder)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)

    def key_escape(self) -> None:
        self.dismiss(None)


class ConsoleCmdProvider(Provider):
    """Textual command palette provider for SSL Matrix console commands."""

    _COMMANDS: ClassVar[list[tuple[str, str, str]]] = [
        # Connection
        ("connect", "Connect to console", "_cmd_connect"),
        ("disconnect", "Disconnect from console", "_cmd_disconnect"),
        ("sync", "Refresh all console state", "_cmd_sync"),
        # Channel operations
        ("rename", "Rename a channel", "_cmd_rename"),
        ("reset names", "Reset all channel names to defaults", "_cmd_reset_names"),
        # DAW layers
        ("layers", "Show DAW layer assignments", "_cmd_layers"),
        ("set layer", "Set profile for a DAW layer", "_cmd_set_layer"),
        ("clear layer", "Clear a DAW layer profile", "_cmd_clear_layer"),
        # Automation / Motors
        ("auto legacy", "Set automation mode to Legacy", "_cmd_auto_legacy"),
        ("auto delta", "Set automation mode to Delta", "_cmd_auto_delta"),
        ("motors on", "Enable motors", "_cmd_motors_on"),
        ("motors off", "Disable motors", "_cmd_motors_off"),
        # Wheel / V-pot
        ("wheel mode", "Set V-pot wheel mode for a layer", "_cmd_wheel_mode"),
        # Templates
        ("template save", "Save current console state as template", "_cmd_template_save"),
        ("template load", "Load a saved template", "_cmd_template_load"),
        ("template list", "List all saved templates", "_cmd_template_list"),
        ("template delete", "Delete a saved template", "_cmd_template_delete"),
        # Projects
        ("project info", "Show current project and title", "_cmd_project_info"),
        ("new project", "Create a new project on console", "_cmd_new_project"),
        # Split board
        ("split", "Configure split board mode", "_cmd_split"),
        ("split clear", "Clear split board config", "_cmd_split_clear"),
        # Insert routing
        ("assign", "Assign insert device to channel", "_cmd_assign"),
        ("deassign", "Remove insert from channel", "_cmd_deassign"),
        # Total Recall
        ("tr take", "Take a Total Recall snapshot", "_cmd_tr_take"),
        ("tr enable", "Toggle Total Recall on/off", "_cmd_tr_enable"),
        # Soft keys
        ("softkey list", "List soft key assignments", "_cmd_softkey_list"),
        # Navigation
        ("channels", "Show channel strips", "_cmd_show_channels"),
        ("routing", "Show insert routing", "_cmd_show_routing"),
        ("templates", "Show templates view", "_cmd_show_templates"),
        ("settings", "Show console settings", "_cmd_show_settings"),
        # App
        ("quit", "Exit TUI", "_cmd_quit"),
    ]

    async def search(self, query: str) -> Hits:
        """Yield fuzzy-matched command hits for the given query."""
        matcher = self.matcher(query)
        for name, help_text, method_name in self._COMMANDS:
            score = matcher.match(name)
            if score > 0:
                callback = getattr(self, method_name)
                yield Hit(
                    score,
                    matcher.highlight(name),
                    callback,
                    help=help_text,
                )

    # --- Helpers ---

    def _require_connected(self) -> bool:
        if not self.app.client._running:
            self.app.notify("Not connected", severity="error")
            return False
        return True

    def _run_in_thread(self, fn: Callable) -> None:
        self.app.run_worker(fn, thread=True)

    def _prompt_input(self, prompt: str, placeholder: str, callback: Callable) -> None:
        """Show an input modal and call callback with the result."""

        def handle_result(result: Optional[str]) -> None:
            if result is not None:
                callback(result)

        self.app.push_screen(InputScreen(prompt, placeholder), handle_result)

    # --- Connection ---

    def _cmd_connect(self) -> None:
        self.app.do_connect()

    def _cmd_disconnect(self) -> None:
        self.app.do_disconnect()

    def _cmd_sync(self) -> None:
        if not self._require_connected():
            return
        self._run_in_thread(lambda: self.app.client.request_sync())
        self.app.notify("Syncing...")

    # --- Channel operations ---

    def _cmd_rename(self) -> None:
        if not self._require_connected():
            return
        sel = self.app.selected_channel

        def on_input(value: str) -> None:
            # If a channel is selected, input is just the name
            if sel is not None:
                name = value.strip()[:6]
                if not name:
                    self.app.notify("Name required", severity="error")
                    return
                ch = sel
            else:
                parts = value.split(None, 1)
                if len(parts) < 2:
                    self.app.notify("Usage: <channel> <name>", severity="error")
                    return
                try:
                    ch = int(parts[0])
                except ValueError:
                    self.app.notify("Channel must be a number", severity="error")
                    return
                name = parts[1][:6]
            self._run_in_thread(lambda: self.app.client.rename_channel(ch, name))
            self.app.notify(f"Ch {ch} → '{name}'")

        if sel is not None:
            self._prompt_input(f"Rename channel {sel}:", "KICK", on_input)
        else:
            self._prompt_input("Rename channel:", "1 KICK", on_input)

    def _cmd_reset_names(self) -> None:
        if not self._require_connected():
            return
        from .handlers.channels import build_set_default_chan_names

        def do_reset():
            ds = self.app.client.state.desk.serial
            ms = self.app.client.my_serial
            self.app.client.send(build_set_default_chan_names(ds, ms))

        self._run_in_thread(do_reset)
        self.app.notify("Channel names reset to defaults")

    # --- DAW layers ---

    def _cmd_layers(self) -> None:
        if not self._require_connected():
            return
        with self.app.client._lock:
            layers = self.app.client.state.daw_layers
            proto_names = {0: "None", 1: "HUI", 2: "MCU", 3: "CC"}
            lines = [
                f"L{dl.number}: {proto_names.get(dl.protocol, '?')} ({dl.profile_name})"
                for dl in layers
            ]
        self.app.notify("\n".join(lines) if lines else "No layers", severity="information")

    def _cmd_set_layer(self) -> None:
        if not self._require_connected():
            return

        def on_input(value: str) -> None:
            parts = value.split(None, 1)
            if len(parts) < 2:
                self.app.notify("Usage: <layer 1-4> <profile_name>", severity="error")
                return
            try:
                layer = int(parts[0])
                if not 1 <= layer <= 4:
                    raise ValueError
            except ValueError:
                self.app.notify("Layer must be 1-4", severity="error")
                return
            profile = parts[1]
            self._run_in_thread(lambda: self.app.client.set_protocol_for_layer(layer, profile))
            self.app.notify(f"Layer {layer} → '{profile}'")

        self._prompt_input("Set layer profile:", "1 HUI Default", on_input)

    def _cmd_clear_layer(self) -> None:
        if not self._require_connected():
            return

        def on_input(value: str) -> None:
            try:
                layer = int(value.strip())
                if not 1 <= layer <= 4:
                    raise ValueError
            except ValueError:
                self.app.notify("Layer must be 1-4", severity="error")
                return
            from .handlers.profiles import build_clear_profile_for_daw_layer

            def do_clear():
                ds = self.app.client.state.desk.serial
                ms = self.app.client.my_serial
                self.app.client.send(build_clear_profile_for_daw_layer(ds, ms, layer))

            self._run_in_thread(do_clear)
            self.app.notify(f"Layer {layer} cleared")

        self._prompt_input("Clear which layer?", "1-4", on_input)

    # --- Automation / Motors ---

    def _cmd_auto_legacy(self) -> None:
        if not self._require_connected():
            return
        self._run_in_thread(lambda: self.app.client.set_auto_mode(0))
        self.app.notify("Automation → Legacy")

    def _cmd_auto_delta(self) -> None:
        if not self._require_connected():
            return
        self._run_in_thread(lambda: self.app.client.set_auto_mode(1))
        self.app.notify("Automation → Delta")

    def _cmd_motors_on(self) -> None:
        if not self._require_connected():
            return
        self._run_in_thread(lambda: self.app.client.set_motors_off(0))
        self.app.notify("Motors ON")

    def _cmd_motors_off(self) -> None:
        if not self._require_connected():
            return
        self._run_in_thread(lambda: self.app.client.set_motors_off(1))
        self.app.notify("Motors OFF")

    # --- Wheel / V-pot ---

    def _cmd_wheel_mode(self) -> None:
        if not self._require_connected():
            return
        modes = "0=Pan, 1=Linear, 2=Boost-Cut, 3=Off"

        def on_input(value: str) -> None:
            parts = value.split()
            if len(parts) < 2:
                self.app.notify(f"Usage: <layer 1-4> <mode {modes}>", severity="error")
                return
            try:
                layer = int(parts[0])
                mode = int(parts[1])
            except ValueError:
                self.app.notify("Both layer and mode must be numbers", severity="error")
                return
            from .handlers.softkeys import build_set_default_wheel_mode

            def do_set():
                ds = self.app.client.state.desk.serial
                ms = self.app.client.my_serial
                self.app.client.send(build_set_default_wheel_mode(ds, ms, layer, mode))

            self._run_in_thread(do_set)
            mode_names = {0: "Pan", 1: "Linear", 2: "Boost-Cut", 3: "Off"}
            self.app.notify(f"Layer {layer} wheel → {mode_names.get(mode, '?')}")

        self._prompt_input(f"Set wheel mode ({modes}):", "1 0", on_input)

    # --- Templates ---

    def _cmd_template_save(self) -> None:
        if not self._require_connected():
            return
        from .templates import save_template

        def do_save():
            with self.app.client._lock:
                state = self.app.client.state
                filename = save_template(state)
            self.app._last_template = filename
            return filename

        def on_done(worker):
            if worker.result:
                self.app.notify(f"Saved: {worker.result}")

        w = self.app.run_worker(do_save, thread=True)
        w.add_done_callback(on_done)

    def _cmd_template_load(self) -> None:
        if not self._require_connected():
            return
        from .templates import list_templates

        templates = list_templates()
        if not templates:
            self.app.notify("No templates saved", severity="warning")
            return

        def on_input(value: str) -> None:
            from .templates import build_apply_commands, diff_template, load_template

            filename = value.strip()
            try:
                tpl = load_template(filename)
            except FileNotFoundError:
                self.app.notify(f"Not found: {filename}", severity="error")
                return

            with self.app.client._lock:
                state = self.app.client.state
                diffs = diff_template(tpl, state)
                commands = build_apply_commands(tpl, state)

            if not any(diffs.values()):
                self.app.notify("No changes to apply")
                return

            # Show diff summary and apply
            changed = [cat for cat, items in diffs.items() if items]
            self.app.notify(f"Applying: {', '.join(changed)}")

            def do_apply():
                for cmd_bytes, _desc in commands:
                    self.app.client.send_raw(cmd_bytes)
                    time.sleep(0.05)
                self.app.client.request_sync()

            self._run_in_thread(do_apply)
            self.app._last_template = filename

        # Show available templates in the prompt
        names = [t[0] for t in templates[:5]]
        hint = ", ".join(names)
        if len(templates) > 5:
            hint += f" (+{len(templates) - 5} more)"
        self._prompt_input(f"Load template ({hint}):", templates[0][0], on_input)

    def _cmd_template_list(self) -> None:
        from .templates import list_templates

        templates = list_templates()
        if not templates:
            self.app.notify("No templates saved", severity="information")
            return
        lines = [f"{fn}  ({title}, {saved})" for fn, title, saved in templates[:8]]
        if len(templates) > 8:
            lines.append(f"...+{len(templates) - 8} more")
        self.app.notify("\n".join(lines), severity="information")

    def _cmd_template_delete(self) -> None:
        from .templates import delete_template, list_templates

        templates = list_templates()
        if not templates:
            self.app.notify("No templates", severity="information")
            return

        def on_input(value: str) -> None:
            try:
                delete_template(value.strip())
                self.app.notify(f"Deleted: {value.strip()}")
            except FileNotFoundError:
                self.app.notify(f"Not found: {value.strip()}", severity="error")

        self._prompt_input("Delete which template?", templates[0][0], on_input)

    # --- Projects ---

    def _cmd_project_info(self) -> None:
        if not self._require_connected():
            return
        with self.app.client._lock:
            pn = getattr(self.app.client.state, "project_name", "")
            tn = getattr(self.app.client.state, "title_name", "")
        self.app.notify(f"Project: {pn}\nTitle: {tn}", severity="information")

    def _cmd_new_project(self) -> None:
        if not self._require_connected():
            return

        def on_input(value: str) -> None:
            from .handlers.projects import build_make_new_project_with_name

            def do_create():
                ds = self.app.client.state.desk.serial
                ms = self.app.client.my_serial
                self.app.client.send(build_make_new_project_with_name(ds, ms, value.strip()))

            self._run_in_thread(do_create)
            self.app.notify(f"Creating project: {value.strip()}")

        self._prompt_input("New project name:", "", on_input)

    # --- Split board ---

    def _cmd_split(self) -> None:
        if not self._require_connected():
            return

        def on_input(value: str) -> None:
            parts = value.strip().split()
            if len(parts) < 2:
                self.app.notify(
                    "Usage: <left_layers> <right_layers> e.g. '1,2 3,4'", severity="error"
                )
                return
            try:
                left = [int(x) for x in parts[0].split(",")]
                right = [int(x) for x in parts[1].split(",")]
            except ValueError:
                self.app.notify("Layer numbers must be integers 1-4", severity="error")
                return
            try:
                self.app.client.set_split(left, right)
            except ValueError as e:
                self.app.notify(str(e), severity="error")
                return
            self.app.notify(f"Split: L={left} R={right}")

        self._prompt_input("Split board (left_layers right_layers):", "1,2 3,4", on_input)

    def _cmd_split_clear(self) -> None:
        self.app.client.clear_split()
        self.app.notify("Split cleared")

    # --- Insert routing ---

    def _cmd_assign(self) -> None:
        if not self._require_connected():
            return
        sel = self.app.selected_channel

        def on_input(value: str) -> None:
            if sel is not None:
                # Input is just the device number
                try:
                    device = int(value.strip())
                except ValueError:
                    self.app.notify("Device must be a number", severity="error")
                    return
                channel = sel
            else:
                parts = value.split()
                if len(parts) < 2:
                    self.app.notify("Usage: <device 1-16> <channel 1-32>", severity="error")
                    return
                try:
                    device = int(parts[0])
                    channel = int(parts[1])
                except ValueError:
                    self.app.notify("Both must be numbers", severity="error")
                    return
            from .handlers.routing import build_set_insert_to_chan_v2

            def do_assign():
                ds = self.app.client.state.desk.serial
                ms = self.app.client.my_serial
                self.app.client.send(build_set_insert_to_chan_v2(ds, ms, channel, device, 0))

            self._run_in_thread(do_assign)
            self.app.notify(f"Device {device} → Channel {channel}")

        if sel is not None:
            self._prompt_input(f"Assign insert device to ch {sel}:", "1", on_input)
        else:
            self._prompt_input("Assign insert (device channel):", "1 1", on_input)

    def _cmd_deassign(self) -> None:
        if not self._require_connected():
            return

        def on_input(value: str) -> None:
            try:
                device = int(value.strip())
            except ValueError:
                self.app.notify("Device must be a number", severity="error")
                return
            from .handlers.routing import build_deassign_chan

            def do_deassign():
                ds = self.app.client.state.desk.serial
                ms = self.app.client.my_serial
                self.app.client.send(build_deassign_chan(ds, ms, device))

            self._run_in_thread(do_deassign)
            self.app.notify(f"Device {device} deassigned")

        self._prompt_input("Deassign which device?", "1-16", on_input)

    # --- Total Recall ---

    def _cmd_tr_take(self) -> None:
        if not self._require_connected():
            return
        from .handlers.total_recall import build_take_tr_snap

        def do_take():
            ds = self.app.client.state.desk.serial
            ms = self.app.client.my_serial
            self.app.client.send(build_take_tr_snap(ds, ms))

        self._run_in_thread(do_take)
        self.app.notify("TR snapshot taken")

    def _cmd_tr_enable(self) -> None:
        if not self._require_connected():
            return
        from .handlers.total_recall import build_set_tr_enable

        def on_input(value: str) -> None:
            val = value.strip().lower()
            enable = val in ("1", "on", "yes", "true")

            def do_enable():
                ds = self.app.client.state.desk.serial
                ms = self.app.client.my_serial
                self.app.client.send(build_set_tr_enable(ds, ms, 1 if enable else 0))

            self._run_in_thread(do_enable)
            self.app.notify(f"Total Recall {'ON' if enable else 'OFF'}")

        self._prompt_input("Total Recall on/off:", "on", on_input)

    # --- Soft keys ---

    def _cmd_softkey_list(self) -> None:
        if not self._require_connected():
            return
        with self.app.client._lock:
            keys = self.app.client.state.softkeys.keys
            if not keys:
                self.app.notify("No soft key data (sync first)", severity="information")
                return
            lines = [f"Key {i + 1}: {k.keycap_name or '(blank)'}" for i, k in enumerate(keys[:12])]
        self.app.notify("\n".join(lines), severity="information")

    # --- Navigation ---

    def _cmd_show_channels(self) -> None:
        self.app.action_show_tab("channels")

    def _cmd_show_routing(self) -> None:
        self.app.action_show_tab("routing")

    def _cmd_show_templates(self) -> None:
        self.app.action_show_tab("templates")

    def _cmd_show_settings(self) -> None:
        self.app.action_show_tab("settings")

    # --- App ---

    def _cmd_quit(self) -> None:
        self.app.exit()
