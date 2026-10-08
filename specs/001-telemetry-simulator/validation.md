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
