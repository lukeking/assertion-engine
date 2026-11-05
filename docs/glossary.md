# 術語表

本檔是本專案術語定義的唯一位置：演算法文件（`docs/algorithms/`）與 README 用到這些詞時只連到這裡，不另寫定義。
目前收 M1（規則 DSL 與語法樹）用到的詞，之後的里程碑在同一份檔案追加詞條。DSL 是 domain-specific language，
為一個領域專門設計的小語言；本專案的 DSL 用來寫檢查遙測（telemetry：無人機每一筆回報的狀態資料）的規則。

本檔不是文法規格（文法在 `specs/002-rule-dsl-parser/contracts/grammar.ebnf`），也不定義規則怎麼評估。

## 誰負責什麼

一條規則從文字到判定違規，經過三段：

1. 解析器（parser）把規則文字變成一棵語法樹。樹帶的是結構：誰包含誰、誰和誰比較。
2. 檢查器（checker）替樹上每個節點推出型別，並把每個名稱對到它的來源（欄位、具名參數或衍生量）。
   型別與來源另外記在樹旁邊，不寫進樹本身。
3. 評估器（evaluator）拿遙測資料把規則算出真或假。這是 M2（GAR-19）與 M3（GAR-20）的工作，M1 沒有評估器。

本檔寫的是每種節點與名稱的意思。講到「實際怎麼算」的細節（例如 `held_for` 是不是「至少」N 秒），
本檔只寫「由 M2／M3 定義」，不先替它們決定。

## 詞條的格式

- 每個詞條是一個 `###` 標題：先寫給人讀的說法，括號裡用 inline code（反引號框起來的程式碼字樣）寫程式識別字，
  也就是程式碼裡實際用的名稱，例如 `` ### 蘊涵（`Implies`） ``。主題沒有程式識別字的詞條（例如「維度」「規則」）標題只寫說法。
- 標題下是：定義（一句）、判準（怎麼分辨是不是它）、例子、不要混用（容易和它搞混、或本專案不拿來指它的詞）。
  節點詞條另列寫法與型別；尚未決定的事寫在「待定」，並寫明由誰決定。
- `tests/contract/test_glossary.py` 讀這些標題：`src/assertion_engine/dsl/syntax.py` 的每種節點，
  以及名稱的三種來源（`field`、`parameter`、`derived`），都必須有一個標題帶著它的識別字。
  新增一種節點卻沒寫詞條，測試會失敗並列出缺的識別字。同一個識別字只放在它自己詞條的標題裡，
  否則刪掉那個詞條時測試抓不到。
- 同一個測試也拿欄位表、衍生量表與單位清單對照 `src/assertion_engine/dsl/vocabulary.py`、`units.py`：
  程式改了這裡沒改，測試會失敗。所以內文不寫「共幾個」，數量以表格為準。
- spec、research、contracts 等既有文件有些用詞和本檔不同（例如「量綱」「具名門檻」「蘊含」）。本檔不改它們；
  要不要統一，由 user 另行決定。

## 讀語法樹圖的方框

`assertion-rules tree` 畫出的語法樹圖，每個方框由上到下是（`src/assertion_engine/dsl/tree_view.py` 的 `label`）：

1. 節點種類，例如 `Compare`：見「語法樹的節點」。
2. 這個節點在規則文字裡對應的原文片段。
3. 檢查器推出的型別，例如 `scalar[m]`：見「型別與單位」。
4. 只有 `Name` 有第四行：名稱的來源，`field`、`parameter` 或 `derived`：見「名稱的來源」。

## 規則與語法樹

### 規則

- 定義：規則集（rule set：一個 TOML 設定檔，宣告具名參數、衍生量與規則）裡 `[rules.<短名>]` 的一條；
  整棵樹必須算成真，算成假就是違規。
- 判準：檢查器只要求樹根的型別是 `bool`（否則錯誤碼 `not_boolean_rule`）；有沒有違規由 M2 的評估器判定。
- 「必須成立」是「身為規則」的性質，不屬於哪一種節點：`battery-floor` 的樹根是 `Compare`，
  `low-battery-stay-close` 的樹根是 `Implies`，兩條都必須算成真。
- 每條規則另有一個類別（`category`）：`threshold`（門檻比較）、`logic`（邏輯組合）、`temporal`（時序約束）、
  `trend`（趨勢外推），對應 `specs/002-rule-dsl-parser/rule-corpus.md` 的四節。
