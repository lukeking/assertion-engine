# Implementation Plan: M1 不變量 DSL 與 Parser Tree

**Branch**: `002-rule-dsl-parser` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-rule-dsl-parser/spec.md`

## Summary

在既有的 `assertion_engine.dsl` 套件實作規則 DSL：規則集是 TOML 檔（具名門檻、衍生量、規則），每條規則是一個運算式，
由手寫 lexer 與 Pratt parser 轉成不可變語法樹；獨立的 checker 做名稱、參數個數、型別與量綱檢查。
17 條語料放在 `rules/corpus.toml`，是 parser 的回歸測試集；覆蓋率測試保證文法的每條產生式都有語料需要。
`assertion-rules` CLI 提供 check／dump／tree，tree 用 Matplotlib 畫出含型別的語法樹圖。
M1 只解析、不評估：時間保留字有語法與型別，語意屬於 M2／M3。

## Technical Context

**Language/Version**: CPython 3.14（沿用 M0）
**Primary Dependencies**: Python 標準庫（`tomllib`、`dataclasses`、`decimal`）；Matplotlib 3.11.x（已是依賴，畫語法樹）；不新增依賴
**Storage**: 規則集 TOML（`rules/corpus.toml`）；預期語法樹 JSON（`tests/fixtures/rule_trees/`）；無資料庫
**Testing**: pytest unit／contract／integration／architecture；寫檔測試只用 pytest `tmp_path`；Ruff；Matplotlib Agg
**Target Platform**: Linux x86_64 與 GitHub Actions `ubuntu-latest`（沿用 M0 的 `change-gate`）
**Project Type**: 單一 Python package 內的函式庫子套件＋CLI
**Performance Goals**: 不適用。規則在載入時解析一次，不在逐筆事件的路徑上；M1 不做延遲宣稱（research Decision 10）
**Constraints**: fail-closed，第一個錯誤就停；同一文字的語法樹 byte-identical；運算式只接受 ASCII；
`dsl` 不得引用 evaluator／fuzzer／simulator／playback；fuzzer 不得引用 `dsl`（既有）
**Scale/Scope**: 17 條語料規則、1 個規則集衍生量＋4 個內建衍生量、27 個具名門檻；22 個錯誤碼 × 至少 2 例 ＝ 至少 44 個無效案例

## Constitution Check

*GATE: Passed before Phase 0 research; re-checked after Phase 1 design below.*

依 `.specify/memory/constitution.md` v1.0.1：

- [x] **I. 對抗式驗證** — M1 不實作 Fuzzer。架構測試保留「fuzzer 不得引用 dsl／evaluator」，並新增「dsl 不得引用 evaluator、fuzzer、
      simulator、playback」；`dsl` 從「必須是空套件」清單移除。
- [x] **II. 尾延遲優先** — 本 feature 沒有逐筆事件路徑，不設也不宣稱任何效能數字；延遲階梯留給 M2 的 Evaluator。
- [x] **III. 語法由語料庫反推** — 17 條語料（≥10）經 user 逐條審閱；research 的「語料逼出來的需求」表是每個語法決策的來源；
      語料以 `rules/corpus.toml` 進版控並作為回歸測試集；SC-006 覆蓋率測試讓沒有語料需要的產生式無法存在。
      這是第一版文法，沒有既有規則需要遷移；之後的破壞性變更依 ADR 003 提供遷移路徑。
- [x] **IV. 可追溯且可理解** — research 列出 Crafting Interpreters（ch. 6、§17.6）、Pratt 1973、Koymans 1990、Reingold & Tilford 1981、
      BIPM SI 手冊；實作時寫 `docs/algorithms/002-rule-dsl-parsing.md` 做白話橋接。文法對應由「結合力表 ↔ EBNF 層級」逐列測試與
      grammar.ebnf 每條產生式的 `builds:` 註記執行。
- [x] **V. 可重現** — M1 不動 Simulator／Fuzzer，沒有亂數；語法樹的正規序列化由 SC-008 的重複解析測試鎖住。
- [x] **VI. 證據等級** — research 每格分數標 E1／E2／E3；Gate（SC-001～SC-005）只收測試實測。
- [x] **視覺化驗收** — 每條語料規則可產出含型別的語法樹 PNG（FR-014）；SC-009 由 user 看實際圖片簽核，不用文字描述代替。
- [x] **不套用他案 spike 設計** — 沒有任何吞吐量測。

## Project Structure

### Documentation (this feature)

```text
specs/002-rule-dsl-parser/
├── spec.md
├── rule-corpus.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── grammar.ebnf
│   ├── syntax-tree.md
│   ├── ruleset.md
│   └── cli.md
├── checklists/
│   └── requirements.md
└── tasks.md              # created later by speckit-tasks
```

### Source Code (repository root)

```text
pyproject.toml                         # + assertion-rules script
rules/
└── corpus.toml                        # 17 rules, 1 derived, 27 parameters
docs/
├── algorithms/
│   └── 002-rule-dsl-parsing.md        # Pratt / RD contrast, MTL mapping, dimensions, tree layout
└── decisions/
    └── 003-rule-dsl-syntax.md
