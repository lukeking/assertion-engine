# Implementation Plan: M0 專案骨架與遙測模擬器

**Branch**: `001-telemetry-simulator` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-telemetry-simulator/spec.md`

## Summary

以 Python 3.14 建立單一 `src`-layout 專案：Simulator 從 TOML 情境設定產生 byte-for-byte 可重現的 canonical JSON telemetry 與 ground-truth artifacts；Matplotlib playback 只讀成品，提供 2D N/E 路徑、同步時間圖與互動 controls。uv 鎖定 Python dependencies，pytest／Ruff 與 GitHub Actions 組成 change gate。M0 只實作 Simulator、artifact validation 與 playback；DSL、Evaluator、Fuzzer 僅建立邊界，未來 Evaluator 是否移入 C++20 由 E1 tail-latency evidence 觸發。

## Technical Context

**Language/Version**: CPython 3.14；未來 Evaluator 可在 E1 latency trigger 成立時引入 C++20，本 feature 不含 C++ build
**Primary Dependencies**: Python standard library、Matplotlib 3.11.x、jsonschema 4.x；uv 0.11.x 管理與鎖定；pytest、Ruff 為 development dependencies
**Storage**: 人類可編輯的 TOML scenario config；UTF-8 canonical JSON telemetry／ground truth files；無 database
**Testing**: pytest unit／contract／integration／architecture tests；所有寫檔測試只使用 pytest `tmp_path`；Ruff lint/format；Matplotlib Agg headless rendering
**Target Platform**: Linux x86_64 開發與 GitHub Actions `ubuntu-latest`；有 GUI backend 時提供 interactive playback，CI 使用非互動 Agg backend
**Project Type**: 單一 Python package，提供 Simulator CLI 與 local playback CLI
**Performance Goals**: M0 不宣稱 real-time engine performance。Simulator 必須能產生 provisional L0–L3 benchmark artifacts；未來 Evaluator 對每階回報 p50/p95/p99/max 與 GC pause distribution，max budget 分別為 100/50/20/10 ms。所有數字目前為 E2 算術／E3 tier choice，不是 Gate
**Constraints**: 單載具；telemetry snapshot 只含 6 個欄位；phase 不得洩漏；同輸入兩份 artifacts 各自 byte-identical；playback 唯讀且不得插值／平滑／重算；invalid config 在任何 output publish 前 fail closed
**Scale/Scope**: 基準 45 s、10 Hz、451 snapshots；2 m/s、0.2 m observation spacing；單機、單 scenario、無 network service；可藉 observation spacing 產生 20/50/100 Hz benchmark inputs

## Constitution Check

*GATE: Passed before Phase 0 research; re-checked after Phase 1 design below.*

依 `.specify/memory/constitution.md` v1.0.1：

- [x] **I. 對抗式驗證** — M0 不實作 Fuzzer／Evaluator；兩者保留獨立 packages，architecture test 從一開始禁止 Fuzzer import DSL 或 Evaluator。
- [x] **II. 尾延遲優先** — 本 feature 不設未量測的 performance Gate。`research.md` 推導的 E2/E3 provisional ladder 已填入憲章原則 II；T035 核對兩處與 Simulator rates 一致。未來 benchmark 必須回報 p50/p95/p99/max 與 GC pauses，Gate 僅能由 E1 結果建立。
- [x] **III. 語法由語料庫反推** — M0 不設計或實作 grammar。ADR 002 只選 parser strategy；M1 必須先有不少於 10 條真實規則 corpus 才能寫 EBNF 與 parser。
- [x] **IV. 可追溯且可理解** — 技術選擇均在 `research.md` 連到官方來源；[M0 演算法說明](../../docs/algorithms/001-m0-telemetry-and-playback.md) 記錄教材章節、白話直覺與資料對應。T007／T012／T014／T022／T023 要求各演算法模組引用對應章節，T035 核對；未來手寫 parser 必須讓 EBNF rule 與 parsing function 一一對應。
- [x] **V. 可重現** — Scenario Configuration 強制 explicit seed；canonical serializer、3-run hash tests 與無 run-specific metadata 保證兩份 artifacts 各自 byte-identical。
- [x] **VI. 證據等級** — research scoring 每格標 E1/E2/E3；provisional latency ladder 明確不是 Gate。
- [x] **視覺化驗收** — Matplotlib playback 提供 2D N/E path、同步 altitude/speed/battery plots 與 phase cursor；CI 以 Agg 產生 headless rendered evidence。
- [x] **不套用他案 spike 設計** — 未採 mapf-router 的 throughput spike；未來儀器量測 tail latency、max 與 GC pauses。

## Project Structure

### Documentation (this feature)

```text
specs/001-telemetry-simulator/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── common.schema.json
│   ├── telemetry-artifact.schema.json
│   └── ground-truth.schema.json
└── tasks.md              # created later by speckit-tasks
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── ci.yml
pyproject.toml
uv.lock
scenarios/
└── normal-flight.toml
src/
└── assertion_engine/
    ├── __init__.py
    ├── telemetry.py
    ├── artifacts.py
    ├── simulator/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── scenario.py
    │   └── cli.py
    ├── playback/
    │   ├── __init__.py
    │   ├── loader.py
    │   ├── view_model.py
    │   ├── matplotlib_view.py
    │   └── cli.py
    ├── dsl/
    │   └── __init__.py
    ├── evaluator/
    │   └── __init__.py
    └── fuzzer/
        └── __init__.py
