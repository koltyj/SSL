"""Secondary tab view widgets for the SSL console TUI.

Provides read-only views of console routing, saved session templates,
and console settings (DAW layers, automation mode, split config).

Each view exposes update_from(snapshot) which is called by SSLApp on
every StateUpdated message. TemplatesView is static — it reads from disk
on mount and does not subscribe to live state updates.
"""

from __future__ import annotations

from textual.widgets import Static

from . import templates as tpl_module


class RoutingView(Static):
    """Read-only view of insert device assignments and channel routing."""

    def __init__(self, **kwargs):
        super().__init__("Loading routing...", **kwargs)

    def update_from(self, snapshot: dict) -> None:
        """Re-render from a StateUpdated snapshot dict."""
        with self.app.client._lock:
            devices = list(self.app.client.state.devices)
            channel_inserts = list(getattr(self.app.client.state, "channel_inserts", []))

        lines = ["[bold]Insert Devices[/bold]", ""]
        for dev in devices:
            status = "ASSIGNED" if dev.is_assigned else "free"
            stereo = " [dim](stereo)[/dim]" if dev.is_stereo else ""
            lines.append(
                f"  [{('green' if dev.is_assigned else 'dim')}]"
                f"Dev {dev.number:>2}[/{'green' if dev.is_assigned else 'dim'}]"
                f"  {dev.name or '(unnamed)':<20}  {status}{stereo}"
            )

        lines.append("")
        lines.append("[bold]Channel Insert Assignments[/bold]")
        lines.append("")
        if channel_inserts:
            for ci in channel_inserts:
                inserts_str = ", ".join(str(i) for i in ci.inserts) if ci.inserts else "—"
                stereo_tag = " [dim](stereo)[/dim]" if ci.has_stereo else ""
                lines.append(
                    f"  Ch {ci.channel:>2}  Chain: {ci.chain_name or '(none)':<16}"
                    f"  Devs: {inserts_str}{stereo_tag}"
                )
        else:
            lines.append("  [dim](no channel insert data — run sync)[/dim]")

        self.update("\n".join(lines))


class TemplatesView(Static):
    """Read-only list of saved session templates from disk."""

    def __init__(self, **kwargs):
        super().__init__("Loading templates...", **kwargs)

    def on_mount(self) -> None:
        """Populate on first mount from the template directory."""
        self._refresh_list()

    def _refresh_list(self) -> None:
        templates = tpl_module.list_templates()
        lines = ["[bold]Saved Session Templates[/bold]", ""]
        if not templates:
            lines.append(
                "  [dim](no templates found — use 'template save <name>' in the REPL)[/dim]"
            )
        else:
            for filename, title, saved_at in templates:
                display_title = title or "(untitled)"
                display_date = saved_at[:16] if saved_at else "?"
                lines.append(
                    f"  [green]{filename}[/green]   [dim]{display_title}  {display_date}[/dim]"
                )
        self.update("\n".join(lines))


class SettingsView(Static):
    """Read-only console settings: DAW layers, automation mode, split config."""

    def __init__(self, **kwargs):
        super().__init__("Loading settings...", **kwargs)

    def update_from(self, snapshot: dict) -> None:
        """Re-render from a StateUpdated snapshot dict."""
        lines = ["[bold]Console Info[/bold]", ""]

        console_name = snapshot.get("console_name", "")
        firmware = snapshot.get("firmware", "")
        lines.append(f"  Name:     {console_name or '(unknown)'}")
        lines.append(f"  Firmware: {firmware or '(unknown)'}")

        lines.append("")
        lines.append("[bold]DAW Layers[/bold]")
        lines.append("")
        daw_layers = snapshot.get("daw_layers", [])
        proto_names = {0: "none", 1: "HUI", 2: "MCU", 3: "CC"}
        for num, protocol, profile_name in daw_layers:
            proto_str = proto_names.get(protocol, f"?{protocol}")
            lines.append(
                f"  Layer {num}  [{('green' if protocol else 'dim')}]{proto_str}[/{'green' if protocol else 'dim'}]"
                f"  {profile_name or '(no profile)'}"
            )

        lines.append("")
        lines.append("[bold]Automation[/bold]")
        lines.append("")
        auto_mode = snapshot.get("automation_mode", 0)
        auto_label = "Delta" if auto_mode else "Legacy"
        lines.append(f"  Mode: [green]{auto_label}[/green]")

        motors_off = snapshot.get("motors_off", False)
        motors_label = "OFF" if motors_off else "ON"
        motors_color = "dim" if motors_off else "green"
        lines.append(f"  Motors: [{motors_color}]{motors_label}[/{motors_color}]")

        mdac = snapshot.get("mdac_meters", False)
        mdac_label = "MDAC" if mdac else "standard"
        lines.append(f"  Meters: {mdac_label}")

        lines.append("")
        lines.append("[bold]Split Board[/bold]")
        lines.append("")
        split = snapshot.get("split_config")
        if split is None:
            lines.append("  [dim](not configured)[/dim]")
        else:
            left = split.get("left", [])
            right = split.get("right", [])
            lines.append(f"  Left  layers: {left}")
            lines.append(f"  Right layers: {right}")

        self.update("\n".join(lines))