src/assertion_engine/dsl/
├── __init__.py                        # public API: load_ruleset, parse_expression, Diagnostic
├── errors.py                          # Diagnostic, RuleSetError, closed code list
├── lexer.py                           # tokens with spans
├── syntax.py                          # frozen node dataclasses, to_document()
├── parser.py                          # Pratt parser, binding-power table, coverage collector
├── units.py                           # Dimension, unit table
├── vocabulary.py                      # fields, functions, built-in derived definitions
├── checker.py                         # names, arity, types, dimensions, derived graph
├── ruleset.py                         # TOML loading pipeline
├── tree_view.py                       # Matplotlib Agg tree rendering and layout
└── cli.py                             # assertion-rules check / dump / tree
tests/
├── architecture/
│   └── test_dependency_boundaries.py  # modified: dsl leaves RESERVED_PACKAGES, gains its own forbidden imports
├── contract/
│   ├── test_rule_corpus.py            # SC-001–SC-003 ladder, SC-008, corpus ↔ rule-corpus.md names
│   ├── test_grammar_coverage.py       # SC-006, binding-power rows ↔ grammar levels
│   ├── test_precedence_bite.py        # SC-007
│   └── test_invalid_rules.py          # SC-005
├── integration/
│   └── test_rules_cli.py
├── unit/
│   └── dsl/
│       ├── test_lexer.py
│       ├── test_parser.py
│       ├── test_units.py
│       ├── test_checker.py
│       ├── test_ruleset.py
│       └── test_tree_view.py
└── fixtures/
    ├── rule_trees/                    # 17 golden canonical trees
    └── invalid_rules.toml             # ≥ 2 cases per diagnostic code
