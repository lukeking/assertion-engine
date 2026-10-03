"""FR-014/SC-004: playback reads literal events; controls change viewing time."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal

import pytest

from assertion_engine.artifacts import validate_pair
from assertion_engine.playback.view_model import PlaybackSession


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def a1_literal_pair(pair):
    """Independent A1 table: no generator or timeline computation."""
    pair = deepcopy(pair)
    states = [
        ("0", 0, "0", [0, 0, -1], "100"),
        ("0.333333", 0, "-0.333333", [0, 0, -1], "99.933333"),
        ("0.666667", 0, "-0.333333", [0, 0, 0], "99.866667"),
        ("1", 0, "-0.333333", [3, 0, 0], "99.8"),
        ("1.333333", 1, "-0.333333", [3, 0, 0], "99.733333"),
        ("1.666667", 2, "-0.333333", [3, 0, 0], "99.666667"),
        ("2", 3, "-0.333333", [-3, 0, 0], "99.6"),
        ("2.333333", 2, "-0.333333", [-3, 0, 0], "99.533333"),
        ("2.666667", 1, "-0.333333", [-3, 0, 0], "99.466667"),
        ("3", 0, "-0.333333", [0, 0, Decimal("0.333333")], "99.4"),
        ("3.333333", 0, "-0.222222", [0, 0, Decimal("0.333333")], "99.333333"),
        ("3.666667", 0, "-0.111111", [0, 0, Decimal("0.333333")], "99.266667"),
        ("4", 0, "0", [0, 0, 0], "99.2"),
    ]
    for document in pair:
        document["scenario"]["config"].update(
            target_altitude_m=Decimal("0.3333334"),
            hover_duration_s=Decimal("0.6666666"),
            northbound_distance_m=3,
            cruise_speed_mps=3,
            descent_rate_mps=Decimal("0.3333334"),
            sample_rate_hz=3,
            sample_interval_s=Decimal("0.333333"),
        )
    pair[0]["snapshots"] = [
        {
            "vehicle_id": "vehicle-001",
            "sequence_number": k,
            "mission_time_s": Decimal(time),
            "position_ned_m": [north, 0, Decimal(down)],
            "velocity_ned_mps": velocity,
            "battery_percent": Decimal(battery),
        }
        for k, (time, north, down, velocity, battery) in enumerate(states)
    ]
    pair[1]["terminal_time_s"] = 4
    for phase, start, end, boundary in zip(
        pair[1]["phases"],
        ["0", "0.333333", "1", "2", "3"],
        ["0.333333", "1", "2", "3", "4"],
        [0, 2, 3, 6, 9],
    ):
        phase.update(
            start_time_s=Decimal(start),
            end_time_s=Decimal(end),
            start_sequence_number=boundary,
        )
    return validate_pair(*pair)


def test_controls_preserve_partial_cadence_and_terminal(artifact_pair):
    clock = Clock()
    pair = validate_pair(*artifact_pair)
    session = PlaybackSession(*pair, clock=clock)
    assert (session.state, session.cursor, session.speed) == ("ready", 0, 1.0)
    session.play()
    clock.advance(0.4)
    session.pause()
    assert (session.state, session.cursor) == ("paused", 0)
    clock.advance(100)
    session.tick()
    assert session.cursor == 0
    session.play()
    clock.advance(0.3)
    session.set_speed(2)
    clock.advance(0.16)
    session.tick()
    assert session.cursor == 1  # 0.4 + 0.3 + 0.16*2; no lost partial frame.
    assert session.snapshot.mission_time_s == 1
    session.pause()
    session.step()
    assert (session.state, session.cursor) == ("paused", 2)
    session.restart()
    assert (session.state, session.cursor, session.speed) == ("ready", 0, 2)
    session.play()
    clock.advance(10)
    session.tick()
    assert (session.state, session.cursor) == ("completed", 5)
    assert session.snapshot is pair[0].snapshots[-1]
    session.play()
    session.pause()
    session.step()
    clock.advance(10)
    session.tick()
    assert (session.state, session.cursor) == ("completed", 5)
    session.restart()
    assert session.cursor == 0
    assert session.telemetry is pair[0]
    assert session.ground_truth is pair[1]


def test_pause_settles_elapsed_time_and_step_is_exactly_one(artifact_pair):
    clock = Clock()
    session = PlaybackSession(*validate_pair(*artifact_pair), clock=clock)
    session.play()
    clock.advance(1.2)
    session.pause()
    assert session.cursor == 1
    session.play()
    session.step()
    assert (session.cursor, session.state) == (2, "paused")
    clock.advance(20)
    session.tick()
    assert session.cursor == 2


@pytest.mark.parametrize("speed", [0, -1, float("inf"), float("nan")])
def test_speed_requires_positive_finite_value(artifact_pair, speed):
    pair = validate_pair(*artifact_pair)
    with pytest.raises(ValueError, match="speed"):
        PlaybackSession(*pair, speed=speed)
    session = PlaybackSession(*pair)
    with pytest.raises(ValueError, match="speed"):
        session.set_speed(speed)
    assert session.speed == 1


def test_display_only_derivations_and_original_mission_time(artifact_pair):
    telemetry, truth = validate_pair(*artifact_pair)
    # Derivation depends on event vector, including all three axes, not scenario motion.
    snapshot = replace(
        telemetry.snapshots[0],
        position_ned_m=(8, 4, -7),
        velocity_ned_mps=(2, 3, 6),
        mission_time_s=Decimal("0.123456"),
    )
    telemetry = replace(telemetry, snapshots=(snapshot, *telemetry.snapshots[1:]))
    session = PlaybackSession(telemetry, truth)
    assert session.altitude_m == 7
    assert session.scalar_speed_mps == 7
    assert session.snapshot.mission_time_s == Decimal("0.123456")
    assert session.snapshot.battery_percent == 100
    assert session.snapshot.position_ned_m == (8, 4, -7)


def test_A1_phase_ownership_uses_sequence_not_display_time(artifact_pair):
    pair = a1_literal_pair(artifact_pair)
    session = PlaybackSession(*pair)
    expected = [
        "takeoff",
        "takeoff",
        "hover",
        "northbound",
        "northbound",
        "northbound",
        "return",
        "return",
        "return",
        "landing",
        "landing",
        "landing",
        "landing",
    ]
    assert [phase.start_sequence_number for phase in pair[1].phases] == [0, 2, 3, 6, 9]
    for k, name in enumerate(expected):
        assert session.cursor == k
        assert session.phase.name == name
        assert session.snapshot is pair[0].snapshots[k]
        if k == 1:
            assert session.snapshot.mission_time_s == pair[1].phases[1].start_time_s
        session.step()
    assert session.state == "completed"


def test_same_boundary_empty_phase_and_terminal_multiple_starts(artifact_pair):
    # Literal one-second ticks: hover owns no snapshot when both starts are 1.
    pair = deepcopy(artifact_pair)
    for document in pair:
        document["scenario"]["config"]["hover_duration_s"] = 0
    pair[0]["snapshots"] = [
        {
            "vehicle_id": "vehicle-001",
            "sequence_number": k,
            "mission_time_s": k,
            "position_ned_m": position,
            "velocity_ned_mps": velocity,
            "battery_percent": Decimal(battery),
        }
        for k, position, velocity, battery in [
            (0, [0, 0, 0], [0, 0, -1], "100"),
            (1, [0, 0, -1], [1, 0, 0], "99.8"),
            (2, [1, 0, -1], [-1, 0, 0], "99.6"),
            (3, [0, 0, -1], [0, 0, 1], "99.4"),
            (4, [0, 0, 0], [0, 0, 0], "99.2"),
        ]
    ]
    pair[1]["terminal_time_s"] = 4
    for phase, start, end in zip(pair[1]["phases"], [0, 1, 1, 2, 3], [1, 1, 2, 3, 4]):
        phase.update(start_time_s=start, end_time_s=end, start_sequence_number=start)
    session = PlaybackSession(*validate_pair(*pair))
    session.step()
    assert session.phase.name == "northbound"

    # All positive motion phases can fall between 1 Hz ticks after a long hover.
    for document in pair:
        document["scenario"]["config"].update(
            target_altitude_m=Decimal("0.1"),
            hover_duration_s=Decimal("0.6"),
            northbound_distance_m=Decimal("0.1"),
        )
    pair[0]["snapshots"] = [
        {
            "vehicle_id": "vehicle-001",
            "sequence_number": 0,
            "mission_time_s": 0,
            "position_ned_m": [0, 0, 0],
            "velocity_ned_mps": [0, 0, -1],
            "battery_percent": 100,
        },
        {
            "vehicle_id": "vehicle-001",
            "sequence_number": 1,
            "mission_time_s": 1,
            "position_ned_m": [0, 0, 0],
            "velocity_ned_mps": [0, 0, 0],
            "battery_percent": Decimal("99.8"),
        },
    ]
    pair[1]["terminal_time_s"] = 1
    for phase, start, end, boundary in zip(
        pair[1]["phases"],
        [0, Decimal("0.1"), Decimal("0.7"), Decimal("0.8"), Decimal("0.9")],
        [Decimal("0.1"), Decimal("0.7"), Decimal("0.8"), Decimal("0.9"), 1],
        [0, 1, 1, 1, 1],
    ):
        phase.update(start_time_s=start, end_time_s=end, start_sequence_number=boundary)
    session = PlaybackSession(*validate_pair(*pair))
    session.step()
    assert session.state == "completed"
    assert session.phase.name == "landing"