- 例子：`battery-floor` 的運算式是 `battery_percent >= battery_floor_percent`，意思是電量不得低於電量下限。
- 不要混用：「違規」只指規則算成假。規則本身寫錯（解析或檢查失敗）是載入錯誤：整份規則集被拒，談不上違規。

### 語法樹、節點（`Node`）

- 定義：解析器把一條規則的文字變成的樹；每個節點是一個構造（比較、四則運算、函式呼叫……），
  它的子節點是這個構造的組成部分，樹根就是整條規則。
- 判準：`syntax.py` 的 `Node` 列出所有節點種類，每種在「語法樹的節點」有一個詞條。
  每個節點帶 `span`，記它在規則文字裡的起訖行與欄；方框第二行的原文片段就是從這裡取的。括號不屬於任何節點。
- 例子：`battery_percent >= battery_floor_percent` 是一個 `Compare` 節點，兩個子節點都是 `Name`。
- 不要混用：語法樹只帶結構，不含型別與名稱的來源（那是檢查器另外記的）。節點的組成部分本檔稱「子節點」，
  不稱「欄位」（見「欄位」）。

## 型別與單位

型別（type）是一個值屬於哪一種東西：`bool`、純量或向量。純量與向量另外帶單位，寫在方括號裡：
`scalar[m]` 讀作「單位是 m 的一個數」，`vector[m/s]` 讀作「三個分量都以 m/s 計的向量」；`bool` 沒有單位，不帶方括號。
種類不對（例如拿向量去比大小）是錯誤碼 `type_mismatch`；單位對不上是 `dimension_mismatch`。

### 單位（`dimension`）

- 定義：一個值測量的是哪一種東西（長度、時間、電量百分比……），以及用哪個單位；一般物理裡同一種東西有好幾個單位
  （公尺、公里、英呎都量長度），本 DSL 每種只允許一個（長度只用 `m`），所以兩者一致，說「單位對不上」就是精確的。
- 判準：能不能乘一個固定的數換過去（公里乘 1000 就是公尺）。能，就是同一種東西，才可以相加、相減、比較；
  不能（公尺與秒），檢查器就拒絕。例外是 `%`，見下面。
- 本專案的單位只有這些：`1`（沒有單位，例如序號）、`%`、`m`、`s`、`m/s`、`%/s`。規則集宣告具名參數與衍生量時只能用這些。
- 單位會組合：乘除時單位跟著乘除，`m` 除以 `s` 是 `m/s`，`m/s` 乘 `s` 是 `m`。算式中間可以算出清單以外的組合
  （例如 `m` 乘 `m` 是 `m^2`），型別標籤照樣印出來；只有宣告受這份清單限制。程式裡把單位記成長度、時間、
  電量百分比三個整數次方（`src/assertion_engine/dsl/units.py` 的 `Dimension`）。
- `%` 是獨立的單位：本專案的 `%` 是電量百分比。照上面的判準，百分比乘 0.01 就是一般的數，國際單位制（SI）也把它當成沒有單位；
  本專案刻意把 `%` 當成獨立的一種，讓「電量加序號」這種錯誤被擋下。代價是 `%` 不能和沒有單位的數混用，語料裡沒有需要混用的規則
  （`specs/002-rule-dsl-parser/research.md` Decision 4）。
- 例子：`return-reserve` 的 `return_time_s * drain_rate_percent_per_s` 是 `s` 乘 `%/s`，得到 `%`，才能和 `battery_percent` 比較。
- 不要混用：「量綱」「因次」是同一個概念在物理課本的譯名，本檔不用（spec、research、contracts 仍寫「量綱」）；
  「無因次」讀作「沒有單位」，即 `1`；「維度」只指向量的分量，見「維度」。

### 維度

- 定義：向量的分量，也就是向量沿哪幾個方向各有一個數；本專案只用在 NED 的三軸與 `hnorm` 用的兩軸。
- NED：遙測的位置與速度用 NED 局部座標，N 是北、E 是東、D 是下（往下為正），單位公尺，原點是起飛點，也就是「家」。
  所以高度是 `-position_ned_m.d`（內建衍生量 `altitude_m`）。
- 判準：說「三維」數的是分量個數，不是單位。`position_ned_m` 與 `velocity_ned_mps` 各有北、東、下三個分量，
  `.n`、`.e`、`.d` 取其中一軸（見 `Component`）。
- `norm` 用三軸算向量的長度；`hnorm` 只用北、東兩軸，算水平長度。所以 `home_distance_m`（`hnorm(position_ned_m)`）
  是離家的水平距離：原地下降不會讓它變短。
