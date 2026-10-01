# Feature Specification: M0 專案骨架與遙測模擬器

**Feature Branch**: `001-telemetry-simulator`
**Created**: 2026-09-29
**Status**: Draft
**Input**: User description: "GAR-17 — 建立專案骨架、CI 與可產生基本正常軌跡的 Telemetry Simulator；以 `docs/decisions/001-m0-simulator-boundaries.md` 為已接受邊界。"

## Clarifications

### Session 2026-09-29

- Q: Playback 的最小視覺介面包含哪些視圖？ → A: 2D N/E 路徑圖，加同步的高度、速度與電量時間圖。
- Q: 相同情境版本、設定與種子重跑時，可重現性用什麼尺度判定？ → A: Event artifact 與 ground truth 必須各自 byte-for-byte 相同。
- Q: 快照剛好落在情境階段切換時點時，ground truth 歸入哪個階段？ → A: 階段採 `[start, end)`；邊界快照屬於新階段，任務終點快照納入最後階段。

### Session 2026-10-01

- Q: 任務終點未落在取樣格上時如何處理？ → A: 拒絕設定；內部階段切換仍可不對齊取樣格。終點對齊檢查使用未量化的任務總時長與取樣率，不能因輸出時間四捨五入而接受未對齊設定。
- Q: Generate 的明示 output parent 不存在時如何處理？ → A: 設定與待發布成品驗證成功後，自動建立所需 parent directories；無效 arguments／設定不建立目錄，既有 final target 不覆寫。
- Q: GitHub 尚無 CI gating，M0 的 T030 是否包含 merge gating？ → A: 包含；workflow 實際 PASS 後，以真實 check 名稱設定 required status checks，讓 main 的 merge 受其結果約束。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 產生可重現的正常任務 (Priority: P1)

作為引擎開發者，我能以明確的情境設定與亂數種子產生一份單機正常飛行的完整遙測事件成品，讓後續 ingestion、規則評估與 fuzzer 都有同一份可重播的基準輸入。

**Why this priority**: 沒有穩定且可追溯的輸入，後續元件無法判斷行為差異來自規則、注入，還是模擬資料本身。

**Independent Test**: 使用基準設定與固定種子產生 event artifact 與 ground truth，驗證正常任務完整走過起飛、懸停、向北飛行、返航與降落，且重跑後兩份輸出各自維持相同 hash。

**Acceptance Scenarios**:

1. **Given** 基準正常情境與固定種子，**When** 使用者產生遙測，**Then** 系統輸出一份不可變的有序事件成品，涵蓋起飛、懸停、向北飛行、返航與降落。
2. **Given** 完全相同的情境版本、設定與種子，**When** 使用者重跑產生流程，**Then** 兩次產生的 event artifact 與 ground truth 各自 byte-for-byte 相同。
3. **Given** 基準情境，**When** 使用者檢查任一遙測快照，**Then** 快照含完整事件契約，且不含情境階段或其他預期答案。
4. **Given** 有效設定與明示的巢狀 output path，其 parent 尚不存在，**When** 使用者產生遙測，**Then** 系統先完成驗證，再建立 parent directories 並發布兩份完整成品。

---

### User Story 2 - 以 rendered playback 檢查軌跡 (Priority: P2)

作為規格審查者，我能打開已完成的事件成品，以 rendered playback（把完成事件繪成可操作畫面）觀察飛行路徑、任務時間與關鍵狀態，並對照獨立保存的情境 ground truth（由情境設定提供的正確階段時間線），確認資料確實表達預期的正常任務。

**Why this priority**: 視覺證據讓人能直接看出階段順序、返航與降落是否合理，而不必只相信測試通過或逐行閱讀事件。

**Independent Test**: 載入一份既有事件成品，在不重新產生資料的前提下播放、暫停、逐步前進、改變播放速度與重新開始，確認顯示值始終對應原始事件的 `mission_time_s`。

**Acceptance Scenarios**:

1. **Given** 已完成的事件成品與分離的 ground truth，**When** 使用者開啟 playback，**Then** 畫面呈現 2D N/E 路徑、同步的高度／速度／電量時間圖，以及目前任務時間與階段。
2. **Given** playback 正在播放，**When** 使用者暫停、單步前進或改變播放速度，**Then** 顯示順序仍與事件成品一致，且不改寫任何事件的 `mission_time_s`。
3. **Given** 相同的事件成品，**When** 使用者重新開始 playback，**Then** 畫面回到第一筆事件，不重新計算運動或電量。

---

### User Story 3 - 以自動化門檻安全延伸專案 (Priority: P3)

作為貢獻者，我能從乾淨 checkout 找到 Simulator、DSL、Evaluator、Fuzzer、情境與測試的責任邊界，並在每次變更時得到自動化變更門檻（change gate）的驗證結果，避免後續里程碑破壞 M0 的事件契約與可重現性。

