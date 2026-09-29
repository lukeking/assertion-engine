# 001: M0 Telemetry Simulator boundaries

**Status:** Accepted

**Date:** 2026-09-29

## Context

M0 must produce a basic normal telemetry trajectory without prematurely designing the DSL,
building sensor fusion, or claiming physical fidelity it has not measured. The simulator also
serves the project's learning path: a textual requirement must remain traceable through generated
events, rendered playback, and automated evidence.

## Decision

### Event contract

M0 emits one vehicle's state-level telemetry as complete snapshots. Each snapshot contains:

- `vehicle_id`
- `sequence_number`
- `mission_time_s`
- `position_ned_m = (north, east, down)`
- `velocity_ned_mps = (north, east, down)`
- `battery_percent`

The local NED origin is the takeoff point. Flight above that point therefore has a negative
`down` coordinate. Scalar speed is derived from the velocity vector and is not stored separately.
M0 generates one vehicle, but retains `vehicle_id`; cross-vehicle rules and coordination remain
out of scope.

Snapshots represent an upstream state estimate, not raw GPS, IMU, voltage, or current readings.
Sensor fusion and source-specific adapters remain outside M0. A future adapter may normalize
formats, units, and coordinate frames, but must not silently smooth, interpolate, or replace the
event's observation time.

### Scenario and evidence

The first normal scenario performs takeoff, hover, northbound flight, return, and landing. Scenario
phase labels are ground truth for generation, verification, and visual annotation; they are not
telemetry fields and must not leak the expected answer to the Assertion Engine.

Generation and playback are separate:

1. A scenario configuration deterministically produces an immutable event artifact.
2. Visual playback reads the completed artifact and never recomputes motion or battery state.
3. A future replayer will feed the same artifact through ingestion and evaluation.
4. Scenario ground truth is stored separately from telemetry events.

Playback speed, pause, and stepping do not alter `mission_time_s`.

### Sampling and battery

Sampling rate is configurable and derived from scenario motion and the desired observation
resolution. The initial baseline is 2 m/s with 0.2 m between observations, yielding 10 Hz. Higher
rates may later exercise engine tail latency even when they oversample the flight path. No single
rate is asserted as universally correct.

M0 uses a deterministic linear aggregate battery model with configurable initial percentage and
drain per second. It represents an upstream remaining-capacity estimate and makes no claim about
battery chemistry, sensor noise, estimator behavior, or phase-specific power consumption.

### Practical-validation ladder

The three drone capability projects use this evidence ladder:

1. A deterministic project-owned simulator establishes software behavior.
2. PX4 SITL checks assumptions against a real flight stack and richer simulation.
3. Real flight logs expose actual rates, noise, gaps, and estimator behavior.
4. Hardware is introduced only when a concrete question cannot be answered by the earlier levels.

Industry convention is external evidence, not automatic truth. Compatibility requirements become
hard constraints only when the project actually integrates with that system.

## Latency boundary

Future latency claims distinguish:

- input age: engine receipt time minus observation time;
- engine latency: alert time minus engine receipt time;
- end-to-end detection latency: alert time minus observation time.

Only the end-to-end value supports a claim about real detection response. M0 preserves event time
but does not yet implement the ingestion, evaluator, or alert stages.

## Deferred

- The technology stack and parser strategy remain M0 plan decisions.
- The latency ladder remains unanchored beyond the initial 10 Hz scenario until measured evidence
  from the simulator, PX4 SITL, and logs exists.
- Sensor/estimator failures such as drift, delay, stuck values, and threshold-cliff battery
  estimates are later adversarial scenarios, not M0's normal trajectory.
- Physical sensor loading and detailed energy models are omitted until their magnitude matters to
  a stated acceptance target.

## Revisit when

- a real PX4 or ROS telemetry source is integrated;
- multi-vehicle assertions enter scope;
- real logs invalidate the event fields or sampling assumptions;
- a requirement depends on raw sensor behavior rather than estimated vehicle state.

## References

- [PX4 coordinate frames](https://docs.px4.io/main/en/ros/external_position_estimation)
- [PX4 simulation](https://docs.px4.io/main/en/simulation/)
- [PX4 battery estimation](https://docs.px4.io/main/en/config/battery)