```

**Structure Decision**: 沿用 M0 的單一 `src` layout，所有 M1 程式碼放進已預留的 `dsl/`。parser 只依賴 lexer 與 syntax；checker 依賴
syntax、units、vocabulary；ruleset 串起整條載入流程；tree_view 與 cli 是唯一碰到 Matplotlib 與檔案系統的模組。
`syntax.py` 不取名 `ast.py`，避免與標準庫同名造成閱讀混淆。

## Phase 0: Research Decisions

- [research.md](research.md) 先把 17 條語料轉成「語料逼出來的需求」表，再做 10 個決策；三個有替代方案的決策附加權評分：
  規則集容器（TOML 4.15）、時間概念語法（保留字呼叫 4.55）、解析技術（Pratt 4.25）。
- user 2026-10-28 裁示：採用 research 的語法；`or`／`not` 只登記為保留字；用 Pratt parser。spec FR-004 與 Clarifications 已同步。
- 重大決策收斂於 [ADR 003](../../docs/decisions/003-rule-dsl-syntax.md)，含重新評估的觸發條件。
- 所有 `NEEDS CLARIFICATION` 已消除。

## Phase 1: Design & Contracts

- [contracts/grammar.ebnf](contracts/grammar.ebnf)：8 個優先序層級、每條產生式的 `builds:` 與 `used by:` 註記；SC-006 與結合力表測試都讀這份。
- [contracts/syntax-tree.md](contracts/syntax-tree.md)：15 種節點、span 規則、以 `canonical_bytes` 產生的正規序列化；數字常值以字串保存，
  因為 `canonical_bytes` 會量化數值（E1：`src/assertion_engine/artifacts.py:97`）。
- [contracts/ruleset.md](contracts/ruleset.md)：TOML 形狀、單位表、內建詞彙、時間保留字的型別、型別與量綱規則。
- [contracts/cli.md](contracts/cli.md)：`check`／`dump`／`tree`、診斷格式、exit code；`tree` 拒絕覆寫既有檔案。
- [data-model.md](data-model.md)：實體、九步載入流程、Pratt 結合力表、產生式覆蓋率收集、解析深度上限、22 個錯誤碼的封閉清單。
- [quickstart.md](quickstart.md)：所有輸出寫到 `mktemp -d`，不寫進工作樹。

### 測試的獨立性

預期語法樹不能由 parser 自己產生再回頭比對——那等於讓實作批改自己的考卷。順序如下：

1. 測試先以手寫的巢狀 tuple 寫出每條語料規則的預期結構（只看形狀，例如 `(">=", "battery_percent", "battery_floor_percent")`），
   這是從文法與 contract 推出來的，不經過 parser。
2. parser 的輸出結構與手寫結構一致之後，才產生 `tests/fixtures/rule_trees/*.json`（含 span）並 commit；之後的回歸以這些 bytes 比對。
3. span 由單元測試對代表性案例逐一手寫驗證；golden 檔裡的 span 是在結構驗證之後才凍結的。

SC-007 的咬合檢查：parser 的結合力表可以從參數注入；測試把每一組相鄰層級對調後解析語料，斷言至少一條語法樹改變，
並把任一層級改錯時至少一條 golden 比對失敗。

### 交給 tasks 階段的實作順序提示

1. 架構邊界與 package 骨架（`dsl` 解除「必須為空」）。
2. lexer → syntax → parser，先達 Gate「基本規則」（SC-001），再補時間保留字（SC-002、SC-003）。
3. units → vocabulary → checker → ruleset（含錯誤碼與無效案例，SC-005）。
4. 覆蓋率與咬合測試（SC-006、SC-007）、決定性（SC-008）。
5. 語法樹圖（FR-014）在 checker 完成後就先做，讓基本規則的樹早點看得到（learning-style：視覺化不推遲到最後）。
6. 覆蓋率與咬合測試、白話橋接文件（FR-015）、user 看 17 張圖簽核（SC-009）與 README 的套件表更新。

## Post-Design Constitution Re-check

- [x] 文法的每條產生式都有 `used by:` 指回語料；沒有語料需要的 `or`／`not` 只是保留字。
- [x] 文法對應有兩個執行者：產生式覆蓋率測試、結合力表與層級的逐列測試。
- [x] 時間保留字是各自獨立的節點種類，M2／M3 可以從語法樹判斷哪些規則需要歷史、哪些要等期限。
- [x] 量綱檢查在載入時擋下公式錯誤；`%` 作為專案自訂基本量的取捨已在 research 與 ADR 標明。
- [x] 預期語法樹由手寫結構先行，不讓 parser 產生自己的答案。
- [x] 語法樹圖是 rendered PNG，簽核看實際圖片。
- [x] 沒有新增依賴；Graphviz 不可用（E1）時以既有 Matplotlib 處理。

## Complexity Tracking

No constitution violations require justification.
