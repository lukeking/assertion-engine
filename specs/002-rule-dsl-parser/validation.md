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
