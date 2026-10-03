# CLI Contract

## Generate

```text
assertion-sim generate --scenario <scenario.toml> --output <new-directory>
```

### Preconditions

- `--scenario` names a readable TOML file that passes `ScenarioConfiguration` validation, including exact terminal alignment on the unquantized sample grid.
- `--output` is explicit and does not already exist.
- The output parent may be absent; the command creates missing parent directories after arguments, configuration and the complete artifact pair have passed validation.
- The command never derives an output destination from `.env`, the current user, a network service or a shared storage setting.

### Output preparation

1. Validate arguments and configuration, including the unquantized terminal tick count; reject an existing final target without changing it.
2. Generate both byte sequences in memory and validate the completed pair before filesystem creation.
3. Create any missing directories in the caller-supplied output parent. An existing parent directory is reused.
4. Stage beneath that parent and atomically publish the completed final directory.

If parent creation fails, for example because an ancestor is a file or permissions
deny creation, return exit `1` with a path diagnostic. On operational failure,
remove staging created by this invocation. Parent directories already created may
remain; do not remove parents or pre-existing content during cleanup.

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
| `1` | Parent creation, staging, publication, or other operational/internal failure | Final output directory is absent; invocation staging is cleaned; created parent directories may remain |
| `2` | Invalid arguments, invalid scenario including terminal alignment, or existing output target | No artifact or parent directory is created; any existing target/content is unchanged |

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
- Ground-truth phase `start_sequence_number` values pass exact source-derived validation; current phase is selected by snapshot sequence, not rounded time equality.
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
- Phase labels use validated sequence boundaries even when a displayed snapshot time coincides with a rounded phase start.

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
- M0 accepts telemetry artifact `1.0.0` and ground-truth artifact `2.0.0`; configuration schema and scenario source versions are unchanged. Unsupported versions fail closed with exit `2`.
- Ground truth `1.0.0` lacks the required sequence ownership boundary. Migrate by running generate with the same scenario version, configuration and seed into a new output directory; retain the original artifacts. Playback does not infer missing boundaries or rewrite legacy files.
- Any future incompatible change requires a new schema version and an explicit migration or adapter path.
