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
  integration and T026 actual five-phase rendered/GUI inspection were pending at
  that core-review checkpoint; their completed acceptance is recorded below.
  This core approval alone did not complete CP4/M0 acceptance.

## CP4 acceptance — T025/T026 reviewed and main-verified

- Product baseline: `0d856dcf062db97041fc5b0393f51ed6f55b369d`; all tracked
  non-Markdown files byte-match that SHA (`build/playback-acceptance/source-identity.json`).
  This verification slice changes no product or tests and has no manufactured TDD RED.
- Fresh `uv sync --locked`, with `UV_NO_SYNC` removed: `Resolved 23 packages in 1ms`,
  `Checked 22 packages in 0.48ms`, exit 0. Exact playback runner:
  `uv run --locked pytest -p no:cacheprovider --basetemp <explicit-build-directory>
  tests/unit/playback/ tests/integration/test_playback_read_only.py`.
  BEFORE: `76 passed in 11.27s`; AFTER: `76 passed in 10.75s`, zero skips, exit 0.
  Literal fixture tests load saved JSON and have no generator dependency.
- Reused the existing US1 pair in `build/artifacts/m0-playback-acceptance-20261005/`;
  preserved historical generation/pytest logs. Before/after telemetry SHA-256:
  `1cc55ccd8ba9fa11d2c242704ad5503d0e82635bb22c1c2c654cbcffe540494b`;
  ground truth: `b12d092c618dc03f06e63984cfba3a10d9c3d712535dca747784422c38e6fac7`.
  Canonical whole-domain bytes equal each input before and after controls and reload.
- Agg registered callbacks/fake viewing clock: ready → play → snapshot 12/time 1.2
  → pause and stable cursor through 99 wall seconds → step to 13/time 1.3 → 4x
  → resume to 23/time 2.3 → restart → completed 450/time 45 → stable completed
  controls → restart. All 451 saved snapshots retain exact identity, order, time and
  phase. `control-sequence.json`, `snapshot-traversal.json`, `artist-evidence.json`,
  `acceptance-evidence.json` and `domain-{before,after}-{0,1}.json` contain the raw proof
  under `build/playback-acceptance/`. This callback evidence alone is not GUI interaction.
- Actual 1440×960 images in the same artifact directory: `phase-takeoff.png` (5 s),
  `phase-hover.png` (12.5 s), `phase-northbound.png` (20 s), `phase-return.png` (30 s),
  `phase-landing.png` (40 s), `terminal-view.png` and installed CLI `terminal.png`
  (45 s). The two terminal PNGs are byte-equal after resetting the view slider to
  CLI default 1x. Executor actually viewed all seven; main separately reported actual
  full-size inspection of the five phase images and CLI terminal. Phase/time labels
  are readable, five bands appear in order, all cursors synchronize, the northbound
  and return markers are at north 10 m, and the terminal marker is at the origin
  with altitude/speed zero and battery 91%. Battery declines linearly.
- Sandbox display access initially failed with socket `EPERM`; raw probe retained in
  `build/playback-acceptance/sandbox-gui-probe/`. Host retry opened real TkAgg:
  display valid/socket connected, 13 control checkpoints, 11 native Tk release events,
  48 actual TimerTk ticks. Tk canvas button/slider events exercised play, pause, one
  saved-event step, speed, resume, restart, completion, stable terminal controls and
  restart after completion through `MatplotlibView.show()`/Tk mainloop and real clock.
  Inputs/domain bytes remained equal. This is automated native GUI interaction;
  no human manual interaction is claimed. `gui-evidence.json`, `gui-control-sequence.json`,
  `gui-live-timer.json`, `gui-widget-events.json`, `gui-host-run.*` preserve the proof.
  Executor also viewed actual Tk pixels `gui-terminal-canvas.png` (1200×800) and
  rendered `gui-terminal-view.png` (1440×960), both in the artifact directory.
  Main also reported actual Tk canvas inspection: terminal label/marker/plots are readable.
- Final Ruff repo: `All checks passed!`, `78 files already formatted`; explicit
  ignored driver/replay: `All checks passed!`, `2 files already formatted`, exit 0.
  The first replay stopped only at three driver E501 string lines; raw failure remains
  in `replay.*`/`driver-ruff-check.*`. Strings were wrapped and the four final Ruff
  checks recorded under `final-*-result.json` and corresponding raw stdout/stderr.
- Replay: `.venv/bin/python -B build/playback-acceptance/replay.py`; exact host-GUI
  retry command and replay boundaries are in `build/playback-acceptance/README.md`.
  Raw commands, exit codes, environment flags, PNG/data hashes and visual inspection
  are preserved in that evidence directory (`artifact-manifest.json`, `visual-inspection.json`).
- Independent fresh review APPROVED without findings, pinned to
  `ffc5e6ae5dff66127cc6602db05f716cbfaa94b3`, covering the complete
  `0d856dc..ffc5e6a` acceptance slice. Reviewer ran 76 tests before, 76 after
  acceptance and 76 after restoration, zero skips; actual image inspection and
  native Tk retry passed (13 controls, 11 events, 49 real ticks).
- Main replayed the unchanged reviewer `proof.py` (SHA-256
  `15d2b8bc3f68284ac4d55777c114cc80f053263892edac7597eeea6cc9d4b42c`)
  in its own checkout pinned to the reviewed SHA. Initial locked sync timed out
  with an empty cache; offline bootstrap from the existing cache succeeded, followed
  by a fresh locked sync with `UV_NO_SYNC` removed and verified editable source paths.
  BEFORE: `76 passed in 19.48s`; AFTER: `76 passed in 14.69s`; restored:
  `76 passed in 14.99s`, zero skips. Native Tk passed 13 controls/11 events/48 ticks.
  All 451 saved events, input/domain byte equality, unchanged hashes and CLI/view
  terminal PNG equality pass. Fresh phase/terminal PNGs byte-match the reviewer’s
  inspected images; main also opened the fresh actual Tk terminal canvas.
- Reviewer and main each added one metre to the displayed north marker. The unchanged
  existing rendering test failed at `assert [2.0] == [1]` (main: `1 failed in 2.06s`),
  demonstrating a behavior assertion failure. Restoration leaves all 115 tracked
  files byte-equal to the reviewed SHA and the isolated checkouts clean.
- Preserved review report, proof, raw commands/results, mutation patch, byte manifests
  and artifacts: `build/playback-acceptance-{reviewer,main}-evidence/`; original executor
  evidence: `build/playback-acceptance-executor-evidence/`. T025/T026 promote to `[X]`
  in a separate post-approval commit. CP4 is complete; CP5 and full M0 remain pending.

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
  its later approval and completed CP4 acceptance are recorded above.
  CP5 and full M0 acceptance remain pending.

## CI preparation — not implemented yet

- GitHub API verified current session admin permission and effective main ruleset
  `20876648`: deletion, non-fast-forward and pull-request rules; no required checks yet.
- Official release tags resolved through GitHub API (2026-10-02):
  - actions/checkout v7.0.1: `3d3c42e5aac5ba805825da76410c181273ba90b1`.
  - astral-sh/setup-uv v10.2.0: `c18668ad3cf93ea998bef934396af7bb5c839dc7`.
- T030 still must implement workflow, obtain actual PASS/check names, then configure
  required checks and read effective rules back. T032 isolated gate mutations and
  T033 clean-checkout/CI verification remain open; T028 approval is recorded below.

## Permanent gate rejection fixtures — T028 reviewed and main-verified

- Complete reviewed slice: `ef2fee0a40aca6d084a54e985b62f2db54948189` to
  `a5abdefa5992fecf848d7e497c34fded2c952eea`. Five committed fixtures and six tests;
  no product behavior changes. Each document fixture changes exactly one T003 field:
  snapshot 0 adds `phase`, snapshot 0 removes `battery_percent`, snapshot 2 changes
  sequence `2` to `3`, or ground-truth source seed changes `42` to `43`.
  Specific validator diagnostics identify FR-004/006/010/011 and SC-002 violations;
  repairing the intended field restores equality with the entire T003 document.
- The independent canonical T003 telemetry literal is 1293 bytes. Reviewer confirmed
  byte equality with standard-library JSON encoding for these integer/tenth values;
  neither generator nor production serializer defines the expected bytes.
  `noncanonical.telemetry.json` is exactly that literal plus one LF (1294 bytes),
  with unchanged JSON semantics. The test-level byte gate rejects it; positive
  controls check actual `canonical_bytes` output for decoded and typed telemetry.
  Document validation still accepts human-formatted input, as before.
- Executor baseline: `102 passed in 0.42s`; test-first isolated valid stand-ins:
  `5 failed, 103 passed in 0.31s`, exit 1, all five failures `DID NOT RAISE`;
  final contract suite: `108 passed in 0.29s`, exit 0, zero skips.
  Logs, single-defect diffs and the disposable-copy RED replay are preserved under
  `build/t028-executor-evidence/`. No temporary source mutation touched the main tree.
- Fresh independent review APPROVED without findings. The first reviewer dispatch
  stopped at a usage limit before producing evidence; resumed review used an isolated
  checkout pinned to the same SHA. BEFORE and RESTORED contract suites each passed
  108 tests, zero skips/errors, exit 0. Removing the sequence guard, removing source
  identity rejection, and making the serializer append a second LF each produce
  exactly `1 failed, 5 passed`, exit 1, at the intended unchanged new test assertion.
  Source imports and offline schema contents resolve into the selected checkout.
- Main replayed the unchanged reviewer proof in its separate pinned checkout with
  the same 108/108 passing contract suites and three intended mutation failures.
  After each restoration, all 121 tracked files byte-match the reviewed SHA;
  reviewer and main checkouts are clean. Proof SHA-256:
  `c58b28fa838eb34b3587ae97f4470e705ba2483e9720cd0e86033fbecca53009`.
  Replay: `python3 build/t028-reviewer-evidence/proof.py <isolated-checkout>
  <explicit-evidence-directory>` after installing that checkout's locked environment.
  Findings, patches, raw logs/XML and results: `build/t028-reviewer-evidence/`;
  main replay: `build/t028-main-evidence/reviewer-replay/`.
- Main whole-repository verification at the unchanged implementation SHA:
  `403 passed in 16.13s`, zero skips, exit 0; Ruff `All checks passed!`, format
  `79 files already formatted`. Commands/logs/results are in
  `build/t028-main-evidence/verification.json` and corresponding stdout/stderr files.
  Fresh `uv sync --locked --offline` succeeded for both resumed isolated checkouts.
  T028 promotes to `[X]` only in this separate post-approval commit. T030 is next;
  workflow enforcement, whole-gate mutation proof and full M0 acceptance remain pending.

## T030 — locked CI and effective main checks — 2026-10-07

- Implementation commit: `73d5c6becef85d62d352b73c860527b51eaedc14`.
  `.github/workflows/ci.yml` runs on every `push` and `pull_request` using
  `ubuntu-latest`, Python `3.14`, uv `0.11.9` and read-only repository contents.
  The exact gate is `uv sync --locked`, `uv run ruff format --check .`,
  `uv run ruff check .`, then `MPLBACKEND=Agg uv run pytest`.
