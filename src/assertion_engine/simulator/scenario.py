"""Deterministic state estimates for the five normal-flight segments.

See docs/algorithms/001-m0-telemetry-and-playback.md §1–§2: each tick asks
where a constant-velocity segment is, without advancing a rounded previous
position. Exact t=k*interval and source phase endpoints determine N/E/D motion
and battery; snapshots save Q(values), phases save Q(times) and ceil(start*rate).
The generator's motion branches are independent of artifact validation.
"""

from math import ceil

from assertion_engine.artifacts import (
    PHASE_NAMES,
    exact_number,
    quantize,
    source_timeline,
)
from assertion_engine.telemetry import (
    GroundTruthArtifact,
    PhaseInterval,
    ScenarioSource,
    TelemetryArtifact,
    TelemetrySnapshot,
)


def generate(source: ScenarioSource) -> tuple[TelemetryArtifact, GroundTruthArtifact]:
    """Generate both endpoints and keep ground-truth labels out of snapshots."""
    config = source.config
    rate, interval, starts, terminal_tick = source_timeline(config)
    altitude = exact_number(config["target_altitude_m"])
    climb = exact_number(config["climb_rate_mps"])
    descent = exact_number(config["descent_rate_mps"])
    distance = exact_number(config["northbound_distance_m"])
    speed = exact_number(config["cruise_speed_mps"])
    battery = exact_number(config["initial_battery_percent"])
    drain = exact_number(config["battery_drain_percent_per_s"])
    snapshots = []
    for k in range(terminal_tick + 1):
        time = k * interval
        if k == terminal_tick:
            position, velocity = (0, 0, 0), (0, 0, 0)
        elif time < starts[1]:
            position, velocity = (0, 0, -climb * time), (0, 0, -climb)
        elif time < starts[2]:
            position, velocity = (0, 0, -altitude), (0, 0, 0)
        elif time < starts[3]:
            position = (speed * (time - starts[2]), 0, -altitude)
            velocity = (speed, 0, 0)
        elif time < starts[4]:
            position = (distance - speed * (time - starts[3]), 0, -altitude)
            velocity = (-speed, 0, 0)
        else:
            position = (0, 0, -altitude + descent * (time - starts[4]))
            velocity = (0, 0, descent)
        snapshots.append(
            TelemetrySnapshot(
                vehicle_id=config["vehicle_id"],
                sequence_number=k,
                mission_time_s=quantize(time),
                position_ned_m=tuple(quantize(axis) for axis in position),
                velocity_ned_mps=tuple(quantize(axis) for axis in velocity),
                battery_percent=quantize(battery - drain * time),
            )
        )
    phases = tuple(
        PhaseInterval(
            name=name,
            start_time_s=quantize(starts[i]),
            end_time_s=quantize(starts[i + 1]),
            start_sequence_number=ceil(starts[i] * rate),
        )
        for i, name in enumerate(PHASE_NAMES)
    )
    return (
        TelemetryArtifact(source, tuple(snapshots)),
        GroundTruthArtifact(source, quantize(starts[-1]), phases),
    )
