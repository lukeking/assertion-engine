# M1 validation evidence

工具：CPython 3.14.4；uv 0.11.9；pytest 9.1.1；Ruff 0.16.10；Matplotlib 3.11.2（版本鎖在 `uv.lock`）。
Runner：`MPLBACKEND=Agg uv run pytest`；靜態檢查：`uv run ruff format --check .`、`uv run ruff check .`。

## Gate「基本規則」（SC-001）— CP3

受測 commit：`74a8ed3aac0e27fe640cac6139e9ad4656cdeee7`（`feat(002): parse basic rules into syntax trees`）。

已到達階的 7 條規則（`tests/contract/test_rule_trees.py` 的 `BASIC_RULES`，等於語料 threshold＋logic 兩類）：

| 類別 | 規則 |
|---|---|
| threshold | `battery-floor`、`altitude-ceiling`、`horizontal-speed-limit`、`return-reserve` |
| logic | `geofence-cylinder`、`low-battery-stay-close`、`descent-speed-near-ground` |

另有 5 個衍生量定義（4 個內建定義字串與 `return_time_s`）比對手寫結構。

RED→GREEN（executor 在 stub 上取得，main 重跑 GREEN）：

- Stub（`tokenize` 回 `()`、`parse` 一律回 `Name("x", …)`、collector 不記錄、`BINDING_POWERS` 為空），
  尚無 golden：`95 failed, 172 passed`。失敗在斷言上，不是 import error：lexer 的 kind／span、
  `a - b - c` 左結合、多行 span、collector 的 `Counter`、`rule_shapes.py` 結構比對、golden 檔名集合
  （`missing tests/fixtures/rule_trees`），以及 7 個 golden bytes 測試（讀檔失敗，不略過）。
- 真 parser、尚無 golden：`8 failed, 259 passed`，只剩檔名集合與 7 個 golden bytes 測試。
- 產生 golden 之後：`tests/unit/dsl` `125 passed`、`tests/contract` `142 passed`；
  全套 `566 passed`（CP2 結束時 461）。Ruff：`89 files already formatted`、`All checks passed!`。
- main 在受測 commit 上：`tests/unit/dsl` 加 `tests/contract/test_rule_trees.py` `155 passed`；
  `battery-floor.json` 等於 `contracts/syntax-tree.md` 範例加一個 LF；`descent-speed-near-ground` 的
  Compare `[1,1,3,44]`、Conditional `[1,23,3,43]`、then 分支 `[2,28,2,55]` 由運算式原文重算一致。

SC-008：每條規則解析 3 次 byte-identical 的測試在 stub 上也通過，因為任何決定性的函式都會通過；
它只排除非決定性，正確性由結構比對與 golden bytes 擋。

比較運算子掃描（executor，一次一個突變、在 scratch 複本跑 `tests/unit/dsl` 與 `tests/contract`）：
30 個突變、28 個被抓到、2 個存活。

- `parser.py` 的 `powers["conditional"] > minimum` 改 `>=`：等價突變。呼叫端的 minimum 只會是 0、
  別的層級的結合力或結合力減 1，在預設表與層級差大於 1 的表（含 T039 的對調）下不會等於 conditional 的結合力。
- `_unexpected` 的 `token.kind == "end_of_input"` 改 `!=`：只決定回報 `unexpected_end` 還是
  `unexpected_token`，要靠錯誤路徑測試抓，屬 T023。

Golden 的產生方式：結構比對全部通過後，以 `assertion_engine.dsl.parser.parse` 解析 `rules/corpus.toml`
的運算式，寫出 `canonical_bytes({"rule": <短名>, "tree": to_document(tree)})`；golden 不手改。

## 無效規則被拒並指出位置（SC-005）— CP4

受測 commit：checker `631e882`（修正 `8bf798b`）；載入流程與語法錯誤碼 `2b5b5de`（修正 `20a063a`、
contract 字句 `9a976a9`）；CLI `79f7cf8a8b90d5e8567b2467a5882b419e576490`。

`tests/fixtures/invalid_rules.toml` 共 57 例，`nonpositive_duration` 以外的 21 碼各至少 2 例（`nonpositive_duration`
屬時間保留字，T033 補）：

| 錯誤碼 | 例數 | 錯誤碼 | 例數 | 錯誤碼 | 例數 |
|---|---:|---|---:|---|---:|
| `invalid_character` | 3 | `chained_comparison` | 3 | `unknown_name` | 3 |
| `invalid_number` | 3 | `reserved_word` | 3 | `arity_mismatch` | 2 |
| `empty_expression` | 2 | `invalid_axis` | 2 | `type_mismatch` | 3 |
| `unexpected_token` | 3 | `nesting_too_deep` | 3 | `dimension_mismatch` | 2 |
| `unexpected_end` | 3 | `invalid_ruleset` | 5 | `not_boolean_rule` | 3 |
| `unclosed_parenthesis` | 3 | `unknown_unit` | 2 | `derived_unit_mismatch` | 2 |
| `trailing_input` | 2 | `name_conflict` | 3 | `derived_cycle` | 2 |

每例比對錯誤碼、位置與 owner，只對錯誤碼不會通過。

RED→GREEN（executor 在 stub 上取得，main 重跑 GREEN）：

- checker：stub（單位一律 (0,0,0)、checker 全部接受）`166 failed, 128 passed`（`tests/unit/dsl`）→
  `294 passed`；全套 566 → 735。
- 載入流程與語法錯誤碼：stub loader 加上當時的 lexer／parser，`139 failed, 558 passed`；CP3 留下的 6 種錯碼輸入
  （`1e3`、`2.`、空字串、`(a + b`、`a < b < c`、`or`／`not`）各自失敗在錯誤碼斷言上，深度 101 為 `DID NOT RAISE`
  → `tests/unit/dsl` `398 passed`、`tests/contract` `300 passed`；全套 997，`20a063a` 後 998。
- CLI：stub（印錯的文字、exit code 錯）`17 failed, 4 passed`（通過的 4 例是 argparse 自己處理的缺參數）→
  `22 passed`；全套 1020。
- main 在 `79f7cf8`：`tests/unit/dsl`、`tests/contract/test_invalid_rules.py`、`tests/integration/test_rules_cli.py`
  `579 passed`；Ruff `100 files already formatted`、`All checks passed!`；`uv sync --locked` 通過、`uv.lock` 不變。
  直接執行 `assertion-rules`：`check` 印 `ok: 1 rules, 0 derived, 1 parameters`；拼錯名稱印 cli.md 格式的
  標頭、原文行與 caret 行並 exit 1；`dump --rule battery-floor` 的 bytes 等於 golden。

深度上限（user 2026-10-29 裁示保留現行計數，data-model「Parse depth limit」已改寫）：main 在 pin 於 `2b5b5de`
的 worktree 實測三種計數——只數括號、前綴與參數時，600 個 `implies` → `RecursionError`；再加上 `implies`
時，100 層 `(a and b < c + d * (…))` → `RecursionError`；現行的每個運算元一層，兩者都回 `nesting_too_deep`。

CP3 比較運算子掃描留下的 `_unexpected` 存活突變（`==` 改 `!=`），在 `79f7cf8` 上讓 13 條測試失敗，已由
T023 的錯誤路徑測試抓到。
