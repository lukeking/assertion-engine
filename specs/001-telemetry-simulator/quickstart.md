# Quickstart: M0 Telemetry Simulator

Run these acceptance steps from the repository root on Linux with CPython 3.14
and uv 0.11.x (CI uses uv 0.11.9). Recorded execution results are in
[validation.md](validation.md); this guide does not mark the whole feature complete.

Use a clean checkout or ensure all three `build/artifacts/quickstart-normal-run-*`
destinations below are absent. For a repeat run, choose three new explicit names
and update every command consistently; retain existing artifacts.

## 1. Reproduce the locked environment

```bash
uv python install 3.14
uv sync --locked
```

`uv sync --locked` must fail if `pyproject.toml` and `uv.lock` disagree.

## 2. Generate the baseline normal mission

Use an explicit repo-local destination. After configuration and artifact validation,
the generator creates missing parent directories such as `build/artifacts/`, so this
command also works from a clean checkout. It refuses to overwrite an existing final
destination; invalid arguments or configuration create no parent directories.

```bash
uv run assertion-sim generate \
  --scenario scenarios/normal-flight.toml \
  --output build/artifacts/quickstart-normal-run-1
```

Expected files:

```text
build/artifacts/quickstart-normal-run-1/
├── telemetry.json
└── ground-truth.json
```

## 3. Prove byte reproducibility

Generate two additional independent destinations:

```bash
uv run assertion-sim generate \
  --scenario scenarios/normal-flight.toml \
  --output build/artifacts/quickstart-normal-run-2

uv run assertion-sim generate \
  --scenario scenarios/normal-flight.toml \
  --output build/artifacts/quickstart-normal-run-3
```

Compare exactly these three runs, without including older or additional runs:

```bash
sha256sum \
  build/artifacts/quickstart-normal-run-1/telemetry.json \
  build/artifacts/quickstart-normal-run-2/telemetry.json \
  build/artifacts/quickstart-normal-run-3/telemetry.json
sha256sum \
  build/artifacts/quickstart-normal-run-1/ground-truth.json \
  build/artifacts/quickstart-normal-run-2/ground-truth.json \
  build/artifacts/quickstart-normal-run-3/ground-truth.json
```

Each set must report one repeated hash across all three runs.

Save run 1's input hashes for the playback check, then deliberately retry its
existing destination. The generator must print `target already exists` to stderr
and return exit `2`; the hash check must report both inputs `OK`.

```bash
sha256sum \
  build/artifacts/quickstart-normal-run-1/telemetry.json \
  build/artifacts/quickstart-normal-run-1/ground-truth.json \
  > build/artifacts/quickstart-input.sha256
uv run assertion-sim generate \
  --scenario scenarios/normal-flight.toml \
  --output build/artifacts/quickstart-normal-run-1
overwrite_exit=$?
test "$overwrite_exit" -eq 2 && \
  sha256sum --check build/artifacts/quickstart-input.sha256
```

The generator retry is an expected failure; run this block in an interactive
shell without `set -e`, so the exit check executes. Use a new hash-manifest name
too if retaining a previous walkthrough's results.

## 4. Inspect rendered playback

Interactive playback requires a display and an installed Matplotlib GUI backend.
If `MPLBACKEND` was set to `Agg` for headless work, unset it before opening the UI:

```bash
unset MPLBACKEND
uv run assertion-playback \
  --telemetry build/artifacts/quickstart-normal-run-1/telemetry.json \
  --ground-truth build/artifacts/quickstart-normal-run-1/ground-truth.json
```

Check that the N/E route goes north and returns to the origin, altitude rises to
10 m then returns to zero, and battery declines linearly from 100% to 91%. The
phases must appear in order: takeoff, hover, northbound, return and landing. Press
Play then Pause, Step to advance one snapshot, change the speed
slider, and Restart to return to the first snapshot. While paused, stepping the
baseline advances `mission_time_s` by 0.1 s; speed changes only the wall-clock
rate. Close the window normally to return exit `0`.

For CI or a machine without a display:

```bash
MPLBACKEND=Agg uv run assertion-playback \
  --telemetry build/artifacts/quickstart-normal-run-1/telemetry.json \
  --ground-truth build/artifacts/quickstart-normal-run-1/ground-truth.json \
  --headless-output build/artifacts/quickstart-normal-run-1/terminal.png
sha256sum --check build/artifacts/quickstart-input.sha256
```

The PNG parent already exists from generation. Headless playback writes the
terminal frame and exits `0`; verify origin, altitude/speed zero, landing at 45 s
and battery 91% in `terminal.png`. Run the same hash check after closing the
interactive window: both JSON inputs must remain `OK`. A headless run checks
rendering but does not exercise native GUI controls.

## 5. Run the change gate

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
MPLBACKEND=Agg uv run pytest
```

The test suite writes generated artifacts only beneath pytest-provided `tmp_path` directories. It never inherits an output destination from environment variables and never writes to shared storage.

These are the unchanged CI/local gate entrypoints. Each command must exit `0`;
retain the Ruff and pytest summary lines when recording acceptance evidence.
No static typechecker is configured.
