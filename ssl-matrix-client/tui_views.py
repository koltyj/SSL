"""Secondary tab view widgets for the SSL Matrix TUI.

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
        paths = tpl_module.list_templates()
        lines = ["[bold]Saved Session Templates[/bold]", ""]
        if not paths:
            lines.append(
                "  [dim](no templates found — use 'template save <name>' in the REPL)[/dim]"
            )
        else:
            for p in sorted(paths, key=lambda x: x.stat().st_mtime, reverse=True):
                size_kb = p.stat().st_size / 1024
                mtime = p.stat().st_mtime
                import datetime

                dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                lines.append(f"  [green]{p.stem}[/green]   [dim]{dt}  {size_kb:.1f} KB[/dim]")
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
