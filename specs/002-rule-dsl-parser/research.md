# Phase 0 Research: M1 Rule DSL and Parser Tree

## Evidence convention

沿用 001：**E1** 本 checkout 實測；**E2** 官方文件、文獻或算術推得；**E3** 工程判斷，仍待實作證據。
分數不是 Gate；Gate 只收 E1。

## 起點：語料逼出來的需求

把 [rule-corpus.md](rule-corpus.md) 的 17 條逐條問「要寫出這條，語言必須有什麼」，得到下表。
後面每個決策都回指這張表；表上沒有的能力不進文法（spec SC-006）。

| 需求 | 逼出它的規則 |
|---|---|
| 欄位與具名門檻比較 | 全部 |
| 向量分量（`.d`） | 衍生量 `altitude_m`、`descent_speed_mps` |
| 水平向量長度、三維向量長度 | `horizontal-speed-limit`、`geofence-*`（水平）；`no-sudden-jump`（三維） |
| 向量加減、向量乘純量 | `no-sudden-jump`、`geofence-forecast` |
| 四則運算、一元負號 | `return-reserve`、`battery-drain-rate`、`battery-runout-forecast`、`altitude-trend-ceiling` |
| 且 | `geofence-cylinder`、`monotonic-sequence` |
| 若 A 則 B | `low-battery-stay-close`、`battery-tier-*` |
| 條件值 | `descent-speed-near-ground` |
| 前一筆事件的值 | `telemetry-heartbeat`、`monotonic-sequence`、`no-sudden-jump` |
| N 秒前的值 | `battery-tier-low` |
| 條件持續 N 秒 | `battery-tier-low`、`battery-tier-critical` |
| N 秒內必須發生 | `battery-tier-emergency` |
| 視窗斜率 | `battery-drain-rate`、`battery-runout-forecast`、`altitude-trend-ceiling` |
| 具名衍生量（可由規則集自訂） | `return-reserve` 與 `battery-runout-forecast` 共用的返航時間 |
| 量綱：%、m、s、m/s、%/s | 全部具名門檻 |
| 常值 `0` 與任意量綱比較 | `battery-tier-critical`（「正在下降」＝下降速度 > 0） |
| 無因次常值 `1` | `monotonic-sequence`（序號加 1） |

**語料沒有用到的**：「或」、「非」、`!=`、`.n`／`.e`、小數常值。其中「或」與「非」是 FR-004 列出的能力，
與 SC-006「每條產生式都要有語料用到」衝突——見 Decision 2 的待決事項。

## Decision 1: 規則集容器——TOML 檔裝具名門檻、衍生量與規則，DSL 只寫運算式

**Decision**: 一份規則集是一個 TOML 檔（與 `scenarios/*.toml` 同一種格式），分三節：`[parameters.<名稱>]` 宣告具名門檻的單位、
`[derived.<名稱>]` 宣告衍生量的單位與定義運算式、`[rules.<短名>]` 寫規則的類別與運算式。DSL 只負責單一運算式；
宣告、名稱、metadata 都交給 TOML。規則短名沿用語料的 kebab-case，因為它是 TOML key，不會和減號衝突。

### Weighted comparison

尺度 1（差）到 5（強），每格標證據等級。

| 準則 | 權重 | TOML＋運算式 DSL | 完整 DSL 檔（含 `param`／`rule` 宣告） | 規則寫在 Python 字串裡 |
|---|---:|---:|---:|---:|
| 文法只含語料需要的產生式（SC-006） | 30% | 5 E2 | 3 E2 | 4 E2 |
| 與既有情境檔一致、免新解析層 | 20% | 5 E1 | 2 E2 | 3 E2 |
| 撰寫體驗 | 20% | 3 E3 | 5 E3 | 2 E3 |
| M2 綁定門檻值的方便性 | 15% | 4 E3 | 3 E3 | 3 E3 |
| 學習價值 | 15% | 3 E3 | 5 E3 | 2 E3 |
| **加權總分** | **100%** | **4.15** | **3.50** | **2.95** |

