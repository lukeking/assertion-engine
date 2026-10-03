"""Immutable neutral data boundary from the M0 data-model artifact contracts."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from types import MappingProxyType
from typing import Literal

type Number = int | float | Decimal | Fraction
type NedVector = tuple[Number, Number, Number]
type PhaseName = Literal["takeoff", "hover", "northbound", "return", "landing"]


@dataclass(frozen=True)
class ScenarioSource:
    name: str
    version: str
    seed: int
    config: Mapping[str, str | Number]

    def __post_init__(self):
        # Normalized config contains only scalar values, all of which are immutable.
        if any(
            not isinstance(value, (str, int, float, Decimal, Fraction))
            for value in self.config.values()
        ):
            raise TypeError("normalized source config must contain scalar values")
        object.__setattr__(self, "config", MappingProxyType(dict(self.config)))


@dataclass(frozen=True)
class TelemetrySnapshot:
    vehicle_id: str
    sequence_number: int
    mission_time_s: Number
    position_ned_m: NedVector
    velocity_ned_mps: NedVector
    battery_percent: Number

    def __post_init__(self):
        object.__setattr__(self, "position_ned_m", tuple(self.position_ned_m))
        object.__setattr__(self, "velocity_ned_mps", tuple(self.velocity_ned_mps))


@dataclass(frozen=True)
class TelemetryArtifact:
    scenario: ScenarioSource
    snapshots: tuple[TelemetrySnapshot, ...]
    artifact_version: str = "1.0.0"

    def __post_init__(self):
        object.__setattr__(self, "snapshots", tuple(self.snapshots))


@dataclass(frozen=True)
class PhaseInterval:
    name: PhaseName
    start_time_s: Number
    end_time_s: Number
    start_sequence_number: int


@dataclass(frozen=True)
class GroundTruthArtifact:
    scenario: ScenarioSource
    terminal_time_s: Number
    phases: tuple[PhaseInterval, ...]
    artifact_version: str = "2.0.0"

    def __post_init__(self):
        object.__setattr__(self, "phases", tuple(self.phases))