tests/
├── architecture/
│   └── test_dependency_boundaries.py
├── contract/
│   ├── test_artifact_schemas.py
│   └── test_canonical_serialization.py
├── integration/
│   ├── test_generate_normal_flight.py
│   └── test_playback_read_only.py
├── unit/
│   ├── simulator/
│   └── playback/
└── fixtures/
    └── invalid_artifacts/
```

**Structure Decision**: 採單一 Python `src` layout。`telemetry.py` 與 `artifacts.py` 是中立 contract／serialization layer；Simulator 與 playback 依賴它們。DSL、Evaluator、Fuzzer 各自保留 package boundary，M0 不放業務邏輯。Fuzzer 可共享 telemetry contract，但 CI architecture test 禁止它 import DSL AST、grammar 或 Evaluator semantics。

## Phase 0: Research Decisions

- 技術棧、parser strategy、canonical artifact、playback 與 provisional latency ladder 的證據與 alternatives 記於 [research.md](research.md)。
- 重大決策收斂於 [ADR 002](../../docs/decisions/002-staged-python-parser-strategy.md)。
- 所有 `NEEDS CLARIFICATION` 已消除；Phase 1 沒有 unresolved design input。

## Phase 1: Design & Contracts

- [data-model.md](data-model.md) 定義 Scenario Configuration、Telemetry Snapshot、兩份 artifacts、Phase Interval 與 Playback Session lifecycle。
- 時間使用 normalized source 的未量化數值重建精確有理 interval，以整數 tick 算出 `t_k` 再量化六位小數；`sample_interval_s` 是衍生 metadata，validator 不以其累加結果判定連續性。3 Hz 的明示驗證案例記於 data-model.md，T004／T005／T008／T009／T014 承接。
- 終點以未量化的總時長 `T × r` 檢查整數 tick count；未對齊則在任何 output directory 建立前拒絕，內部階段切換仍可不對齊。T004／T008／T011／T012／T014 承接對齊、量化後看似對齊仍拒絕及 CLI 無寫入測試。
- [M0 演算法說明](../../docs/algorithms/001-m0-telemetry-and-playback.md) 是實作模組的引用與白話橋接入口；包含 piecewise motion、numeric quantization 與 read-only playback 的來源與測試對應。
- `contracts/*.schema.json` 使用 JSON Schema Draft 2020-12 描述外部 artifact shape；跨欄位、連續性、phase order 與 byte canonicalization 由 semantic validator 與 contract tests 補足。
- [contracts/cli.md](contracts/cli.md) 固定 generate／playback command behavior、exit semantics 與 output destination rules。
- Generate 在 arguments／設定／完整成品驗證後才建立明示的 output parent；既有 final target 拒絕覆寫，operational failure 清理 staging 並可保留已建立的 parents。T010／T011／T015／T016 承接巢狀路徑成功、拒絕無副作用與 parent 建立失敗測試。
- 目前 GitHub 尚無 CI gating；T030 在實作 workflow 並取得真實 PASS 後，用實際 check 名稱設定 main 的 required status checks，T033 讀回生效規則與 PR checks 核對。`MERGEABLE / CLEAN` 僅表示合併狀態，不作為 CI gating 證據。
- [quickstart.md](quickstart.md) 以明示的 `build/artifacts/` 與 pytest `tmp_path` 操作，沒有任何 shared storage 或 inherited destination。

## Post-Design Constitution Re-check

- [x] Fuzzer dependency boundary 有明確 CI executor，而非只有目錄宣告。
- [x] Latency ladder 同時包含 event rate、10-rule future corpus、event interval 與 max budget；全部保留 E2/E3 標記，未升格為 Gate。
- [x] Parser decision 有 corpus-first 與 EBNF mapping guard；M0 沒有偷跑 grammar。
- [x] Reproducibility 有 canonical byte contract、schema、hash acceptance test 與 explicit seed。
- [x] Rendered evidence 同時可互動與 headless 驗證；教學呈現不依賴 ASCII 想像。
- [x] 所有 future C++／parser-generator 轉向都有可量測 reopen trigger。

## Complexity Tracking

No constitution violations require justification. The two-language architecture is explicitly deferred until an E1 trigger fires; M0 keeps one runtime and one build system.