**E1**: `tomllib` 在本機 CPython 3.14.4 可用；M0 的 `simulator/config.py` 已用它讀情境。

**Alternatives considered**: 完整 DSL 檔讓宣告也成為語言的一部分，學習價值最高，但會長出語料沒有要求的產生式
（`param`、`rule`、區塊結構），而且 M0 已有一套 TOML 驗證慣例。規則寫進 Python 會把語料和程式碼綁死，Fuzzer 也更難保持獨立。

**Reopen trigger**: 規則需要 TOML 字串裝不下的結構（例如規則之間互相引用、區域變數），或撰寫時字串跳脫成為實際負擔。

## Decision 2: 具體語法——符號做算術與比較，英文關鍵字做邏輯，時間概念是保留字形式的呼叫

**Decision**:

- 算術與比較用符號：`+ - * /`、`< <= > >= == !=`；不允許串接比較（`a < b < c` 以專屬錯誤拒絕）。
- 邏輯用關鍵字：`and`、`implies`、`if … then … else …`（條件值，可在任何運算式位置，但放在比較右側時要加括號）。
- 向量分量用後綴 `.n`／`.e`／`.d`。
- 純函式用一般呼叫：`norm(v)`（三維長度）、`hnorm(v)`（水平長度）。
- 時間概念是**保留字**，形狀和呼叫一樣，時間長度一律放最後一個參數：
  `prev(x)`、`ago(x, d)`、`held_for(c, d)`、`within(c, d)`、`slope(x, w)`。
  做成保留字而不是一般函式，是因為它們會讓 Evaluator 需要記憶過去或等待未來——這是語意上的分界，語法樹上要看得出來。
- 常值：整數與小數；`0` 可以和任何量綱比較或相加，其他常值是無因次。

### Weighted comparison

| 準則 | 權重 | 保留字呼叫（`held_for(c, d)`） | 中綴時間語法（`c for d`、`within d: c`） | MTL 符號（`H[0,d] c`、`F[0,d] c`） |
|---|---:|---:|---:|---:|
| 規則作者讀得懂 | 30% | 4 E3 | 5 E3 | 2 E3 |
| 文法大小 | 20% | 5 E2 | 3 E2 | 4 E2 |
| 與解析技術的契合、歧義風險 | 20% | 5 E2 | 3 E2 | 4 E2 |
| 對應時序邏輯理論（學習） | 15% | 4 E2 | 4 E2 | 5 E2 |
| 加新時間概念不用改文法形狀 | 15% | 5 E2 | 2 E2 | 3 E2 |
| **加權總分** | **100%** | **4.55** | **3.60** | **3.40** |

**E2 basis**: 五個時間保留字對應 Koymans 的 metric temporal logic（見 Decision 5 的出處）：`prev` 是「前一刻」、
`held_for(c, d)` 是過去 d 秒內 c 一直成立、`within(c, d)` 是未來 d 秒內 c 至少成立一次。後兩者一個看過去、一個看未來，
正好是 spec 要求「兩種不同的節點」的理由：Evaluator 對前者可以當場判定，對後者要等到期限才知道。

### 17 條語料的寫法

具名門檻都在規則集的 `[parameters]` 宣告單位；`return_time_s` 是規則集自訂的衍生量。

