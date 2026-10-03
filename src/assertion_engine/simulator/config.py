"""Validate explicit TOML and normalize the immutable scenario source.

See docs/algorithms/001-m0-telemetry-and-playback.md §1: measure ticks from
the origin with an exact rational ruler. TOML decimals stay Decimal in source
config; source_timeline derives Fraction rate/endpoints before metadata uses Q.
"""

import re
import tomllib
from dataclasses import asdict, dataclass, fields
from decimal import Decimal
from pathlib import Path

from assertion_engine.artifacts import exact_number, quantize, source_timeline
from assertion_engine.telemetry import ScenarioSource

_NUMERIC_FIELDS = (
    "target_altitude_m",
    "climb_rate_mps",
    "hover_duration_s",
    "northbound_distance_m",
    "cruise_speed_mps",
    "descent_rate_mps",
    "observation_spacing_m",
    "initial_battery_percent",
    "battery_drain_percent_per_s",
)


@dataclass(frozen=True)
class ScenarioConfiguration:
    """Validated, non-derived input values; no output precision loss."""

    schema_version: str
    scenario_name: str
    scenario_version: str
    seed: int
    vehicle_id: str
    target_altitude_m: int | Decimal
    climb_rate_mps: int | Decimal
    hover_duration_s: int | Decimal
    northbound_distance_m: int | Decimal
    cruise_speed_mps: int | Decimal
    descent_rate_mps: int | Decimal
    observation_spacing_m: int | Decimal
    initial_battery_percent: int | Decimal
    battery_drain_percent_per_s: int | Decimal

    def __post_init__(self):
        for name in (
            "schema_version",
            "scenario_name",
            "scenario_version",
            "vehicle_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name}: expected a non-empty string")
        if self.schema_version != "1.0.0":
            raise ValueError("schema_version: supported version is 1.0.0")
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", self.scenario_version):
            raise ValueError("scenario_version: expected a major.minor.patch version")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed: expected a non-negative integer")
        for name in _NUMERIC_FIELDS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
                raise ValueError(f"{name}: expected a finite number")
            try:
                exact_number(value)
            except ValueError as error:
                raise ValueError(f"{name}: {error}") from error
        # This checks numeric ranges, exact terminal alignment, representable
        # metadata/tick ordering and total battery before any output exists.
        source_timeline(asdict(self))

    def to_source(self) -> ScenarioSource:
        config = asdict(self)
        for key in ("scenario_name", "scenario_version", "seed"):
            del config[key]
        rate, interval, _, _ = source_timeline(config)
        config["sample_rate_hz"] = quantize(rate)
        config["sample_interval_s"] = quantize(interval)
        return ScenarioSource(
            self.scenario_name, self.scenario_version, self.seed, config
        )


def load_config(path: str | Path) -> ScenarioSource:
    """Read caller-supplied TOML; reject missing, extra and invalid source fields."""
    path = Path(path)
    try:
        values = tomllib.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"scenario {path}: {error}") from error
    required = {field.name for field in fields(ScenarioConfiguration)}
    missing = required - values.keys()
    if missing:
        raise ValueError("missing required field(s): " + ", ".join(sorted(missing)))
    extra = values.keys() - required
    if extra:
        raise ValueError("unknown source field(s): " + ", ".join(sorted(extra)))
    return ScenarioConfiguration(**values).to_source()
