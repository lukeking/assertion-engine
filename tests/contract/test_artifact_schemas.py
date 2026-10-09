"""FR-004–FR-011: independently authored artifact shapes and exact semantics."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from fractions import Fraction

import pytest

from assertion_engine.artifacts import (
    ArtifactValidationError,
    decode_json,
    exact_number,
    source_timeline,
    validate_pair,
)
from assertion_engine.telemetry import TelemetrySnapshot


def test_FR004_literal_pair_and_immutable_types(artifact_pair):
    telemetry, truth = validate_pair(*artifact_pair)
    assert len(telemetry.snapshots) == 6
    assert [snapshot.mission_time_s for snapshot in telemetry.snapshots] == [
        0,
        1,
        2,
        3,
        4,
        5,
    ]
    assert [phase.start_sequence_number for phase in truth.phases] == [0, 1, 2, 3, 4]
    assert [field.name for field in fields(TelemetrySnapshot)] == [
        "vehicle_id",
        "sequence_number",
        "mission_time_s",
        "position_ned_m",
        "velocity_ned_mps",
        "battery_percent",
    ]
    assert telemetry.artifact_version == "1.0.0"
    assert truth.artifact_version == "2.0.0"
    assert telemetry.scenario == truth.scenario
    with pytest.raises(FrozenInstanceError):
        telemetry.snapshots[0].battery_percent = 0
    with pytest.raises(TypeError):
        telemetry.snapshots[0].position_ned_m[0] = 1
    with pytest.raises(TypeError):
        telemetry.scenario.config["target_altitude_m"] = 2
    with pytest.raises(TypeError):
        telemetry.snapshots[0] = telemetry.snapshots[1]
    with pytest.raises(TypeError):
        truth.phases[0] = truth.phases[1]
    artifact_pair[0]["scenario"]["config"]["target_altitude_m"] = 8
    assert telemetry.scenario.config["target_altitude_m"] == 1


def set_path(document, path, value):
    for key in path[:-1]:
        document = document[key]
    if value is DELETE:
        del document[path[-1]]
    else:
        document[path[-1]] = value


DELETE = object()


@pytest.mark.parametrize(
    ("side", "path", "value"),
    [
        (0, ("snapshots", 0, "phase"), "takeoff"),
        (0, ("snapshots", 0, "battery_percent"), DELETE),
        (0, ("snapshots", 0, "position_ned_m"), [0, 0]),
        (0, ("snapshots", 0, "velocity_ned_mps"), [0, 0, 0, 0]),
        (0, ("snapshots", 2, "vehicle_id"), "other"),
        (0, ("snapshots", 0, "battery_percent"), 101),
        (0, ("snapshots", 0, "battery_percent"), -1),
        (0, ("snapshots", 0, "mission_time_s"), 1),
        (0, ("snapshots", 0, "sequence_number"), 1),
        (0, ("snapshots", 2, "sequence_number"), 3),
        (0, ("snapshots", 2, "sequence_number"), 2.5),
        (0, ("snapshots", 2, "mission_time_s"), 1),
        (0, ("snapshots", 2, "mission_time_s"), 2.01),
        (0, ("snapshots", 2, "position_ned_m"), [0, 1, -1]),
        (0, ("snapshots", 0, "velocity_ned_mps"), [0, 0, 1]),
        (0, ("snapshots", 3, "position_ned_m"), [2, 0, -1]),
        (0, ("snapshots", 1, "battery_percent"), 99.7),
        (0, ("snapshots", 5, "position_ned_m"), [0, 0, -1]),
        (0, ("snapshots", 5, "velocity_ned_mps"), [0, 0, 1]),
        (0, ("artifact_version",), "2.0.0"),
        (1, ("artifact_version",), "1.0.0"),
        (1, ("scenario", "seed"), 43),
        (0, ("scenario", "seed"), -1),
        (0, ("scenario", "seed"), 0.5),
        (0, ("scenario", "seed"), True),
        (0, ("scenario", "generated_at"), "today"),
        (0, ("scenario", "config", "sample_rate_hz"), 2),
        (0, ("scenario", "config", "sample_interval_s"), 0.5),
        (1, ("phases", 0, "name"), "hover"),
        (1, ("phases", 1, "start_time_s"), 1.1),
        (1, ("phases", 1, "end_time_s"), 1.9),
        (1, ("terminal_time_s",), 4),
        (1, ("phases", 1, "start_sequence_number"), DELETE),
        (1, ("phases", 1, "start_sequence_number"), -1),
        (1, ("phases", 1, "start_sequence_number"), 1.5),
        (1, ("phases", 1, "start_sequence_number"), 2),
        (1, ("phases", 2, "start_sequence_number"), 0),
        (1, ("phases", 4, "start_sequence_number"), 6),
    ],
    ids=[
        "FR004-phase-leak",
        "FR004-six-fields",
        "FR007-position-vector",
        "FR008-velocity-vector",
        "FR005-single-vehicle",
        "FR009-battery-over",
        "FR009-battery-under",
        "FR006-time-origin",
        "FR006-sequence-origin",
        "FR006-sequence-gap",
        "FR006-integer-sequence",
        "FR006-time-order",
        "FR006-off-grid-time",
        "FR007-east",
        "FR008-ned-sign",
        "FR007-north-path",
        "FR009-linear-drain",
        "FR007-terminal-position",
        "FR008-terminal-velocity",
        "FR011-telemetry-version",
        "FR010-legacy-truth",
        "FR011-pair-source",
        "FR011-negative-seed",
        "FR011-integer-seed",
        "FR011-boolean-seed",
        "FR011-run-metadata",
        "FR006-rate-metadata",
        "FR006-interval-metadata",
        "FR010-phase-order",
        "FR010-phase-gap",
        "FR010-phase-end",
        "FR010-terminal-time",
        "FR010-missing-sequence-boundary",
        "FR010-negative-sequence-boundary",
        "FR010-integer-sequence-boundary",
        "FR010-wrong-sequence-boundary",
        "FR010-unordered-sequence-boundary",
        "FR010-out-of-range-sequence-boundary",
    ],
)
def test_FR017_reject_artifact_violations(artifact_pair, side, path, value):
    set_path(artifact_pair[side], path, value)
    with pytest.raises(ArtifactValidationError):
        validate_pair(*artifact_pair)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_FR017_nonfinite_vectors_and_source(artifact_pair, value):
    artifact_pair[0]["snapshots"][0]["position_ned_m"][0] = value
    with pytest.raises(ArtifactValidationError):
        validate_pair(*artifact_pair)
    artifact_pair[0]["snapshots"][0]["position_ned_m"][0] = 0
    for document in artifact_pair:
        document["scenario"]["config"]["hover_duration_s"] = value
    with pytest.raises(ArtifactValidationError):
        validate_pair(*artifact_pair)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_FR017_decode_rejects_nonfinite_json(token):
    with pytest.raises(ArtifactValidationError):
        decode_json('{"number":' + token + "}")


def test_FR017_overflow_number_cannot_bypass_validation(artifact_pair):
    artifact_pair[0]["snapshots"][1]["mission_time_s"] = decode_json(
        '{"number":1e309}'
    )["number"]
    with pytest.raises(ArtifactValidationError):
        validate_pair(*artifact_pair)


@pytest.mark.parametrize("mode", ["missing-tick", "extra-tick", "four-phases"])
def test_FR010_exact_terminal_count_and_five_phases(artifact_pair, mode):
    if mode == "missing-tick":
        artifact_pair[0]["snapshots"].pop()
    elif mode == "extra-tick":
        artifact_pair[0]["snapshots"].append(
            deepcopy(artifact_pair[0]["snapshots"][-1])
        )
    else:
        artifact_pair[1]["phases"].pop()
    with pytest.raises(ArtifactValidationError):
        validate_pair(*artifact_pair)


def three_hz_pair(artifact_pair):
    # Literal states: this table never calls a generator or the target quantizer.
    states = [
        (0, 0, 0, -1, 100),
        (0.333333, 0, -0.333333, -1, 99.933333),
        (0.666667, 0, -0.666667, -1, 99.866667),
        (1, 0, -1, 0, 99.8),
        (1.333333, 0, -1, 0, 99.733333),
        (1.666667, 0, -1, 0, 99.666667),
        (2, 0, -1, 3, 99.6),
        (2.333333, 1, -1, 3, 99.533333),
        (2.666667, 2, -1, 3, 99.466667),
        (3, 3, -1, -3, 99.4),
        (3.333333, 2, -1, -3, 99.333333),
        (3.666667, 1, -1, -3, 99.266667),
        (4, 0, -1, 1, 99.2),
        (4.333333, 0, -0.666667, 1, 99.133333),
        (4.666667, 0, -0.333333, 1, 99.066667),
        (5, 0, 0, 0, 99),
    ]
    for document in artifact_pair:
        document["scenario"]["config"].update(
            northbound_distance_m=3,
            cruise_speed_mps=3,
            sample_rate_hz=3,
            sample_interval_s=Decimal("0.333333"),
        )
    artifact_pair[0]["snapshots"] = [
        {
            "vehicle_id": "vehicle-001",
            "sequence_number": k,
            "mission_time_s": time,
            "position_ned_m": [north, 0, down],
            "velocity_ned_mps": [speed, 0, 0] if 6 <= k < 12 else [0, 0, speed],
            "battery_percent": battery,
        }
        for k, (time, north, down, speed, battery) in enumerate(states)
    ]
    for phase, boundary in zip(artifact_pair[1]["phases"], [0, 3, 6, 9, 12]):
        phase["start_sequence_number"] = boundary
    return artifact_pair


def test_FR006_three_hz_exact_grid(artifact_pair):
    telemetry, truth = validate_pair(*three_hz_pair(artifact_pair))
    assert len(telemetry.snapshots) == 16
    assert [snapshot.mission_time_s for snapshot in telemetry.snapshots[:4]] == [
        0,
        0.333333,
        0.666667,
        1,
    ]
    assert telemetry.snapshots[-1].mission_time_s == 5
    assert truth.terminal_time_s == 5


def test_FR006_rounded_interval_accumulation_rejected(artifact_pair):
    pair = three_hz_pair(artifact_pair)
    pair[0]["snapshots"][2]["mission_time_s"] = Decimal("0.666666")
    pair[0]["snapshots"][-1]["mission_time_s"] = Decimal("4.999995")
    with pytest.raises(ArtifactValidationError):
        validate_pair(*pair)


@pytest.mark.parametrize("hover", [Decimal("1.05"), Decimal("1.0000004")])
def test_FR006_unrounded_terminal_alignment(artifact_pair, hover):
    for document in artifact_pair:
        document["scenario"]["config"]["hover_duration_s"] = hover
    with pytest.raises(ArtifactValidationError, match="terminal.*align"):
        validate_pair(*artifact_pair)


def a1_pair(artifact_pair):
    states = [
        (0, 0, 0, [0, 0, -1], 100),
        (0.333333, 0, -0.333333, [0, 0, -1], 99.933333),
        (0.666667, 0, -0.333333, [0, 0, 0], 99.866667),
        (1, 0, -0.333333, [3, 0, 0], 99.8),
        (1.333333, 1, -0.333333, [3, 0, 0], 99.733333),
        (1.666667, 2, -0.333333, [3, 0, 0], 99.666667),
        (2, 3, -0.333333, [-3, 0, 0], 99.6),
        (2.333333, 2, -0.333333, [-3, 0, 0], 99.533333),
        (2.666667, 1, -0.333333, [-3, 0, 0], 99.466667),
        (3, 0, -0.333333, [0, 0, 0.333333], 99.4),
        (3.333333, 0, -0.222222, [0, 0, 0.333333], 99.333333),
        (3.666667, 0, -0.111111, [0, 0, 0.333333], 99.266667),
        (4, 0, 0, [0, 0, 0], 99.2),
    ]
    for document in artifact_pair:
        document["scenario"]["config"].update(
            target_altitude_m=Decimal("0.3333334"),
            hover_duration_s=Decimal("0.6666666"),
            northbound_distance_m=3,
            cruise_speed_mps=3,
            descent_rate_mps=Decimal("0.3333334"),
            sample_rate_hz=3,
            sample_interval_s=Decimal("0.333333"),
        )
    artifact_pair[0]["snapshots"] = [
        {
            "vehicle_id": "vehicle-001",
            "sequence_number": k,
            "mission_time_s": time,
            "position_ned_m": [north, 0, down],
            "velocity_ned_mps": velocity,
            "battery_percent": battery,
        }
        for k, (time, north, down, velocity, battery) in enumerate(states)
    ]
    artifact_pair[1]["terminal_time_s"] = 4
    for phase, start, end, boundary in zip(
        artifact_pair[1]["phases"],
        [0, 0.333333, 1, 2, 3],
        [0.333333, 1, 2, 3, 4],
        [0, 2, 3, 6, 9],
    ):
        phase.update(start_time_s=start, end_time_s=end, start_sequence_number=boundary)
    return artifact_pair


def test_FR010_A1_exact_sequence_ownership(artifact_pair):
    telemetry, truth = validate_pair(*a1_pair(artifact_pair))
    assert [phase.start_sequence_number for phase in truth.phases] == [0, 2, 3, 6, 9]
    assert telemetry.snapshots[1].mission_time_s == truth.phases[1].start_time_s
    assert telemetry.snapshots[1].velocity_ned_mps == (0, 0, -1)
    assert telemetry.snapshots[2].velocity_ned_mps == (0, 0, 0)
    assert telemetry.snapshots[12].velocity_ned_mps == (0, 0, 0)
    ownership = [
        next(
            phase.name
            for phase in reversed(truth.phases)
            if phase.start_sequence_number <= k
        )
        for k in [1, 2, 12]
    ]
    assert ownership == ["takeoff", "hover", "landing"]


def test_FR010_A1_rounded_boundary_rejected(artifact_pair):
    pair = a1_pair(artifact_pair)
    pair[1]["phases"][1]["start_sequence_number"] = 1
    with pytest.raises(ArtifactValidationError):
        validate_pair(*pair)


def test_FR010_A1_rounded_time_motion_rejected(artifact_pair):
    pair = a1_pair(artifact_pair)
    pair[0]["snapshots"][1]["velocity_ned_mps"] = [0, 0, 0]
    with pytest.raises(ArtifactValidationError):
        validate_pair(*pair)


def test_FR010_empty_phase_and_terminal_ownership(artifact_pair):
    for document in artifact_pair:
        document["scenario"]["config"]["hover_duration_s"] = 0
    artifact_pair[0]["snapshots"].pop(1)
    for snapshot, sequence, time, battery in zip(
        artifact_pair[0]["snapshots"],
        [0, 1, 2, 3, 4],
        [0, 1, 2, 3, 4],
        [100, 99.8, 99.6, 99.4, 99.2],
    ):
        snapshot.update(
            sequence_number=sequence, mission_time_s=time, battery_percent=battery
        )
    for phase, start, end, boundary in zip(
        artifact_pair[1]["phases"], [0, 1, 1, 2, 3], [1, 1, 2, 3, 4], [0, 1, 1, 2, 3]
    ):
        phase.update(start_time_s=start, end_time_s=end, start_sequence_number=boundary)
    artifact_pair[1]["terminal_time_s"] = 4
    telemetry, truth = validate_pair(*artifact_pair)
    assert (
        truth.phases[1].start_sequence_number == truth.phases[2].start_sequence_number
    )
    assert telemetry.snapshots[1].velocity_ned_mps == (1, 0, 0)
    assert truth.phases[-1].name == "landing"


def test_FR017_committed_schema_registry_is_offline(artifact_pair, monkeypatch):
    import socket

    def no_network(*args, **kwargs):
        pytest.fail("schema references must resolve from committed local schemas")

    monkeypatch.setattr(socket, "create_connection", no_network)
    validate_pair(*artifact_pair)


def test_FR006_shared_exact_source_arithmetic(artifact_pair):
    config = a1_pair(artifact_pair)[0]["scenario"]["config"]
    config.pop("sample_rate_hz")
    config.pop("sample_interval_s")
    assert exact_number(0.2) == Fraction(1, 5)
    assert source_timeline(config) == (
        Fraction(3),
        Fraction(1, 3),
        (
            Fraction(0),
            Fraction(1666667, 5_000_000),
            Fraction(1),
            Fraction(2),
            Fraction(3),
            Fraction(4),
        ),
        12,
    )
    assert config["target_altitude_m"] == Decimal("0.3333334")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_altitude_m", 0),
        ("climb_rate_mps", -1),
        ("hover_duration_s", -1),
        ("northbound_distance_m", 0),
        ("cruise_speed_mps", 0),
        ("descent_rate_mps", 0),
        ("observation_spacing_m", 0),
        ("initial_battery_percent", 101),
        ("battery_drain_percent_per_s", -1),
        ("battery_drain_percent_per_s", 21),
        ("observation_spacing_m", Decimal("0.0000001")),
        ("observation_spacing_m", Decimal("10000000")),
        ("observation_spacing_m", Decimal("0.0000008")),
    ],
    ids=[
        "FR001-altitude",
        "FR001-climb",
        "FR001-hover",
        "FR001-distance",
        "FR001-cruise",
        "FR001-descent",
        "FR001-spacing",
        "FR009-initial",
        "FR009-drain",
        "FR009-exhausted",
        "FR006-zero-rounded-interval",
        "FR006-zero-rounded-rate",
        "FR006-colliding-published-times",
    ],
)
def test_FR001_shared_source_prevalidation(artifact_pair, field, value):
    config = artifact_pair[0]["scenario"]["config"]
    config[field] = value
    with pytest.raises(ArtifactValidationError):
        source_timeline(config)


@pytest.mark.parametrize("field", ["sample_rate_hz", "sample_interval_s"])
def test_FR006_matching_pair_with_wrong_rounded_metadata(artifact_pair, field):
    for document in artifact_pair:
        document["scenario"]["config"][field] = 2
    with pytest.raises(ArtifactValidationError, match=field):
        validate_pair(*artifact_pair)


@pytest.mark.parametrize("field", ["sample_rate_hz", "sample_interval_s"])
def test_FR011_pair_source_equality_precedes_quantization(artifact_pair, field):
    artifact_pair[1]["scenario"]["config"][field] = Decimal("1.0000001")
    with pytest.raises(ArtifactValidationError):
        validate_pair(*artifact_pair)


@pytest.mark.parametrize("hover", [Decimal("5.05"), Decimal("5.0000004")])
def test_FR006_ten_hz_unrounded_terminal_alignment(artifact_pair, hover):
    for document in artifact_pair:
        document["scenario"]["config"].update(
            target_altitude_m=10,
            hover_duration_s=hover,
            northbound_distance_m=20,
            cruise_speed_mps=2,
            observation_spacing_m=Decimal("0.2"),
            sample_rate_hz=10,
            sample_interval_s=Decimal("0.1"),
        )
    with pytest.raises(ArtifactValidationError, match="terminal.*align"):
        validate_pair(*artifact_pair)