```text
# 內建衍生量（詞彙表提供，同樣用 DSL 定義）
altitude_m           := -position_ned_m.d                  # m
descent_speed_mps    := velocity_ned_mps.d                 # m/s，下降為正
horizontal_speed_mps := hnorm(velocity_ned_mps)            # m/s
home_distance_m      := hnorm(position_ned_m)              # m，家＝NED 原點

# 規則集自訂衍生量
return_time_s := home_distance_m / cruise_speed_mps + altitude_m / descent_rate_mps   # s

battery-floor:
  battery_percent >= battery_floor_percent
altitude-ceiling:
  altitude_m <= altitude_ceiling_m
horizontal-speed-limit:
  horizontal_speed_mps <= horizontal_speed_max_mps
return-reserve:
  battery_percent > return_time_s * drain_rate_percent_per_s + return_reserve_percent

geofence-cylinder:
  home_distance_m <= fence_radius_m and altitude_m <= fence_altitude_m
low-battery-stay-close:
  battery_percent < battery_low_percent implies home_distance_m <= low_battery_radius_m
descent-speed-near-ground:
  descent_speed_mps <= (if altitude_m < near_ground_altitude_m
                        then near_ground_descent_max_mps
                        else descent_max_mps)

telemetry-heartbeat:
  mission_time_s - prev(mission_time_s) <= heartbeat_max_s
monotonic-sequence:
  sequence_number == prev(sequence_number) + 1 and mission_time_s > prev(mission_time_s)
battery-tier-low:
  held_for(battery_percent < battery_low_percent, reaction_time_s)
    implies home_distance_m < ago(home_distance_m, closing_window_s)
battery-tier-critical:
  held_for(battery_percent < battery_critical_percent, reaction_time_s)
    implies descent_speed_mps > 0
battery-tier-emergency:
  battery_percent < battery_emergency_percent
    implies within(altitude_m < landed_altitude_m, landing_deadline_s)
no-sudden-jump:
  norm(position_ned_m - prev(position_ned_m)) / (mission_time_s - prev(mission_time_s))
    <= jump_rate_max_mps

battery-drain-rate:
  -slope(battery_percent, drain_window_s) <= drain_rate_max_percent_per_s
battery-runout-forecast:
  (battery_percent - battery_critical_percent) / -slope(battery_percent, trend_window_s)
    >= return_time_s
altitude-trend-ceiling:
  altitude_m + slope(altitude_m, climb_window_s) * lookahead_s <= altitude_ceiling_m
geofence-forecast:
  hnorm(position_ned_m + velocity_ned_mps * lookahead_s) <= fence_radius_m
```

量綱驗算（E2 算術）：`return-reserve` 的右側是 s × %/s ＋ % ＝ %；`battery-runout-forecast` 的左側是
% ÷ %/s ＝ s；`no-sudden-jump` 是 m ÷ s ＝ m/s；`geofence-forecast` 是 m ＋ m/s × s ＝ m。17 條都在量綱上自洽。

### 「或」與「非」：保留字先登記，文法不放

語料 17 條沒有一條需要 `or` 或 `not`；`implies` 吸收了「若 A 則 B」這類原本會寫成「非 A 或 B」的規則。
FR-004 原本要求它們存在，SC-006 要求每條產生式都有語料用到——兩條需求在現有語料下互相矛盾。考慮過三種解法：

- 語料補上真的需要它們的規則（例如「電量低於返航所需時，必須已在返航**或**已在下降」）。
- **採用**：M1 文法不放 `or`／`not`，但先登記為保留字；之後加入不會讓既有規則失效。
- 照 FR-004 放進文法，SC-006 對這兩條產生式例外。

user 2026-10-28 裁示採第二種，FR-004 已改寫。GAR-18 驗收的「邏輯運算」由 `and`、`implies`、`if … then … else …` 滿足。

**Reopen trigger（或／非）**: 第一條真的需要 `or` 或 `not`、且無法以 `implies` 清楚表達的語料規則出現時。

**Reopen trigger**: 新規則需要 `.n`／`.e` 以外的向量操作（內積、方位角），或有規則必須寫出「帶單位的常值」。

## Decision 3: 解析技術——Pratt parser，配一張與文法層級逐列對應的結合力表

**Decision**: 運算式用 Pratt parser（top-down operator precedence）：每種 token 有「放在開頭時怎麼解析」（prefix）和
「放在中間時怎麼解析」（infix）兩個處理函式，加上一個結合力（binding power）。文法的每一個優先序層級在結合力表裡有恰好一列，
`tests/contract/` 的測試逐列比對表的順序與 [contracts/grammar.ebnf](contracts/grammar.ebnf) 的層級順序。
決策 002 允許 recursive descent 或 Pratt；這裡用分數選。

### Weighted comparison