class SigmaChannelsView(Static):
    """Read-only Sigma channel dashboard."""

    def __init__(self, **kwargs):
        super().__init__("Loading Sigma channels...", **kwargs)

    def update_from(self, snapshot: dict) -> None:
        channels = snapshot.get("channels", [])
        lines = [
            "[bold]Sigma Channels[/bold]",
            "",
            " Ch  Name        Fader    Pan   Solo  Mute Phase",
            " -----------------------------------------------",
        ]
        for ch in channels:
            lines.append(
                f" {ch['number']:>2}  "
                f"{(ch.get('name') or '—')[:10]:<10}  "
                f"{ch.get('fader', 0.0):>5.3f}  "
                f"{ch.get('pan', 0.0):>+5.2f}   "
                f"{'ON' if ch.get('solo') else '--':>3}   "
                f"{'ON' if ch.get('mute') else '--':>3}   "
                f"{'ON' if ch.get('phase') else '--':>3}"
            )
        self.update("\n".join(lines))


class SigmaMonitorView(Static):
    """Read-only Sigma monitor/headphone dashboard."""

    def __init__(self, **kwargs):
        super().__init__("Loading Sigma monitor state...", **kwargs)

    def update_from(self, snapshot: dict) -> None:
        monitor = snapshot.get("monitor", {})
        headphone = snapshot.get("headphone", {})
        lines = ["[bold]Monitor[/bold]", ""]
        for idx, enabled in enumerate(monitor.get("sources", []), start=1):
            lines.append(f"  Source {idx}: {'ON' if enabled else 'OFF'}")
        lines.extend(
            [
                "",
                f"  Dim level:       {monitor.get('dim_level', 0.0):.3f}",
                f"  Secondary dim:   {monitor.get('secondary_dim', 0.0):.3f}",
                "",
                "[bold]Headphone[/bold]",
                "",
            ]
        )
        for idx, enabled in enumerate(headphone.get("sources", []), start=1):
            lines.append(f"  HP Source {idx}: {'ON' if enabled else 'OFF'}")
        self.update("\n".join(lines))


class SigmaConsoleView(Static):
    """Read-only Sigma console overview."""

    def __init__(self, **kwargs):
        super().__init__("Loading Sigma console state...", **kwargs)

    def update_from(self, snapshot: dict) -> None:
        insert = snapshot.get("insert", {})
        level = snapshot.get("level", {})
        misc = snapshot.get("misc", {})
        network = snapshot.get("network", {})
        heartbeat_age = snapshot.get("heartbeat_age")
        heartbeat = "never" if heartbeat_age in (None, float("inf")) else f"{heartbeat_age:.1f}s"
        lines = [
            "[bold]Console[/bold]",
            "",
            f"  Online:          {snapshot.get('online', False)}",
            f"  Address:         {snapshot.get('console_ip') or '(unknown)'}",
            f"  Heartbeat:       {heartbeat}",
            "",
            "[bold]Insert[/bold]",
            "",
            f"  Insert A:        {insert.get('insert_a', 0)}",
            f"  Insert B:        {insert.get('insert_b', 0)}",
            f"  Insert A SUM:    {insert.get('insert_a_sum', False)}",
            f"  Insert B SUM:    {insert.get('insert_b_sum', False)}",
            "",
            "[bold]Level / Misc[/bold]",
            "",
            f"  Meter mode:      {level.get('meter_mode', 0)}",
            f"  Level value:     {level.get('level_value', 0.0):.3f}",
            f"  Level fader:     {level.get('level_fader', 0.0):.3f}",
            f"  Talkback mode:   {misc.get('talkback_mode', 0)}",
            f"  Oscillator:      {misc.get('oscillator', False)}",
            f"  Listenback:      {misc.get('listenback', False)}",
            f"  DAW control:     {misc.get('daw_control', 0)}",
            "",
            "[bold]Network[/bold]",
            "",
            f"  Master/slave:    {network.get('master_slave', False)}",
            f"  IP:              {network.get('ip', '(unknown)')}",
            f"  Subnet:          {network.get('subnet', '(unknown)')}",
        ]
        self.update("\n".join(lines))


class SigmaNotesView(Static):
    """Static Sigma release caveats and operator notes."""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)

    def on_mount(self) -> None:
        self.update(
            "[bold]Sigma Notes[/bold]\n\n"
            "  Mode:          experimental\n"
            "  Validation:    reverse-engineered, not hardware-validated\n"
            "  Safe first tests:\n"
            "    1. rename a channel\n"
            "    2. move one fader\n"
            "    3. toggle solo or mute\n"
            "    4. toggle one monitor source\n\n"
            "  If connection fails:\n"
            "    - verify the Sigma IP address\n"
            "    - verify the Sigma UDP port for your unit\n"
            "    - prefer a trusted local studio LAN\n\n"
            "  Use the command palette for live Sigma control."
        )
