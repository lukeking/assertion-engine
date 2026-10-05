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

## CP4 core — reviewed and main-verified

- Executor assertion RED: `31 failed, 13 passed, 1 skipped`; error-boundary RED:
  `2 failed, 47 passed, 1 skipped`. Raw `/tmp/assertion-engine-cp4-{red,red-errors}.log`.
- Main registered `assertion-playback`, refreshed installed entrypoints, and ran fixture-only
  playback unit/integration tests: `50 passed in 10.86s`, zero skips.
- Loader/session/Matplotlib/CLI are implemented; no generator import. Legacy migration,
  source pairing, actual artists/widgets, controls and immutable input hashes are tested.
- The original float-clock cadence defect is repaired in `f4435df`: literal 10 Hz
  fixture tests first produced `4 failed, 19 passed in 0.27s`; main independently
  reproduced `4 failed, 19 passed in 0.32s` against `841092e` in an isolated checkout.
  This covers the late cursor at wall time 0.3, early terminal completion immediately
  before 1, repeated ticks and lost partial pause/resume progress. Viewing-clock
  endpoints, speed and saved timestamp gaps use exact decimal-string rational values;
  there is no epsilon, mission-time rewrite or source-timeline regeneration.
- First independent full-slice review, `286c851..f4435df`, rejected two weak tests:
  substituting rounded interval metadata still passed all 64 playback tests, while
  removing the actual CLI registration and reinstalling passed 63 with one skip.
  Main replayed the complete reviewer proof and independently confirmed both findings.
- Regression commit `7669417` adds literal saved 3 Hz gaps, repeated ticks and partial
  pause/speed cases, and requires installed CLI registration. Main's isolated RED is
  `6 failed, 6 passed, 23 deselected in 0.21s` for rounded interval substitution and
  `1 failed in 0.38s` for actual registration removal/reinstall. Restored playback:
  `76 passed in 11.39s`, zero skips.
- Reviewed SHA: `76694178e80c376a3a96772092c6656fbbe65d6d`; second independent review
  approved T017–T024 over the complete `286c851..7669417` playback slice, including
  original `80daac8`, shared entry-point registration, tests and status records.
- Main inspected and replayed `build/cp4-review-round2/proof.py` in the pinned
  `/tmp/assertion-engine-review-cp4-core` checkout: baseline `76 passed in 11.77s`,
  independent probes `14 passed in 2.19s`, restored `76 passed in 11.52s`, zero skips.
  Import paths and installed metadata resolve to that checkout; final tracked tree is
  clean and all mutated files byte-match the reviewed SHA.
- Eight actual mutations failed their intended behavior assertions: original float
  cadence, early epsilon, rounded-time phase selection, first eligible phase,
  canonical-byte bypass, initial headless frame, rounded interval substitution, and
  removal/reinstallation of the real CLI registration. The last two produce
  `6 failed, 6 passed, 23 deselected in 0.20s` and `1 failed, 75 passed in 10.02s`.
  No import, collection, syntax or lint failure serves as mutation evidence.
- Independent probes verify complete domain/source and input-byte equality after
  controls, A1 ownership/source precision, large monotonic-clock origins, fractional
  speed/pause cadence, and real staging/render/publication error cleanup. Full suite
  after remediation: `397 passed in 16.41s`; Ruff `All checks passed!`, format
  `78 files already formatted`.
- Reviewer reports/proofs/logs and main replay evidence are preserved under ignored
  `build/cp4-core-review/{round1-reviewer,round1-main,remediation,round2-reviewer,round2-main}/`;
  `main-evidence.json` records the verification summaries. Restore each historical
  proof under its original `build/cp4-review*/` path in a checkout pinned to its SHA
  before replaying; permanent regression tests remain in the committed suite.
- T017–T024 promote to `[X]` in a separate post-approval commit. T025 generated-pair
  integration and T026 actual five-phase rendered/GUI inspection remain `[ ]`.
  This approves core implementation; complete CP4/M0 acceptance remains pending.

## Architecture slice — reviewed and main-verified