| 準則 | 權重 | Pratt＋結合力表 | 每層一個函式的 recursive descent | 兩者混用 |
|---|---:|---:|---:|---:|
| 文法與解析步驟的對應（憲章 IV、FR-002） | 30% | 3 E2 | 5 E2 | 4 E2 |
| 學習價值 | 25% | 5 E3 | 4 E3 | 5 E3 |
| 錯誤位置品質 | 15% | 4 E3 | 4 E3 | 4 E3 |
| 加一個運算子的成本 | 15% | 5 E2 | 3 E2 | 4 E2 |
| 程式碼量 | 15% | 5 E2 | 3 E2 | 4 E2 |
| **加權總分** | **100%** | **4.25** | **4.00** | **4.25** |

Pratt 與混用同分；混用要同時教兩種技術、兩種技術之間還有一條接縫，所以選單純的 Pratt。
它在對應性上的弱點（層級藏在數字裡）由「結合力表 ↔ EBNF 層級」的逐列測試補上——對應從散文變成會失敗的檢查。

**E2 basis**: Crafting Interpreters 第 6 章示範每條文法規則寫成一個函式、每個優先序一條規則的 recursive descent；
同書 17.6 節示範以 prefix／infix／precedence 三欄的表驅動的 Pratt parser。

**Alternatives considered**: 每層一個函式的 recursive descent 是對應性最直接的寫法（Crafting Interpreters 第 6 章），
定稿文法的 8 個優先序層級意味著 8 個形狀幾乎相同的函式；它留在 [M1 演算法說明](../../docs/algorithms/002-rule-dsl-parsing.md) 當對照教材。

**Reopen trigger**: 結合力表與 EBNF 的逐列對應測試無法維持（例如出現需要特殊回溯的語法），或錯誤訊息品質成為驗收要求。

## Decision 4: 解析與檢查分兩段——parser 只管形狀，checker 管名稱、型別與量綱

**Decision**: parser 把文字轉成語法樹，不查任何名稱；checker 拿語法樹與詞彙表做名稱解析、參數個數、型別（布林／數值／三維向量）
與量綱推導。量綱表示成三個基本量的整數指數：長度（m）、時間（s）、電量百分比（%）。單位字串只接受一張固定表：
`1`、`%`、`m`、`s`、`m/s`、`%/s`。衍生量的定義也用同一個 parser 解析，checker 驗證宣告的單位與推導出的量綱相同，並拒絕循環定義。

**E2 basis**: BIPM SI 手冊第 9 版 §2.3.3 定義量的量綱為基本量指數的乘積，並把比值類的量歸為「單位為一」的量。

**專案選擇（E3）**: SI 把百分比視為無因次；這裡刻意把 `%` 當成獨立的基本量，好讓「電量 % 和序號相加」這種錯誤被擋下。
代價是 `%` 和真正無因次的量不能混用；語料裡沒有需要混用的規則。

**Reopen trigger**: 語料出現需要 % 與無因次量互換的規則，或需要第四個基本量（例如角度、溫度）。

## Decision 5: 時間保留字的出處——Koymans 的 metric temporal logic

**Decision**: 時間保留字的命名與參數順序是本專案自訂的語法；它們的意義對應 MTL 的有界時間運算子，
M1 只用這個對應寫白話橋接，不實作語意。

**E2 basis**: Koymans (1990), "Specifying Real-Time Properties with Metric Temporal Logic", *Real-Time Systems* 2(4): 255–299，
在時序邏輯上加上量測時間距離的函數，引入帶時間界限的運算子。

## Decision 6: 語法樹的形狀與正規序列化

**Decision**: 語法樹是不可變的 dataclass；每個節點帶 `span`（起訖的行與欄，從 1 起算，終點不含）。
時間保留字各自是一種節點（`Previous`、`Ago`、`HeldFor`、`Within`、`Slope`），不共用 `Call`。
數字常值以原文字串保存。正規序列化沿用 `artifacts.canonical_bytes`（排序 key、精簡分隔符、結尾 LF）；
因為它會量化數值，常值必須以字串進入序列化。回歸測試集的預期樹放 `tests/fixtures/rule_trees/<短名>.json`。