**Why this priority**: M0 的骨架與 change gate 是後續 M1–M4 能獨立發展又不互相背書的基礎。

**Independent Test**: 從乾淨 checkout 執行文件化的驗證入口，確認基準版本通過；再以隔離的測試變體製造一個契約違規，確認 gate 會失敗且指出違反的要求。

**Acceptance Scenarios**:

1. **Given** 乾淨 checkout，**When** 貢獻者查看專案結構，**Then** 能分辨 Simulator、DSL、Evaluator、Fuzzer、情境與測試的責任邊界，且 M0 只有 Simulator 與 playback 具備業務行為。
2. **Given** 符合規格的基準版本，**When** 自動化驗證執行，**Then** 所有 M0 驗收項目通過。
3. **Given** 一個故意破壞事件契約或可重現性的隔離變體，**When** 同一套自動化驗證執行，**Then** gate 失敗並指出相對應的規格要求。
4. **Given** CI workflow 已實際執行且 check 名稱已確認，**When** required status checks 已設定為 main 的生效合併規則，**Then** 缺少或失敗的必要檢查會阻擋 merge，成功的檢查可作為合併依據。

### Edge Cases

- 情境設定缺少必要值、取樣頻率不大於零、初始電量超出 0–100%，或耗電率為負值時，產生流程必須在寫出事件成品前拒絕該設定並指出原因。
- 任務終點未落在設定決定的取樣格上時，產生流程必須拒絕設定並指出終點對齊問題；檢查須在輸出時間量化與任何 output directory 建立之前完成。內部階段切換可不對齊取樣格。
- 明示 output parent 不存在時，產生流程在設定與成品驗證成功後建立所需目錄；既有 final target 必須保留並拒絕覆寫。Parent 建立或成品發布失敗時，必須指出路徑且不得發布 partial artifact 目錄。
- 階段切換落在取樣邊界時，ground truth MUST 以 `[start, end)` 將該快照歸入新階段；任務終點的降落快照納入最後階段。`sequence_number` 與 `mission_time_s` 仍必須各自保持連續且嚴格遞增，不得重複或遺漏快照。
- 設定會讓電量在任務結束前低於 0% 時，產生流程必須拒絕該正常情境；事件成品不得含超出 0–100% 的電量。
- playback 收到缺欄位、順序錯誤或無法配對 ground truth 的成品時，必須清楚拒絕播放，不得自行補值、平滑、插值或重新產生事件。
- 暫停、單步、倍速與重新開始只能改變觀看方式；任何控制都不得修改事件成品或其任務時間。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 接受一份明確的正常情境設定與亂數種子，並在產生前驗證所有必要值、有效範圍與任務終點對齊取樣格；未對齊時 MUST 在任何 output directory 建立前拒絕設定。
- **FR-002**: 基準情境 MUST 依序包含起飛、懸停、向北飛行、返航與降落，並在起飛原點結束。
- **FR-003**: 基準情境 MUST 使用 2 m/s 的巡航速度與 0.2 m 的目標觀測間距，形成 10 Hz 的初始取樣基線；取樣率 MUST 可由情境設定調整。
- **FR-004**: 每筆遙測快照 MUST 是單一載具在該任務時間的完整上游狀態估計（state-level snapshot），且只包含 `vehicle_id`、`sequence_number`、`mission_time_s`、`position_ned_m`、`velocity_ned_mps` 與 `battery_percent`。
- **FR-005**: `vehicle_id` MUST 存在於每筆快照；M0 每份事件成品 MUST 只包含一個載具。
- **FR-006**: 第一筆快照 MUST 使用 `sequence_number = 0` 與 `mission_time_s = 0`；後續序號 MUST 逐筆加一，任務時間 MUST 依設定的取樣率嚴格遞增，並以完整取樣間隔抵達已對齊的任務終點。
- **FR-007**: `position_ned_m` 與 `velocity_ned_mps` MUST 使用以起飛點為原點的 local NED（North-East-Down，北、東、下）；載具位於起飛點上方時 `down` MUST 為負值。
- **FR-008**: 系統 MUST 從速度向量推導純量速率，不得在遙測快照中另存重複的純量速率欄位。
- **FR-009**: 電量 MUST 由可設定的初始百分比與每秒線性綜合耗電率決定，所有輸出 MUST 保持在 0–100% 之間。
- **FR-010**: 情境階段 MUST 作為獨立 ground truth 保存，且 MUST NOT 出現在遙測快照中。階段 MUST 使用 `[start, end)`；切換時點的快照屬於新階段，任務終點快照納入最後階段。
- **FR-011**: 相同的情境版本、設定與種子 MUST 產生各自 byte-for-byte 相同的 event artifact 與 ground truth；兩份輸出 MUST 帶有足以重現其來源的情境版本、設定與種子資訊。
- **FR-012**: Simulator MUST 產生 upstream state estimate，不得宣稱或模擬 raw GPS、IMU、電壓、電流、sensor fusion、雜訊或 estimator fidelity。
- **FR-013**: playback MUST 只讀取已完成的事件成品與分離的 ground truth，不得重新計算、平滑、插值或替換運動、電量與觀測時間。
- **FR-014**: playback MUST 提供播放、暫停、單步前進、重新開始與可調播放速度，並呈現 2D N/E 路徑、同步的高度／速度／電量時間圖，以及目前階段與任務時間。
- **FR-015**: playback controls MUST NOT 改變事件順序、事件內容或 `mission_time_s`。
- **FR-016**: 專案骨架 MUST 為 Simulator、DSL、Evaluator、Fuzzer、情境與測試保留清楚且互不混淆的責任邊界；M0 MUST NOT 實作 DSL、Evaluator 或 Fuzzer 行為。
- **FR-017**: 每次 proposed change MUST 執行同一套自動化驗證，涵蓋事件契約、正常情境、可重現性、ground-truth 分離與 playback 唯讀邊界。M0 MUST 在 workflow 實際 PASS 後以真實 check 名稱設定 main 的 required status checks；缺少或失敗的必要檢查 MUST 阻擋 merge。
- **FR-018**: 自動化 gate MUST 在符合規格時通過，並在隔離驗證中遇到已知契約違規時失敗且指出對應要求。

