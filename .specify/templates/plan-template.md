# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [MUST 以 p50/p95/p99/max 表述；「每秒 N 事件」為誤導性指標（憲章原則 II）。階梯見憲章原則 II；L0–L3 的 100/50/20/10 ms 為 E2/E3 處理預算，效能 Gate 僅由 E1 建立]\
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

依 `.specify/memory/constitution.md` v1.0.1：

- [ ] **I. 對抗式驗證** — Fuzzer 是否獨立於 Evaluator？是否**未共用** DSL 語法樹
      或規則語意？「應該被偵測到」的期望結果是否由 Fuzzer 端獨立決定？
- [ ] **II. 尾延遲優先** — 效能是否以 p50/p95/p99/**max** 表述而非平均吞吐？
      若使用 GC 環境，是否報告暫停分佈並將暫停期間錯過的事件計入偵測率？
      （階梯已推導但尚非效能 Gate；未實測的達成階數仍應標記未定錨）
- [ ] **III. 語法由語料庫反推** — 是否已有 ≥10 條真實規則語料庫？
      語法是否由它反推，而非先設計再找例子？語料庫是否納入回歸測試？
- [ ] **IV. 可追溯且可理解** — 是否同時具備文獻引用與白話橋接？
      手寫 parser 是否有明確的形式文法對應（否則沒人說得清它接受什麼）？
- [ ] **V. 可重現** — Simulator 與 Fuzzer 是否接受顯式種子？漏檢可否原樣重播？
- [ ] **VI. 證據等級** — 宣稱是否標註 E1/E2/E3？Gate 是否僅採用 E1？
- [ ] **視覺化驗收** — 是否含語法樹、規則觸發時點、視窗趨勢線的視覺佐證？
- [ ] **不套用他案 spike 設計** — 是否誤用了 mapf-router 的平均吞吐量測法？
      （本專案決定成敗的是尾延遲與暫停時間，儀器不同）

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
