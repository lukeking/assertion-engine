# Data Model: M0 Telemetry Simulator

## Overview

The model separates three responsibilities:

1. `ScenarioConfiguration` says what normal mission to generate.
2. `TelemetryArtifact` records only observable state snapshots.
3. `GroundTruthArtifact` records the expected phase timeline for tests and playback annotations.

Telemetry never contains a phase label. Playback joins the two artifacts by identical
scenario source metadata and uses ground-truth sequence boundaries for phase ownership;
mission time remains the snapshot's display time. It never modifies either artifact.

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
- snapshot count = `N + 1`, where `N = T × r` uses unquantized terminal time/rate → 451, including both endpoints.
- terminal battery = 91%.

### Exact tick time and serialized precision

Sampling calculations use the finite non-derived parameters in normalized `scenario.config`,
interpreting their canonical decimal numeric representations as exact rational values.
For example, spacing `0.2` means `1/5`, not the binary-float approximation to `0.2`.
These input parameters retain their normalized numeric values in source metadata; the
six-place rule below applies to calculated values, not an extra rounding of source inputs.

Let `r = cruise_speed_mps / observation_spacing_m` and `Δt = 1/r` before quantization.
For sequence number `k`, calculate the internal observation time as `t_k = k × Δt`.
Do not accumulate either binary floats or a six-place `sample_interval_s`.

Define `Q(x)` as rounding to the nearest multiple of `10^-6`, with exact ties to even,
and normalize negative zero to zero. The JSON `mission_time_s` is `Q(t_k)`;
the derived source metadata is `sample_rate_hz = Q(r)` and `sample_interval_s = Q(Δt)`.
Neither derived metadata field replaces `r` or `Δt` in generation or validation.

The semantic validator reconstructs `r` and `Δt` from non-derived source parameters,
checks the two metadata values against `Q(r)` and `Q(Δt)`, and checks each timestamp
against `Q(k × Δt)` by exact decimal numeric equality. It also checks strict ordering;
adjacent serialized differences need not equal the rounded interval metadata.
Prevalidation rejects settings whose quantized rate/interval metadata is non-positive or whose
published tick times cease to be strictly increasing, before output staging.

For an accepted 3 Hz, 5 s mission, the first timestamps are
`0, 0.333333, 0.666667, 1`; the last is `5` at tick 15. Its rounded interval metadata
is `0.333333`. Requiring every serialized difference to equal that metadata would
reject valid data; accumulating it would incorrectly end at `4.999995`.