- Official GitHub tag refs independently verified by executor and main:
  [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1)
  → `3d3c42e5aac5ba805825da76410c181273ba90b1`;
  [setup-uv v10.2.0](https://github.com/astral-sh/setup-uv/releases/tag/v10.2.0)
  → `c18668ad3cf93ea998bef934396af7bb5c839dc7`.
  Both refs resolve directly to commits, and both action definitions use Node 24.
  The pinned setup-uv definition supports `version` and `python-version`;
  Python selection sets `UV_PYTHON`, and uv installs that interpreter as needed.
  [uv 0.11.9](https://github.com/astral-sh/uv/releases/tag/0.11.9) is verified.
- Real remote PASS at the implementation commit:
  [pull_request run](https://github.com/lukeking/assertion-engine/actions/runs/37638599576)
  and [push run](https://github.com/lukeking/assertion-engine/actions/runs/37638598182)
  both conclude `success`; the actual check context is `change-gate`.
  PR job `112851270734` passed all four gate steps. Its log reports
  `403 passed in 9.57s`, `All checks passed!`, and `79 files already formatted`.
- Main ruleset `20876648` was updated only after that observed PASS. Read-back
  through `gh api repos/lukeking/assertion-engine/rules/branches/main` confirms
  an active `required_status_checks` rule requiring `change-gate` from the
  observed GitHub Actions app `15368`, with
  `strict_required_status_checks_policy: true` and `do_not_enforce_on_create: false`.
  Full ruleset read-back preserves the original deletion/non-fast-forward/PR
  rules, `refs/heads/main` scope and empty bypass list exactly. Missing or failed
  required checks are prohibited by this effective rule; a deliberate blocked-merge
  experiment has not been run in T030. T032/T033 retain the isolated whole-gate
  failure and final acceptance checks. Draft PR state alone is not gating evidence.
- Local executor exact gate: `403 passed in 22.16s`, zero skips; main independent
  exact gate: `403 passed in 17.16s`, zero skips. Both Ruff runs report
  `All checks passed!`, both formatting runs `79 files already formatted`, and
  both locked syncs exit 0. This YAML setup layer has no workflow unit runner:
  verification is explicitly degraded (upstream definition/ref validation, local
  gate and actual hosted Actions execution), with no fabricated behavioral RED.
- Re-run upstream probes: `gh api repos/actions/checkout/git/ref/tags/v7.0.1`,
  `gh api repos/astral-sh/setup-uv/git/ref/tags/v10.2.0`,
  `gh api repos/astral-sh/uv/releases/tags/0.11.9`. Re-read remote evidence with
  `gh run view 37638599576 --json status,conclusion,jobs,url` and
  `gh api repos/lukeking/assertion-engine/commits/73d5c6becef85d62d352b73c860527b51eaedc14/check-runs`.
  Reviewable before/after ruleset and effective-rule snapshots, exact update
  payload, checks, run responses and logs: `build/t030-main-evidence/`;
  executor action definitions and command summaries: `build/t030-executor-evidence/`.
  T030 remains `[-]` pending independent review and main replay.

## T030 approval and main replay — 2026-10-07

- Fresh independent review APPROVED the full `9e07c1c..545907b` slice, with
  no blocking or non-blocking findings. Reviewer final exact gate:
  `403 passed in 15.66s`, zero skips; Ruff lint/format passed.
- Main replayed the final `proof.py` unchanged in a separate checkout pinned to
  `545907b9ebfd5e18d21d095eb674437b1cb78d95`. Replay covered official action refs
  and definitions, actual push/PR PASS at both implementation and reviewed SHAs,
  required-check query, live effective main rules, preserved original rules,
  setup chronology, installed source identity and the exact local gate:
  `403 passed in 18.29s`, zero skips; `79 files already formatted`,
  `All checks passed!`, locked sync exit 0.
- Reviewer and main both changed project version `0.1.0` → `0.1.1` only in their
  isolated checkouts while retaining the committed lockfile. Real
  `uv sync --locked` rejected it with the intended lockfile-staleness diagnostic,
  without a network/dependency failure. Restored locked sync passed. Both
  checkouts' 122 tracked files byte-match the reviewed SHA and have clean status.
- Final proof SHA-256:
  `966d1522aeaed09043b22096fbb196ff4552122fad6a8aa73e5cbd9886ea3d42`.
  Replay command: `python3 build/t030-reviewer-evidence/proof.py --checkout
  /tmp/assertion-engine-t030-main --output build/t030-main-replay --before-ruleset
  build/t030-main-evidence/ruleset-before.json`. Checkout must be isolated and
  pinned to the reviewed SHA; GitHub calls are read-only. Full logs, commands,
  snapshots and byte manifests: `build/t030-reviewer-evidence/` and
  `build/t030-main-replay/`. The scripts are ignored local evidence; committed
  commands/run URLs allow an independent reconstruction.
- Reviewed-SHA hosted [PR run](https://github.com/lukeking/assertion-engine/actions/runs/37639431078)
  and [push run](https://github.com/lukeking/assertion-engine/actions/runs/37639416030)
  both passed. `gh pr checks 5 --required` reports both `change-gate` executions
  SUCCESS; `gh pr view 5` still reports OPEN/draft and MERGEABLE/CLEAN.
  T030 promotes to `[X]` only in this post-approval commit. T031–T036 and
  full M0 acceptance remain pending; PR #5 remains draft.

## T031 — README reviewed and main-verified — 2026-10-07

- Implementation commit: `72eea6a13e3957e4942b44f2e0d8bb324d6354fb`.
  Fresh independent review APPROVED the full
  `fec98f0c777034acdd8db1acf4a48146f66e275f..72eea6a13e3957e4942b44f2e0d8bb324d6354fb`
  slice (`README.md` and the T031 marker), without findings. README covers all
  package/scenario/test responsibilities, M0 scope, environment and installed CLI
  examples, canonical artifacts and the provisional E2/E3 latency ladder.
- Documentation has no unit runner: verification is explicitly degraded, with no
  behavioral TDD RED. The README command typo below verifies the documentation
  smoke check; it does not fulfill T032's product-source whole-gate mutations.
- Reviewer and main ran the same standalone `proof.py` unchanged in separate
  disposable checkouts pinned to the implementation SHA. Both setup commands
  ran individually and passed: CPython 3.14.4, uv 0.11.9 and locked sync. Installed
  modules resolve into the supplied checkout, and both console entrypoints match
  `pyproject.toml`. The proof rejects a preexisting generation destination rather
  than deleting content. Writable uv/Matplotlib caches and temporary test files
  use explicit local scratch paths; no shared storage is involved.
- The README's four gate commands exactly match `.github/workflows/ci.yml`.
  Reviewer: `403 passed in 24.87s`, zero skips; main replay: `403 passed in 21.62s`,
  zero skips. Both report `79 files already formatted` and `All checks passed!`;
  locked sync exits 0. All six README links, including the research anchor, resolve;
  all four ladder rows and their arithmetic match the research authority.
- Each isolated checkout temporarily changed the README command `generate` to
  `generat-typo`. The unchanged expected-success smoke check rejected the extracted
  command with exit 2 and `invalid choice: 'generat-typo'`; no generation directory
  was created. The exact committed README bytes were restored before executing
  the valid examples. All 122 tracked files byte-match the reviewed SHA before
  and after each run, and final Git status is clean.
- Extracted generation and Agg headless playback commands exit 0 at the exact
  README destination, `build/artifacts/readme-normal-run`. The pair has 451
  six-field snapshots spanning 0–45 s, telemetry `1.0.0`, ground truth `2.0.0`,
  matching scenario sources and phase sequence boundaries `0, 100, 150, 250, 350`.
  Playback preserves both input hashes:
  telemetry `1cc55ccd8ba9fa11d2c242704ad5503d0e82635bb22c1c2c654cbcffe540494b`;
  ground truth `b12d092c618dc03f06e63984cfba3a10d9c3d712535dca747784422c38e6fac7`.
  Both produce a valid 1440 × 960 terminal PNG. Reviewer inspected the rendered
  image: landing at 45 s, snapshot 450, completed state, origin and synchronized
  plots. The GUI invocation was checked with appended `--help`; this slice does
  not claim a new interactive GUI walkthrough.
- Final proof SHA-256:
  `050f952328968c62103dbe98cf16280eb2519ef2be365665e08491a57f728428`.
  Replay command: `python3 build/t031-reviewer-evidence/proof.py --checkout
  /tmp/assertion-engine-t031-main --output build/t031-main-replay`.
  Use a new output directory and a disposable checkout at the reviewed SHA.
  Full command/exit/stdout/stderr evidence, source identity, byte manifests and
  mutation results are in `build/t031-reviewer-evidence/run-host/` and
  `build/t031-main-replay/`; the proof and logs are ignored local evidence.
- Initial sandbox setup attempts could not write uv's managed Python directory.
  The reviewer and main final proofs passed with host access for the exact setup
  command. The preliminary main check also caught a shell block whose successful
  sync had masked the earlier install failure; setup was rerun command by command.
  These environment failures are retained in local evidence and are not counted
  as a contract rejection or TDD RED.
- T031 promotes to `[X]` only in this separate post-approval commit. T032–T036,
  whole-gate failure acceptance and full M0 acceptance remain pending; PR #5 stays
  draft.

## T032 — isolated product-source gate failures — 2026-10-08

- Executor source baseline: `b6a7ca914ea404db45ab597c17a6d321ba4c3bd2`.
  Two new scratch clones, `/tmp/assertion-engine-t032-executor-complete-phase`
  and `/tmp/assertion-engine-t032-executor-complete-bytes`, are detached at that
  SHA and each installs its own `.venv`. CPython `3.14.4`, uv `0.11.9`.
  Before, during and after each mutation, assertions check the installed
  `assertion_engine`, artifacts, telemetry, simulator config/scenario/CLI module
  `__file__` paths against that clone's `src/`, the interpreter prefix against
  that clone's `.venv`, and its offline schema registry. No main-workspace source,
  schema, fixture, test expectation or workflow is changed.
- This is an evidence exercise against existing behavioral tests, with meaningful
  mutation RED. It introduces no tests and makes no new-test TDD claim. Every row
  below runs the exact T030 gate: `uv sync --locked`,
  `uv run ruff format --check .`, `uv run ruff check .`, then
  `MPLBACKEND=Agg uv run pytest`. The first three commands always exit 0 and report
  `79 files already formatted` / `All checks passed!`; only the mutated pytest
  commands exit 1. Every run has zero skips and no collection/import errors.

| Clone / source state | pytest summary | Gate command exit codes, in order |
| --- | --- | --- |
| phase / baseline | `403 passed in 17.01s` | `0, 0, 0, 0` |
| phase / mutated | `8 failed, 395 passed in 13.97s` | `0, 0, 0, 1` |
| phase / restored | `403 passed in 15.56s` | `0, 0, 0, 0` |
| bytes / baseline | `403 passed in 17.43s` | `0, 0, 0, 0` |
| bytes / mutated | `23 failed, 380 passed in 10.33s` | `0, 0, 0, 1` |
| bytes / restored | `403 passed in 15.75s` | `0, 0, 0, 0` |

- Phase mutation: `_document` adds `"phase": "takeoff"` only while converting a
  `TelemetrySnapshot` dataclass. The probe observes 451 seven-field snapshots;
  unchanged shape validation raises
  `snapshots.0: Additional properties are not allowed ('phase' was unexpected)`.
  This violates FR-004's six fields and FR-010's separate ground truth, and
  exercises FR-017/FR-018, SC-002 and SC-006. The primary unchanged failures are
  `tests/contract/test_gate_rejection.py::test_FR011_FR018_SC006_canonical_positive_controls`
  (typed telemetry differs from its independent six-field byte literal) and
  `tests/integration/test_generate_normal_flight.py::test_SC001_three_runs_publish_complete_identical_pairs`
  (CLI expected success receives the specific shape diagnostic before publishing).
  The other six failures are in `tests/integration/test_generate_failures.py`:
  `test_cli_operational_failures_clean_only_invocation_staging` for `mkdir`,
  `staging`, `telemetry.json`, `ground-truth.json`, and `publish`, plus
  `test_cli_created_parents_remain_after_staging_failure`. These are downstream
  failures because the phase rejection occurs before their intended filesystem
  stage; they are not six additional independent contract violations.
- Byte mutation: a module-level `_canonical_calls` counter increments once per
  `canonical_bytes` call and inserts that many spaces **before** the single final
  LF. Three calls for `{"z": [2, 1], "a": "中文"}` produce one/two/three spaces and
  different bytes, with identical decoded JSON and exactly one LF each. The
  unchanged literal three-call assertion
  `tests/contract/test_canonical_serialization.py::test_FR011_sorted_compact_utf8_single_lf_repeated`
  fails on the expected byte mismatch, both within the full gate and directly:
  `1 failed in 0.07s`, exit 1. This establishes FR-011, FR-018 and SC-006 rejection
  without changing JSON semantics or introducing a second LF.
- All 23 byte-mutation failures are accounted for: 13 in
  `tests/contract/test_canonical_serialization.py` (the three-call test, ten
  `test_FR011_calculated_quantization` cases,
  `test_FR011_source_inputs_preserved_derived_values_quantized`, and
  `test_FR011_typed_pair_source_has_identical_canonical_bytes`), the canonical
  positive control above, eight in `tests/integration/test_playback_read_only.py`
  (`test_module_cli_renders_terminal_frame_without_window`,
  `test_complete_control_sequence_never_changes_input_hashes`, three
  `test_render_failure_returns_one_preserves_inputs_and_cleans_staging` cases
  for `OSError`/`ValueError`/`RuntimeError`, `test_gui_normal_close_returns_zero`,
  `test_headless_selects_agg_before_view_and_invalid_output_name_rejects`, and
  `test_installed_script_entrypoint`), and
  `tests/unit/playback/test_loader.py::test_load_immutable_fixture_pair`.
  The contract failures compare against fixed canonical bytes. The nine loader /
  playback failures report `input bytes are not canonical JSON` because the
  mutated serializer no longer reproduces the existing canonical input bytes.
- SC-001 limitation measured explicitly: running its three-CLI-process test with
  the byte mutation still gives `1 passed in 1.03s`, exit 0. Each new process resets
  the counter, serializing telemetry with one space and truth with two. All three
  telemetry hashes are
  `f02793554bb469cc165114c0720c0d237a510745ae21fe5b25fa4723af5a7499`;
  all three truth hashes are
  `cbc72fbc742d912cdaa0b2b6425a4d393e651d21c555963873e3e2c7b2208525`.
  SC-001 alone does not detect this within-process mutation. Its fixed-literal
  FR-011 companion provides the required three-call rejection; the gate is RED
  for that reason. No stronger SC-001 mutation coverage is claimed.
- Both clones restore the saved exact source bytes. Before and after each full
  exercise, every one of the 122 tracked files byte-matches its `git show SHA:path`
  content and `git status --porcelain` is empty. The shared explicit uv dependency
  cache is `/home/luke/.cache/uv`; `.venv` and source identities remain separate.
  Matplotlib config and pytest temporary files use each clone's explicit
  `build/t032-cache/` paths. No shared database or output storage is used.
- Frozen rerunnable proof SHA-256:
  `ccc7ae28a37a58fb7365e4ed3b47428b5c92edc82b80f0568df14f07d054d794`.
  Final command/exit/stdout/stderr records, every failed pytest node ID, probes,
  exact patches and tracked byte manifests are in
  `build/t032-executor-evidence/run-complete/results.json` and adjacent files.
  Replay the unchanged ignored proof with
  `python3 build/t032-executor-evidence/proof.py --repo "$PWD" --sha <reviewed-SHA>
  --output build/t032-review-replay --scratch-prefix /tmp/t032-review-replay
  --uv-cache /home/luke/.cache/uv
  --python /home/luke/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14`.
  Select new output/clone names: the proof refuses preexisting destinations.
  Its SHA argument binds every clone, installed-origin assertion and byte manifest
  to the supplied commit, so later documentation/marker commits can be reviewed.
- Preliminary attempts remain under `run-executor`, `run-host` and `run-final`.
  The first sync failed with sandbox DNS resolution; a slow cold-cache host sync
  was interrupted before any mutation. A Ruff stdin preflight corrected mutation
  formatting before application. An initial valid phase RED stopped at a proof
  parser that expected pytest's optional failure-reason suffix; it restored the
  clone and was superseded by the complete replay above. Environment/preflight
  issues are not counted as contract RED, and incomplete runs are not final PASS.
- Independent review and main replay are still pending at this executor record.
  T033 required-check/whole-gate acceptance and full M0 acceptance remain pending.

### Self-contained T032 reproduction without ignored evidence files

Run from a checkout containing the chosen source commit with uv `0.11.9` and an
available CPython `3.14` interpreter. Use a new `/tmp` prefix below; both suffixed
clone paths must be absent. Optional `UV_CACHE_DIR` and `UV_PYTHON` select an
explicit writable cache and interpreter. Otherwise caches are created inside
each clone and uv selects Python from the committed `.python-version`; cold
caches require normal dependency-download access. The snippet prints raw runner
output, checks expected exits and primary failure identities, restores only its
own mutation, and verifies all tracked bytes and clean status. Replace the SHA
argument with the reviewed documentation/marker commit when replaying that slice.

```sh
python3 - "$PWD" b6a7ca914ea404db45ab597c17a6d321ba4c3bd2 /tmp/t032-reproduction-new <<'PY'
import importlib
import os
from pathlib import Path
import subprocess
import sys

repo, sha, prefix = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3])
clones = [Path(str(prefix) + "-" + kind) for kind in ("phase", "bytes")]
assert all(p.resolve().is_relative_to(Path("/tmp")) and not os.path.lexists(p) for p in clones)
source_path = "src/assertion_engine/artifacts.py"
phase_old = '''    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _document(getattr(value, field.name)) for field in fields(value)
        }
'''
phase_new = '''    if is_dataclass(value) and not isinstance(value, type):
        document = {
            field.name: _document(getattr(value, field.name)) for field in fields(value)
        }
        if isinstance(value, TelemetrySnapshot):
            document["phase"] = "takeoff"
        return document
'''
counter_old = 'DERIVED_CONFIG_FIELDS = {"sample_rate_hz", "sample_interval_s"}\n'
counter_new = counter_old + "_canonical_calls = 0\n"
byte_old = '''    try:
        return (_encode(_document(value)) + "\\n").encode("utf-8")
'''
byte_new = '''    global _canonical_calls
    _canonical_calls += 1
    try:
        return (_encode(_document(value)) + " " * _canonical_calls + "\\n").encode(
            "utf-8"
        )
'''
fr011 = "tests/contract/test_canonical_serialization.py::test_FR011_sorted_compact_utf8_single_lf_repeated"
phase_target = "tests/contract/test_gate_rejection.py::test_FR011_FR018_SC006_canonical_positive_controls"
sc001 = "tests/integration/test_generate_normal_flight.py::test_SC001_three_runs_publish_complete_identical_pairs"
identity = '''import importlib, sys
from pathlib import Path
root = Path.cwd().resolve()
for name in ("assertion_engine", "assertion_engine.artifacts", "assertion_engine.telemetry",
             "assertion_engine.simulator.config", "assertion_engine.simulator.scenario", "assertion_engine.simulator.cli"):
    path = root / "src" / (name.replace(".", "/") + ".py")
    if name == "assertion_engine":
        path = root / "src/assertion_engine/__init__.py"
    origin = Path(importlib.import_module(name).__file__).resolve()
    assert origin == path, (name, origin, path)
    print(name, origin)
assert Path(sys.prefix).resolve() == root / ".venv"
assert sys.version_info[:2] == (3, 14)
'''
commands = [["uv", "sync", "--locked"], ["uv", "run", "ruff", "format", "--check", "."],
            ["uv", "run", "ruff", "check", "."], ["uv", "run", "pytest"]]

def run(command, expected=0):
    result = subprocess.run(command, cwd=clone, env=env, capture_output=True, text=True)
    print("COMMAND", command, "EXIT", result.returncode, flush=True)
    print(result.stdout, end="", flush=True)
    print(result.stderr, end="", file=sys.stderr, flush=True)
    assert result.returncode == expected, (command, result.returncode)
    return result.stdout

def unchanged():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=clone, text=True).strip() == sha
    for name in subprocess.check_output(["git", "ls-files", "-z"], cwd=clone).split(b"\0"):
        if name:
            path = name.decode()
            assert (clone / path).read_bytes() == subprocess.check_output(["git", "show", sha + ":" + path], cwd=clone), path
    assert subprocess.check_output(["git", "status", "--porcelain"], cwd=clone) == b""

def gate(mutated=False):
    for index, command in enumerate(commands):
        if index == 3:
            env["MPLBACKEND"] = "Agg"
        output = run(command, 1 if mutated and index == 3 else 0)
        if index == 0:
            run(["uv", "run", "python", "-c", identity])
    if mutated:
        assert "FAILED " + (phase_target if kind == "phase" else fr011) in output

for kind, clone in zip(("phase", "bytes"), clones):
    subprocess.run(["git", "clone", "--no-hardlinks", "--no-checkout", "--", str(repo), str(clone)], check=True)
    subprocess.run(["git", "checkout", "--detach", sha], cwd=clone, check=True)
    env = dict(os.environ)
    for variable in ("PYTHONPATH", "PYTEST_ADDOPTS", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT"):
        env.pop(variable, None)
    for variable, suffix in (("UV_CACHE_DIR", "uv"), ("MPLCONFIGDIR", "matplotlib"), ("TMPDIR", "tmp")):
        directory = clone / "build/t032-cache" / suffix
        directory.mkdir(parents=True)
        env[variable] = os.environ[variable] if variable == "UV_CACHE_DIR" and variable in os.environ else str(directory)
    unchanged()
    gate()
    path = clone / source_path
    original = path.read_bytes()
    text = original.decode()
    replacements = [(phase_old, phase_new)] if kind == "phase" else [(counter_old, counter_new), (byte_old, byte_new)]
    for old, new in replacements:
        assert text.count(old) == 1
        text = text.replace(old, new, 1)
    try:
        path.write_text(text)
        gate(mutated=True)
        if kind == "bytes":
            assert "At index 0 diff" in run(["uv", "run", "pytest", fr011], 1)
            run(["uv", "run", "pytest", "-s", sc001])
    finally:
        path.write_bytes(original)
        unchanged()
    gate()
    unchanged()
PY
```


## T032 approval and main replay — 2026-10-08

- Fresh independent review APPROVED the complete
  `b6a7ca914ea404db45ab597c17a6d321ba4c3bd2..9d7875305b5a277ced11e0df5b58d2351c14cf01`
  slice (`validation.md` and the T032 awaiting-review marker), without findings.
  Reviewer phase gate: `403 passed in 18.88s` →
  `8 failed, 395 passed in 14.78s` → `403 passed in 16.10s`.
  Reviewer byte gate: `403 passed in 18.26s` →
  `23 failed, 380 passed in 10.50s` → `403 passed in 16.54s`.
- Main replayed the reviewer's frozen `final-proof.py` unchanged at reviewed SHA
  `9d7875305b5a277ced11e0df5b58d2351c14cf01`, using two fresh separately installed
  clones at `/tmp/assertion-engine-t032-main-reviewer-final-{phase,bytes}`.
  Phase gate: `403 passed in 18.21s` →
  `8 failed, 395 passed in 15.57s` → `403 passed in 15.44s`.
  Byte gate: `403 passed in 16.54s` →
  `23 failed, 380 passed in 9.79s` → `403 passed in 15.27s`.
  Each sync/format/lint exits 0; only mutated full-suite pytest exits 1.
  All full gates have zero skips. The direct byte assertion reports
  `1 failed in 0.08s`; direct SC-001 reports `1 passed in 0.99s` with the same
  documented counter-reset limitation and three identical hash pairs.
- Main also reran the independent read-only inspection: committed reproduction
  code compiles, mutation constants/targets/gate commands match the frozen proof,
  installed-source assertions hold, failure groups match raw logs, and all
  122 tracked files in both restored clones and the pinned review checkout
  byte-match the reviewed SHA with empty Git status. Main separately checked
  the intended raw phase/byte diagnostics and Ruff summaries.
- The final proof retains SHA-256
  `ccc7ae28a37a58fb7365e4ed3b47428b5c92edc82b80f0568df14f07d054d794`.
  Main command records, raw logs, probes, patches and manifests are under
  `build/t032-main-evidence/run-reviewer-final-proof/`; independent inspection
  is `build/t032-main-evidence/final-inspection.json`. Reviewer findings and
  final proof are under `build/t032-reviewer-evidence/`.
  Replay with the prior proof CLI, the reviewed SHA above, and new destinations;
  the committed reproduction block remains sufficient without ignored files.
- T032 promotes to `[X]` only in this separate post-approval commit.
  T033–T036, whole-gate/required-check acceptance and full M0 acceptance remain
  pending. PR `#5` stays draft.

## T033 — clean gate and effective required-check acceptance — 2026-10-08

- Source baseline: `1f3ba71fffee02f030902c21dbe7685c34b11d38`.
  Executor cloned it into the new detached checkout
  `/tmp/assertion-engine-t033-executor-run1`, with its own installed `.venv`.
  CPython `3.14.4`, uv `0.11.9`. Before and after verification, all 122 tracked
  files byte-match `git show <SHA>:<path>` and Git status is empty. Installed
  package, artifact, telemetry, Simulator and playback module origins resolve
  into this checkout's `src/`; interpreter prefix is its `.venv`. The three
  offline validators' schemas match this checkout's committed schema files,
  and installed console entrypoints match `pyproject.toml`.
- The four commands below exactly match `.github/workflows/ci.yml`; each exits 0.
  The full runner reports zero failures, errors or skips. Pytest temporary files
  and Matplotlib configuration use explicit checkout-local cache directories;
  dependencies use the explicitly selected `/home/luke/.cache/uv` cache.

| Exact CI/local entrypoint | Executor raw result |
| --- | --- |
| `uv sync --locked` | exit `0` |
| `uv run ruff format --check .` | `79 files already formatted` |
| `uv run ruff check .` | `All checks passed!` |
| `MPLBACKEND=Agg uv run pytest` | `403 passed in 18.52s` |

- Installed `uv run assertion-sim generate --scenario scenarios/normal-flight.toml
  --output build/artifacts/t033-normal-run` and `MPLBACKEND=Agg uv run
  assertion-playback --telemetry build/artifacts/t033-normal-run/telemetry.json
  --ground-truth build/artifacts/t033-normal-run/ground-truth.json
  --headless-output build/artifacts/t033-normal-run/terminal.png` both exit 0.
  Generation publishes exactly the two JSON files into a previously absent
  explicit destination, and its stdout paths/hashes match those files. Assertions
  verify telemetry `1.0.0`, ground truth `2.0.0`, matching source, canonical bytes,
  451 snapshots with exactly the six contract fields, contiguous indices 0–450,
  increasing mission time 0–45 s, five ordered phases with sequence boundaries
  `0, 100, 150, 250, 350`, terminal origin/zero velocity/91% battery, and a valid
  fully decodable 1440 × 960 PNG. Playback preserves both input hashes:
  telemetry `1cc55ccd8ba9fa11d2c242704ad5503d0e82635bb22c1c2c654cbcffe540494b`;
  ground truth `b12d092c618dc03f06e63984cfba3a10d9c3d712535dca747784422c38e6fac7`.
  This is CLI/headless acceptance; it adds no interactive or SC-005 visual claim.
- Permanent T028 negatives and T027/T029 scanner controls pass independently with
  `MPLBACKEND=Agg uv run pytest -v tests/contract/test_gate_rejection.py
  tests/architecture/test_dependency_boundaries.py`: `81 passed in 0.75s`,
  zero failures, errors or skips. These are six fixed-literal contract controls,
  24 forbidden-import cases, 24 allowed-import cases, one multi-target/location
  case, 15 reserved-package executable-content cases, nine empty-placeholder
  controls and two production scans. Direct calls to the existing validator and
  scanner also confirm the specific diagnostics below and no production boundary
  or reserved-package violations. The noncanonical fixture still has valid paired
  semantics; the independent literal byte assertion rejects its extra LF.

| Permanent fixture | Observed rejection / requirement |
| --- | --- |
| `extra-phase.telemetry.json` | `snapshots.0: Additional properties are not allowed ('phase' was unexpected)`; FR-004/FR-010, SC-002 |
| `missing-field.telemetry.json` | `snapshots.0: 'battery_percent' is a required property`; FR-004, SC-002 |
| `wrong-sequence.telemetry.json` | `snapshots[2].sequence_number is not contiguous`; FR-006, SC-002 |
| `mismatched-source.ground-truth.json` | `artifact pair scenario source differs`; FR-011 |
| `noncanonical.telemetry.json` | `FR-011/FR-018 SC-006: noncanonical bytes`; independent byte control |

- Existing T032 evidence was audited, without repeating its six gates per run.
  Frozen `build/t032-reviewer-evidence/final-proof.py` retains SHA-256
  `ccc7ae28a37a58fb7365e4ed3b47428b5c92edc82b80f0568df14f07d054d794`.
  Reviewer `run-review/results.json` and main
  `run-reviewer-final-proof/results.json` agree with their raw stdout/stderr:
  every baseline/restored gate is `403 passed`, each mutated gate has first-three
  exits `0, 0, 0` and pytest exit `1`; phase mutation yields `8 failed, 395 passed`,
  byte mutation `23 failed, 380 passed`. Failure node IDs, group counts, phase
  shape diagnostic and the literal three-call byte mismatch match the T032 record.
  Semantic probes, installed origins and all 122-file before/restored/final byte
  manifests were checked against their historical reviewed SHA `9d787530...`.
  Source, tests, scenarios, workflow, package/lock files and schemas are unchanged
  between that SHA and this baseline, making the approved mutation evidence
  applicable to this clean gate. T032's self-contained reproduction above remains
  the procedure for freshly exercising both mutations without ignored artifacts.
- The measured counter-reset limitation remains: under T032's byte mutation,
  direct within-process FR-011 is RED, while direct SC-001's three fresh CLI
  processes are GREEN with identical three-run hashes. T033 does not claim
  SC-001 detected that mutation. Together, the clean gate, permanent controls
  and audited isolated contract/byte failures support FR-016–FR-018 and SC-006.
  This evidence/documentation slice adds no tests or product code and makes no
  new-test TDD RED claim.
- Main's live GitHub reads completed between `2026-10-08T13:48:26Z` and
  `13:49:46Z` (21:48:26–21:49:46 +0800). Executor independently reconciled their
  raw responses and JSON snapshots. PR #5's latest head is the baseline SHA above;
  actual [pull_request check](https://github.com/lukeking/assertion-engine/actions/runs/37779250537/job/113317867905)
  and [push check](https://github.com/lukeking/assertion-engine/actions/runs/37779244011/job/113317841615)
  both have context `change-gate`, source GitHub Actions app `15368`, completed
  status and `success` conclusion. `gh pr checks 5 --required` reports both
  `change-gate` executions SUCCESS. Both hosted run/job snapshots also show all
  four exact gate steps successful at that same head SHA.
- Live `repos/lukeking/assertion-engine/rules/branches/main` read-back includes
  effective required checks from ruleset `20876648`: context `change-gate`,
  `integration_id: 15368`, `strict_required_status_checks_policy: true`,
  `do_not_enforce_on_create: false`. Full ruleset read-back is active, includes
  only `refs/heads/main`, excludes no refs, has an empty bypass list, and retains
  deletion/non-fast-forward/pull-request rules. These names and source IDs match
  the actual required PR checks. The head has no competing legacy commit-status
  entries.
- Missing/failed merge blocking is verified at the effective-policy boundary:
  GitHub's [required-check ruleset semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
  require the specified check and source before merging, and
  [required-check troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)
  distinguishes a missing/pending or failed required check from accepted
  success/skipped/neutral conclusions on the latest SHA. Strict mode also requires
  an up-to-date branch. Applying those documented semantics to the read-back
  policy establishes the missing/failed restriction; no blocked-merge request or
  disposable remote PR experiment was performed. This hosted policy has no local
  server test runner, so verification is explicitly degraded to live policy,
  actual checks and official semantics. `MERGEABLE / CLEAN` and draft state are
  not used as evidence for that restriction; PR #5 remains open/draft.
- Local command/exit/raw-output records, hashes and manifests:
  `build/t033-executor-evidence/run-executor/`; GitHub raw read-backs:
  `build/t033-main-evidence/github/`; their independent reconciliation:
  `build/t033-executor-evidence/github-audit.json`. The standalone local proof's
  SHA-256 is `e27c43b425c1f33209189ceaaf1a3b140fb98f17e9a41074426c4157334ce40b`.
  Replay unchanged with new destinations (historical T032 artifacts must remain
  under the supplied repository's `build/`):

```sh
python3 build/t033-executor-evidence/proof.py --repo "$PWD" \
  --sha 1f3ba71fffee02f030902c21dbe7685c34b11d38 \
  --output build/t033-review-replay \
  --scratch /tmp/assertion-engine-t033-review-replay \
  --uv-cache /home/luke/.cache/uv \
  --python /home/luke/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14
python3 build/t033-executor-evidence/github-audit.py \
  --snapshots build/t033-main-evidence/github \
  --output build/t033-review-github-audit.json
```

For an independent local rerun when ignored proofs are unavailable, create a new
detached checkout at the source SHA above, select uv `0.11.9` and CPython `3.14`,
and set explicit writable `UV_CACHE_DIR`, `MPLCONFIGDIR` and `TMPDIR` destinations.
Unset inherited `PYTHONPATH`, `PYTEST_ADDOPTS`, `VIRTUAL_ENV` and
`UV_PROJECT_ENVIRONMENT`. Check every tracked file against `git show SHA:path`
and empty status before/after; after locked sync assert installed module origins
and `.venv` prefix belong to that checkout, and `_validators()` schema documents
equal its three committed schemas. Run the four exact table commands, the focused
controls command and the two exact CLI commands above; use a new absent generation
directory and an existing explicit PNG parent. Hash both inputs before/after
playback, validate their pair, and check six fields/451 snapshots, source/versions,
terminal state and full PNG decoding as specified above. The committed assertions
in the unchanged focused tests supply the literal fixture and scanner oracles.

Re-read GitHub policy/checks with these read-only commands; obtain `HEAD_SHA` from
the live PR response and substitute the current hosted run IDs before reviewing
a later head. Confirm all four job steps, check source/name/head and full ruleset
scope/enforcement/bypass conditions again; prior snapshots do not prove a later
head's checks:

```sh
gh api repos/lukeking/assertion-engine/rules/branches/main
gh api repos/lukeking/assertion-engine/rulesets/20876648
gh api repos/lukeking/assertion-engine/pulls/5
gh pr checks 5 --repo lukeking/assertion-engine --required \
  --json name,state,bucket,event,link,workflow
gh api repos/lukeking/assertion-engine/commits/HEAD_SHA/check-runs
gh api repos/lukeking/assertion-engine/commits/HEAD_SHA/status
gh run view 37779250537 --repo lukeking/assertion-engine \
  --json headSha,event,status,conclusion,jobs,url
gh run view 37779244011 --repo lukeking/assertion-engine \
  --json headSha,event,status,conclusion,jobs,url
```

T033 awaits independent review and main replay. T034–T036 and full M0 acceptance
remain pending; this record does not mark the feature ready to merge.

## T033 approval and main replay — 2026-10-08

- Fresh independent review APPROVED the full
  `1f3ba71fffee02f030902c21dbe7685c34b11d38..ccb466a060551edcb88ad231ee9b257bd9881463`
  slice without blocking or non-blocking findings. The reviewed diff contains
  only the appended validation evidence and T033's awaiting-review marker.
  Reviewer exact gate: `403 passed in 18.77s`; permanent fixture/scanner controls:
  `81 passed in 0.75s`. Both have zero failures, errors or skips; locked sync and
  Ruff format/lint pass. Installed CLI smoke reproduces the two recorded hashes,
  validates the 451-snapshot pair and PNG, and preserves input bytes.
- Main replayed the reviewer's frozen `final-proof.py` unchanged at reviewed SHA
  `ccb466a060551edcb88ad231ee9b257bd9881463`, in the newly installed checkout
  `/tmp/assertion-engine-t033-main-reviewer-final`. Main exact gate:
  `403 passed in 17.10s`; permanent controls: `81 passed in 0.77s`, zero failures,
  errors or skips. Sync/format/lint and both CLI commands exit 0; source/schema
  identities, canonical pair assertions and unchanged input hashes hold.
- Reviewer and main independently exercise a new alternating-LF byte mutation
  only in their respective scratch checkouts: the three calls yield one, two,
  then one trailing LF while decoding to the same JSON. The unchanged FR-011
  fixed-literal three-call assertion fails at index 1, with
  `1 failed in 0.07s` / `1 failed in 0.06s`, respectively. Mutation format/lint
  pass. Restoring saved exact source bytes makes the direct test pass again:
  `1 passed in 0.05s` for both. This is independent review mutation evidence,
  not a new-test TDD claim or a stronger SC-001 claim.
- Both proofs reconcile the historical T032 raw outputs, command records,
  identities, probes and byte manifests, and confirm unchanged gate-related
  content. They also independently read live effective main rules/full ruleset
  and reviewed-head required checks. Reviewed-SHA
  [PR job](https://github.com/lukeking/assertion-engine/actions/runs/37789007813/job/113351071054)
  and [push job](https://github.com/lukeking/assertion-engine/actions/runs/37789000820/job/113351046357)
  both succeed with all four gate steps, context `change-gate` and app `15368`.
  Active ruleset `20876648` retains strict required checks, exact main scope and
  no bypass. The reported test-merge SHA has no checks or commit statuses.
  The effective-policy/no-attempted-merge verification boundary above is unchanged.
- Main separately inspects the raw runner summaries, command metadata and intended
  `At index 1 diff` diagnostic, then checks every tracked byte in the pinned review
  checkout, reviewer proof checkout and main proof checkout against the reviewed
  SHA: all three cover 122 files and have empty Git status. Main's read-only
  inspection is `build/t033-main-evidence/final-inspection.json`; replay outputs
  are under `build/t033-main-evidence/run-reviewer-final-proof/`. Reviewer findings,
  raw proof and executor-record inspection are under `build/t033-reviewer-evidence/`.
- Frozen reviewer proof SHA-256:
  `18d8df4f87326f298f8e3f3a2daac9425970578d48ee1d61c9e2c61c629e7a25`.
  Replay uses the same CLI arguments as the local proof above with this reviewer
  script and reviewed SHA, plus new output/scratch destinations. The full review
  proof additionally binds live PR head to the reviewed SHA; main ran it before
  pushing the completion marker. After the head advances, use the standalone
  current-head gate/CLI/policy procedure above for fresh acceptance rather than
  treating historical checks as evidence for the new head.
- T033 promotes to `[X]` only in this separate post-approval commit. CP5 acceptance
  is complete at the documented evidence boundaries. T034–T036 and full M0
  acceptance remain pending; PR `#5` stays draft.

## T034 — repeatable quickstart acceptance — 2026-10-09

- Product baseline: `d0201de56111f14307d7a337f13dfa9e5315a003`.
  Executor used the new detached checkout
  `/tmp/assertion-engine-t034-executor-run2`, CPython `3.14.4` and uv
  `0.11.9`. Before/after the baseline gate, all 122 tracked files byte-match
  that SHA and Git status is empty. Final verification permits only the updated
  quickstart overlay; every other tracked file, including source/tests/schemas,
  scenarios, package/lock files and workflow, still matches the baseline bytes.
  Installed package, artifact and both CLI module origins resolve into the
  disposable checkout's `src/`; interpreter prefix is its own `.venv`.
  Installed console entrypoints match `pyproject.toml`, and the three offline
  validator schemas match that checkout's committed schema files.
- The updated walkthrough names exactly three absent destinations:
  `build/artifacts/quickstart-normal-run-1`, `-2` and `-3`. The proof reads
  and executes the final guide's shell blocks, including Python installation,
  locked sync, generation, explicit six-file hash comparison, overwrite refusal,
  headless playback and the final gate. The interactive block is covered
  separately below. Executed guide SHA-256:
  `89e37d48f764dbfa23afe14381b71212a3759009d40ccc91a22f9092a4f8a448`.
- Sandbox setup failures remain visible: default `uv python find 3.14` exits
  `2` because the default uv cache is read-only; the first disposable sync
  exits `1` because sandbox DNS cannot refresh Hatchling metadata from PyPI.
  Raw records are `build/t034-executor-evidence/00-environment-probe*` and
  `run-executor/04-baseline-gate-1.*`. The successful run copies the existing
  uv cache and managed Python installation into explicit checkout-local
  `build/t034-cache/` directories, selects writable Matplotlib configuration,
  Python-bin and temporary directories there, and sets `UV_OFFLINE=1`.
  `UV_NO_SYNC` and inherited Python/pytest/project-environment overrides are
  removed. These are dependency/environment failures, not contract negatives.
  No documented gate command is changed.

| Exact unchanged CI/local entrypoint | Clean baseline | Final documented gate |
| --- | --- | --- |
| `uv sync --locked` | exit `0` | exit `0` |
| `uv run ruff format --check .` | `79 files already formatted` | `79 files already formatted` |
| `uv run ruff check .` | `All checks passed!` | `All checks passed!` |
| `MPLBACKEND=Agg uv run pytest` | `403 passed in 21.69s` | `403 passed in 18.64s` |

- Both full pytest runs have zero failures, errors or skips. This documentation
  and acceptance slice adds no product tests or code, uses no e2e suite, and
  makes no test-first RED claim. No static typechecker is configured.
- Each of the three installed generate commands exits `0` and initially
  publishes exactly `telemetry.json` and `ground-truth.json`. Explicit
  `sha256sum` output contains exactly those six paths; the three telemetry
  files share `1cc55ccd8ba9fa11d2c242704ad5503d0e82635bb22c1c2c654cbcffe540494b`,
  and the three ground-truth files share
  `b12d092c618dc03f06e63984cfba3a10d9c3d712535dca747784422c38e6fac7`.
  This directly establishes SC-001 for the unchanged normal scenario/config/seed.
- Retrying run 1 returns exit `2` and `target already exists`; both JSON
  hashes and the complete destination tree remain unchanged. The documented
  exit check is the final conditional expression, so an unexpected exit cannot
  be hidden by a later successful checksum command. Replaying that block with
  an intentionally wrong expected exit `0` returns `1` without running the
  checksum check. A copied telemetry file with one appended space makes
  `sha256sum --check` return `1` and report telemetry `FAILED`, while copied
  ground truth remains `OK`; primary inputs are retained. Changing only the
  disposable `pyproject.toml` jsonschema upper bound from `<5` to `<6`
  makes `uv sync --locked` return `1` with the stale-lock diagnostic; saved
  exact bytes are restored before the final gate.
- Installed Agg playback exits `0`, writes a fully decodable 1440 × 960 PNG
  into run 1's existing parent, and preserves both JSON input hashes. Real
  validators confirm canonical telemetry `1.0.0` / ground truth `2.0.0`,
  matching source, 451 snapshots with exactly six fields, contiguous sequence
  numbers 0–450, increasing mission time 0–45 s, five ordered phases with
  sequence boundaries `0, 100, 150, 250, 350`, terminal origin/zero velocity
  and 91% battery. Main independently opened the generated PNG and observed
  the readable landing/45 s/snapshot 450/completed label, origin marker,
  terminal zero altitude/speed, 91% battery, five phase bands and synchronized
  terminal cursors.
- Main separately runs the actual installed playback `cli.main`, original
  `MatplotlibView.show()`, native Tk mainloop and product `TimerTk` on the
  available host display using `TkAgg`. Evidence records 13 control
  checkpoints, 11 native Tk widget release events, 42 real timer ticks and
  CLI exit `0`. Automated native canvas events exercise Play, Pause,
  one-snapshot Step, speed and Restart; observed mission times/cursors stay tied
  to saved snapshots, and input/domain bytes remain equal. This is actual
  native GUI execution with generated events, not human manual interaction.
  Main opened its 1200 × 800 terminal canvas image and observed the same
  terminal route/plots/phase/time checks. Sandbox Tk cannot reach the display,
  so the native run uses host execution. The first GUI instrumentation attempt
  failed before Play because the canvas was not primed; only scratch
  instrumentation was corrected, and both attempts' raw logs are retained.
- CLI/headless raw commands, exit codes, summaries, hash/tree records,
  identities, negative controls and 122-file byte manifests are under
  `build/t034-executor-evidence/run-executor-offline/`. Frozen scratch proof
  SHA-256: `a57f4359ce00109872d620618ef30b39fed77ddb7add6caf197dab5dd82983a6`.
  Native GUI controls/ticks/events/images and byte records are under
  `build/t034-main-evidence/native-gui-retry-run/`; command/raw logs are
  `native-gui-retry-command.json`, `native-gui-retry.stdout` and
  `native-gui-retry.stderr` in their parent evidence directory.

Replay the local proof with new output and scratch destinations; `--guide`
selects the current documented commands while product bytes remain pinned:

```sh
python3 build/t034-executor-evidence/proof.py --repo "$PWD" \
  --sha d0201de56111f14307d7a337f13dfa9e5315a003 \
  --output build/t034-executor-evidence/replay-new \
  --scratch /tmp/assertion-engine-t034-replay-new \
  --uv-cache-source /home/luke/.cache/uv \
  --python /home/luke/.local/share/uv/python/cpython-3.14.4-linux-x86_64-gnu/bin/python3.14 \
  --guide specs/001-telemetry-simulator/quickstart.md
MPLBACKEND=TkAgg uv run python build/t034-main-evidence/native_gui.py \
  --repo "$PWD" --sha d0201de56111f14307d7a337f13dfa9e5315a003 \
  --telemetry build/artifacts/t034-main-native-gui/telemetry.json \
  --ground-truth build/artifacts/t034-main-native-gui/ground-truth.json \
  --output build/t034-main-evidence/native-gui-replay-new
```

When ignored proof files are unavailable, create a new detached checkout at
the baseline SHA, copy the current quickstart there, select Python 3.14/uv
0.11.9 and explicit writable cache/configuration/temporary paths, and unset
inherited Python/pytest/project-environment overrides including `UV_NO_SYNC`.
Run the four table entrypoints, then the numbered quickstart commands exactly.
Require three equal hashes per artifact, overwrite exit `2` with unchanged
inputs/tree, a valid terminal PNG and both post-playback checksum results `OK`.
Use a real available GUI backend/display for its separate interactive controls
and visual checks; closing the window normally must return exit `0`.
Compare all product files against the pinned SHA before/after. The guide's
explicit names and expected outcomes supply the committed reproduction path;
the scratch drivers supplement it with captured assertions and raw records.

T034 awaits independent review and main replay. T035–T036 and full M0 acceptance
remain pending; this record does not mark the feature ready to merge.

## T034 approval and main replay — 2026-10-09

- Fresh independent review APPROVED the complete
  `d0201de56111f14307d7a337f13dfa9e5315a003..6b24846f81e13328025b7648e229fb72d553066e`
  slice without blocking or non-blocking findings. It covers quickstart,
  appended validation evidence and T034's awaiting-review marker only.
  Reviewer exact gate: `403 passed in 21.07s`, zero failures/errors/skips;
  locked sync exits 0, Ruff reports `79 files already formatted` and
  `All checks passed!`.
- Main replayed the reviewer's standalone frozen `final-proof.py` unchanged,
  SHA-256 `bfe94005b769abe330b7ed1a0d7a7a44a4c57b87a814eb361c02e9069948fef9`,
  at the reviewed SHA in `/tmp/assertion-engine-t034-main-reviewer-final`.
  Main exact gate: `403 passed in 20.77s`, zero failures/errors/skips;
  locked sync and both Ruff commands pass. All documented noninteractive
  blocks, installed CLI stdout paths/hashes, exact six-path hash comparison,
  valid terminal PNG and unchanged input hashes pass. Expected overwrite
  exit 2, deliberately wrong expected-exit rejection, copied-file checksum
  failure and separate stale-lock rejection/restoration all reproduce.
- Reviewer and main independently mutate only scratch `PlaybackSession.step()`
  to skip one saved event. Unchanged
  `test_pause_settles_elapsed_time_and_step_is_exactly_one` fails at cursor
  `3` versus required `2`, while mutation Ruff format/lint remain green.
  Reviewer: `1 passed in 0.15s` → `1 failed in 0.18s` → `1 passed in 0.17s`;
  main: `1 passed in 0.15s` → `1 failed in 0.17s` → `1 passed in 0.17s`.
  These are assertion-bite checks, not new test-first TDD claims.
- Both final proofs execute native Tk through actual installed `cli.main`,
  original `show()`, Tk mainloop and product TimerTk: each records 13 control
  checkpoints, 11 native release events, 44 real ticks and CLI exit 0.
  Inputs/domain bytes remain equal. Main separately matches numeric requested
  widget coordinates to all native release coordinates, confirms explicit
  canvas initialization, and actually opens both fresh headless and native
  canvas PNGs: terminal labels, origin, zero altitude/speed, 91% battery,
  ordered five-phase bands and synchronized cursors are readable and correct.
- Reviewer retained the initial timestamp-valid bytecode restoration failure
  and sandbox TkAgg display failure. The final proof disables bytecode writes
  before new clones and uses authorized host display access. Main preserves
  that proof and environment unchanged. Main independently reads all 30 raw
  command records, intended mutation diagnostic and runner summaries, then
  byte-checks all seven retained reviewer checkouts plus both main checkouts:
  each has 122 tracked files matching the reviewed SHA and empty Git status.
  Root product source/tests/schemas/workflow are unchanged.
- Reviewer report/replay/raw inspection are under `build/t034-reviewer-evidence/`;
  main raw replay is `build/t034-main-evidence/run-reviewer-final-proof/`, and
  separate raw/coordinate/byte inspection is `final-inspection.json` in its
  parent directory. The local replay command above accepts the frozen reviewer
  driver in place of the executor driver, the reviewed SHA, new destinations,
  no `--guide` overlay and `--gui required`; `REPLAY.md` holds the exact command.
  The committed quickstart and standalone procedure remain available when
  ignored evidence is absent.
- T034 promotes to `[X]` only in this separate post-approval commit. T035–T036,
  CP6 and full M0 acceptance remain pending; PR `#5` stays draft.

## T035 — requirement and algorithm concordance — 2026-10-09

This section consolidates FR-001–FR-018 and SC-001–SC-006. The current local
source baseline is `f33e76ef782013dece8b77bb906c4378fef9bd38`; T035 changes
only this evidence document. It adds no product behavior or tests and claims
no new-test TDD RED. T036 and whole-feature closeout remain pending.

The executor's fresh detached checkout is
`/tmp/assertion-engine-t035-executor-before`, with its own `.venv`. Installed
package, all ten inspected module origins, both console entrypoints and all
three offline schema documents resolve to that checkout. Its 122 tracked
files byte-match the baseline before/after the gate, and Git status is empty.
Environment: Linux x86_64, WSL2 kernel `6.6.87.2`, glibc `2.39`, CPython
`3.14.4`, uv `0.11.9`, Matplotlib `3.11.2`, jsonschema `4.26.0`, pytest `9.1.1`,
Ruff `0.16.10`, package `0.1.0`. Telemetry/config/source/scenario versions are
`1.0.0`; ground truth is `2.0.0`, with required sequence ownership boundaries.
Dependency versions remain locked in `uv.lock`.

Dependencies and managed Python were copied from the prior explicit T034
scratch environment into the new evidence directory. Writable uv/Python-bin,
Matplotlib configuration and temporary paths are explicit there; `UV_OFFLINE=1`
and `PYTHONDONTWRITEBYTECODE=1`. Inherited Python/pytest/project-environment
overrides, including `UV_NO_SYNC`, are removed. Tests write only to pytest's
`tmp_path`; rate artifacts use new explicit evidence destinations. No e2e suite
or typechecker is configured. The gate commands are unchanged:

| Exact CI/local entrypoint | Fresh baseline | Final evidence replay |
| --- | --- | --- |
| `uv sync --locked` | exit `0` | exit `0` |
| `uv run ruff format --check .` | `79 files already formatted`; exit `0` | `79 files already formatted`; exit `0` |
| `uv run ruff check .` | `All checks passed!`; exit `0` | `All checks passed!`; exit `0` |
| `MPLBACKEND=Agg uv run pytest` | `403 passed in 23.52s`; exit `0` | `403 passed in 22.32s`; exit `0` |

Both runners have zero failures/errors/skips. Final replay uses the new pinned
`/tmp/assertion-engine-t035-executor-final` checkout with the same versions and
installed-source/schema checks; all 122 tracked files remain byte-identical and
its Git status is empty. Intermediate replay also passed `403 passed in 21.82s`.
Before/current/final raw evidence is retained in
`build/t035-executor-evidence/{before,current,final}/`; final `commands.json`
captures each command's own environment snapshot. Preliminary driver Ruff
checks caught import/long-string style issues, and inspection found that a shared
metadata dictionary retroactively added the Agg flag to earlier command records.
Both scratch-driver issues were repaired before the final replay; neither was a
product behavior failure or TDD RED. Final explicit driver Ruff checks pass.

The following exact node IDs were checked against pytest collection and their
assertions were read, including literal state/byte tables, rejected inputs,
artist data and immutable-input checks. A row identifies representative tests;
the entire 403-test gate ran. Visual and remote-policy claims additionally need
the historical evidence linked in their rows; a passing test name alone does
not provide those forms of acceptance.

| Requirement | Exact current test node ID(s) | Assertion / complementary evidence |
| --- | --- | --- |
| FR-001 | `tests/unit/simulator/test_config.py::test_FR001_baseline_normalization_and_exact_rate`; `tests/integration/test_generate_failures.py::test_cli_invalid_config_has_no_parent_side_effects[hover_duration_s = 5.0-hover_duration_s = 5.0000004-terminal]` | Explicit seed/source and exact rate; even a terminal time that rounds to 45 s is rejected with exit 2 before parent/final creation. The full config suite also checks required fields, types, ranges and representable metadata. |
| FR-002 | `tests/unit/simulator/test_scenario.py::test_FR002_baseline_literal_states_and_half_open_boundaries` | Literal states before/at each boundary and terminal origin/zero velocity; exactly five ordered ground-truth phases. |
| FR-003 | `tests/integration/test_generate_normal_flight.py::test_T013_checked_in_baseline_matches_literal_source`; `tests/unit/simulator/test_scenario.py::test_FR003_four_supported_rates[0.2-10-0.1-451-boundaries0]` | Checked-in 2 m/s and 0.2 m inputs yield 10 Hz. All four parameter IDs, generated artifacts and constitution/research concordance are recorded below. |
| FR-004 | `tests/contract/test_artifact_schemas.py::test_FR004_literal_pair_and_immutable_types`; `tests/integration/test_generate_normal_flight.py::test_SC001_three_runs_publish_complete_identical_pairs` | Immutable six-field types; the installed CLI's 451 snapshots each equal a complete independent six-field state oracle. |
| FR-005 | `tests/contract/test_artifact_schemas.py::test_FR017_reject_artifact_violations[FR005-single-vehicle]`; `tests/integration/test_generate_normal_flight.py::test_SC001_three_runs_publish_complete_identical_pairs` | Rejects a different snapshot vehicle; every baseline snapshot has the literal source vehicle ID. |
| FR-006 | `tests/unit/simulator/test_scenario.py::test_FR006_three_hz_all_literal_snapshots`; `tests/contract/test_artifact_schemas.py::test_FR006_rounded_interval_accumulation_rejected` | Exact index/grid starts at zero, includes the aligned terminal tick, remains strictly increasing; 3 Hz literal times reject accumulation of rounded interval metadata. FR-001's CLI rejection covers no-directory effects. |
| FR-007 | `tests/unit/simulator/test_scenario.py::test_FR002_baseline_literal_states_and_half_open_boundaries`; `tests/contract/test_artifact_schemas.py::test_FR017_reject_artifact_violations[FR007-east]` | Literal local NED path has negative down above origin, positive/negative north motion and terminal origin; incorrect east motion is rejected. |
| FR-008 | `tests/unit/playback/test_view_model.py::test_display_only_derivations_and_original_mission_time`; `tests/contract/test_artifact_schemas.py::test_FR004_literal_pair_and_immutable_types` | Stored vector `(2,3,6)` gives display speed 7; six fields contain no stored scalar-speed duplicate. |
| FR-009 | `tests/unit/simulator/test_scenario.py::test_FR002_baseline_literal_states_and_half_open_boundaries`; `tests/contract/test_artifact_schemas.py::test_FR001_shared_source_prevalidation[FR009-exhausted]` | Literal linear battery values, 100% to 91%; source prevalidation rejects exhausted normal missions. Full config/shape tests cover valid zero drain and the 0–100 range. |
| FR-010 | `tests/unit/simulator/test_scenario.py::test_FR010_A1_sequence_boundaries_precede_time_quantization`; `tests/unit/playback/test_view_model.py::test_same_boundary_empty_phase_and_terminal_multiple_starts` | Independent truth preserves exact ceil boundaries; A1 tick 1 stays takeoff despite equal displayed times. Equal starts give empty phases; terminal belongs to landing. Six-field checks prevent phase leakage. |
| FR-011 | `tests/contract/test_canonical_serialization.py::test_FR011_sorted_compact_utf8_single_lf_repeated`; `tests/integration/test_generate_normal_flight.py::test_SC001_three_runs_publish_complete_identical_pairs` | Fixed UTF-8 sorted/compact/single-LF bytes over three in-process calls; three installed CLI processes produce identical pairs and source metadata. Source precision tests prevent input rounding. [T034 three-run hashes](#t034--repeatable-quickstart-acceptance--2026-10-09) are historical. |
| FR-012 | `tests/integration/test_generate_normal_flight.py::test_SC001_three_runs_publish_complete_identical_pairs`; `tests/architecture/test_dependency_boundaries.py::test_FR016_production_future_packages_are_empty` | Complete upstream state estimates contain exactly six allowed fields; no raw sensor/fusion/noise/fidelity assertion or future Evaluator behavior. This is M0 scope/shape evidence, not physical-fidelity measurement. |
| FR-013 | `tests/unit/playback/test_loader.py::test_load_immutable_fixture_pair`; `tests/unit/playback/test_view_model.py::test_FR013_SC004_three_hz_repeated_ticks_use_saved_event_gaps` | Fixture-only loader preserves hashes and immutable input; session returns the same saved snapshot object, using actual saved time gaps. Playback dependency scan forbids simulator imports. |
| FR-014 | `tests/unit/playback/test_matplotlib_view.py::test_drawn_route_series_annotations_and_synchronized_cursor`; `tests/unit/playback/test_matplotlib_view.py::test_registered_widget_callbacks_and_timer_advance_events` | Exact route/series/phase annotations/cursors plus registered Play/Pause/Step/Restart/speed callbacks. [CP4 native controls](#cp4-acceptance--t025t026-reviewed-and-main-verified) and [T034 replay](#t034-approval-and-main-replay--2026-10-09) provide historical automated native GUI evidence. |
| FR-015 | `tests/integration/test_playback_read_only.py::test_complete_control_sequence_never_changes_input_hashes`; `tests/unit/playback/test_view_model.py::test_controls_preserve_partial_cadence_and_terminal` | Controls retain original mission times, input hashes and artifact identities, while cursor/rate change. Historical CP4 generated-pair traversal checks all 451 saved snapshots. |
| FR-016 | `tests/architecture/test_dependency_boundaries.py::test_FR016_production_dependency_boundaries`; `tests/architecture/test_dependency_boundaries.py::test_FR016_production_future_packages_are_empty` | AST production scans enforce Fuzzer/DSL/Evaluator and playback/simulator isolation; literal positive/negative scanner controls guard the instrument; all three future packages contain only placeholders. |
| FR-017 | `tests/contract/test_gate_rejection.py::test_FR004_FR010_SC002_extra_phase_rejected`; `tests/architecture/test_dependency_boundaries.py::test_FR016_production_dependency_boundaries` | Current full CI/local gate covers contract/scenario/reproducibility/truth/playback/boundaries. [T033 policy acceptance](#t033-approval-and-main-replay--2026-10-08) records actual `change-gate` checks and effective main rules; no fresh remote-policy claim is made here. |
| FR-018 | `tests/contract/test_gate_rejection.py::test_FR011_FR018_SC006_noncanonical_bytes_rejected`; `tests/contract/test_gate_rejection.py::test_FR004_FR010_SC002_extra_phase_rejected` | Fixed single-defect negatives reject byte and phase violations. [T032 isolated unchanged-gate failures](#t032-approval-and-main-replay--2026-10-08) supply historical behavioral mutation RED; current clean gate is green. |
| SC-001 | `tests/integration/test_generate_normal_flight.py::test_SC001_three_runs_publish_complete_identical_pairs` | Three fresh installed CLI processes compare complete bytes, stdout hashes and file hashes for both artifacts. [T034 actual three-run hashes](#t034--repeatable-quickstart-acceptance--2026-10-09) agree. T032's within-process counter mutation is detected by FR-011's fixed-literal test, not by this process-reset test. |
| SC-002 | `tests/integration/test_generate_normal_flight.py::test_SC001_three_runs_publish_complete_identical_pairs`; `tests/contract/test_gate_rejection.py::test_FR004_FR010_SC002_extra_phase_rejected` | Every baseline snapshot equals the six-field literal oracle, contiguous indices 0–450 and strictly increasing grid times; no phase label. Permanent extra-phase rejection has the specific diagnostic. |
| SC-003 | `tests/unit/simulator/test_scenario.py::test_FR002_baseline_literal_states_and_half_open_boundaries`; `tests/unit/simulator/test_scenario.py::test_FR003_four_supported_rates[0.2-10-0.1-451-boundaries0]` | 451 snapshots at 10 Hz, five phases, origin → north 20 m → origin, 45 s terminal zero velocity and 91% battery. |
| SC-004 | `tests/unit/playback/test_view_model.py::test_FR013_SC004_three_hz_repeated_ticks_use_saved_event_gaps`; `tests/integration/test_playback_read_only.py::test_complete_control_sequence_never_changes_input_hashes` | Cursor uses original event identities/times throughout controls and completion. [CP4 generated-pair control/traversal record](#cp4-acceptance--t025t026-reviewed-and-main-verified) additionally checks all 451 baseline snapshots. |
| SC-005 | `tests/unit/playback/test_matplotlib_view.py::test_drawn_route_series_annotations_and_synchronized_cursor`; `tests/unit/playback/test_matplotlib_view.py::test_A1_display_collision_uses_sequence_phase_for_label_and_marker` | Artist assertions supplement actual five-image visual inspection below. [CP4 visual/native acceptance](#cp4-acceptance--t025t026-reviewed-and-main-verified) and [T034 terminal reinspection](#t034-approval-and-main-replay--2026-10-09) are historical; native controls were automated, not human manual acceptance. |
| SC-006 | `tests/contract/test_gate_rejection.py::test_FR011_FR018_SC006_canonical_positive_controls`; `tests/contract/test_canonical_serialization.py::test_FR011_sorted_compact_utf8_single_lf_repeated` | Current clean full gate PASS plus [T032 phase/byte mutations](#t032-approval-and-main-replay--2026-10-08) at reviewed SHA and [T033 permanent-controls/policy acceptance](#t033-approval-and-main-replay--2026-10-08). Existing T032 self-contained procedure reproduces both historical REDs. |

Historical evidence boundaries are explicit: CP4 rendered/native evidence has
product SHA `0d856dcf062db97041fc5b0393f51ed6f55b369d` and reviewed SHA
`ffc5e6ae5dff66127cc6602db05f716cbfaa94b3` (2026-10-06). On 2026-10-09 the
executor reopened all five original 1440 × 960 phase PNGs at
`build/artifacts/m0-playback-acceptance-20261005/`: labels read takeoff/5 s,
hover/12.5 s, northbound/20 s, return/30 s and landing/40 s. The five bands
are ordered/readable; three time cursors align; northbound and return markers
are at north 10 m, with altitude 10 m; takeoff/landing show altitude 5 m.
This is a present reinspection of historical rendered pixels, with their paths
and SHA-256 recorded in `build/t035-executor-evidence/visual-reinspection.json`.
It adds no new GUI execution. Current `src/` bytes equal that historical product
SHA. T034's separate automated native replay is reviewed at
`6b24846f81e13328025b7648e229fb72d553066e` (2026-10-09).

T032 whole-gate RED is pinned to reviewed SHA
`9d7875305b5a277ced11e0df5b58d2351c14cf01` (2026-10-08): phase mutation
`8 failed, 395 passed`; byte mutation `23 failed, 380 passed`; all restored
gates report `403 passed`. Current source/tests/schemas/scenario/workflow/
package/lock bytes equal that SHA. T033 remote check/policy evidence is pinned
to `ccb466a060551edcb88ad231ee9b257bd9881463` (2026-10-08), not current head:
actual hosted `change-gate` successes, Actions app `15368`, active main ruleset
`20876648`, strict mode and no bypass. Missing/failed restriction was verified
at the effective-policy boundary with official semantics; no attempted blocked
merge was performed. T035 does not refresh GitHub or elevate that boundary.

Algorithm/source concordance was checked against complete module code,
docstrings, the referenced documentation sections and the tests above. The
links below are the primary sources already cited in the algorithm document;
the project's model choices are identified separately from their mathematical
or API basis. Constitution IV's source + chapter + plain-language + data mapping
is present for all five required modules:

| Task / module citation | Source and chapter | Plain-language bridge and actual data/code mapping |
| --- | --- | --- |
| T007 `src/assertion_engine/artifacts.py` → §1 | CPython 3.14 [`Fraction` constructor/rounding](https://github.com/python/cpython/blob/3.14/Doc/library/fractions.rst), [`Decimal.quantize` / ROUND_HALF_EVEN](https://docs.python.org/3.14/library/decimal.html#decimal.Decimal.quantize), [`json` parsing/encoding](https://docs.python.org/3.14/library/json.html) | Measure every tick from zero rather than carry rounded error. `exact_number`/`source_timeline` derive Fraction rate, interval, starts and integer terminal count from non-derived source; `validate_pair` checks `Q(k × interval)` and `ceil(start × rate)`. `quantize` implements Q with `round(Fraction × 1_000_000)` and a Decimal result, rather than calling Decimal.quantize. Serializer explicitly supplies sorted keys, compact encoding, finite numbers, unchanged source precision and one LF. |
| T012 `src/assertion_engine/simulator/config.py` → §1 | Same §1 numeric sources; source-to-grid/ceil mapping is project E2 arithmetic | TOML decimal tokens remain Decimal; `ScenarioConfiguration` prevalidates via `source_timeline` before I/O, then `to_source` quantizes only derived rate/interval metadata. The exact source ruler remains authoritative. Config and CLI tests reject rounded-looking terminal alignment with no parent creation. |
| T014 `src/assertion_engine/simulator/scenario.py` → §1–§2 | §1 numeric sources; OpenStax [University Physics Volume 1 §3.4, equation 3.13](https://openstax.org/books/university-physics-volume-1/pages/3-4-motion-with-constant-acceleration) with acceleration zero | Ask each tick's location directly within a fixed-velocity segment: `p_start + v × elapsed`. Code uses `time = k × interval` and exact starts, then quantizes NED motion/battery into snapshots; truth saves `ceil(start × rate)`. Five-phase order/half-open ownership and the linear battery model are accepted FR-002/009/010 choices, not physical-fidelity claims from the textbook. |
| T022 `src/assertion_engine/playback/view_model.py` → §3 | OpenStax [University Physics Volume 1 §4.1, Velocity Vector / Example 4.3](https://openstax.org/books/university-physics-volume-1/pages/4-1-displacement-and-velocity-vectors) | Speed is the saved vector's magnitude (`math.hypot`); altitude is saved `-down`. Cursor indexes immutable snapshots; last eligible ground-truth sequence boundary selects phase. Rational viewing-clock progress consumes saved event-time gaps; pause/step/speed/restart never regenerate source motion or mission times. |
| T023 `src/assertion_engine/playback/matplotlib_view.py` → §4 | Matplotlib [Animations / FuncAnimation explanation](https://matplotlib.org/stable/users/explain/animations/animations.html#funcanimation), [widgets Button/Slider API](https://matplotlib.org/stable/api/widgets_api.html) | Album/page-turning bridge: the wall clock changes when the saved cursor advances. Actual code uses `figure.canvas.new_timer(interval=25)` and updates artists in its callback; it does not instantiate FuncAnimation. The animation source supplies artist-update intuition; Button/Slider are the actual widget APIs. Marker, three cursors and label all read one session snapshot; rounded truth times only place annotations. Agg and GUI share this view/session. |

Constitution II (v1.0.1), research's provisional ladder, source rate formula and
the four literal generation tests agree. With cruise speed 2 m/s,
`spacing = 2/rate`; with mission duration 45 s, snapshots are `45 × rate + 1`.
`event interval = 1/rate` yields the values below. The corpus count 10 is the
future minimum rule corpus from constitution III; M0 implements no rules or
Evaluator. The installed CLI also generated four new pairs under
`build/t035-executor-evidence/final/rates/<rate>/artifacts/`.

| Tier | Rate | Spacing | Snapshot count | Interval / future max budget | Future rules / evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| L0 | 10 Hz | 0.20 m | 451 | 0.1 s / 100 ms | 10; E2 arithmetic |
| L1 | 20 Hz | 0.10 m | 901 | 0.05 s / 50 ms | 10; E2 arithmetic + E3 tier choice |
| L2 | 50 Hz | 0.04 m | 2251 | 0.02 s / 20 ms | 10; E2 arithmetic + E3 tier choice |
| L3 | 100 Hz | 0.02 m | 4501 | 0.01 s / 10 ms | 10; E2 arithmetic + E3 tier choice |

Exact test IDs for these four rows are
`tests/unit/simulator/test_scenario.py::test_FR003_four_supported_rates[0.2-10-0.1-451-boundaries0]`,
`tests/unit/simulator/test_scenario.py::test_FR003_four_supported_rates[0.1-20-0.05-901-boundaries1]`,
`tests/unit/simulator/test_scenario.py::test_FR003_four_supported_rates[0.04-50-0.02-2251-boundaries2]`,
and `tests/unit/simulator/test_scenario.py::test_FR003_four_supported_rates[0.02-100-0.01-4501-boundaries3]`.
They assert literal counts/boundaries, complete sequence continuity, increasing
times and terminal origin/zero velocity/91% battery. Generator input capability
is measured E1. The intervals/budgets are E2 arithmetic, with E3 future tier
selection; they remain **not an Evaluator latency E1 or performance Gate**.
Future Evaluator acceptance requires p50/p95/p99/max, GC pause distribution,
input age/detection latency and reproducibility provenance, as research states.

Standalone ignored replay captures command/cwd/explicit environment/exit/raw
stdout/stderr, installed identities, all 24 collected-node rows, five module
citations, both ladder tables, four generated pairs and 122-file byte manifests.
It also checks this T035 ladder table against literal rates/counts/intervals/
budgets and both authority tables. The committed four-rate snippet below was
extracted from this document and executed successfully in the isolated checkout;
`committed-reproduction.*` retains its actual CLI output and assertions.
Frozen replay SHA-256:
`e1d1f174676dc0c2c964d467833b8bf54241abfbbc187132a0dbc9cd1c213b5b`.
It refuses existing output/clone paths. Run it with new destinations; `--validation`
selects this working document before its commit, and may be omitted when the
chosen SHA already includes the T035 section:

```sh
python3 build/t035-executor-evidence/proof.py --repo "$PWD" \
  --sha f33e76ef782013dece8b77bb906c4378fef9bd38 \
  --output build/t035-replay-new --scratch /tmp/assertion-engine-t035-replay-new \
  --uv-cache-source /tmp/assertion-engine-t034-main-reviewer-final/build/reviewer-environment/uv \
  --python /tmp/assertion-engine-t034-main-reviewer-final/build/reviewer-environment/python/cpython-3.14.4-linux-x86_64-gnu/bin/python3.14 \
  --validation specs/001-telemetry-simulator/validation.md
```

When ignored scripts/caches are unavailable, the following committed procedure
is sufficient: create a new detached local clone at the chosen SHA (containing
this section, or copy this validation document into its matching path), select
uv 0.11.9 and CPython 3.14, choose explicit writable `UV_CACHE_DIR`,
`UV_PYTHON_INSTALL_DIR`, `UV_PYTHON_BIN_DIR`, `MPLCONFIGDIR` and `TMPDIR` beneath
that clone's ignored `build/`, and remove inherited `PYTHONPATH`, `PYTHONHOME`,
`PYTEST_ADDOPTS`, `PYTEST_PLUGINS`, `VIRTUAL_ENV`, `UV_PROJECT_ENVIRONMENT` and
`UV_NO_SYNC`. Cold caches need normal dependency-download access; offline mode
is appropriate only for an explicitly provisioned cache/interpreter. Run the
four exact gate commands above individually and retain outputs/exits. Assert
that installed module origins, `.venv` prefix, console entrypoints and offline
schemas belong to that checkout. Before/after, compare tracked product bytes
to `git show SHA:path`; allow only the stated validation overlay if needed.

Run `MPLBACKEND=Agg uv run pytest --collect-only -q` and ensure each backticked
node ID in the 24 requirement rows and four-rate list occurs literally in the
collected output. Read each cited test's assertions. Read the five complete
modules/docstrings and algorithm §§1–4, using the concordance table to check
the source/chapter/bridge/data correspondence; compare the four constitution II
and research ladder rows, their E2/E3 markings and future 10-rule corpus.
Generate the four rate artifacts through the real installed CLI in this new
checkout with the self-contained snippet below; it refuses existing outputs:

```sh
uv run python - <<'PY'
from pathlib import Path
import subprocess
import json

baseline = Path("scenarios/normal-flight.toml").read_text()
assert baseline.count("observation_spacing_m = 0.2\n") == 1
root = Path("build/t035-rates-new")
assert not root.exists()
root.mkdir(parents=True)
for rate, spacing, count in [(10, "0.2", 451), (20, "0.1", 901),
                             (50, "0.04", 2251), (100, "0.02", 4501)]:
    scenario = root / f"{rate}.toml"
    scenario.write_text(baseline.replace("observation_spacing_m = 0.2\n",
                                         f"observation_spacing_m = {spacing}\n"))
    target = root / str(rate)
    subprocess.run(["assertion-sim", "generate", "--scenario", str(scenario),
                    "--output", str(target)], check=True)
    telemetry = json.loads((target / "telemetry.json").read_text())
    truth = json.loads((target / "ground-truth.json").read_text())
    config = telemetry["scenario"]["config"]
    assert config["sample_rate_hz"] == rate
    assert config["sample_interval_s"] == 1 / rate
    assert len(telemetry["snapshots"]) == count
    assert telemetry["snapshots"][-1]["mission_time_s"] == 45
    assert [p["start_sequence_number"] for p in truth["phases"]] == [
        n * rate for n in (0, 10, 15, 25, 35)]
    print(rate, spacing, count, 1000 / rate, "ms; future rules=10; E2/E3")
PY
```

Use the committed [quickstart](quickstart.md) for fresh three-run byte hashes
and playback; use the [self-contained T032 procedure](#self-contained-t032-reproduction-without-ignored-evidence-files)
for isolated whole-gate negatives. Visual inspection requires actually opening
the five phase/terminal images as CP4 records; native controls require a real
GUI backend/display and must state whether interaction was automated or human.
The T033 read-only GitHub commands above reproduce remote policy/check evidence
at a later head; historical URLs/SHA do not prove its current hosted state.

T035 awaits independent review and main replay. This concordance does not mark
T036, CP6 or M0 complete and does not resolve handoff Open Questions.


## T035 approval and main replay — 2026-10-09

- Fresh independent review APPROVED the full
  `f33e76ef782013dece8b77bb906c4378fef9bd38..f19532306c1f7c83092b4522fd1249bf51cfc890`
  slice without blocking or nonblocking findings. The diff contains only the
  T035 evidence section and its awaiting-review marker. Reviewer exact baseline
  gate: `403 passed in 22.13s`; restored final gate: `403 passed in 21.75s`.
  Exact cited representative nodes: `31 passed in 7.06s`. Locked sync exits 0;
  Ruff reports `79 files already formatted` and `All checks passed!`.
- Main captured and replayed the executed reviewer proof byte-for-byte in the
  new `/tmp/assertion-engine-t035-main-reviewer-replay` checkout at reviewed SHA.
  Its SHA-256 equals the frozen `final-proof.py`:
  `76c9b3d92d890f13cf8a7c92c6050f717d8f2f4ab109913ab0e144e2582c54f8`.
  Main exact baseline: `403 passed in 21.34s`; restored final exact gate:
  `403 passed in 21.95s`; representatives: `31 passed in 6.70s`.
  Both full gates have zero failures, errors or skips; sync and Ruff pass.
- Main independently reads all 27 raw command/exit/environment/log records.
  The audit confirms 24 distinct FR/SC rows, 31 exact cited nodes, all five
  module citations and the T035/constitution/research ladder agreement. The
  exact committed rate snippet generates eight real JSON artifacts: rates
  10/20/50/100 Hz, counts 451/901/2251/4501, paired versions 1.0.0/2.0.0,
  exact source/sequence boundaries and terminal time 45 s/battery 91%.
  Historical CP4 source and T032 product/test/schema/workflow/lock comparisons
  are empty diffs against their actual SHAs. Neither proof refreshes native
  GUI or remote-policy evidence, nor measures future Evaluator latency.
- Reviewer and main mutate only isolated `scenario.py` to quantize phase starts
  before ceil. The existing A1 assertion catches `[0, 1, 3, 6, 9]` instead of
  `[0, 2, 3, 6, 9]`: each reports `1 failed in 0.16s`, followed by
  `1 passed in 0.14s` after saved-byte restoration. Both audits also reject
  L1 count `901 -> 999` and a nonexistent FR-001 test reference with the intended
  AssertionErrors; the restored document audit passes. These are instrument
  checks against existing tests/documentation, not new test-first TDD claims.
- Main separately verifies all three retained reviewer checkouts and its own
  replay: each has 122 tracked files byte-identical to reviewed SHA and empty
  Git status. The reviewer retains its initial nonexistent `simulator.writer`
  identity-probe failure in `run-1/`; it is a scratch instrumentation failure,
  excluded from product RED. Root product source/tests/schemas/scenario/
  workflow/package/lock files remain unchanged. Reviewer and main also actually
  reopen the historical five phase PNGs; this is reinspection of saved pixels.
- Frozen proof/report/replay instructions and raw review records are under
  `build/t035-reviewer-evidence/`. Main raw replay is under
  `build/t035-main-evidence/reviewer-replay/`; independent record, artifact,
  diagnostic and four-checkout inspection is `final-inspection.json` in its
  parent directory. Replay the frozen script unchanged with the six arguments
  documented above, the reviewed SHA, new output/scratch names and no validation
  overlay. The committed standalone procedure remains sufficient without
  ignored evidence files.
- T035 promotes to `[X]` only in this separate post-approval commit. T036, CP6
  and full M0 acceptance remain pending; PR `#5` stays draft. Luke requires all
  remaining handoff Open Questions and their failure to be surfaced during SDD
  to be reviewed together at spec001 closeout; this slice does not resolve them.

## T036 — final M0 acceptance — 2026-10-09

Product baseline: `5689e7cf0d78e12d10c14420d1995cadfaee4897`.
T001–T035 are reviewed and main-verified. The remaining scope is one checkpoint,
T036, so the delegation gate selects inline acceptance followed by independent
review. This slice changes only validation evidence and task markers. It adds
no product code or tests and claims no new test-first RED.

Main uses the new detached clone `/tmp/assertion-engine-t036-main-2`, CPython
`3.14.4`, uv `0.11.9`, Matplotlib `3.11.2`, jsonschema `4.26.0`, pytest `9.1.1`
and Ruff `0.16.10`. Its own `.venv`, installed product module origins, both
console entrypoints and offline schema contents are checked against that clone.
Writable uv/Python/Matplotlib/temp locations are explicit beneath
`build/t036-main-evidence/run-2/environment/`; provisioned caches allow offline
sync. Inherited Python/pytest/uv environment overrides are removed and bytecode
writes are disabled. All 122 tracked files match the pinned SHA before and
after the initial gate; Git status is empty.

| Unchanged CI/local entrypoint | Main baseline result |
| --- | --- |
| `uv sync --locked` | exit `0` |
| `uv run ruff format --check .` | `79 files already formatted` |
| `uv run ruff check .` | `All checks passed!` |
| `MPLBACKEND=Agg uv run pytest` | `403 passed in 29.86s`, zero skips |

### Installed CLI and artifact acceptance

Three actual installed `assertion-sim generate` processes publish fresh pairs
under the clone's `build/t036-artifacts/fresh/1`, `/2` and `/3`. Each initially
contains exactly two files. Each compact stdout object has exactly the four
contract keys; its paths and hashes match the actual files. Complete bytes
match across all three runs, with these SHA-256 values:

- Telemetry: `1cc55ccd8ba9fa11d2c242704ad5503d0e82635bb22c1c2c654cbcffe540494b`.
- Ground truth: `b12d092c618dc03f06e63984cfba3a10d9c3d712535dca747784422c38e6fac7`.

Actual loader/canonical validation confirms telemetry `1.0.0`, ground truth
`2.0.0`, identical normalized source, 451 contiguous six-field snapshots,
mission time 0–45 s, five phases in order with boundaries
`0, 100, 150, 250, 350`, and terminal origin/zero velocity/91% battery.
The full gate includes literal rate/time/phase/vehicle/battery assertions and
the A1 rounded-time collision case; the acceptance probe supplements them.

| Real installed command case | Exit and observed side effects |
| --- | --- |
| Valid generate into initially absent nested parents | `0`; complete pair published |
| Retry existing pair | `2`, `target already exists`; both bytes and exact directory contents unchanged |
| Invalid arguments / 45.0000004 s terminal config | `2`; explicit absent parent trees stay absent, terminal diagnostic present |
| File as output ancestor | `1`; path diagnostic, original ancestor bytes retained, final target absent |
| Valid headless playback | `0`; terminal PNG fully decoded at 1440 × 960, JSON input hashes unchanged |
| Speed `0` / `-1`, missing input / missing PNG parent | `2`; no output or missing parent created |
| Ground truth `1.0.0` / `9.0.0` | `2`; version diagnostic, legacy regeneration guidance, no PNG, all inputs unchanged |
| Missing-field / wrong-sequence / extra-phase telemetry | `2`; no PNG, copied invalid input and original pair unchanged |
| Headless output aliases either JSON input | `2`; both original hashes unchanged |

The unchanged targeted command
`MPLBACKEND=Agg uv run pytest tests/integration/test_generate_failures.py tests/integration/test_playback_read_only.py tests/architecture/test_dependency_boundaries.py`
reports `119 passed in 19.64s`, zero skips. Its assertions also cover staging,
write and publication failures, cleanup that preserves existing parents and
sentinels, mismatched sources, rendering/input-I/O failures and executable
dependency boundaries. These injected operational errors run real product
entrypoints with substituted I/O boundaries; they are not rewritten CLI logic.

### Fresh rendered and native acceptance

Main actually opens five freshly generated phase images under the clone's
`build/t036-artifacts/`: `takeoff.png`, `hover.png`, `northbound.png`,
`return.png` and `landing.png`. Their selected snapshots are respectively
0/100/150/250/450, at 0/10/15/25/45 s. Phase/time labels are readable; the N/E
marker and all three time cursors match the selected saved event; five colored
annotations remain ordered. The route reaches north 20 m and returns to the
origin, altitude rises to 10 m then falls to zero, speed matches the phases,
and battery falls linearly from 100% to 91%. Main separately opens the installed
headless `terminal.png` and the real Tk terminal canvas: landing/45 s/snapshot
450/completed, origin, zero altitude/speed and 91% battery are visible.

Fresh native evidence is under the clone's `build/t036-native-controls/`.
The existing inspected Tk driver runs the installed playback `cli.main`,
actual `MatplotlibView.show()`/Tk mainloop/`TimerTk` and monotonic clock. It
checks 13 control checkpoints, 11 real Tk release events and 38 real timer
ticks, returning CLI exit `0`. Generated canvas events exercise Play, Pause,
one-snapshot Step, speed slider, resume, Restart, completed controls and Restart
after completion. At every observation, snapshot identity/time, sequence-based
phase, drawn cursors, input hashes and canonical domain bytes are unchanged.
This is automated native GUI interaction; no human manual interaction is claimed.

Two driver errors are retained and excluded from product RED: run 1 attempted
to assign the read-only `cursor` property before rendering; the correction uses
the real `step()` method. The initial run-2 native attempt completed its control
sequence but could not express an evidence path relative to the clone because
its output was outside that clone. The retry uses a new checkout-local evidence
directory and passes. Raw failing and successful outputs are kept separately;
passed gate/CLI/render checks are not repeated for the native path repair.

### Whole-gate negatives and hosted policy

The committed self-contained T032 procedure is executed at this current product
SHA in two new clones, `/tmp/assertion-engine-t036-main-2-negative-phase` and
`/tmp/assertion-engine-t036-main-2-negative-bytes`. Its exact gate commands are
unchanged. Sync and both Ruff commands remain successful under each mutation;
the failure comes from product assertion tests, not environment/import errors.

| Isolated current-head gate | Clean baseline | Mutated pytest, exit `1` | Restored full gate |
| --- | --- | --- | --- |
| Extra snapshot `phase` in product serializer | `403 passed in 27.19s` | `8 failed, 395 passed in 24.42s` | `403 passed in 26.70s` |
| Per-call trailing spaces in canonical bytes | `403 passed in 27.20s` | `23 failed, 380 passed in 16.98s` | `403 passed in 28.00s` |

Phase mutation fails
`tests/contract/test_gate_rejection.py::test_FR011_FR018_SC006_canonical_positive_controls`.
Byte mutation fails
`tests/contract/test_canonical_serialization.py::test_FR011_sorted_compact_utf8_single_lf_repeated`
with its fixed-literal byte difference (`1 failed in 0.15s` when isolated).
The fresh-process SC-001 test still passes (`1 passed in 1.46s`) because the
counter resets in each CLI process; this known limitation remains explicit.
After restoration, main independently compares all 122 tracked files in each
of the three clones to the pinned SHA and verifies empty Git status. No
discarded mutation occurs in the primary workspace.

Fresh read-only GitHub API evidence in
`build/t036-main-evidence/github-baseline/` confirms PR `#5` OPEN/draft at the
same baseline SHA; both [PR run](https://github.com/lukeking/assertion-engine/actions/runs/37854748570)
and [push run](https://github.com/lukeking/assertion-engine/actions/runs/37854742056)
are SUCCESS and all four exact gate steps are successful. Effective main rules
still require `change-gate` from Actions app `15368`, strict up-to-date policy,
`do_not_enforce_on_create: false`; active ruleset `20876648` scopes only main
and has no bypass actors. The hosted-policy boundary remains the T033 live
policy/check/official-semantics boundary, with no blocked-merge experiment.
An initial step extractor included two Actions setup steps and therefore failed
its four-step-count assertion; retained raw job responses were reconciled using
the four actual gate command names. This probe error is not a workflow failure.

### Current-head reproduction and scope

Raw commands/exits/stdout/stderr, environment identity, manifests and hashes
are in `build/t036-main-evidence/run-2/`. The local acceptance driver is
`build/t036-main-evidence/acceptance.py`; its native dependency is the preserved
`build/t034-main-evidence/native_gui.py`, and its clean-environment bootstrap is
`build/t035-executor-evidence/proof.py`. These ignored helpers are evidence
carriers, not prerequisites for acceptance on another machine.

Without ignored helpers, create a new detached clone at the chosen SHA, verify
tracked bytes and clean status, and use the explicit environment/origin/schema
checks from the T035 standalone procedure. Execute the committed
[quickstart](quickstart.md) in that clone with three new destinations: locked
sync, three installed generations, byte hashes, overwrite refusal, installed
headless terminal PNG and all four unchanged gate commands. Run the targeted
error/boundary command above. Use the actual GUI backend/display and quickstart
controls for native acceptance, retaining before/after hashes and stating
whether the controls were human-operated or automated. Open the terminal and
five phase images rather than substituting file-existence checks.

To reproduce the five saved-event views, load the generated pair with
`load_pair`, construct `PlaybackSession(*pair)` and `MatplotlibView(session)`,
and call `session.step()` until each literal cursor 0/100/150/250/450. Save each
view with its phase filename and check label/marker/cursor data against the
selected original snapshot before opening it. Do not assign the read-only
cursor or call Simulator from playback. Execute the committed self-contained
T032 snippet with the chosen current SHA and two new `/tmp` clone names to
reproduce whole-gate negatives. Use T033's read-only GitHub commands with the
current PR head/run IDs to refresh hosted evidence.

FR-012/FR-016 scope remains M0 Simulator, shared artifact validation and
read-only playback. The architecture gate checks empty DSL/Evaluator/Fuzzer
packages and forbidden imports. The accepted ADR/spec excludes raw sensors,
noise/estimator fidelity, rules/grammar, ingestion, alerts and real hardware.
The T035 requirement/algorithm concordance and E2/E3 latency boundaries remain
applicable; this slice makes no Evaluator latency or physical-fidelity claim.

T036 awaits independent review and main replay. CP6/full M0 acceptance and PR
ready/closeout are not declared here. Luke's required joint disposition of all
handoff Open Questions, the SDD carry-forward gap and slice-selection standard
must precede ready/closeout; user decisions cannot be filled in by an agent.

## T036 approval and main replay — 2026-10-09

- Independent fresh-context review of the complete slice
  `5689e7cf0d78e12d10c14420d1995cadfaee4897..0478ff79cac1a9b29f1a1804b4ce2f4af4ed0720`
  is **APPROVED**, with no blocking or non-blocking findings. Only validation
  and T036's awaiting-review marker changed. The reviewer constructs its own
  literal oracle for all 451 baseline snapshots, source, timeline and rendered
  artist data; it does not run the implementer's acceptance driver.
- Frozen reviewer proof SHA-256:
  `2fa6add9949b806850c7e43d9d5aa352e7e32f59979a30c4702036dd20c8bd5b`.
  Reviewer exact baseline/mutated/restored gate summaries are
  `403 passed in 24.94s`, `23 failed, 380 passed in 13.91s`, and
  `403 passed in 23.01s`, zero skips. Focused errors/boundaries report
  `119 passed in 15.93s`; fixed-literal FR-011 reports `1 failed in 0.14s`
  under mutation, while process-reset SC-001 remains `1 passed in 1.42s`.
  Fresh native Tk passes 13 controls, 11 release events and 34 timer ticks,
  CLI exit `0`; reviewer actually opens all seven fresh images and the seven
  corresponding supplied images. A corrected viewer-path error is retained
  outside product RED.
- Main replays that same proof unchanged in
  `/tmp/assertion-engine-t036-main-review-replay` at reviewed SHA `0478ff79`.
  Exact baseline/mutated/restored gate results are
  `403 passed in 23.20s`, `23 failed, 380 passed in 14.97s`, and
  `403 passed in 23.32s`, zero skips; sync/both Ruff commands pass.
  Focused errors/boundaries report `119 passed in 16.04s`; FR-011 mutation
  reports `1 failed in 0.14s`, counter-reset SC-001 `1 passed in 1.52s`.
  Fresh native Tk passes 13 controls/11 releases/33 ticks and CLI exit `0`.
  Main actually opens the five fresh phase PNGs, installed headless terminal
  and real native canvas; labels, route, all three plots and terminal values
  remain correct. Inputs and domain bytes remain equal.
- Main independently reads all 42 replay command records, checks expected exits
  and raw runner summaries, confirms the frozen proof hash, and compares every
  tracked byte in both reviewer/main clones to the reviewed SHA: 122 files
  each, clean status. Primary before/after manifests are identical. Every
  mutation was confined to the pinned disposable clones and restored.
- Reviewer artifacts are `build/t036-reviewer-evidence/{proof.py,REPLAY.md,report.md,final-inspection.json}`
  and `run-1/`; main unchanged replay is `main-replay/` there. Main's separate
  raw/image/byte inspection is `build/t036-main-evidence/review-final-inspection.json`.
  `REPLAY.md` provides the exact frozen command; the committed standalone
  quickstart/T032/T033/T036 procedures remain sufficient without ignored helpers.
- T036 promotes to `[X]` only in this separate post-approval commit. All 36
  implementation tasks are reviewed and main-verified at the stated evidence
  boundaries. PR `#5` remains draft pending Luke's required disposition of
  the remaining handoff/process questions before ready/closeout. `GAR-17` is
  the external feature tracker; its completed status belongs after merge.
