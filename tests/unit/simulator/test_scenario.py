"""FR-002–011: literal motion and phase oracles independent of the validator."""

from dataclasses import fields
from decimal import Decimal

import pytest

from assertion_engine.artifacts import canonical_bytes, decode_json
from assertion_engine.simulator.scenario import generate
from assertion_engine.telemetry import ScenarioSource, TelemetryArtifact


def source(**overrides):
    return ScenarioSource(
        "normal-flight",
        "1.0.0",
        42,
        {
            "schema_version": "1.0.0",
            "vehicle_id": "vehicle-001",
            "target_altitude_m": 10,
            "climb_rate_mps": 1,
            "hover_duration_s": 5,
            "northbound_distance_m": 20,
            "cruise_speed_mps": 2,
            "descent_rate_mps": 1,
            "observation_spacing_m": Decimal("0.2"),
            "initial_battery_percent": 100,
            "battery_drain_percent_per_s": Decimal("0.2"),
            "sample_rate_hz": 10,
            "sample_interval_s": Decimal("0.1"),
            **overrides,
        },
    )


def snapshots(telemetry):
    assert isinstance(telemetry, TelemetryArtifact)
    return telemetry.snapshots


def test_FR002_baseline_literal_states_and_half_open_boundaries():
    telemetry, truth = generate(source())
    states = snapshots(telemetry)
    assert len(states) == 451
    assert [field.name for field in fields(states[0])] == [
        "vehicle_id",
        "sequence_number",
        "mission_time_s",
        "position_ned_m",
        "velocity_ned_mps",
        "battery_percent",
    ]
    for index, time, position, velocity, battery in [
        (0, 0, (0, 0, 0), (0, 0, -1), 100),
        (99, Decimal("9.9"), (0, 0, Decimal("-9.9")), (0, 0, -1), Decimal("98.02")),
        (100, 10, (0, 0, -10), (0, 0, 0), 98),
        (149, Decimal("14.9"), (0, 0, -10), (0, 0, 0), Decimal("97.02")),
        (150, 15, (0, 0, -10), (2, 0, 0), 97),
        (249, Decimal("24.9"), (Decimal("19.8"), 0, -10), (2, 0, 0), Decimal("95.02")),
        (250, 25, (20, 0, -10), (-2, 0, 0), 95),
        (349, Decimal("34.9"), (Decimal("0.2"), 0, -10), (-2, 0, 0), Decimal("93.02")),
        (350, 35, (0, 0, -10), (0, 0, 1), 93),
        (449, Decimal("44.9"), (0, 0, Decimal("-0.1")), (0, 0, 1), Decimal("91.02")),
        (450, 45, (0, 0, 0), (0, 0, 0), 91),
    ]:
        snapshot = states[index]
        assert snapshot.sequence_number == index
        assert snapshot.vehicle_id == "vehicle-001"
        assert (
            snapshot.mission_time_s,
            snapshot.position_ned_m,
            snapshot.velocity_ned_mps,
            snapshot.battery_percent,
        ) == (
            time,
            position,
            velocity,
            battery,
        )
    assert [
        (phase.name, phase.start_time_s, phase.end_time_s, phase.start_sequence_number)
        for phase in truth.phases
    ] == [
        ("takeoff", 0, 10, 0),
        ("hover", 10, 15, 100),
        ("northbound", 15, 25, 150),
        ("return", 25, 35, 250),
        ("landing", 35, 45, 350),
    ]
    assert telemetry.scenario == truth.scenario == source()
    assert telemetry.artifact_version == "1.0.0"
    assert truth.artifact_version == "2.0.0"


@pytest.mark.parametrize(
    ("spacing", "rate", "interval", "count", "boundaries"),
    [
        ("0.2", 10, "0.1", 451, [0, 100, 150, 250, 350]),
        ("0.1", 20, "0.05", 901, [0, 200, 300, 500, 700]),
        ("0.04", 50, "0.02", 2251, [0, 500, 750, 1250, 1750]),
        ("0.02", 100, "0.01", 4501, [0, 1000, 1500, 2500, 3500]),
    ],
)
def test_FR003_four_supported_rates(spacing, rate, interval, count, boundaries):
    telemetry, truth = generate(
        source(
            observation_spacing_m=Decimal(spacing),
            sample_rate_hz=rate,
            sample_interval_s=Decimal(interval),
        )
    )
    states = snapshots(telemetry)
    assert len(states) == count
    assert [phase.start_sequence_number for phase in truth.phases] == boundaries
    assert [snapshot.sequence_number for snapshot in states] == list(range(count))
    assert states[1].mission_time_s == Decimal(interval)
    assert all(a.mission_time_s < b.mission_time_s for a, b in zip(states, states[1:]))
    assert (
        states[-1].mission_time_s,
        states[-1].position_ned_m,
        states[-1].velocity_ned_mps,
        states[-1].battery_percent,
    ) == (
        45,
        (0, 0, 0),
        (0, 0, 0),
        91,
    )


