<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.0.1
Bump rationale: PATCH — fill the existing M0 latency-ladder obligation with the
accepted E2/E3 derivation; no principle or performance Gate is added or relaxed.

Modified principles:
  - II. 尾延遲優先: replace TODO with the derived provisional ladder and its source.
Added sections: none.
Removed sections: none.

Template synchronization:
  - updated .specify/templates/plan-template.md — version and ladder references.
  - checked .specify/templates/spec-template.md — no changed requirement to propagate.
  - checked .specify/templates/tasks-template.md — no changed task category to propagate.
  - .specify/templates/commands/ is absent; repo-local skills contain no ladder TODO.
Runtime guidance:
  - updated specs/001-telemetry-simulator/plan.md and tasks.md.
Follow-up TODOs: none for this amendment; measured latency Gates remain future E1 work.
-->

# Stream Assertion Engine Constitution

本專案為**能力建構導向**（非求職導向）：以無人機領域的職缺描述作為能力規格。
本專案為該 JD 所涵蓋的三個專案之一（另兩個為 `mapf-router`、`slot-allocator`），
各專案獨立開設 GitHub repo。

學習路徑為**從實作反推理論**：先做出可運作的系統，再回頭理解背後的理論。

**本專案是三個專案中唯一真正的即時系統，也是「對抗式思維」最直接的載體。**
`kickoff.md` 明訂它是「獨立於主調度系統之外的守門人」——這個獨立性不是實作細節，
是它存在的理由。原則順序依此排定。

## Core Principles

### I. 對抗式驗證 (Adversarial Validation) — NON-NEGOTIABLE

Fuzzer MUST 獨立於 Rule Evaluator 之外實作：

- Fuzzer MUST 置於獨立模組（`src/fuzzer/`），
  **MUST NOT 共用 DSL 語法樹、規則語意或評估邏輯的任何程式碼**
- 「這筆注入應該被偵測到」的**期望結果 MUST 由 Fuzzer 端獨立決定**，
  MUST NOT 透過呼叫 Evaluator 取得。若兩者共用判斷依據，
  它們會一起錯而互相背書，偵測率報告即失去意義
- 引擎本身作為主調度系統的守門人，同理 MUST NOT 依賴被監控系統的自我回報
- CI MUST 以相依性檢查強制上述隔離

**理由**：本專案的產出是「偵測率與誤報率」這組數字。若量測工具與被量測對象
共享語意，這組數字衡量的只是自我一致性，而非真實防禦能力。

### II. 尾延遲優先 (Tail Latency First)

效能 MUST 以尾延遲表述，MUST NOT 以平均吞吐宣稱達標：

- 「每秒可處理 N 事件」在即時系統中是**誤導性指標**，MUST NOT 單獨作為驗收依據
- 效能報告 MUST 含 p50 / p95 / p99 / **max** 四個數值；max 尤其關鍵
- 若採用具垃圾回收的執行環境，報告 MUST 含 GC 暫停時間分佈；
  暫停期間錯過的事件 MUST 計入偵測率
- 效能 MUST 以「階數 + 場景」表述，場景須指明遙測發布頻率與規則數量

M0 的基準為 2 m/s 巡航與 0.2 m 觀測間距，發布頻率為 `2 / 0.2 = 10 Hz`。
依 `事件間隔 = 1 / 發布頻率` 反推下列階梯；規則數 10 是未來最小語料庫，
M0 尚未實作 Evaluator 或量測其延遲。

| 階數 | 發布頻率 | 未來規則數 | 觀測間距 | 事件間隔／未來 max budget | 證據 |
|---|---:|---:|---:|---:|---|
| L0 | 10 Hz | 10 | 0.20 m | 100 ms | E2 算術 |
| L1 | 20 Hz | 10 | 0.10 m | 50 ms | E2 算術 + E3 階數選擇 |
| L2 | 50 Hz | 10 | 0.04 m | 20 ms | E2 算術 + E3 階數選擇 |
| L3 | 100 Hz | 10 | 0.02 m | 10 ms | E2 算術 + E3 階數選擇 |