- 不要混用：不用「維度」指單位（見「單位」）。英文 dimension 兩種意思都有，中文把它們分開。

### 布林（`bool`）

- 定義：只有真、假兩種值的型別。
- 判準：比較、`and`、`implies`、`held_for`、`within` 的結果是 `bool`；`if` 的條件、`and` 與 `implies` 的兩邊、
  `held_for` 與 `within` 的第一個引數必須是 `bool`；規則的樹根必須是 `bool`。
- 例子：`battery_percent >= battery_floor_percent` 是 `bool`。
- 不要混用：沒有單位的數是 `scalar[1]`，不是 `bool`。

### 純量（`scalar`）

- 定義：一個數，帶一個單位。
- 判準：只有一個數就是純量，不論單位：`scalar[%]`、`scalar[m]`、`scalar[1]` 都是純量。所有具名參數都是純量。
- 例子：`battery_percent` 是 `scalar[%]`，`home_distance_m` 是 `scalar[m]`。
- 不要混用：「純量」的「純」不表示沒有單位，這個名稱只是用來和「向量」對比。research 寫的「數值」分不出純量與向量
  （向量也由數組成），本檔不用。

### 向量（`vector`）

- 定義：北、東、下三個數一組，三個分量用同一個單位。
- 判準：有北、東、下三個數的就是向量。內建名稱裡的向量都是欄位：`position_ned_m`（`vector[m]`）與
  `velocity_ned_mps`（`vector[m/s]`）；算式也能算出向量，例如兩個位置相減。同單位的向量可以相加減，向量可以乘或除以純量、取負號；要比大小，先用 `.n`／`.e`／`.d`、`norm` 或 `hnorm` 變成純量。
  兩個向量不能相乘，也不能直接比較。
- 例子：`position_ned_m + velocity_ned_mps * lookahead_s`（`geofence-forecast`）：位置加上速度乘預警時距，
  得到預估的未來位置，仍是 `vector[m]`。
- 不要混用：「三維向量」的「三維」數的是分量（見「維度」），不是單位。

## 名稱的來源

規則裡的每個名稱（`Name` 節點），檢查器都會對到下面三種來源之一，對不到就是錯誤碼 `unknown_name`。
來源寫在語法樹圖方框的第四行。判準：

- 遙測每筆直接帶的：欄位（`field`）。
- 規則集宣告、只有單位沒有值的：具名參數（`parameter`）。
- 由一段算式從其他名稱算出來的：衍生量（`derived`）。

欄位、函式（`norm`、`hnorm`）與內建衍生量是內建的；具名參數由每個規則集各自宣告，不是內建的。

### 欄位（`field`）

- 定義：遙測每一筆直接帶的量。
- 判準：內建、唯讀，清單見下表，取自 M0 模擬器輸出的每一筆遙測；`vehicle_id` 不開放給規則用。
  規則集不能宣告新的欄位，也不能拿欄位的名稱宣告別的東西。
- 例子：`battery-floor` 的 `battery_percent`。
- 不要混用：contracts 的英文把節點的組成部分（例如 `Compare` 的 `left`、`right`）也叫 field；本檔講節點時稱「子節點」，
  不稱「欄位」。

| 名稱 | 型別 | 說法 |
|---|---|---|
| `sequence_number` | `scalar[1]` | 序號 |
| `mission_time_s` | `scalar[s]` | 任務時間 |
| `position_ned_m` | `vector[m]` | 位置 |
| `velocity_ned_mps` | `vector[m/s]` | 速度 |
| `battery_percent` | `scalar[%]` | 電量 |

### 具名參數（`parameter`）

- 定義：規則集自己宣告的一個名稱，只帶單位、不帶值；值由規則以外提供。
- 判準：寫在規則集的 `[parameters.<名稱>]`，只有 `unit` 一個鍵；型別是它單位的純量。
  M1 只檢查名稱與單位，不綁定數值（spec FR-009）；數值在 M2 綁定並檢查。
- 涵蓋：比 spec 的「具名門檻」寬。語料裡有門檻（`battery_low_percent`）、持續時間（`reaction_time_s`、`landing_deadline_s`）、
  視窗長度（`closing_window_s`、`drain_window_s`）、速率（`cruise_speed_mps`）。
- 例子：`battery-floor` 的 `battery_floor_percent`，單位 `%`。
- 不要混用：「具名門檻」（spec、research 的用詞，只說到門檻那一部分）。函式呼叫括號裡的值本檔稱「引數」，不稱「參數」；
  spec FR-010 的「參數個數」指的是引數個數。

