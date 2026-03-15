"""State models for SSL Sigma console. EXPERIMENTAL — untested against real hardware."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SigmaChannel:
    """A single Sigma channel (1-16)."""

    number: int = 0
    name: str = ""
    fader: float = 0.0
    pan: float = 0.0
    solo: bool = False
    mute: bool = False
    phase: bool = False
    solo_safe: bool = False
    mono: bool = False
    stereo: bool = True
    mix_a: bool = True
    mix_b: bool = False


@dataclass
class SigmaMonitor:
    """Monitor section — 7 selectable sources plus global toggles."""

    sources: list[bool] = field(default_factory=lambda: [False] * 7)
    cut: bool = False
    dim: bool = False
    alt: bool = False
    mono: bool = False
    dim_level: float = 0.0
    secondary_dim: float = 0.0


@dataclass
class SigmaHeadphone:
    """Headphone section — 4 selectable sources."""

    sources: list[bool] = field(default_factory=lambda: [False] * 4)


@dataclass
class SigmaInsert:
    """Insert routing — A/B with sum options."""

    insert_a: int = 0  # 0=off, 2=on, 3=on+sum
    insert_b: int = 0
    insert_a_sum: bool = False
    insert_b_sum: bool = False
    mix_b_to_mix_a: bool = False


@dataclass
class SigmaLevel:
    """Level metering and control."""

    meter_mode: int = 0  # 0-3
    level_toggle: bool = False
    level_value: float = 0.0
    level_fader: float = 0.0
    meter_source: int = 0


@dataclass
class SigmaDim:
    """Dim level settings."""

    dim_level: float = 0.0
    secondary_dim: float = 0.0


@dataclass
class SigmaMisc:
    """Miscellaneous console state."""

    talkback_mode: int = 0  # 0/1/2
    oscillator: bool = False
    listenback: bool = False
    scene_recall: int = 0
    connection_status: bool = False
    daw_control: int = 0


@dataclass
class SigmaNetwork:
    """Network configuration."""

    master_slave: bool = False  # False=master
    ip_octets: list[int] = field(default_factory=lambda: [192, 168, 1, 201])
    subnet_octets: list[int] = field(default_factory=lambda: [255, 255, 255, 0])
    gateway_octets: list[int] = field(default_factory=lambda: [0, 0, 0, 0])


@dataclass
class SigmaState:
    """Full state of a connected SSL Sigma console."""

    channels: list[SigmaChannel] = field(
        default_factory=lambda: [SigmaChannel(number=i) for i in range(1, 17)]
    )
    monitor: SigmaMonitor = field(default_factory=SigmaMonitor)
    headphone: SigmaHeadphone = field(default_factory=SigmaHeadphone)
    insert: SigmaInsert = field(default_factory=SigmaInsert)
    level: SigmaLevel = field(default_factory=SigmaLevel)
    dim: SigmaDim = field(default_factory=SigmaDim)
    misc: SigmaMisc = field(default_factory=SigmaMisc)
    network: SigmaNetwork = field(default_factory=SigmaNetwork)
    online: bool = False
    last_heartbeat: float = 0.0
    synced: bool = False
    console_ip: str = ""

    def get_channel(self, num: int) -> Optional[SigmaChannel]:
        """Get channel by 1-based number."""
        if 1 <= num <= len(self.channels):
            return self.channels[num - 1]
        return None

    @property
    def heartbeat_age(self) -> float:
        if self.last_heartbeat == 0:
            return float("inf")
        return time.time() - self.last_heartbeat
