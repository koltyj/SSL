"""Tests for models.py: ConsoleState, DeskInfo, and dataclass defaults."""

import time

from ssl_matrix_client.models import (
    ConsoleState,
    DeskInfo,
    XpatchState,
)


class TestConsoleState:
    def test_default_channels(self):
        s = ConsoleState()
        assert len(s.channels) == 32
        assert s.channels[0].number == 1
        assert s.channels[31].number == 32

    def test_default_daw_layers(self):
        s = ConsoleState()
        assert len(s.daw_layers) == 4
        assert s.daw_layers[0].number == 1
        assert s.daw_layers[3].number == 4

    def test_default_devices(self):
        s = ConsoleState()
        assert len(s.devices) == 16
        assert s.devices[0].number == 1
        assert s.devices[15].number == 16

    def test_get_channel_valid(self):
        s = ConsoleState()
        ch = s.get_channel(1)
        assert ch is not None
        assert ch.number == 1

    def test_get_channel_out_of_range(self):
        s = ConsoleState()
        assert s.get_channel(0) is None
        assert s.get_channel(33) is None

    def test_get_daw_layer_valid(self):
        s = ConsoleState()
        dl = s.get_daw_layer(4)
        assert dl is not None
        assert dl.number == 4

    def test_get_daw_layer_out_of_range(self):
        s = ConsoleState()
        assert s.get_daw_layer(0) is None
        assert s.get_daw_layer(5) is None

    def test_get_device_valid(self):
        s = ConsoleState()
        dev = s.get_device(16)
        assert dev is not None
        assert dev.number == 16

    def test_get_device_out_of_range(self):
        s = ConsoleState()
        assert s.get_device(0) is None
        assert s.get_device(17) is None

    def test_field_independence(self):
        """Two ConsoleState instances don't share mutable fields."""
        a = ConsoleState()
        b = ConsoleState()
        a.channels[0].name = "MODIFIED"
        assert b.channels[0].name == ""


class TestDeskInfo:
    def test_firmware_format(self):
        d = DeskInfo(version=3, sub=0, issue=5)
        assert d.firmware == "V3.0/5"

    def test_heartbeat_age_never(self):
        d = DeskInfo()
        assert d.heartbeat_age == float("inf")

    def test_heartbeat_age_recent(self):
        d = DeskInfo(last_heartbeat=time.time() - 2.0)
        age = d.heartbeat_age
        assert 1.5 < age < 3.0


class TestXpatchState:
    def test_default_channels(self):
        xp = XpatchState()
        assert len(xp.channels) == 16
        assert xp.channels[0].number == 1
        assert xp.channels[15].number == 16