def test_FR006_three_hz_all_literal_snapshots():
    telemetry, truth = generate(
        source(
            target_altitude_m=1,
            hover_duration_s=1,
            northbound_distance_m=3,
            cruise_speed_mps=3,
            observation_spacing_m=1,
            sample_rate_hz=3,
            sample_interval_s=Decimal("0.333333"),
        )
    )
    states = snapshots(telemetry)
    assert len(states) == 16
    # No generator or production quantizer supplies this oracle.
    expected = [
        ("0", "0", "0", (0, 0, -1), "100"),
        ("0.333333", "0", "-0.333333", (0, 0, -1), "99.933333"),
        ("0.666667", "0", "-0.666667", (0, 0, -1), "99.866667"),
        ("1", "0", "-1", (0, 0, 0), "99.8"),
        ("1.333333", "0", "-1", (0, 0, 0), "99.733333"),
        ("1.666667", "0", "-1", (0, 0, 0), "99.666667"),
        ("2", "0", "-1", (3, 0, 0), "99.6"),
        ("2.333333", "1", "-1", (3, 0, 0), "99.533333"),
        ("2.666667", "2", "-1", (3, 0, 0), "99.466667"),
        ("3", "3", "-1", (-3, 0, 0), "99.4"),
        ("3.333333", "2", "-1", (-3, 0, 0), "99.333333"),
        ("3.666667", "1", "-1", (-3, 0, 0), "99.266667"),
        ("4", "0", "-1", (0, 0, 1), "99.2"),
        ("4.333333", "0", "-0.666667", (0, 0, 1), "99.133333"),
        ("4.666667", "0", "-0.333333", (0, 0, 1), "99.066667"),
        ("5", "0", "0", (0, 0, 0), "99"),
    ]
    assert [
        (s.mission_time_s, s.position_ned_m, s.velocity_ned_mps, s.battery_percent)
        for s in states
    ] == [
        (Decimal(time), (Decimal(north), 0, Decimal(down)), velocity, Decimal(battery))
        for time, north, down, velocity, battery in expected
    ]
    assert [phase.start_sequence_number for phase in truth.phases] == [0, 3, 6, 9, 12]
    assert truth.terminal_time_s == 5


def test_FR010_A1_sequence_boundaries_precede_time_quantization():
    telemetry, truth = generate(
        source(
            target_altitude_m=Decimal("0.3333334"),
            hover_duration_s=Decimal("0.6666666"),
            northbound_distance_m=3,
            cruise_speed_mps=3,
            descent_rate_mps=Decimal("0.3333334"),
            observation_spacing_m=1,
            sample_rate_hz=3,
            sample_interval_s=Decimal("0.333333"),
        )
    )
    states = snapshots(telemetry)
    assert len(states) == 13
    assert [phase.start_sequence_number for phase in truth.phases] == [0, 2, 3, 6, 9]
    assert (
        states[1].mission_time_s == truth.phases[1].start_time_s == Decimal("0.333333")
    )
    assert states[1].velocity_ned_mps == (0, 0, -1)
    assert states[2].velocity_ned_mps == (0, 0, 0)
    assert states[3].velocity_ned_mps == (3, 0, 0)
    assert states[9].velocity_ned_mps == (0, 0, Decimal("0.333333"))
    assert states[12].mission_time_s == 4
    assert states[12].velocity_ned_mps == (0, 0, 0)
    assert [
        next(p.name for p in reversed(truth.phases) if p.start_sequence_number <= k)
        for k in (1, 2, 12)
    ] == [
        "takeoff",
        "hover",
        "landing",
    ]
    data = decode_json(canonical_bytes(telemetry))
    assert data["scenario"]["config"]["target_altitude_m"] == Decimal("0.3333334")


@pytest.mark.parametrize(
    ("hover", "altitude", "descent", "boundaries", "tick1_velocity"),
    [
        (0, 1, 1, [0, 1, 1, 2, 3], (1, 0, 0)),
        (Decimal("0.1"), Decimal("0.2"), Decimal("0.2"), [0, 1, 1, 2, 3], (1, 0, 0)),
    ],
)
def test_FR010_zero_and_unsampled_hover(
    hover, altitude, descent, boundaries, tick1_velocity
):
    # Second mission starts phases at 0,.2,.3,1.65,3 and ends at 4;
    # the nonzero hover interval contains no tick on its 1 Hz grid.
    distance = 1 if hover == 0 else Decimal("1.35")
    telemetry, truth = generate(
        source(
            target_altitude_m=altitude,
            hover_duration_s=hover,
            northbound_distance_m=distance,
            cruise_speed_mps=1,
            descent_rate_mps=descent,
            observation_spacing_m=1,
            sample_rate_hz=1,
            sample_interval_s=1,
        )
    )
    states = snapshots(telemetry)
    assert len(states) == 5
    assert [phase.start_sequence_number for phase in truth.phases] == boundaries
    assert len(truth.phases) == 5
    if hover == 0:
        assert truth.phases[1].start_time_s == truth.phases[1].end_time_s == 1
    else:
        assert (truth.phases[1].start_time_s, truth.phases[1].end_time_s) == (
            Decimal("0.2"),
            Decimal("0.3"),
        )
    assert states[1].velocity_ned_mps == tick1_velocity
    assert states[-1].position_ned_m == (0, 0, 0)
    assert states[-1].velocity_ned_mps == (0, 0, 0)


def test_FR006_motion_uses_exact_time_and_rounds_ties_even():
    telemetry, _ = generate(
        source(
            target_altitude_m=Decimal("0.0000025"),
            climb_rate_mps=Decimal("0.0000025"),
            hover_duration_s=1,
            northbound_distance_m=1,
            cruise_speed_mps=1,
            descent_rate_mps=Decimal("0.0000025"),
            observation_spacing_m=1,
            sample_rate_hz=1,
            sample_interval_s=1,
            battery_drain_percent_per_s=Decimal("0.0000005"),
        )
    )
    states = snapshots(telemetry)
    assert len(states) == 6
    assert states[1].position_ned_m == (0, 0, Decimal("-0.000002"))
    assert states[1].battery_percent == 100
    assert states[3].battery_percent == Decimal("99.999998")
