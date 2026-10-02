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
- T003–T007 await independent review; no Simulator/playback business code yet.
