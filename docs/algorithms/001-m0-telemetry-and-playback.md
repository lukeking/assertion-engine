# M0 遙測與 playback：來源、直覺與實作對應

本文件承接憲章原則 IV。它是已接受設計的實作說明，並非已完成程式或實測證據。
各演算法模組 MUST 引用下表對應章節，並留下資料結構對應；T035 核對引用與實作一致。
理論教學仍與 feature 驗收解耦。

| 實作模組 | 對應章節 | 驗證任務 |
|---|---|---|
| `simulator/config.py`、`artifacts.py` | §1 精確取樣格與輸出量化 | T004、T005、T008 |
| `simulator/scenario.py` | §1 取樣格、§2 分段正常運動 | T009、T010 |
| `playback/view_model.py` | §3 唯讀狀態與速度 | T018、T020 |
| `playback/matplotlib_view.py` | §4 畫面與觀看時鐘 | T019、T026 |

## 1. 精確取樣格與輸出量化

來源：[CPython 3.14 `fractions` 文件的 Fraction constructor 與 rounding 說明](https://github.com/python/cpython/blob/3.14/Doc/library/fractions.rst)、
[Python `decimal` 的 quantize 與 ROUND_HALF_EVEN](https://docs.python.org/3.14/library/decimal.html#decimal.Decimal.quantize)、
[Python `json` 的 parse_float 與 encoder parameters](https://docs.python.org/3.14/library/json.html)。
有理數保存分子／分母；十進位量化提供固定精度；JSON 的數值解析與編碼是另一個邊界。

白話直覺：尺上的每一格都從原點量，不能把上一格的四捨五入誤差帶到下一格。
先從 normalized source 參數計算 `r = cruise_speed_mps / observation_spacing_m`，
再保留 `Δt = 1/r` 的有理值；`sequence_number = k` 對應 `t_k = k × Δt`。
保存前才套用 data-model.md 的 `Q`，所以 3 Hz 的前幾筆是
`0、0.333333、0.666667、1`，不是反覆加上 `0.333333`。

`artifacts.py` 的 semantic validator 從 source 的非衍生參數重建取樣格，
比對 `Q(k × Δt)`、衍生 metadata 與嚴格遞增；serializer 處理 sorted keys、
compact separators、有限數值與單一 LF。這些是本專案的契約選擇，
不是 Python 函式庫自動保證的 artifact 規格。

## 2. 分段正常運動

來源：[OpenStax《University Physics Volume 1》§3.4，式 3.13](https://openstax.org/books/university-physics-volume-1/pages/3-4-motion-with-constant-acceleration)。
在一段內取加速度為零，位置式簡化為 `p(t) = p_start + v × (t - start)`。

白話直覺：每個階段是一段固定方向與速度的路徑，直接詢問某個 tick 在該段的位置，
而不是每次把上個位置再推進一步。對 N/E/D 三軸各自套用此式：
起飛時 D 速度為負，北向飛行時 N 速度為正，返航為負，降落時 D 速度為正。
`position_ned_m` 與 `velocity_ned_mps` 保存這些三軸值；終點回原點並將速度設為零。

五段順序、`[start,end)` 與終點歸入 landing 來自
[feature 的 FR-002／FR-010](../../specs/001-telemetry-simulator/spec.md#functional-requirements)。
`battery_percent = initial_battery_percent - drain × t_k` 是 FR-009 接受的線性模型，
不是教材提供的電池物理模型。`scenario.py` 使用未量化 tick 時間計算，
telemetry 與獨立 phase timeline 依各自的 artifact 契約保存。

## 3. 唯讀狀態與速度

來源：[OpenStax《University Physics Volume 1》§4.1 的 Velocity Vector 與 Example 4.3](https://openstax.org/books/university-physics-volume-1/pages/4-1-displacement-and-velocity-vectors)。
向量大小將各軸的速度平方相加再開根號，即
`speed = sqrt(v_n² + v_e² + v_d²)`。

白話直覺：速度向量同時告訴方向與快慢；圖上只顯示快慢時，計算向量大小即可，
不需要另一個可能與向量不一致的 telemetry 欄位。
`view_model.py` 從已保存的 `velocity_ned_mps` 推導 speed，從 `-position_ned_m[2]`
推導 altitude。它不重新產生位置或電量。

cursor 是已保存 snapshot 的索引；phase lookup 依獨立 ground truth 的半開區間，
phase/time 顯示遵守 [PlaybackSession 契約](../../specs/001-telemetry-simulator/data-model.md#playbacksession)。
pause、step、restart 與 speed 只改 cursor 或觀看時鐘，從不改事件順序或任務時間。

## 4. 畫面與觀看時鐘

來源：[Matplotlib Animations 的 FuncAnimation 說明](https://matplotlib.org/stable/users/explain/animations/animations.html#funcanimation)、
[matplotlib.widgets 的 Button／Slider](https://matplotlib.org/stable/api/widgets_api.html)。
動畫 callback 更新圖上的 artists；widgets 將使用者操作送到 session。

白話直覺：播放像翻閱已完成的相簿，調倍速只改翻頁快慢。
`matplotlib_view.py` 每次從同一 cursor 讀取 route marker、三張時間圖與 phase/time label，
timer 的 wall-clock 間隔不成為新的 `mission_time_s`。
Agg terminal frame 與 interactive UI 共用 view model；所有 plotted values 來自既有事件。
