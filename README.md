# assertion-engine

M0 provides deterministic, single-vehicle telemetry generation and local read-only
playback. The baseline mission takes off, hovers, flies north, returns and lands:
45 seconds at 10 Hz, with 451 snapshots including both endpoints.

The Simulator produces upstream state estimates in local North-East-Down (NED)
coordinates. M0 does not model raw GPS/IMU readings, sensor fusion, noise or
estimator fidelity. DSL parsing, rule evaluation, sliding windows, alerts, stream
ingestion, Fuzzer injection and hardware connections are outside M0.

## Responsibilities

| Location | Responsibility |
|---|---|
| `src/assertion_engine/telemetry.py` and `artifacts.py` | Shared immutable data types, offline schema/semantic validation and canonical serialization. |
| `src/assertion_engine/simulator/` | Validate TOML scenarios, generate the mission and publish a complete artifact pair. |
| `src/assertion_engine/playback/` | Validate and view completed artifacts; controls change only the cursor and wall-clock playback rate. It does not depend on the Simulator or regenerate, smooth or interpolate mission state. |
| `src/assertion_engine/dsl/` | Reserved package boundary for future grammar and parsing; no M0 behavior. |
| `src/assertion_engine/evaluator/` | Reserved package boundary for future rule evaluation; no M0 behavior. |
| `src/assertion_engine/fuzzer/` | Reserved package boundary for future adversarial inputs; no M0 behavior. Architecture checks prohibit imports from DSL and Evaluator. |
| `scenarios/` | Human-authored, versioned TOML inputs with an explicit seed; `normal-flight.toml` is the baseline. |
| `tests/` | Unit, contract, integration and architecture checks, including fixed negative fixtures, three-run byte equality and read-only playback checks. Generated test files use pytest `tmp_path`. |

## Environment

Run commands from the repository root on Linux with CPython 3.14 and uv 0.11.x
(CI pins uv 0.11.9). `pyproject.toml` and the committed `uv.lock` define the
installed package and its development dependencies, including pytest and Ruff.

```bash
uv python install 3.14
uv sync --locked
```

Locked sync rejects a stale lockfile. Interactive playback needs an available
Matplotlib GUI backend and a display; headless rendering uses Agg.

## Generate and inspect a mission

Generate into an explicit new directory:

```bash
uv run assertion-sim generate \
  --scenario scenarios/normal-flight.toml \
  --output build/artifacts/readme-normal-run
```

The command validates the configuration and complete pair before creating missing
parents, then publishes `telemetry.json` and `ground-truth.json`. Stdout reports
both paths and their SHA-256 hashes. It refuses to overwrite an existing output
directory; choose a new destination for another run.

Open those completed artifacts in the playback UI:

```bash
uv run assertion-playback \
  --telemetry build/artifacts/readme-normal-run/telemetry.json \
  --ground-truth build/artifacts/readme-normal-run/ground-truth.json
```

The UI shows the N/E route, synchronized altitude/speed/battery plots, and current
phase and mission time. Play/pause, step, speed and restart preserve the input
artifacts and each snapshot's `mission_time_s`.

Without a display, render the terminal frame to the existing generation directory:

```bash
MPLBACKEND=Agg uv run assertion-playback \
  --telemetry build/artifacts/readme-normal-run/telemetry.json \
  --ground-truth build/artifacts/readme-normal-run/ground-truth.json \
  --headless-output build/artifacts/readme-normal-run/terminal.png
```

The PNG parent must already exist. See the
[quickstart](specs/001-telemetry-simulator/quickstart.md) for three-run hash
comparison and the full playback walkthrough, and the
[CLI contract](specs/001-telemetry-simulator/contracts/cli.md) for exit codes and
failure side effects.

## Artifact contract

Telemetry artifact `1.0.0` stores exactly six fields per snapshot:
`vehicle_id`, `sequence_number`, `mission_time_s`, `position_ned_m`,
`velocity_ned_mps` and `battery_percent`. Phase labels stay in the separate
ground-truth artifact `2.0.0`; its sequence boundaries determine phase ownership
even when displayed timestamps coincide after rounding. Playback derives altitude
and scalar speed only for display.

Both artifacts carry matching scenario version, normalized configuration and seed.
Identical inputs produce byte-identical telemetry files and byte-identical ground
truth files across runs. Canonical JSON uses UTF-8, sorted object keys, compact
separators, finite numbers and one trailing LF. Calculated values round to six
decimal places with ties to even; normalized source parameters retain their input
precision. Run-specific timestamps, paths and UUIDs are excluded. See the
[data model](specs/001-telemetry-simulator/data-model.md) for exact sampling,
canonical bytes and legacy ground-truth migration.

## Local change gate

Run the same commands as [CI](.github/workflows/ci.yml):

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
MPLBACKEND=Agg uv run pytest
```

CI runs on pushes and pull requests without a GUI or network schema resolution.
The required `change-gate` check protects merges to `main`. Current acceptance
evidence and remaining whole-gate validation are recorded in
[validation.md](specs/001-telemetry-simulator/validation.md).

## Provisional latency ladder

These are future Evaluator targets, not measured M0 real-time performance or a
performance gate. At 2 m/s, observation spacing is `2 / rate` and the event
interval is `1 / rate`. The rule count refers to the future minimum corpus;
M0 implements no rules or Evaluator.

| Tier | Event rate | Future rules | Observation spacing | Event interval / future max budget | Evidence |
|---|---:|---:|---:|---:|---|
| L0 | 10 Hz | 10 | 0.20 m | 100 ms | E2 arithmetic |
| L1 | 20 Hz | 10 | 0.10 m | 50 ms | E2 arithmetic + E3 tier choice |
| L2 | 50 Hz | 10 | 0.04 m | 20 ms | E2 arithmetic + E3 tier choice |
| L3 | 100 Hz | 10 | 0.02 m | 10 ms | E2 arithmetic + E3 tier choice |

M0 can generate inputs at these rates. E2 denotes derivation and E3 engineering
judgment; only E1 measurements of the future Evaluator's p50/p95/p99/max latency
and GC pause distribution can establish a performance gate. The
[research](specs/001-telemetry-simulator/research.md#provisional-latency-ladder-not-a-gate)
records the derivation and evidence boundary.
