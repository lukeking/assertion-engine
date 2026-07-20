# 專案三：基於規則語法樹的即時遙測斷言引擎 (Stream-based Assertion Engine)

## 專案目標
建立一套獨立於主調度系統之外的「守門人」引擎：訂閱載具遙測資料流（位置、電量、速度），即時評估自訂 DSL 定義的系統不變量（invariants），並透過 Fuzzer 主動注入異常來驗證其防禦邊界——即 JD 中所強調的「對抗式」除錯邏輯。

## 問題定義
給定持續產生的遙測事件流，設計一個能以低延遲解析規則、評估不變量、並在違規時即時告警的引擎；同時具備滑動視窗式的趨勢預測能力（例如電量下降速率是否會導致無法返航）。

## 驗證方式（無需硬體）
- 遙測資料完全由自寫的 Telemetry Simulator 產生（可設定正常軌跡、邊界情境、異常情境）。
- Fuzzer 對模擬資料流做隨機/結構化的異常注入（突波、資料遺失、時序錯亂），驗證引擎是否能正確捕捉。
- 驗收指標（偵測率、誤報率、延遲）皆可由自動化測試量測，不需接觸真實感測器或飛控系統。

## 技術棧
- 主要：Python（原型 + DSL 解析）或 C++（效能關鍵路徑）
- 解析器：手寫 Recursive Descent Parser 或使用 Lark / ANTLR 生成 Parser Tree
- 資料流：內建 queue 或輕量 pub/sub（如 ZeroMQ）模擬真實 streaming

## 系統架構
```
┌───────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Telemetry           │ --> │ Stream Ingestion   │ --> │ Rule Evaluator       │
│ Simulator            │     │ Layer               │     │ (Parser Tree)        │
└───────────────────┘     └──────────────────┘     └────────────────────┘
                                                              │
                                                              v
                                                     ┌────────────────────┐
                                                     │ Sliding Window        │
                                                     │ Trend Analyzer         │
                                                     └────────────────────┘
                                                              │
                                                              v
                                                     ┌────────────────────┐
                                                     │ Alert / Violation Log  │
                                                     └────────────────────┘
                                                              ^
                                                              │
                                                     ┌────────────────────┐
                                                     │ Fuzzer (異常注入)      │
                                                     └────────────────────┘
```

### 核心元件
1. **Telemetry Simulator**：產生模擬載具狀態流（位置、電量、速度、時間戳），可配置正常/邊界/異常模式。
2. **自訂 DSL**：定義不變量規則的語法（例如 `assert battery_level > min_return_threshold(distance_to_base)`）。
3. **Parser Tree**：將 DSL 規則解析為可執行的語法樹，支援巢狀邏輯與自訂函式。
4. **Rule Evaluator**：對每個遙測事件即時執行語法樹判斷是否違反不變量。
5. **Sliding Window Trend Analyzer**：維護時間窗內的歷史資料，做趨勢外推（例如電量下降速率預測）。
6. **Fuzzer**：獨立於主流程之外，隨機/結構化地產生異常雜訊（突波、遺漏、時序錯亂）注入資料流，驗證引擎防禦邊界，並記錄偵測率與誤報率。

## 開發里程碑
| 里程碑 | 內容 | 驗收標準 |
|---|---|---|
| M0 | 專案骨架、CI、Telemetry Simulator 雛形 | 可產生基本正常軌跡資料流 |
| M1 | DSL 語法設計 + Parser Tree | 可解析基本規則（比較、邏輯運算）為語法樹 |
| M2 | Rule Evaluator + 基礎不變量檢查 | 對模擬資料流即時評估規則並輸出違規事件 |
| M3 | Sliding Window 趨勢預測 | 能對電量/速度等連續指標做窗口內趨勢分析與預警 |
| M4 | Fuzzer 異常注入框架 | 定量報告：注入 N 種異常情境下的偵測率與誤報率 |
| M5 | Dashboard + README + Demo | 提供可重現的模擬情境腳本與偵測結果報告 |

## 非目標（Non-goals）
- 不涉及真實感測器資料擷取或載具通訊硬體協定。
- 不負責路徑重新規劃本身（該職責屬於專案一的 Router），本引擎僅做獨立驗證/告警。

## Repo 結構建議
```
assertion-engine/
├── README.md
├── src/
│   ├── simulator/        # Telemetry Simulator
│   ├── dsl/                # DSL 語法 + Parser Tree
│   ├── evaluator/           # Rule Evaluator + Sliding Window
│   └── fuzzer/               # 異常注入工具
├── scenarios/                 # 預設正常/邊界/異常情境定義
└── tests/
```
