"""Command palette provider for the SSL Matrix TUI.

ConsoleCmdProvider exposes console commands (sync, tab navigation,
automation mode, motors, templates, split, quit) as fuzzy-searchable
palette entries triggered by `:` or `/` in SSLApp.
"""

from __future__ import annotations

from typing import ClassVar

from textual.command import Hit, Hits, Provider


class ConsoleCmdProvider(Provider):
    """Textual command palette provider for SSL Matrix console commands."""

    # Each entry: (name, help_text, action_method_name)
    _COMMANDS: ClassVar[list[tuple[str, str, str]]] = [
        ("sync", "Refresh console state", "_cmd_sync"),
        ("channels", "Show channel names", "_cmd_show_channels"),
        ("routing", "Show insert routing", "_cmd_show_routing"),
        ("templates", "Show session templates", "_cmd_show_templates"),
        ("settings", "Show console settings", "_cmd_show_settings"),
        ("template save", "Save session template", "_cmd_template_save"),
        ("template load", "Load session template", "_cmd_template_load"),
        ("split", "Show split board status", "_cmd_split_status"),
        ("auto legacy", "Set automation mode to Legacy", "_cmd_auto_legacy"),
        ("auto delta", "Set automation mode to Delta", "_cmd_auto_delta"),
        ("motors on", "Enable motors", "_cmd_motors_on"),
        ("motors off", "Disable motors", "_cmd_motors_off"),
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

    # --- Callbacks ---

    def _cmd_sync(self) -> None:
        self.app.run_worker(
            lambda: self.app.client.request_sync(),
            thread=True,
        )

    def _cmd_show_channels(self) -> None:
        self.app.action_show_tab("channels")

    def _cmd_show_routing(self) -> None:
        self.app.action_show_tab("routing")

    def _cmd_show_templates(self) -> None:
        self.app.action_show_tab("templates")

    def _cmd_show_settings(self) -> None:
        self.app.action_show_tab("settings")

    def _cmd_template_save(self) -> None:
        # Future: prompt user for name. For now, notify not implemented.
        self.app.notify("Use: template save <name> in the CLI REPL", severity="information")

    def _cmd_template_load(self) -> None:
        # Future: prompt user for name. For now, notify not implemented.
        self.app.notify("Use: template load <name> in the CLI REPL", severity="information")

    def _cmd_split_status(self) -> None:
        split = self.app.client.get_split()
        if split is None:
            self.app.notify("Split: not configured", severity="information")
        else:
            left = split.get("left", [])
            right = split.get("right", [])
            self.app.notify(f"Split — Left: L{left}  Right: L{right}", severity="information")

    def _cmd_auto_legacy(self) -> None:
        self.app.run_worker(
            lambda: self.app.client.set_auto_mode(0),
            thread=True,
        )

    def _cmd_auto_delta(self) -> None:
        self.app.run_worker(
            lambda: self.app.client.set_auto_mode(1),
            thread=True,
        )

    def _cmd_motors_on(self) -> None:
        self.app.run_worker(
            lambda: self.app.client.set_motors_off(0),
            thread=True,
        )

    def _cmd_motors_off(self) -> None:
        self.app.run_worker(
            lambda: self.app.client.set_motors_off(1),
            thread=True,
        )

    def _cmd_quit(self) -> None:
        self.app.exit()
