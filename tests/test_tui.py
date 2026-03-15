"""Smoke tests for the Textual TUI."""

from unittest.mock import MagicMock

import pytest
from ssl_matrix_client.client import SSLMatrixClient
from ssl_matrix_client.sigma_client import SSLSigmaClient
from ssl_matrix_client.tui import SSLApp, SSLStatusBar
from ssl_matrix_client.tui_commands import ConsoleCmdProvider
from ssl_matrix_client.tui_views import SigmaChannelsView, SigmaConsoleView, SigmaMonitorView
from ssl_matrix_client.tui_widgets import ChannelStrip
from textual.widgets import Label, TabbedContent


@pytest.fixture
def tui_app(monkeypatch):
    monkeypatch.setattr(SSLApp, "do_connect", lambda self: None)
    monkeypatch.setattr(SSLMatrixClient, "disconnect", lambda self: None)
    return SSLApp(console_ip="127.0.0.1")


@pytest.fixture
def sigma_tui_app(monkeypatch):
    monkeypatch.setattr(SSLApp, "do_connect", lambda self: None)
    monkeypatch.setattr(SSLSigmaClient, "disconnect", lambda self: None)
    return SSLApp(console_ip="127.0.0.1", console_type="sigma")


@pytest.mark.asyncio
async def test_tui_mounts_with_ssl_theme(tui_app):
    async with tui_app.run_test():
        assert tui_app.theme == "ssl-console"
        assert tui_app.query_one(TabbedContent).active == "channels"
        assert tui_app.query_one(SSLStatusBar)._hint_text == "1-4:Tabs  /:Commands  q:Quit"


@pytest.mark.asyncio
async def test_action_show_tab_switches_active_tab(tui_app):
    async with tui_app.run_test() as pilot:
        tui_app.action_show_tab("routing")
        await pilot.pause()
        assert tui_app.query_one(TabbedContent).active == "routing"
        assert tui_app.query_one(SSLStatusBar)._hint_text == "1-4:Tabs  /:Commands  q:Quit"


@pytest.mark.asyncio
async def test_state_update_expands_channel_view_without_duplicate_ids(tui_app):
    snapshot = {
        "online": True,
        "heartbeat_age": 2.0,
        "project_name": "Album",
        "title_name": "MixA",
        "channels": [(1, "KICK"), (32, "FX")],
        "daw_layers": [(1, 1, "HUI")],
        "automation_mode": 1,
        "channel_inserts": [(1, "DRUMS", [1, 2], False)],
        "last_template": "mix-a",
        "devices": [],
        "num_channels": 32,
        "console_name": "Matrix",
        "firmware": "V3.0/5",
        "motors_off": False,
        "mdac_meters": False,
        "split_config": None,
    }

    async with tui_app.run_test() as pilot:
        tui_app.post_message(tui_app.StateUpdated(snapshot))
        await pilot.pause()

        strips = sorted(tui_app.query(ChannelStrip), key=lambda strip: strip.channel_num)
        assert len(strips) == 32
        assert strips[0].channel_name == "KICK"
        assert strips[0].daw_protocol == "HUI"
        assert strips[0].auto_mode == "Delta"
        assert strips[0].insert_routing == "DRUMS"
        assert strips[-1].channel_num == 32
        assert strips[-1].channel_name == "FX"


@pytest.mark.asyncio
async def test_disconnect_overlay_updates_attempt_count_and_clears_when_online(tui_app):
    async with tui_app.run_test() as pilot:
        tui_app.post_message(tui_app.ConsoleOffline(3))
        await pilot.pause()

        overlay = tui_app._disconnect_overlay
        assert overlay is not None
        label = overlay.query_one("#disconnect-attempt", Label)
        assert "attempt 3" in str(label.render())

        tui_app.post_message(tui_app.ConsoleOffline(4))
        await pilot.pause()
        assert "attempt 4" in str(label.render())

        tui_app.post_message(tui_app.ConsoleOnline())
        await pilot.pause()
        assert tui_app._disconnect_overlay is None


@pytest.mark.asyncio
async def test_sigma_tui_mounts_with_sigma_tabs(sigma_tui_app):
    async with sigma_tui_app.run_test():
        assert sigma_tui_app.theme == "ssl-console"
        assert sigma_tui_app.query_one(TabbedContent).active == "channels"