- T027/T029 assertion RED: `40 failed, 35 passed`; main GREEN: `75 passed in 0.85s`.
- Static AST scanner resolves absolute/relative imports, aliases and package imports;
  reserved DSL/Evaluator/Fuzzer behavior check is separate and permits docstrings/pass only.
- Initial process logs: `/tmp/assertion-engine-boundary-{red,green}.log`.
- First independent full-slice review, `286c851..a28d180`, rejected one weak test:
  removing Fuzzer from the scanner's reserved-package tuple also removed its test
  cases. The unchanged architecture runner still reported `67 passed`, even after
  adding prohibited production Fuzzer behavior. Main reproduced baseline/restored
  `75 passed` and both incorrect-green states in its own pinned checkout.
- Main replayed the other eight scanner/production mutations: each failed intended
  FR-016 assertions without import, syntax or collection errors. Independent literal
  probes: `57 passed, 0 failed`; restored `75 passed in 0.59s`, zero skips,
  with all 115 tracked files byte-equal to `a28d180`.
- Remediation freezes DSL/Evaluator/Fuzzer names independently in behavioral test
  parameterization and the production existence check. Main's clean changed suite:
  `75 passed in 0.62s`; Ruff `All checks passed!`, `1 file already formatted`.
- Main independently replayed the test-freeze proof: deleting any required package
  retains all 75 cases and produces `5 failed, 70 passed`; the previously escaped
  Fuzzer business-behavior counterexample now produces the same assertion RED.
  With the intact registry, injected Fuzzer behavior fails the production assertion
  (`1 failed, 74 passed`). Restored `75 passed in 0.58s`, zero skips, Ruff passes;
  the installed package and scanner resolve to main's isolated `main-red` checkout.
- Reviewed SHA: `aa2677545a19d674b74c82c893c923b9621fa497`; second fresh independent
  review approved the complete `286c851..aa26775` slice, including original `f7cc270`,
  shared status files and the committed test-freeze repair.
- Main read and replayed the complete second-round proof in its own pinned checkout:
  baseline `75 passed in 0.62s`, restored `75 passed in 0.67s`, zero skips/errors.
  All 19 mutations failed the intended FR-016 assertions while preserving the same
  75 collected IDs and frozen test functions/decorators/literal inputs. These cover
  registry loss, the Fuzzer counterexample, import resolution/traversal/prefix rules,
  production behavior/prohibited imports and missing required initializers.
- Main independently verified `103` literal probes, its installed source paths and
  before/after byte equality for all 115 tracked files. The exact architecture runner
  and Ruff lint/format also pass. T027/T029 promote in a separate post-approval commit;
  CI wiring and remaining full M0 acceptance are outside this slice's approval.
- First reviewer and main proof scripts, mutation patches and raw logs are under
  `build/architecture-review/{reviewer-evidence,main-evidence}/`; test-freeze evidence
  is under `build/architecture-review/{remediation-evidence,main-remediation}/`.
  Second-round scripts, raw logs/XML, collection IDs, patches and byte manifests are
  under `build/architecture-review/{round2-reviewer-evidence,round2-main-evidence}/`.

## Combined pre-handoff check — 2026-10-03

- `MPLBACKEND=Agg uv run --locked pytest` → `371 passed in 14.57s`, zero skips.
- Ruff: `All checks passed!`; format: `78 files already formatted`.
- That historical run preceded the cadence repair and independent core approval
  recorded above. Architecture was still awaiting review at that historical sample;
  its later approval is recorded above. Full CP4/CP5/M0 acceptance remains pending.

## CI preparation — not implemented yet

- GitHub API verified current session admin permission and effective main ruleset
  `20876648`: deletion, non-fast-forward and pull-request rules; no required checks yet.
- Official release tags resolved through GitHub API (2026-10-02):
  - actions/checkout v7.0.1: `3d3c42e5aac5ba805825da76410c181273ba90b1`.
  - astral-sh/setup-uv v10.2.0: `c18668ad3cf93ea998bef934396af7bb5c839dc7`.
- T030 still must implement workflow, obtain actual PASS/check names, then configure
  required checks and read effective rules back. T028/T032 negative fixtures/mutations
  and T033 clean-checkout/CI verification remain open.
