# Phase 0 Research: M0 Telemetry Simulator

## Evidence convention

- **E1**: measured in this checkout or executable environment.
- **E2**: derived from official documentation or arithmetic.
- **E3**: engineering judgment that still needs implementation evidence.
- A score is not a Gate. Constitution Gates may use E1 only.

## Decision 1: Staged Python-first stack

**Decision**: Implement M0 in CPython 3.14 with uv. Keep the artifact boundary language-neutral. Do not add a C++ build in M0; reconsider a C++20 Evaluator hot path only after the real Evaluator produces E1 tail-latency or GC-pause evidence that misses the L0 budget.

### Weighted comparison

Scale: 1 (poor) to 5 (strong). Each cell carries its evidence tier.

| Criterion | Weight | Staged Python → measured C++ | C++ core + Python playback now | Python-only project |
|---|---:|---:|---:|---:|
| M0 delivery and visual evidence | 30% | 5 E1 | 3 E1 | 5 E1 |
| Capability growth | 25% | 4 E3 | 5 E3 | 2 E3 |
| Future tail-latency path | 20% | 4 E2 | 5 E2 | 2 E2 |
| Determinism and reproducibility | 15% | 4 E2 | 4 E2 | 4 E2 |
| Tooling/interop simplicity | 10% | 4 E1/E2 | 2 E1/E2 | 5 E1 |
| **Weighted total** | **100%** | **4.30** | **3.95** | **3.50** |

**E1 probe (2026-09-29)**: local environment has Python 3.12.3, uv 0.11.9 and g++ 13.3.0; CMake is absent. The Python path therefore has a working environment manager now, while a two-language build adds an uninstalled build layer before M0 has a measured need.

**E2 basis**:

- [Python 3.14.7 documentation](https://docs.python.org/3.14/) is the current stable documentation set; Python 3.14 is the selected project minor line.
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) defines a lockfile workflow and `--locked`/`--frozen` checks, so local and CI environments can reject drift instead of silently re-resolving.
- Python's [GC interface](https://docs.python.org/3/library/gc.html) exposes collection statistics and tuning/disable controls. This is observability, not proof that Python meets future real-time needs; the future benchmark must measure pause distribution.
- Python's [`perf_counter_ns`](https://docs.python.org/3/library/time.html#time.perf_counter_ns) provides a monotonic high-resolution clock for future latency instrumentation.

**Alternatives considered**:

- **Hybrid immediately** gives the strongest direct C++ practice and tail-latency ceiling, but M0 would pay two build systems, a language boundary, and CMake setup before an Evaluator exists.
- **Python forever** is the cheapest M0 route, but pre-commits the only real-time project to a runtime before measuring its worst-case behavior.

**Reopen trigger**: after M2 has the Evaluator and the 10-rule corpus, run the ladder below. Introduce a C++20 hot path when E1 data shows either (a) `max` engine latency exceeds the active tier's event interval or (b) GC pauses cause missed evaluation windows. Re-score using measured remediation cost and achieved latency.

## Decision 2: Handwritten recursive-descent parser, deferred to M1

**Decision**: M1 will use a handwritten recursive-descent/Pratt parser in Python, with a checked-in EBNF-like grammar and a one-to-one mapping from grammar rules to parsing functions. M0 creates only the `dsl` package boundary; it does not write grammar or parser behavior before the required corpus exists.

### Weighted comparison

| Criterion | Weight | Handwritten RD/Pratt | Lark LALR | ANTLR 4 |
|---|---:|---:|---:|---:|
| Learning value for this project | 35% | 5 E3 | 3 E3 | 3 E3 |
| Corpus/grammar traceability | 25% | 5 E2 | 4 E2 | 5 E2 |
| Dependency and build burden | 20% | 5 E1/E2 | 3 E2 | 1 E1/E2 |
| Error recovery and grammar growth | 20% | 2 E2 | 4 E2 | 5 E2 |
| **Weighted total** | **100%** | **4.40** | **3.45** | **3.50** |

**E2 basis**:

