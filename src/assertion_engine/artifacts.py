"""Offline shape, semantic and canonical-byte validation of M0 artifacts.

Algorithm source/intuition: docs/algorithms/001-m0-telemetry-and-playback.md §1.
Measure each tick from the origin rather than carrying rounded error forward:
source scalars -> Fraction rate/phase starts -> Q(k/r) and ceil(start*r).
Snapshots and PhaseIntervals hold the published coordinates and boundaries;
the source's unrounded scalars remain the semantic validator's authority.
"""

import json
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource

from assertion_engine.telemetry import (
    GroundTruthArtifact,
    Number,
    PhaseInterval,
    ScenarioSource,
    TelemetryArtifact,
    TelemetrySnapshot,
)

PHASE_NAMES = ("takeoff", "hover", "northbound", "return", "landing")
DERIVED_CONFIG_FIELDS = {"sample_rate_hz", "sample_interval_s"}


class ArtifactValidationError(ValueError):
    """An artifact cannot satisfy its shape, numeric or semantic contract."""


def exact_number(value: Number) -> Fraction:
    """Interpret a finite normalized numeric value as its exact decimal rational."""
    if isinstance(value, bool) or not isinstance(
        value, (int, float, Decimal, Fraction)
    ):
        raise ArtifactValidationError("expected a finite JSON number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ArtifactValidationError("non-finite JSON number")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ArtifactValidationError("non-finite JSON number")
    return value if isinstance(value, Fraction) else Fraction(str(value))


def quantize(value: Number) -> Decimal:
    """Q: exact six-place nearest/ties-to-even rounding, with unsigned zero."""
    units = round(exact_number(value) * 1_000_000)
    sign = "-" if units < 0 else ""
    whole, fractional = divmod(abs(units), 1_000_000)
    return Decimal(f"{sign}{whole}.{fractional:06d}")


def _document(value):
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _document(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {key: _document(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_document(item) for item in value]
    return value


def _source_decimal(value: Number) -> Decimal:
    exact = exact_number(value)
    if not isinstance(value, Fraction):
        return Decimal(str(value))
    # Source numbers have finite canonical decimal representations.
    denominator = exact.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ArtifactValidationError(
            "source number has no finite decimal representation"
        )
    places = max(twos, fives)
    scaled = exact.numerator * 2 ** (places - twos) * 5 ** (places - fives)
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled)).zfill(places + 1)
    text = digits if places == 0 else digits[:-places] + "." + digits[-places:]
    return Decimal(sign + text)


def _encode(value, path=(), preserve_numbers=False):
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ArtifactValidationError("JSON object keys must be strings")
        return (
            "{"
            + ",".join(
                json.dumps(key, ensure_ascii=False)
                + ":"
                + _encode(value[key], (*path, key), preserve_numbers)
                for key in sorted(value)
            )
            + "}"
        )
    if isinstance(value, (tuple, list)):
        return (
            "["
            + ",".join(
                _encode(item, (*path, index), preserve_numbers)
                for index, item in enumerate(value)
            )
            + "]"
        )
    if isinstance(value, (str, bool)) or value is None:
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    preserve_source = preserve_numbers or (
        len(path) >= 2
        and path[-2] == "config"
        and path[-1] not in DERIVED_CONFIG_FIELDS
    )
    number = _source_decimal(value) if preserve_source else quantize(value)
    if number == 0:
        return "0"
    text = format(number, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def canonical_bytes(value) -> bytes:
    """Encode domain-order arrays and sorted keys; preserve source input precision.

    Mapping values outside non-derived config inputs are calculated values and use Q.
    This function serializes; validate_pair performs artifact shape/semantic checks.
    """
    try:
        return (_encode(_document(value)) + "\n").encode("utf-8")
    except UnicodeError as error:
        raise ArtifactValidationError(f"invalid UTF-8 content: {error}") from error


def _reject_constant(token):
    raise ArtifactValidationError(f"non-finite JSON number: {token}")


def decode_json(value: bytes | str) -> dict:
    """Decode decimals without binary-float precision loss or overflow to Infinity."""
    try:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        result = json.loads(value, parse_float=Decimal, parse_constant=_reject_constant)
    except (ValueError, UnicodeError) as error:
        raise ArtifactValidationError(f"invalid JSON: {error}") from error
    if not isinstance(result, dict):
        raise ArtifactValidationError("artifact JSON must be an object")
    return result


@lru_cache(maxsize=1)
def _validators():
    root = Path(__file__).resolve().parents[2]
    contracts = root / "specs" / "001-telemetry-simulator" / "contracts"
    schemas = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(contracts.glob("*.schema.json"))
    }
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    return {
        name: Draft202012Validator(schema, registry=registry)
        for name, schema in schemas.items()
    }


def _finite_numbers(value):
    if isinstance(value, Mapping):
        for item in value.values():
            _finite_numbers(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _finite_numbers(item)
    elif isinstance(value, (float, Decimal, Fraction)):
        exact_number(value)


def _shape(document, schema_name):
    _finite_numbers(document)
    try:
        _validators()[schema_name].validate(document)
    except ValidationError as error:
        path = ".".join(str(part) for part in error.absolute_path) or "artifact"
        raise ArtifactValidationError(f"{path}: {error.message}") from error


def _equal(actual, expected, label):
    if exact_number(actual) != exact_number(expected):
        raise ArtifactValidationError(
            f"{label}: differs from exact source-derived value"
        )


def _source_numbers(config):
    keys = (
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
    try:
        return {key: exact_number(config[key]) for key in keys}
    except KeyError as error:
        raise ArtifactValidationError(
            f"missing source parameter: {error.args[0]}"
        ) from error


def source_timeline(
    config: Mapping,
) -> tuple[Fraction, Fraction, tuple[Fraction, ...], int]:
    """Return exact rate, interval, six phase endpoints and terminal tick index.

    Accept normalized non-derived source parameters; rounded metadata is optional
    and does not participate in arithmetic. This performs numeric prevalidation
    without creating any output or changing the source mapping.
    """
    source = _source_numbers(config)
    for key, value in source.items():
        if key == "initial_battery_percent":
            valid = 0 <= value <= 100
        elif key in ("hover_duration_s", "battery_drain_percent_per_s"):
            valid = value >= 0
        else:
            valid = value > 0
        if not valid:
            raise ArtifactValidationError(f"{key}: invalid source numeric range")
    rate = source["cruise_speed_mps"] / source["observation_spacing_m"]
    interval = 1 / rate
    if quantize(rate) <= 0 or quantize(interval) <= 0:
        raise ArtifactValidationError("sample metadata must remain positive after Q")
    durations = (
        source["target_altitude_m"] / source["climb_rate_mps"],
        source["hover_duration_s"],
        source["northbound_distance_m"] / source["cruise_speed_mps"],
        source["northbound_distance_m"] / source["cruise_speed_mps"],
        source["target_altitude_m"] / source["descent_rate_mps"],
    )
    starts = [Fraction(0)]
    for duration in durations:
        starts.append(starts[-1] + duration)
    terminal = starts[-1]
    ticks = terminal * rate
    if ticks.denominator != 1:
        raise ArtifactValidationError(
            "terminal time does not align to the exact tick grid"
        )
    # Below one microsecond each rounded increment is zero or one unit. N total
    # units requires every one of the N increments to be strictly positive.
    if (
        interval < Fraction(1, 1_000_000)
        and round(terminal * 1_000_000) != ticks.numerator
    ):
        raise ArtifactValidationError(
            "quantized tick times must be strictly increasing"
        )
    if (
        source["initial_battery_percent"]
        < source["battery_drain_percent_per_s"] * terminal
    ):
        raise ArtifactValidationError(
            "source battery would be exhausted before terminal"
        )
    return rate, interval, tuple(starts), ticks.numerator


def _expected_motion(source, starts, time, terminal):
    """Independent validation of source-derived N/E/D path, not simulation output."""
    zero = Fraction(0)
    altitude = source["target_altitude_m"]
    if time == terminal:
        return (zero, zero, zero), (zero, zero, zero)
    phase = max(index for index in range(5) if starts[index] <= time)
    elapsed = time - starts[phase]
    if phase == 0:
        climb = source["climb_rate_mps"]
        return (zero, zero, -climb * elapsed), (zero, zero, -climb)
    if phase == 1:
        return (zero, zero, -altitude), (zero, zero, zero)
    speed = source["cruise_speed_mps"]
    if phase == 2:
        return (speed * elapsed, zero, -altitude), (speed, zero, zero)
    if phase == 3:
        return (source["northbound_distance_m"] - speed * elapsed, zero, -altitude), (
            -speed,
            zero,
            zero,
        )
    descent = source["descent_rate_mps"]
    return (zero, zero, -altitude + descent * elapsed), (zero, zero, descent)


def validate_pair(
    telemetry: Mapping | TelemetryArtifact,
    ground_truth: Mapping | GroundTruthArtifact,
) -> tuple[TelemetryArtifact, GroundTruthArtifact]:
    """Validate paired documents and return copied immutable domain values."""
    telemetry = _document(telemetry)
    ground_truth = _document(ground_truth)
    _shape(telemetry, "telemetry-artifact.schema.json")
    _shape(ground_truth, "ground-truth.schema.json")
    if _encode(telemetry["scenario"], preserve_numbers=True) != _encode(
        ground_truth["scenario"], preserve_numbers=True
    ):
        raise ArtifactValidationError("artifact pair scenario source differs")
    config = telemetry["scenario"]["config"]
    rate, interval, starts, count = source_timeline(config)
    source = _source_numbers(config)
    _equal(config["sample_rate_hz"], quantize(rate), "sample_rate_hz")
    _equal(config["sample_interval_s"], quantize(interval), "sample_interval_s")
    snapshots = telemetry["snapshots"]
    if len(snapshots) != count + 1:
        raise ArtifactValidationError(
            "snapshot count differs from aligned terminal tick count"
        )
    previous = None
    for k, snapshot in enumerate(snapshots):
        if snapshot["sequence_number"] != k:
            raise ArtifactValidationError(
                f"snapshots[{k}].sequence_number is not contiguous"
            )
        if snapshot["vehicle_id"] != config["vehicle_id"]:
            raise ArtifactValidationError(
                f"snapshots[{k}].vehicle_id differs from source"
            )
        time = k * interval
        published = quantize(time)
        _equal(snapshot["mission_time_s"], published, f"snapshots[{k}].mission_time_s")
        if previous is not None and published <= previous:
            raise ArtifactValidationError(
                "quantized tick times must be strictly increasing"
            )
        previous = published
        position, velocity = _expected_motion(source, starts, time, starts[-1])
        for field, expected in (
            ("position_ned_m", position),
            ("velocity_ned_mps", velocity),
        ):
            for axis, value in enumerate(expected):
                _equal(
                    snapshot[field][axis],
                    quantize(value),
                    f"snapshots[{k}].{field}[{axis}]",
                )
        battery = (
            source["initial_battery_percent"]
            - source["battery_drain_percent_per_s"] * time
        )
        _equal(
            snapshot["battery_percent"],
            quantize(battery),
            f"snapshots[{k}].battery_percent",
        )
    _equal(ground_truth["terminal_time_s"], quantize(starts[-1]), "terminal_time_s")
    for index, phase in enumerate(ground_truth["phases"]):
        if phase["name"] != PHASE_NAMES[index]:
            raise ArtifactValidationError(
                "phase names must follow the five-phase order"
            )
        _equal(
            phase["start_time_s"],
            quantize(starts[index]),
            f"phases[{index}].start_time_s",
        )
        _equal(
            phase["end_time_s"],
            quantize(starts[index + 1]),
            f"phases[{index}].end_time_s",
        )
        boundary = math.ceil(starts[index] * rate)
        if phase["start_sequence_number"] != boundary or not 0 <= boundary <= count:
            raise ArtifactValidationError(
                f"phases[{index}].start_sequence_number differs "
                "from exact ceil(start*rate)"
            )
    scenario = ScenarioSource(**telemetry["scenario"])
    return (
        TelemetryArtifact(
            scenario=scenario,
            snapshots=tuple(TelemetrySnapshot(**snapshot) for snapshot in snapshots),
            artifact_version=telemetry["artifact_version"],
        ),
        GroundTruthArtifact(
            scenario=scenario,
            terminal_time_s=ground_truth["terminal_time_s"],
            phases=tuple(PhaseInterval(**phase) for phase in ground_truth["phases"]),
            artifact_version=ground_truth["artifact_version"],
        ),
    )
