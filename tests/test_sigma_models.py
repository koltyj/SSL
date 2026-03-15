"""Tests for SSL Sigma state models."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ssl-matrix-client"))

from models import CONSOLE_PROFILES, lookup_profile
from sigma_models import (
    SigmaChannel,
    SigmaDim,
    SigmaHeadphone,
    SigmaInsert,
    SigmaLevel,
    SigmaMisc,
    SigmaMonitor,
    SigmaNetwork,
    SigmaState,
)


class TestSigmaState:
    def test_state_has_16_channels(self):
        state = SigmaState()
        assert len(state.channels) == 16

    def test_get_channel_range(self):
        state = SigmaState()
        for i in range(1, 17):
            ch = state.get_channel(i)
            assert ch is not None
            assert ch.number == i

    def test_get_channel_out_of_range(self):
        state = SigmaState()
        assert state.get_channel(0) is None
        assert state.get_channel(17) is None
        assert state.get_channel(-1) is None

    def test_channel_defaults(self):
        ch = SigmaChannel(number=1)
        assert ch.fader == 0.0
        assert ch.pan == 0.0
        assert ch.solo is False
        assert ch.mute is False
        assert ch.phase is False
        assert ch.solo_safe is False
        assert ch.mono is False
        assert ch.stereo is True
        assert ch.mix_a is True
        assert ch.mix_b is False
        assert ch.name == ""

    def test_monitor_has_7_sources(self):
        mon = SigmaMonitor()
        assert len(mon.sources) == 7
        assert all(s is False for s in mon.sources)

    def test_headphone_has_4_sources(self):
        hp = SigmaHeadphone()
        assert len(hp.sources) == 4
        assert all(s is False for s in hp.sources)

    def test_heartbeat_age_infinite_when_zero(self):
        state = SigmaState()
        assert state.heartbeat_age == float("inf")

    def test_heartbeat_age_finite_when_set(self):
        import time

        state = SigmaState()
        state.last_heartbeat = time.time() - 5.0
        assert 4.0 < state.heartbeat_age < 7.0


class TestSigmaConsoleProfile:
    def test_sigma_profile_exists(self):
        assert "Sigma" in CONSOLE_PROFILES

    def test_sigma_profile_values(self):
        p = CONSOLE_PROFILES["Sigma"]
        assert p.product_key == "Sigma"
        assert p.display_name == "SSL Sigma"
        assert p.num_channels == 16
        assert p.has_delta is True

    def test_lookup_sigma_exact(self):
        p = lookup_profile("Sigma")
        assert p.product_key == "Sigma"

    def test_lookup_sigma_delta_alt_name(self):
        p = lookup_profile("Sigma Delta")
        assert p.product_key == "Sigma"

    def test_lookup_sigmadelta_alt_name(self):
        p = lookup_profile("SigmaDelta")
        assert p.product_key == "Sigma"


class TestSigmaSubmodelDefaults:
    def test_insert_defaults(self):
        ins = SigmaInsert()
        assert ins.insert_a == 0
        assert ins.insert_b == 0
        assert ins.insert_a_sum is False
        assert ins.insert_b_sum is False
        assert ins.mix_b_to_mix_a is False

    def test_level_defaults(self):
        lvl = SigmaLevel()
        assert lvl.meter_mode == 0
        assert lvl.level_toggle is False
        assert lvl.level_value == 0.0
        assert lvl.level_fader == 0.0
        assert lvl.meter_source == 0

    def test_dim_defaults(self):
        dim = SigmaDim()
        assert dim.dim_level == 0.0
        assert dim.secondary_dim == 0.0

    def test_misc_defaults(self):
        misc = SigmaMisc()
        assert misc.talkback_mode == 0
        assert misc.oscillator is False
        assert misc.listenback is False
        assert misc.scene_recall == 0
        assert misc.connection_status is False
        assert misc.daw_control == 0

    def test_network_defaults(self):
        net = SigmaNetwork()
        assert net.master_slave is False
        assert net.ip_octets == [192, 168, 1, 201]
        assert net.subnet_octets == [255, 255, 255, 0]
        assert net.gateway_octets == [0, 0, 0, 0]


class TestSigmaStateIsolation:
    def test_channel_list_independence(self):
        """Two SigmaState instances should not share channel lists."""
        s1 = SigmaState()
        s2 = SigmaState()
        s1.get_channel(1).fader = 0.9
        assert s2.get_channel(1).fader == 0.0

    def test_monitor_sources_independence(self):
        s1 = SigmaState()
        s2 = SigmaState()
        s1.monitor.sources[0] = True
        assert s2.monitor.sources[0] is False

    def test_network_octets_independence(self):
        s1 = SigmaState()
        s2 = SigmaState()
        s1.network.ip_octets[3] = 99
        assert s2.network.ip_octets[3] == 201