**E1**: `artifacts.canonical_bytes` 對 mapping 排序 key、對數值套用 `quantize`（`src/assertion_engine/artifacts.py:97`）。

## Decision 7: 錯誤模型——第一個錯誤就停，錯誤碼是封閉清單

**Decision**: 解析或檢查遇到第一個錯誤就停（決策 002 已接受不做錯誤恢復），回報錯誤碼、規則短名、運算式內的行與欄、原因與原文片段。
錯誤碼是封閉清單（見 [data-model.md](data-model.md)），每一碼在無效規則集至少有 2 個案例（SC-005）。
位置分兩種：運算式裡的錯誤回報相對於該規則運算式字串的行與欄，因為 `tomllib` 只回傳解析後的值、不帶每個值在檔案中的位置；
TOML 本身的語法錯誤則回報檔案的行與欄。

**E1**: CPython 3.14.4 的 `tomllib.TOMLDecodeError` 帶 `msg`、`lineno`、`colno`、`pos` 屬性（`tomllib.loads("a = ")` 回報第 1 行第 5 欄）。

## Decision 8: 語法樹圖——Matplotlib，葉節點依序排、父節點置中

**Decision**: 用現有的 Matplotlib（Agg backend）畫 PNG。版面：葉節點由左到右依原文順序排，父節點的水平位置是子節點的平均，
深度決定高度。節點標籤是節點種類加原文片段；checker 成功時附上量綱。

**E1**: 本機沒有 Graphviz 的 `dot`；Matplotlib 3.11.2 已是專案依賴。

**E2 basis**: Reingold & Tilford (1981), "Tidier Drawings of Trees", *IEEE Transactions on Software Engineering* SE-7(2): 223–228，
是整齊樹狀圖版面的標準演算法。M1 用的「父節點置中於子節點」是它要改進的較簡單版本；子樹較寬時會比必要的寬，
語料的樹不深，這個代價可以接受。

**Reopen trigger**: 有語料規則的樹圖出現節點重疊，或寬到審查者讀不出來（SC-009）。

## Decision 9: 語料放在 `rules/corpus.toml`，回歸測試直接讀它

**Decision**: 語料規則集放在 repo 根目錄的 `rules/corpus.toml`（與 `scenarios/` 平行，M2 會直接拿它評估）。
`rule-corpus.md` 保留白話意圖；兩邊以短名對應，測試檢查兩邊的短名集合相同。
SC-006 的執行者是覆蓋率測試：parser 在解析時記下每個被走到的產生式名稱，對語料全部規則與衍生量解析一輪後，
走到的集合必須等於 `contracts/grammar.ebnf` 宣告的產生式集合。

## Decision 10: 不做效能宣稱

**Decision**: 規則在載入時解析一次，不在逐筆事件的處理路徑上；M1 不量測、不宣稱任何延遲，憲章原則 II 的延遲階梯不適用於本 feature。
M2 的 Evaluator 才是那道階梯的對象。

## Sources

- [Crafting Interpreters, ch. 6 "Parsing Expressions"](https://craftinginterpreters.com/parsing-expressions.html)
- [Crafting Interpreters, ch. 17 "Compiling Expressions"（§17.6 A Pratt Parser）](https://craftinginterpreters.com/compiling-expressions.html)
- Pratt, V. R. (1973). "Top Down Operator Precedence." *Proceedings of the 1st ACM Symposium on Principles of Programming Languages*, 41–51.
  （原文未取得；書目經 [Wikipedia: Vaughan Pratt](https://en.wikipedia.org/wiki/Vaughan_Pratt) 與 [Crockford 的導讀](https://crockford.com/javascript/tdop/tdop.html) 核對）
- [Koymans (1990), Real-Time Systems 2(4)](https://link.springer.com/doi/10.1007/BF01995674)
- [Reingold & Tilford (1981), IEEE TSE SE-7(2)](https://ieeexplore.ieee.org/document/1702828/authors)
- [BIPM SI Brochure, 9th edition](https://www.bipm.org/en/si-brochure)