### 衍生量（`derived`）

- 定義：一個有名稱的量，由一段算式從欄位、具名參數或其他衍生量算出來。
- 判準：有算式的才是衍生量。內建的見下表；規則集也可以在 `[derived.<名稱>]` 宣告自己的，寫 `unit` 與 `expression`。
  檢查器確認算式算出來的單位等於宣告的單位（否則 `derived_unit_mismatch`）；衍生量可以互相引用，但不能繞成一圈
  （`derived_cycle`）。
- 例子：語料自己宣告的 `return_time_s`（返航時間），算式是 `home_distance_m / cruise_speed_mps + altitude_m / descent_rate_mps`：
  離家水平距離除以巡航速度，加上高度除以下降速率。
- 不要混用：衍生量不是欄位。遙測不直接帶高度，高度是從位置算出來的。

| 名稱 | 單位 | 算式 | 說法 |
|---|---|---|---|
| `altitude_m` | `m` | `-position_ned_m.d` | 高度（相對起飛點） |
| `descent_speed_mps` | `m/s` | `velocity_ned_mps.d` | 下降速度（往下為正） |
| `horizontal_speed_mps` | `m/s` | `hnorm(velocity_ned_mps)` | 水平速度 |
| `home_distance_m` | `m` | `hnorm(position_ned_m)` | 離家水平距離（家是 NED 原點） |

## 語法樹的節點

每種節點一個詞條，順序照 `syntax.py` 的 `Node`。「寫法」是規則文字裡的樣子；「型別」照
`specs/002-rule-dsl-parser/contracts/ruleset.md` 的 Type and dimension rules，其中的 `D` 代表任一單位，
同一行裡的 `D` 指同一個單位。運算元（operand）是被運算的那個值。

### 數字常值（`Number`）

- 寫法：`0`、`1`、`0.5`。
- 定義：規則文字裡直接寫出來的數字。
- 型別：沒有單位的純量 `scalar[1]`；例外是 `0`，在 `+`、`-` 或比較的一邊時取另一邊的單位。
- 判準：時間保留字的時間長度（`ago`、`held_for`、`within`、`slope` 的第二個引數）不能只寫一個數字：
  大於 0 的數沒有單位，是 `dimension_mismatch`；0 或負數是 `nonpositive_duration`。時間長度要算得出 `s`，語料裡都是具名參數。
- 例子：`descent_speed_mps > 0`（`battery-tier-critical`，意思是「正在下降」）的 `0` 取 `m/s`；
  `prev(sequence_number) + 1`（`monotonic-sequence`）的 `1` 沒有單位。
- 不要混用：常值不是具名參數。常值的數寫死在規則裡；語料裡還要再決定的數都用具名參數（spec FR-009）。

### 名稱（`Name`）

- 寫法：`battery_percent`、`home_distance_m`。
- 定義：規則裡的一個名稱，由檢查器對到欄位、具名參數或衍生量（見「名稱的來源」）。
- 型別：它的來源的型別。
- 判準：對不到任何來源是 `unknown_name`。
- 例子：`battery-floor` 的兩個子節點都是 `Name`：`battery_percent`（來源 `field`）與 `battery_floor_percent`（來源 `parameter`）。
- 不要混用：函式名（`norm`、`hnorm`）與時間保留字（`prev`、`ago`、`held_for`、`within`、`slope`）不是 `Name`：
  函式名記在 `Call` 節點裡，時間保留字各自是一種節點。

### 分量（`Component`）

- 寫法：`x.n`、`x.e`、`x.d`。
- 定義：取向量在一軸上的那個數：北（`n`）、東（`e`）或下（`d`）。
- 型別：`vector[D]` 得到 `scalar[D]`。
- 例子：`velocity_ned_mps.d` 是往下的速度，也就是內建衍生量 `descent_speed_mps`。
- 不要混用：`.d` 是往下，不是高度。往下為正，所以高度 `altitude_m` 是 `-position_ned_m.d`。

### 負號（`Negate`）

- 寫法：`-x`。
- 定義：把一個純量或向量變號，單位不變。
- 型別：`scalar[D]` 得到 `scalar[D]`；`vector[D]` 得到 `vector[D]`。
- 例子：`-slope(battery_percent, drain_window_s)`（`battery-drain-rate`）：電量的變化率取負號，成為耗電率，電量在掉時是正數。
- 不要混用：同一個 `-`，只有一個運算元時是 `Negate`；夾在兩個運算元中間是 `Arithmetic` 的減法。