完整推導與後續量測欄位見
[`research.md` 的 provisional latency ladder](../../specs/001-telemetry-simulator/research.md#provisional-latency-ladder-not-a-gate)。
這些數值是處理預算，不是已達成的效能。任何階數升為效能 Gate MUST 由 E1
建立；在實測前，達成階數與引擎延遲宣稱仍屬未定錨。

**理由**：一次 GC 暫停就可能錯過告警窗口，而平均值會把它完全稀釋掉。
守門人偶爾失效，等於沒有守門人。

### III. 語法由真實規則反推 (Grammar Follows Corpus)

DSL 語法是本專案**最難反悔的決定**——Evaluator、視窗語意、Fuzzer 全部建於其上：

- 語法設計前 MUST 先寫出一組**真實想表達的規則語料庫**（不少於 10 條），
  涵蓋門檻比較、邏輯組合、時序約束、趨勢外推
- 語法 MUST 由該語料庫反推需求，MUST NOT 先設計語法再回頭找例子套用
- 語料庫 MUST 納入版控並作為 parser 的回歸測試集
- 語法的破壞性變更 MUST 提供既有規則的遷移路徑

**理由**：先設計語法再找例子，會得到一個優雅但表達不了真實需求的語言；
而等到 M3、M4 才發現時，重做的成本已經涵蓋整個專案。

### IV. 文獻可追溯且可理解 (Traceable AND Comprehensible)

每個演算法模組 MUST 標註文獻或教材來源，**且 MUST 附帶白話橋接說明**：

- MUST 記錄出處與對應章節（解析理論、串流視窗語意尤其適用）
- MUST 附白話說明：這個機制在解決什麼問題、關鍵直覺、
  理論術語與本專案資料結構的對應關係
- 白話說明 MUST 足以讓未讀過該文獻的人理解實作在做什麼；
  「請參閱原文」MUST NOT 作為說明
- 若採手寫 Recursive Descent Parser，其與形式文法（如 EBNF）的對應 MUST 明確記錄——
  手寫解析器最常見的問題就是語法只存在於程式碼裡、沒有人說得清它到底接受什麼

**理由**：本專案採「從實作反推理論」的學習路徑，不預設實作者具備直接閱讀論文的能力。
只有引用而無橋接的追溯，對學習者等於沒有追溯。

### V. 情境與注入可重現 (Reproducible Scenarios)

- Telemetry Simulator 與 Fuzzer MUST 接受顯式亂數種子
- 偵測率／誤報率報告 MUST 記錄：情境集合版本、規則集版本、種子、
  commit SHA、硬體
- 任何被 Fuzzer 找到的漏檢 MUST 可原樣重播，並納入回歸情境集
- 缺乏上述來源資訊的數據 MUST NOT 出現在報告或 README 中

**理由**：偵測率是本專案的核心宣稱，不可重現的偵測率無法比較，也就無法改進。

### VI. 證據等級制 (Evidence Tiers)

所有效能與偵測能力宣稱 MUST 標註證據等級：**E1 實測**／**E2 推論**／**E3 判斷**。
任何 Gate 判定 MUST 僅接受 E1。技術決策文件中若關鍵準則僅有 E3，MUST 標記為暫定。

**理由**：推論一旦未標註，會隨時間被當作既成事實累積。

## 技術棧與待決策事項

`kickoff.md` 留下兩個分岔，MUST 於 M0 的 SDD plan 階段定案並留下決策記錄：

- **技術棧**：Python（原型 + DSL 解析）vs. C++（效能關鍵路徑）
- **解析器策略**：手寫 Recursive Descent Parser vs. Lark / ANTLR 生成
  → 依本專案的能力建構定位，手寫的學習價值顯著較高；
    但此權衡 MUST 於 plan 階段明確記錄，MUST NOT 預設

⚠️ **`mapf-router` 的 spike 設計 MUST NOT 沿用。** 該 spike 量測平均吞吐
（每次節點展開成本），對本專案而言是錯誤的儀器——這裡決定成敗的是尾延遲與
暫停時間分佈。若需 spike，MUST 重新設計為量測 p99 / max 與 GC 暫停。

## 開發流程與品質門檻

- 每個 feature MUST 走 SDD 流程：specify → clarify → plan → tasks → implement
- Parser 與 Evaluator 核心 MUST 測試先行；測試 MUST 先失敗再實作
- **驗收輸出 SHOULD 包含視覺化佐證**（語法樹結構、規則在資料流上的觸發時點、
  滑動視窗內的趨勢線與門檻）。視覺化是理解引擎行為最直接的管道，
  屬學習基礎設施而非 M5 才處理的裝飾
- 理論教學環節與實作交付**刻意解耦**：教學產出不列入 feature 驗收標準，
  亦 MUST NOT 因實作進度而被省略
- 重大技術決策 MUST 於 `docs/decisions/` 留下決策記錄，含重新評估的觸發條件

## Governance

本憲章的效力高於其他開發慣例。衝突時以本憲章為準，或先修訂憲章再行動。

**修訂程序**：MUST 以文件形式提出，載明變更內容、理由與對既有產出的影響，
並更新本檔的 Sync Impact Report 與版本號。

**版本政策**（語意化版本）：MAJOR 移除或不相容地重定義原則；
MINOR 新增原則或章節、實質擴充指引；PATCH 措辭釐清。

**合規審查**：每個 feature 的 plan 階段 MUST 執行 Constitution Check。
違反原則的設計 MUST 記錄理由或改採合規做法。複雜度 MUST 有正當理由——
「之後可能會用到」不構成理由。

**Version**: 1.0.1 | **Ratified**: 2026-07-20 | **Last Amended**: 2026-10-01
