# Quickstart: M0 Telemetry Simulator

These commands describe the completed feature. They are acceptance steps, not evidence that implementation exists during planning.

## 1. Reproduce the locked environment

```bash
uv python install 3.14
uv sync --locked
```

`uv sync --locked` must fail if `pyproject.toml` and `uv.lock` disagree.

## 2. Generate the baseline normal mission

Use an explicit repo-local destination. The generator refuses to overwrite it.

```bash
uv run assertion-sim generate \
  --scenario scenarios/normal-flight.toml \
  --output build/artifacts/normal-run-1
```

Expected files:

```text
build/artifacts/normal-run-1/
├── telemetry.json
└── ground-truth.json
```

## 3. Prove byte reproducibility

Generate two additional independent destinations:

```bash
uv run assertion-sim generate \
  --scenario scenarios/normal-flight.toml \
  --output build/artifacts/normal-run-2

uv run assertion-sim generate \
  --scenario scenarios/normal-flight.toml \
  --output build/artifacts/normal-run-3
```

Compare hashes:

```bash
sha256sum build/artifacts/normal-run-*/telemetry.json
sha256sum build/artifacts/normal-run-*/ground-truth.json
```

Each set must report one repeated hash across all three runs.

## 4. Inspect rendered playback

```bash
uv run assertion-playback \
  --telemetry build/artifacts/normal-run-1/telemetry.json \
  --ground-truth build/artifacts/normal-run-1/ground-truth.json
```

Check that the 2D route returns to the origin, altitude returns to zero, battery declines linearly, and the five phases appear in order. Pause, step once, change speed and restart; `mission_time_s` must continue to come only from the selected snapshot.

For CI or a machine without a display:

```bash
MPLBACKEND=Agg uv run assertion-playback \
  --telemetry build/artifacts/normal-run-1/telemetry.json \
  --ground-truth build/artifacts/normal-run-1/ground-truth.json \
  --headless-output build/artifacts/normal-run-1/terminal.png
```

## 5. Run the change gate

```bash
uv run ruff format --check .
uv run ruff check .
MPLBACKEND=Agg uv run pytest
```

The test suite writes generated artifacts only beneath pytest-provided `tmp_path` directories. It never inherits an output destination from environment variables and never writes to shared storage.