### 四則運算（`Arithmetic`）

- 寫法：`a + b`、`a - b`、`a * b`、`a / b`。
- 定義：兩個運算元的加減乘除。
- 型別：
  - `+`、`-`：兩邊都是純量或都是向量，單位相同，結果保留那個單位。
  - `*`：純量乘純量、向量乘純量、純量乘向量，單位相乘；兩個向量不能相乘。
  - `/`：純量除以純量、向量除以純量，單位相除。
- 判準：同一層連寫時從左邊先組，`a - b - c` 是 `(a - b) - c`。
- 例子：`return_time_s * drain_rate_percent_per_s + return_reserve_percent`（`return-reserve`）：`s` 乘 `%/s` 得 `%`，再加 `%`。
- 不要混用：只有一個運算元的 `-` 是負號，見 `Negate`。

### 比較（`Compare`）

- 寫法：`a < b`、`a <= b`、`a > b`、`a >= b`、`a == b`、`a != b`。
- 定義：比較兩個純量，得到真或假。
- 型別：兩個同單位的純量得到 `bool`；向量不能比較。
- 例子：`battery_percent >= battery_floor_percent`（`battery-floor`）。
- 不要混用：「門檻比較」是規則的類別（`threshold`），不是這種節點；每個類別的規則都可能用到比較。

### 且（`And`）

- 寫法：`a and b`。
- 定義：兩邊都成立才成立。
- 型別：兩個 `bool` 得到 `bool`。
- 判準：連寫時從左邊先組，`a and b and c` 是 `(a and b) and c`。
- 例子：`home_distance_m <= fence_radius_m and altitude_m <= fence_altitude_m`（`geofence-cylinder`）。
- 不要混用：「或」「非」（`or`、`not`）不在 M1 的文法裡，只先登記為保留字（不能拿來當名稱的字）。

### 蘊涵（`Implies`）

- 寫法：`A implies B`。
- 定義：不允許 A 成立而 B 不成立；A 不成立時整條算成立。
- 判準，三種情況：
  - A 真、B 真：真。
  - A 真、B 假：假，這是唯一算成假的情況。
  - A 假：真，不論 B。
- 型別：兩個 `bool` 得到 `bool`。連寫時從右邊先組，`a implies b implies c` 是 `a implies (b implies c)`。
- 邏輯上的名稱是實質蘊涵（material implication），等同「非 A 或 B」。
- 例子：`battery_percent < battery_low_percent implies home_distance_m <= low_battery_radius_m`（`low-battery-stay-close`）：
  電量低時，離家水平距離不得超過 `low_battery_radius_m`；電量不低時，這條不管距離，整條算成立。
- 不要混用：只寫「若 A 則 B」會誤導，因為它沒說 A 不成立時怎麼算。`Implies` 本身只算出真或假，
  「必須成立」是規則的性質，不是 `Implies` 的（見「規則」）。spec、research 寫作「蘊含」。

### 條件式（`Conditional`）

- 寫法：`if c then a else b`。
- 定義：`c` 成立時取 `a`，否則取 `b`。
- 型別：`c` 是 `bool`；`a`、`b` 的型別與單位相同，結果就是那個型別。
- 例子：`descent_speed_mps <= (if altitude_m < near_ground_altitude_m then near_ground_descent_max_mps else descent_max_mps)`
  （`descent-speed-near-ground`）：近地時用較嚴的下降速度上限，其餘高度用一般的上限。
- 不要混用：和 `Implies` 不同。條件式從兩個值挑一個，結果可以是純量；`implies` 的兩邊與結果都是 `bool`。research 稱它「條件值」。

### 函式呼叫（`Call`）

- 寫法：`norm(x)`、`hnorm(x)`。
- 定義：把括號裡的值（引數）交給一個內建函式計算。
- 型別：M1 只有兩個函式，都是 `vector[D]` 得到 `scalar[D]`：
  - `norm`：用北、東、下三軸算向量的長度。
  - `hnorm`：只用北、東兩軸，算水平長度 `sqrt(n^2 + e^2)`。
- 判準：引數個數不對是 `arity_mismatch`；函式名不存在是 `unknown_name`。
- 例子：`norm(position_ned_m - prev(position_ned_m))`（`no-sudden-jump`）：相鄰兩筆位置之間的距離。
- 不要混用：括號裡的值稱「引數」，不稱「參數」（「具名參數」另有所指）。時間保留字（`prev`、`ago` 等）寫法像函式呼叫，
  但各自是一種節點，不是 `Call`。

