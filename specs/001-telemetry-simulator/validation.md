# M0 validation evidence

## CP1 — environment and runner

- CPython 3.14.4; uv 0.11.9; Matplotlib 3.11.2; jsonschema 4.26.0;
  pytest 9.1.1; Ruff 0.16.10. Exact dependency versions are in `uv.lock`.
- `uv sync --locked`: `Resolved 23 packages in 1ms`, `Checked 22 packages in 0.45ms`.
- Installed-package import resolves to `src/assertion_engine/__init__.py`.
- `uv run pytest --collect-only`: `collected 0 items`,
  `no tests collected in 0.01s`, exit 5. The runner executes; domain tests do not exist yet.
  This is setup evidence, not a behavioral PASS or meaningful RED.
- Ruff lint: `All checks passed!`; format: `56 files already formatted`.
- Tool-session caches use `/tmp/assertion-engine-uv-cache` and
  `/tmp/assertion-engine-mpl-cache` because user cache/config directories are read-only
  in the sandbox. Product test destinations remain pytest-owned `tmp_path`.

Reviewed SHA: `f21bde3a061b6370c31c55f05fb58d46818c109d`. Independent review approved
T001/T002; main re-ran locked sync, isolated import, collection and Ruff in the pinned
`/tmp/assertion-engine-review-cp1` checkout with matching results and a clean tree.
Tasks are promoted in a separate post-approval commit.

## CP2 — shared immutable contract

- Tests use hand-authored six-tick fixture pair; expected states/bytes are literal.
- Executor initial assertion RED: `81 failed, 1 passed in 0.93s`; helper RED:
  `14 failed, 86 passed`; source precision pairing RED: `2 failed, 76 deselected`.
- Raw process evidence: `/tmp/assertion-engine-cp2-{red,reusable-red,pair-red,green}.log`
  (session-local; permanent contract tests provide rerunnable evidence).
- Main: `MPLBACKEND=Agg uv run --locked pytest tests/contract/` →
  `102 passed in 0.29s`; Ruff `All checks passed!`, `62 files already formatted`.
- Covers offline Draft 2020-12 shape, exact source grid/phase ownership,
  3 Hz/5 s and A1 cases, NED/battery, canonical bytes and source precision.
- Reviewed SHA: `630adc5589d6ba0901c6882e14070097dcbb25ba`; independent review approved.
  Main read and re-ran `/tmp/assertion-engine-cp2-review-proof.py` in the pinned checkout:
  baseline `102 passed in 0.29s`, Ruff passed, installed package resolved there, tree clean.
- All five real-module mutations failed the intended unchanged tests: rounded phase
  boundary (2 A1 failures), rounded motion ownership (2 A1 failures), source-input
  rounding (1 FR-011 failure), rounded pair comparison (2 FR-011 failures), and rounded
  interval accumulation (1 FR-006/3 Hz failure). No import/collection failures.
- Main restored/verified the isolated checkout; T003–T007 promote in a separate commit.

## CP3 — reproducible generation CLI

- Executor assertion RED: `144 failed, 102 passed`, zero import/collection errors;
  raw `/tmp/assertion-engine-cp3-red.log`. Main rerun: `246 passed in 3.50s`.
- Scope: config types/ranges/precision, baseline/A1/3 Hz motion, four benchmark rates,
  zero/unsampled phases, exact terminal rejection, argument/config no-parent effects,
  existing file/directory/symlink preservation, parent/staging/write/publish failures.
- Three actual installed CLI runs at `build/artifacts/m0-cp3-run-{1,2,3}` each produced
  451 six-field snapshots; terminal time45, origin, zero velocity and 91% battery.
- All three telemetry SHA-256 values:
  `1cc55ccd8ba9fa11d2c242704ad5503d0e82635bb22c1c2c654cbcffe540494b`.
- All three ground-truth SHA-256 values:
  `b12d092c618dc03f06e63984cfba3a10d9c3d712535dca747784422c38e6fac7`.
- Reviewed SHA: `2f53c1ce87daf38dec96326da7a0e3c58632a744`; independent review approved.
  Main inspected and re-ran `/tmp/assertion-engine-cp3-review-proof.py`: 246 baseline
  passes, Ruff passes, five targeted assertion failures, restored 246 passes and clean
  pinned checkout. Mutations: rounded phase ceil, rounded interval ticks, rounded motion
  ownership, parent creation before pair validation, and dangling-symlink existence.
- Main independently read files/recomputed hashes and terminal contracts; T008–T016
  promote in a separate post-approval commit.

## CP4 core — implemented, awaiting review

- Executor assertion RED: `31 failed, 13 passed, 1 skipped`; error-boundary RED:
  `2 failed, 47 passed, 1 skipped`. Raw `/tmp/assertion-engine-cp4-{red,red-errors}.log`.
- Main registered `assertion-playback`, refreshed installed entrypoints, and ran fixture-only
  playback unit/integration tests: `50 passed in 10.86s`, zero skips.
- Loader/session/Matplotlib/CLI are implemented; no generator import. Legacy migration,
  source pairing, actual artists/widgets, controls and immutable input hashes are tested.
- Confirmed unguarded cadence bug in the actual session API: load the generated
  `build/artifacts/m0-cp3-run-1` pair, inject `clock=lambda: clock[0]` with initial0,
  call play(), set clock[0]=0.3, tick(). At10Hz cursor is2/time0.2; expected3/time0.3.
  Float subtraction in `PlaybackSession.tick` loses the exact viewing boundary.
  Add a literal fixture-based assertion RED and fix cadence arithmetic before review.
- T017–T024 remain `[-]`; T025 generated-pair integration and T026 actual five-phase
  rendered/GUI inspection remain `[ ]`. No independent CP4 review has run.