Sources and the implementation mapping are in
[M0 algorithms §1](../../docs/algorithms/001-m0-telemetry-and-playback.md#1-精確取樣格與輸出量化).

### Terminal alignment

Let `T` be the unquantized mission duration obtained from all five source-derived
phase durations. Prevalidation requires `N = T × r` to be an integer, using the exact
rational source values before `Q`. Otherwise reject the configuration before any
output directory or staging is created. No tolerance based on rounded timestamps
is used for this decision.

Generate ticks `k = 0…N`, including both endpoints; the final snapshot time is
`Q(N × Δt) = Q(T)` and its velocity is zero. Internal phase boundaries may fall
between ticks and keep the `[start, end)` ownership rule. The terminal snapshot
belongs to landing.

For example, 10 Hz with `T = 45.05` is rejected because `T × r = 450.5`.
`T = 45.0000004` is also rejected even though `Q(T) = 45`.
The baseline `45 × 10 = 450` and the 3 Hz example `5 × 3 = 15` are accepted.

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
| `mission_time_s` | number | Starts at 0; equals `Q(sequence_number × Δt)` from non-derived source parameters; strictly increasing |
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
| `start_time_s` | number | `Q(s_i)` of the exact source-derived phase start; display/plot coordinate |
| `end_time_s` | number | `Q(e_i)` of the exact phase end; display/plot coordinate |
| `start_sequence_number` | integer | `ceil(s_i × r)`, using the unquantized source phase start and rate; authoritative ownership boundary |

The five exact source intervals are ordered, contiguous and non-overlapping, using
`[s_i, e_i)` with the terminal tick included in landing. Their quantized display
coordinates cover `[0, terminal_time_s]` and may coincide after rounding.

### Phase ownership by sequence

For each phase `i`, store `b_i = ceil(s_i × r)` before quantization. The first boundary
is `b_0 = 0`; all boundaries are non-decreasing integers within `0…N`.
Phase `i < 4` owns snapshot indices `[b_i, b_(i+1))`; landing owns `[b_4, N]`.
Equal adjacent boundaries mean an empty snapshot interval. For a snapshot index `k`,
playback selects the last phase in the fixed five-phase order whose `b_i <= k`.
Thus zero-duration/unsampled phases receive no snapshot, and the terminal index `N`
always belongs to landing, including when several phases start at that index.

The semantic validator derives exact `s_i` from source parameters, verifies every
stored boundary equals `ceil(s_i × r)`, verifies display coordinates equal `Q(s_i)`
and `Q(e_i)`, and checks range/order/coverage against the paired telemetry count.
Playback then reads the validated boundaries; it does not recompute motion, battery,
or the phase timeline and does not compare rounded times to choose a phase.

A1 example: altitude `0.3333334`, climb rate `1`, hover duration `0.6666666`, northbound
distance `3`, cruise speed `3`, descent rate `0.3333334` and observation spacing `1`
give a 3 Hz, 4 s mission with 13 snapshots. Exact phase starts are
`0, 0.3333334, 1, 2, 3`; stored sequence boundaries are `0, 2, 3, 6, 9`.
Tick 1 (`1/3` s) stays takeoff even though its display time and hover's displayed start
are both `0.333333`. Tick 2 is hover; terminal tick 12 is landing.

Current-phase labels and phase-dependent marker styling use these sequence boundaries.
The rounded time intervals remain plot annotations; equality of displayed coordinates
is not evidence that the current snapshot has crossed the exact source boundary.

Baseline boundaries:

| Phase | Exact interval | Snapshot ownership | Position intent |
|---|---|---|---|
| `takeoff` | `[0, 10)` | `[0, 100)` | down moves 0 → -10 m |
| `hover` | `[10, 15)` | `[100, 150)` | position fixed at `(0, 0, -10)` |
| `northbound` | `[15, 25)` | `[150, 250)` | north moves 0 → 20 m |
| `return` | `[25, 35)` | `[250, 350)` | north moves 20 → 0 m |
| `landing` | `[35, 45]` | `[350, 450]` | down moves -10 → 0 m; terminal sample included |

## GroundTruthArtifact

File: `ground-truth.json`.

| Field | Type | Meaning |
|---|---|---|
| `artifact_version` | string | `2.0.0` for ground truth; telemetry remains `1.0.0` |
| `scenario` | `ScenarioSource` | Byte-identical source object to telemetry artifact |
| `terminal_time_s` | number | `Q(T)`; the unquantized source-derived `T × r` must be an integer |
| `phases` | array[`PhaseInterval`] | Exactly five ordered phase intervals with required `start_sequence_number` |

Ground truth is never passed as telemetry to the future Assertion Engine.

Version `2.0.0` makes the sequence boundary mandatory. Ground truth `1.0.0` is rejected
with exit `2`; migrate by regenerating the artifact pair from the same scenario version,
configuration and seed into a new output directory. The config/source contract and
telemetry artifact remain `1.0.0`; playback does not silently enrich an old ground truth.

## Canonical byte contract

Before serialization, all calculated decimal values use `Q` (six fractional places,
nearest with ties to even), and negative zero is normalized to zero. Source input
parameters preserve their normalized numeric values. JSON output then uses:

- UTF-8;
- lexicographically sorted object keys;
- compact `,` and `:` separators;
- finite JSON numbers only (`NaN` and Infinity rejected);
- arrays preserved in domain order;
- exactly one trailing LF;
- no indentation or platform-native newline conversion.

Generation validates configuration and the unquantized terminal tick count, rejects an
existing final target, then produces both byte sequences in memory and validates them
against JSON Schema and semantic rules. Only after validation does it create missing
caller-supplied parent directories, stage beneath that parent, and atomically publish
the completed final directory. Invalid arguments/configuration create no directories.
Operational failure removes this invocation's staging; already-created parent directories
may remain, and existing parents/content are not removed. Tests always request a
pytest-owned `tmp_path`. Exit semantics are defined in [contracts/cli.md](contracts/cli.md).

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