### Scope Boundaries

本 feature 不包含 DSL 語法或 parser、rule evaluation、sliding-window analysis、alert、stream ingestion、fuzzer 注入、多載具協調、sensor/estimator failure、即時硬體連接、真實感測器資料擷取或載具通訊協定。技術棧、parser 策略、事件檔案格式與專案內部架構由 plan 階段決定；不得在 specification 階段預設。

### Key Entities

- **Scenario Configuration**: 正常任務的輸入邊界，包含情境版本、亂數種子、運動、取樣與電量參數。
- **Telemetry Snapshot**: 單一載具在一個任務時間點的完整 state-level 觀測，遵守 FR-004 的事件契約。
- **Event Artifact**: 一次產生流程輸出的不可變、有序快照集合，帶有重現來源所需的情境資訊。
- **Scenario Ground Truth**: 與遙測分離的階段時間線，以 `[start, end)` 表達階段區間並將任務終點納入最後階段；供驗證與視覺標註使用，不提供給未來 Assertion Engine 判斷規則。
- **Playback Session**: 對既有 Event Artifact 的唯讀觀看狀態；控制只影響觀看進度，不影響任務時間或事件內容。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 相同的情境版本、設定與種子連續產生 3 次時，3 份 event artifact 的 hash 完全相同，3 份 ground truth 的 hash 也完全相同。
- **SC-002**: 基準情境的 100% 快照都含且只含 6 個事件契約欄位，序號無缺口，任務時間嚴格遞增，且 0 筆快照含情境階段標籤。
- **SC-003**: 基準情境按 10 Hz 產生事件，從起飛原點出發，依序完成 5 個階段，最後回到原點、完成降落且速度為零。
- **SC-004**: 對基準成品執行播放、暫停、單步、倍速與重新開始後，使用者看到的事件順序與 `mission_time_s` 和原始成品 100% 一致。
- **SC-005**: 不閱讀原始事件檔逐行資料時，審查者仍能從 2D N/E 路徑與同步的高度／速度／電量時間圖正確辨識 5 個任務階段的順序，並在任一畫面讀出目前任務時間與階段。
- **SC-006**: 乾淨 checkout 的自動化 gate 全部通過；對事件契約或可重現性各注入至少 1 個已知違規時，同一 gate 會失敗並指出相對應要求。

## Assumptions

- 主要使用者是本專案的開發者與規格審查者；M0 playback 是本地學習與驗證介面，不是 production dashboard。
- 正常情境的各階段持續時間、目標高度與北向距離由情境設定提供；基準值在 plan 階段選定，但不得改變本規格定義的階段順序與 10 Hz 推導方式。
- explicit seed 是重現契約的一部分；即使基準正常情境目前不使用隨機擾動，產生流程仍接受並記錄它。
- scalar speed 可在 playback 或驗證時由 `velocity_ned_mps` 推導，但不成為事件欄位。
- offline real-flight logs、PX4 SITL 與 hardware evidence 屬後續驗證階梯，不是 M0 驗收依賴。
- 技術棧與 parser 策略依 GAR-17 留到 plan 階段，以能力成長、完成風險與 assertion-engine 自身的 tail latency（最慢那批事件的處理延遲）證據評分；不得沿用其他無人機專案的數值。
- 本規格依賴已接受的 `docs/decisions/001-m0-simulator-boundaries.md` 與專案 constitution；兩者若修訂，本規格需重新核對其事件與證據邊界。