@pytest.mark.asyncio
async def test_sigma_state_update_renders_sigma_views(sigma_tui_app):
    snapshot = {
        "online": True,
        "heartbeat_age": 1.5,
        "project_name": "Sigma",
        "title_name": "192.168.1.201",
        "console_ip": "192.168.1.201",
        "channels": [
            {
                "number": 1,
                "name": "KICK",
                "fader": 0.75,
                "pan": -0.1,
                "solo": True,
                "mute": False,
                "phase": False,
            },
            {
                "number": 2,
                "name": "SNARE",
                "fader": 0.65,
                "pan": 0.2,
                "solo": False,
                "mute": True,
                "phase": True,
            },
        ],
        "monitor": {
            "sources": [True, False, False, True, False, False, False],
            "dim_level": 0.4,
            "secondary_dim": 0.2,
        },
        "headphone": {"sources": [False, True, False, True]},
        "insert": {"insert_a": 2, "insert_b": 3, "insert_a_sum": False, "insert_b_sum": True},
        "level": {"meter_mode": 2, "level_value": -12.5, "level_fader": 0.5},
        "misc": {
            "talkback_mode": 1,
            "oscillator": False,
            "listenback": True,
            "connection_status": True,
            "daw_control": 0,
        },
        "network": {"master_slave": False, "ip": "192.168.1.201", "subnet": "255.255.255.0"},
        "last_template": "",
    }

    async with sigma_tui_app.run_test() as pilot:
        sigma_tui_app.post_message(sigma_tui_app.StateUpdated(snapshot))
        await pilot.pause()

        channels_view = sigma_tui_app.query_one(SigmaChannelsView)
        monitor_view = sigma_tui_app.query_one(SigmaMonitorView)
        console_view = sigma_tui_app.query_one(SigmaConsoleView)

        assert "KICK" in str(channels_view.render())
        assert "Source 1: ON" in str(monitor_view.render())
        assert "192.168.1.201" in str(console_view.render())


@pytest.mark.asyncio
async def test_sigma_action_show_tab_uses_native_tab_ids(sigma_tui_app):
    async with sigma_tui_app.run_test() as pilot:
        sigma_tui_app.action_show_tab("monitor")
        await pilot.pause()
        assert sigma_tui_app.query_one(TabbedContent).active == "monitor"

        sigma_tui_app.action_show_tab("console")
        await pilot.pause()
        assert sigma_tui_app.query_one(TabbedContent).active == "console"

        sigma_tui_app.action_show_tab("notes")
        await pilot.pause()
        assert sigma_tui_app.query_one(TabbedContent).active == "notes"


@pytest.mark.asyncio
async def test_sigma_command_palette_exposes_sigma_names_only(sigma_tui_app):
    async with sigma_tui_app.run_test():
        provider = ConsoleCmdProvider(sigma_tui_app.screen)
        hits = [hit async for hit in provider.search("mon")]
        prompts = {str(hit.text) for hit in hits}

        assert "monitor" in prompts
        assert "monitor source" in prompts
        assert "routing" not in prompts


@pytest.mark.asyncio
async def test_sigma_palette_fader_handler_parses_and_dispatches(sigma_tui_app, monkeypatch):
    sigma_tui_app.client._running = True
    sigma_tui_app.client.set_fader = MagicMock()

    captured_callback = {}

    def fake_prompt(self, _prompt, _placeholder, callback):
        captured_callback["fn"] = callback

    monkeypatch.setattr(ConsoleCmdProvider, "_prompt_input", fake_prompt)
    monkeypatch.setattr(ConsoleCmdProvider, "_run_in_thread", lambda self, fn: fn())

    async with sigma_tui_app.run_test():
        provider = ConsoleCmdProvider(sigma_tui_app.screen)
        provider._cmd_fader()
        captured_callback["fn"]("2 0.625")

    sigma_tui_app.client.set_fader.assert_called_once_with(2, 0.625)


def test_status_bar_health_thresholds():
    bar = SSLStatusBar()
    bar.update_from({"heartbeat_age": 1, "project_name": "", "last_template": ""})
    assert bar._health == "green"

    bar.update_from({"heartbeat_age": 20, "project_name": "", "last_template": ""})
    assert bar._health == "yellow"

    bar.update_from({"heartbeat_age": 40, "project_name": "", "last_template": ""})
    assert bar._health == "red"