### 前一筆（`Previous`）

- 寫法：`prev(x)`。
- 定義：同一個量在前一筆事件（一筆遙測）時的值。
- 型別：和 `x` 相同。
- 判準：數的是事件，不是秒；前一筆離現在多久，要看兩筆之間隔了多少時間。
- 例子：`mission_time_s - prev(mission_time_s) <= heartbeat_max_s`（`telemetry-heartbeat`）：相鄰兩筆的時間差不得超過上限。
- 待定：第一筆事件沒有前一筆，這時怎麼算由 M2 定義。
- 不要混用：`ago(x, d)` 往回數的是秒，見 `Ago`。

### N 秒前（`Ago`）

- 寫法：`ago(x, d)`。
- 定義：同一個量在 `d` 秒前的值。
- 型別：和 `x` 相同；`d` 必須是 `scalar[s]`。
- 例子：`home_distance_m < ago(home_distance_m, closing_window_s)`（`battery-tier-low`）：離家距離比 `closing_window_s` 秒前短，
  也就是正在縮短。
- 待定：精確算法（例如資料還不到 `d` 秒時）由 M2／M3 定義。
- 不要混用：`prev(x)` 往回數的是事件，見 `Previous`。

### 持續成立（`HeldFor`）

- 寫法：`held_for(c, d)`。
- 定義：條件 `c` 已經持續成立 `d` 秒。
- 型別：`c` 是 `bool`，`d` 是 `scalar[s]`，結果是 `bool`。
- 例子：`held_for(battery_percent < battery_low_percent, reaction_time_s)`（`battery-tier-low`）：電量低於門檻持續 `reaction_time_s` 秒。
- 待定：是不是「至少」`d` 秒、中途短暫不成立算不算重新計時，由 M2／M3 定義。
- 不要混用：「持續成立」和「N 秒內成立」（`Within`）是不同形狀；後者要到期限才知道有沒有違規
  （`specs/002-rule-dsl-parser/rule-corpus.md` 的 `battery-tier-emergency`）。

### N 秒內成立（`Within`）

- 寫法：`within(c, d)`。
- 定義：條件 `c` 在 `d` 秒的期限內成立。
- 型別：`c` 是 `bool`，`d` 是 `scalar[s]`，結果是 `bool`。
- 例子：`battery_percent < battery_emergency_percent implies within(altitude_m < landed_altitude_m, landing_deadline_s)`
  （`battery-tier-emergency`）：電量一跌破緊急門檻，必須在 `landing_deadline_s` 秒內落地（高度低於 `landed_altitude_m`）。
- 待定：從哪一刻起算、什麼時候判定，由 M2／M3 定義。
- 不要混用：見 `HeldFor`。

### 視窗斜率（`Slope`）

- 寫法：`slope(x, w)`。
- 定義：`x` 在最近 `w` 秒的視窗（最近一段固定長度的資料）裡的平均變化率。
- 型別：`x` 是 `scalar[D]`，`w` 是 `scalar[s]`，結果是 `scalar[D/s]`；例如 `%` 的斜率是 `%/s`。
- 例子：`-slope(battery_percent, drain_window_s) <= drain_rate_max_percent_per_s`（`battery-drain-rate`）：最近一段時間的平均耗電率不得超過上限。
- 待定：平均變化率怎麼算（取視窗兩端的差，或對視窗裡每一筆做迴歸，也就是找一條最貼近這些點的直線、取它的斜率），
  以及視窗還沒填滿時怎麼算，由 M3（GAR-20）定義。
- 不要混用：斜率只由 `x` 過去的值算出，不讀速度欄位；`slope(altitude_m, w)` 和 `descent_speed_mps` 不是同一個量。

### 時間位移（待定分類）

- 定義（暫定）：取同一個量在較早時間點的值。`Ago` 往回數秒，`Previous` 往回數事件。
- 類比：SQL（資料庫查詢語言）的 `LAG()`、pandas（Python 的資料表套件）的 `shift()`，都是取同一欄較早的值。
- `Slope` 歸不歸入：若 M3 把 `slope(x, w)` 定義成視窗兩端的差除以視窗長度，它就等於 `(x - ago(x, w)) / w`，可以歸入；
  若定義成迴歸，就不是。
- 待定：這個分類由 user 提出，尚未定案；`Slope` 的歸屬等 M3 定義 `slope` 的算法後再決定。