- Python itself publishes a readable [PEG grammar specification](https://docs.python.org/3/reference/grammar.html), demonstrating the traceability shape this project requires: explicit rules alongside the parser implementation.
- [Lark](https://lark-parser.readthedocs.io/en/stable/parsers.html) provides Earley, LALR(1), and CYK algorithms; it is the lower-burden generator alternative if the corpus exposes grammar ambiguity.
- [ANTLR](https://www.antlr.org/download.html) generates Python and C++ targets, but adds the ANTLR tool/runtime workflow and Java-based generator before this small DSL demonstrates that need.

**Guard**: no grammar work starts until at least 10 real rules cover comparisons, Boolean combinations, temporal constraints and trend extrapolation. The corpus is a regression suite, not documentation-only examples.

**Reopen trigger**: switch to Lark or ANTLR only when the checked-in corpus proves that clean RD/Pratt functions cannot express the grammar without duplicated lookahead/backtracking, or when required diagnostics/error recovery dominate parser work. Preference alone is not a trigger.

## Decision 3: Canonical JSON artifacts and TOML input

**Decision**:

- Human-authored scenarios use TOML, parsed by Python's standard library.
- Generation produces two separate UTF-8 JSON files: `telemetry.json` and `ground-truth.json`.
- Ground truth `2.0.0` requires `start_sequence_number = ceil(s_i × r)` for each phase, computed from exact source start/rate before rounding. Playback uses these integer boundaries for ownership; quantized phase times are plot coordinates. This resolves a tick/phase rounding collision without changing the six-field telemetry `1.0.0` or recomputing the timeline in playback. The mapping, empty intervals and migration path are in [data-model.md](data-model.md#phase-ownership-by-sequence).
- Both use JSON Schema Draft 2020-12 shape contracts plus semantic validation.
- Canonical serialization sorts object keys, uses compact separators, rejects NaN/Infinity, writes exactly one trailing LF, and contains no wall-clock timestamp, absolute path, random UUID, or other run-specific value.
- Motion values are computed from integer sample ticks using an unquantized rational interval derived from normalized source parameters; calculated output values are rounded to six fractional decimal places with ties to even. Rounded rate/interval metadata is not accumulated or used as the calculation source. This precision is E3 but is far below M0's 0.2 m/0.1 s observation resolution. The exact policy and 3 Hz example are in [data-model.md](data-model.md#exact-tick-time-and-serialized-precision); the algorithm sources are in [M0 algorithms §1](../../docs/algorithms/001-m0-telemetry-and-playback.md#1-精確取樣格與輸出量化).

**Rationale**:

- A single JSON object can carry source scenario metadata separately from snapshots while preserving the rule that each snapshot contains exactly six fields.
- [Python's JSON encoder](https://docs.python.org/3/library/json.html) supports sorted keys and explicit separator/NaN behavior.
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12) gives a language-neutral contract for future replayers.
- Byte equality can be checked with SHA-256 without interpreting domain content.

**Alternatives considered**:

- **JSON Lines** streams naturally but requires a sidecar/header convention to carry reproducibility metadata and complicates the single-artifact hash for this small M0 scenario.
- **CSV** does not naturally represent NED vectors, metadata, and phase intervals without parallel conventions.
- **Binary formats** improve volume and parsing cost before M0 has a scale problem; they reduce inspectability during the learning phase.

**Reopen trigger**: real logs or benchmark artifacts become large enough that loading one JSON object violates a measured memory/latency target, or a real integration mandates a different wire format. Preserve a versioned adapter and migration path.

## Decision 4: Matplotlib playback

**Decision**: Build a local Matplotlib playback UI with a 2D N/E path, synchronized altitude/speed/battery plots, a phase/time cursor, and play/pause/step/restart/speed controls. Keep artifact loading and view-model calculation independent from Matplotlib.

**Rationale**:

- Matplotlib provides an [animation interface](https://matplotlib.org/stable/users/explain/animations/animations.html) and widget API for local controls.
- Its [backend model](https://matplotlib.org/stable/users/explain/figure/backends.html) supports both interactive GUI backends and non-interactive Agg output. CI can validate rendered evidence without a display server.
- One plotting dependency covers interactive review and headless acceptance evidence; a web server or JavaScript build is unnecessary for M0.

**Alternatives considered**:

- **Plotly/browser UI** offers rich interaction but adds HTML/JavaScript artifact concerns and a second rendering contract.
- **Qt application** offers full desktop controls but adds a GUI framework and event-loop surface larger than the M0 view.

**Reopen trigger**: the required interaction exceeds Matplotlib widgets, or remote/multi-user playback becomes an accepted requirement.

## Decision 5: Test and CI gate

**Decision**:

- Use pytest with `src` layout, installed package imports, and `tmp_path` for every test that writes artifacts.
- Use Ruff for lint and formatting from the same `pyproject.toml`.
- Use uv with a committed `uv.lock`; CI runs `uv sync --locked`, Ruff checks, pytest, JSON Schema contract tests, dependency-boundary tests, and Agg rendering.
- Pin GitHub Actions by full commit SHA with a version comment. The official [uv GitHub Actions guide](https://github.com/astral-sh/uv/blob/main/docs/guides/integration/github.md) recommends `astral-sh/setup-uv`; its workflow can install the selected Python version and use the lockfile.
- Negative contract fixtures prove the gate rejects extra/missing snapshot fields, leaked phase labels, invalid ordering, and non-canonical output. This is the permanent bite proof; tests never mutate the main worktree.

**Rationale**:

- [pytest good practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) recommend a `src` layout for new projects and support configuration in `pyproject.toml`.
- [Ruff configuration](https://docs.astral.sh/ruff/configuration/) lives in `pyproject.toml`, keeping one visible tool contract.
- uv checks lock freshness rather than silently upgrading dependencies.

## Provisional latency ladder (not a Gate)

The baseline movement is 2 m/s. Event interval is `1 / rate`; desired observation spacing is `2 / rate`. Ten rules come from the constitution's future minimum corpus and are not implemented in M0.

| Tier | Event rate | Rule count | Observation spacing | Event interval / future max budget | Evidence |
|---|---:|---:|---:|---:|---|
| L0 | 10 Hz | 10 | 0.20 m | 100 ms | E2 arithmetic |
| L1 | 20 Hz | 10 | 0.10 m | 50 ms | E2 arithmetic + E3 tier |
| L2 | 50 Hz | 10 | 0.04 m | 20 ms | E2 arithmetic + E3 tier |
| L3 | 100 Hz | 10 | 0.02 m | 10 ms | E2 arithmetic + E3 tier |

M0 only guarantees that the Simulator can produce inputs for these rates. After an Evaluator exists, every run reports p50/p95/p99/max engine latency, input age, end-to-end detection latency, GC pause distribution, commit SHA, hardware, scenario version and seed. No row becomes a Gate until E1 measurements establish the achieved tier.

## Baseline normal scenario

These are plan defaults, not physical-fidelity claims:

- vehicle: `vehicle-001`; seed: `42`
- climb to 10 m at 1 m/s: 10 s
- hover: 5 s
- northbound 20 m at 2 m/s: 10 s
- return 20 m at 2 m/s: 10 s
- descend at 1 m/s: 10 s
- total: 45 s; 10 Hz; 451 snapshots including both endpoints
- battery: 100% initial, 0.2 percentage points/s, 91% at mission end

Phase intervals are `[start, end)` at 0/10/15/25/35/45 s; the terminal sample at 45 s is included in `landing`.
