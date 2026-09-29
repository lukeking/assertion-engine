# Data Model: M0 Telemetry Simulator

## Overview

The model separates three responsibilities:

1. `ScenarioConfiguration` says what normal mission to generate.
2. `TelemetryArtifact` records only observable state snapshots.
3. `GroundTruthArtifact` records the expected phase timeline for tests and playback annotations.

Telemetry never contains a phase label. Playback joins the two artifacts by identical scenario source metadata and mission time; it never modifies either artifact.

## ScenarioConfiguration

Human-authored file: `scenarios/normal-flight.toml`.

| Field | Type | Baseline | Validation / meaning |
|---|---|---:|---|
| `schema_version` | string | `1.0.0` | Configuration contract version |
| `scenario_name` | string | `normal-flight` | Non-empty stable name |
| `scenario_version` | string | `1.0.0` | Bump when baseline semantics or values change |
| `seed` | integer | `42` | Explicit even when M0 uses no random disturbance |
| `vehicle_id` | string | `vehicle-001` | Non-empty; identical in every snapshot |
| `target_altitude_m` | decimal | `10.0` | Greater than 0; NED `down = -10.0` at altitude |
| `climb_rate_mps` | decimal | `1.0` | Greater than 0 |
| `hover_duration_s` | decimal | `5.0` | Greater than or equal to 0 |
| `northbound_distance_m` | decimal | `20.0` | Greater than 0 |
| `cruise_speed_mps` | decimal | `2.0` | Greater than 0 |
| `descent_rate_mps` | decimal | `1.0` | Greater than 0 |
| `observation_spacing_m` | decimal | `0.2` | Greater than 0; controls derived event rate |
| `initial_battery_percent` | decimal | `100.0` | In `[0, 100]` |
| `battery_drain_percent_per_s` | decimal | `0.2` | Greater than or equal to 0 |

### Derived values

- `sample_rate_hz = cruise_speed_mps / observation_spacing_m` → 10 Hz.
- `sample_interval_s = 1 / sample_rate_hz` → 0.1 s.
- takeoff duration = `target_altitude_m / climb_rate_mps` → 10 s.
- northbound and return duration = `northbound_distance_m / cruise_speed_mps` → 10 s each.
- landing duration = `target_altitude_m / descent_rate_mps` → 10 s.
- terminal mission time = 45 s.
- snapshot count = `terminal_time * sample_rate + 1` → 451, including both endpoints.
- terminal battery = 91%.

Validation completes before output staging begins. Non-integral alignment between phase boundaries and sample ticks is allowed, but the generator still samples on the global tick grid and uses `[start, end)` phase ownership. The baseline aligns exactly.

## ScenarioSource

Both output artifacts contain the same normalized source object:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Scenario name |
| `version` | string | Scenario semantic version |
| `seed` | integer | Explicit random seed |
| `config` | object | Fully normalized configuration, including derived `sample_rate_hz` and `sample_interval_s` |

No wall-clock generation time, hostname, absolute path, UUID or process-specific value is allowed. Those values would make identical inputs produce different bytes.

## TelemetrySnapshot

Every element of `TelemetryArtifact.snapshots` contains exactly these six fields:

| Field | Type | Validation / meaning |
|---|---|---|
| `vehicle_id` | string | Non-empty and equal to `ScenarioSource.config.vehicle_id` |
| `sequence_number` | integer | Starts at 0; increments by exactly 1 |
| `mission_time_s` | number | Starts at 0; increments by `sample_interval_s`; strictly increasing |
| `position_ned_m` | array[3] number | `[north, east, down]`; east remains 0 in baseline |
| `velocity_ned_mps` | array[3] number | `[north, east, down]`; scalar speed is derived, never stored |
| `battery_percent` | number | In `[0, 100]`; linear aggregate drain |

`additionalProperties` is false. In particular, `phase`, `expected_result`, raw sensor readings and scalar speed are forbidden.

## TelemetryArtifact

File: `telemetry.json`.

| Field | Type | Meaning |
|---|---|---|
| `artifact_version` | string | `1.0.0` |
| `scenario` | `ScenarioSource` | Reproduction source |
| `snapshots` | array[`TelemetrySnapshot`] | Ordered, non-empty mission snapshots |

Semantic validation checks sequence continuity, time continuity, vehicle identity, NED path behavior, battery model and terminal state. JSON Schema checks local shape and primitive ranges.

## PhaseInterval

| Field | Type | Validation / meaning |
|---|---|---|
| `name` | enum | `takeoff`, `hover`, `northbound`, `return`, `landing` |
| `start_time_s` | number | Inclusive |
| `end_time_s` | number | Exclusive, except the terminal sample belongs to `landing` |

The five intervals are ordered, contiguous, non-overlapping and cover `[0, terminal_time_s]` under the terminal inclusion rule.

Baseline boundaries:

| Phase | Interval | Position intent |
|---|---|---|
| `takeoff` | `[0, 10)` | down moves 0 → -10 m |
| `hover` | `[10, 15)` | position fixed at `(0, 0, -10)` |
| `northbound` | `[15, 25)` | north moves 0 → 20 m |
| `return` | `[25, 35)` | north moves 20 → 0 m |
| `landing` | `[35, 45]` | down moves -10 → 0 m; terminal sample included |

## GroundTruthArtifact

File: `ground-truth.json`.

| Field | Type | Meaning |
|---|---|---|
| `artifact_version` | string | `1.0.0` |
| `scenario` | `ScenarioSource` | Byte-identical source object to telemetry artifact |
| `terminal_time_s` | number | Final mission time |
| `phases` | array[`PhaseInterval`] | Exactly five ordered phase intervals |

Ground truth is never passed as telemetry to the future Assertion Engine.

## Canonical byte contract

Before serialization, all calculated decimal values are rounded to six fractional places and negative zero is normalized to zero. JSON output then uses:

- UTF-8;
- lexicographically sorted object keys;
- compact `,` and `:` separators;
- finite JSON numbers only (`NaN` and Infinity rejected);
- arrays preserved in domain order;
- exactly one trailing LF;
- no indentation or platform-native newline conversion.

Generation produces both byte sequences in memory, validates them against JSON Schema and semantic rules, writes them into a temporary directory beneath the requested parent, then renames the completed directory into place. The target directory must not already exist. Tests always request a pytest-owned `tmp_path`.

## PlaybackSession

State transitions:

```text
unloaded → ready → playing ↔ paused → completed
             ↑         │          │
             └─ restart┴──────────┘
```

| State/control | Behavior |
|---|---|
| load | Validate both artifacts, require identical `scenario`, then build a read-only view model |
| play | Advance by snapshot order according to wall-clock playback multiplier |
| pause | Stop wall-clock advancement; mission time does not change |
| step | Advance exactly one snapshot |
| speed | Change wall-clock multiplier only |
| restart | Return cursor to snapshot 0 without regeneration |
| completed | Display terminal sample; restart remains available |

The view model derives altitude as `-down` and scalar speed as the Euclidean norm of `velocity_ned_mps`. Derived values are display-only and never written back.

## Relationships

```text
ScenarioConfiguration
  └─ normalizes to ScenarioSource
       ├─ embedded in TelemetryArtifact ── contains TelemetrySnapshot[]
       └─ embedded in GroundTruthArtifact ── contains PhaseInterval[]

TelemetryArtifact + GroundTruthArtifact
  └─ validated join on identical ScenarioSource
       └─ PlaybackSession (read-only)
```
