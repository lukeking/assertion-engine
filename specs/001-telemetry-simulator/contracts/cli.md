# CLI Contract

## Generate

```text
assertion-sim generate --scenario <scenario.toml> --output <new-directory>
```

### Preconditions

- `--scenario` names a readable TOML file that passes `ScenarioConfiguration` validation.
- `--output` is explicit and does not already exist.
- The command never derives an output destination from `.env`, the current user, a network service or a shared storage setting.

### Success

- Exit code `0`.
- Atomically publishes exactly:
  - `<new-directory>/telemetry.json`
  - `<new-directory>/ground-truth.json`
- Writes one compact JSON object to stdout:

```json
{
  "ground_truth": "<new-directory>/ground-truth.json",
  "ground_truth_sha256": "<64 lowercase hex characters>",
  "telemetry": "<new-directory>/telemetry.json",
  "telemetry_sha256": "<64 lowercase hex characters>"
}
```

Paths in stdout may reflect the user's supplied relative or absolute destination; paths are never embedded in either artifact.

### Failure

| Exit | Meaning | Side effect |
|---:|---|---|
| `1` | Unexpected operational/internal failure | Final output directory is absent |
| `2` | Invalid arguments, invalid scenario, or existing output target | No artifact is published |

Diagnostics go to stderr and identify the invalid field or path without dumping the full scenario.

## Playback

```text
assertion-playback \
  --telemetry <telemetry.json> \
  --ground-truth <ground-truth.json> \
  [--speed <multiplier>] \
  [--headless-output <image.png>]
```

### Preconditions

- Both files pass their JSON Schemas and semantic validators.
- Their normalized `scenario` objects are byte-equivalent after canonical serialization.
- `--speed` is greater than zero; default is `1.0`.
- `--headless-output`, when supplied, must name a file whose parent directory already exists and is explicitly chosen by the caller.

### Interactive success

- Exit code `0` after the window closes normally.
- Opens a Matplotlib UI with:
  - 2D N/E route and current-position marker;
  - synchronized altitude, scalar-speed and battery plots;
  - current phase and `mission_time_s`;
  - play/pause, one-snapshot step, restart and speed controls.
- Controls modify only the playback cursor and wall-clock rate.

### Headless success

- Exit code `0`.
- Writes one PNG representing the terminal frame to `--headless-output` and exits without opening a window.
- Uses the same validated view model as interactive playback.

### Failure

| Exit | Meaning | Side effect |
|---:|---|---|
| `1` | Unexpected rendering/internal failure | No input artifact is changed |
| `2` | Invalid arguments, schema failure, semantic failure, or mismatched scenario sources | No input artifact is changed; headless output is not published |

## Compatibility

- Artifact compatibility is controlled by `artifact_version`.
- M0 accepts exactly `1.0.0`; unsupported versions fail closed with exit `2`.
- Any future incompatible change requires a new schema version and an explicit migration or adapter path.
