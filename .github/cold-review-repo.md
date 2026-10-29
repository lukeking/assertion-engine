# cold review：這個 repo 的權威順序與硬邊界

`~/.agents/bin/render_cold_review_prompt.py` 把下面兩節的內文原樣填進 reviewer prompt，讀的是受審範圍 base 那一版，
所以 PR 改不到審自己的這份契約。這裡只寫每一輪都成立的內容；某個 PR 刻意的改動、哪些不算 finding，寫進那一輪的「來由」。
只能有這兩個 `##` 節，多一節或少一節腳本都會拒絕；內文不要有角括號佔位字，會被當成沒填。

## 權威順序

.specify/memory/constitution.md 是本 repo 的規則，效力高於其他開發慣例；衝突時以憲章為準，或先修訂憲章。docs/decisions/ 是已接受的技術決策，各自寫了重新評估的觸發條件，程序與實作須遵守它們，除非觸發條件成立並另立新決策。Codex 側的 spec-kit 程序是 .agents/skills/speckit-* 與它們呼叫的 .specify/templates/、.specify/scripts/；Claude 側使用 user 層的 spec-kit，不在本 repo。specs/ 下每個 feature 目錄是該 feature 的 spec、plan、tasks 與驗證紀錄，是設計與狀態紀錄，不是工作方式的規則。CLAUDE.md 與 AGENTS.md 只指向當前的 plan。

## 硬邊界

handle-secrets 禁止讀取或引用憑證；只讀此 checkout 在 head 的 tracked 檔案；不寫入、不連網、不用 MCP、不委派。CLAUDE.local.md（不進版控）、memory 檔（~/.claude/projects/*/memory/）、user 層的 spec-kit、規則與 skills、個人 runtime 與 settings.json 不在來源內，讀不到不構成 finding。Fuzzer 不得共用 DSL 語法樹、規則語意或評估邏輯的程式碼（憲章原則 I），這是架構邊界，不是風格偏好。
