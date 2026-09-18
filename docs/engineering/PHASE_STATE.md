# Phase State

## Phase 1 — Baseline Stabilization / Reliability Hardening
Status: COMPLETE
Evidence: Baseline contract regressions were fixed and production verification was completed through live health and restart/recovery evidence.

## Phase 2 — Core Architecture
Status: COMPLETE
Evidence: The cross-layer architecture/reliability audit was completed through TASK-089 on exact code HEAD `654944e059a3438e31e90aa7f4dc90b04b95110f`. TASK-084 through TASK-089 are implemented, regression-covered, and verified by the seven required GitHub Actions checks on that exact HEAD. No additional Phase-2 repository-backed gap was identified during the closure audit.

### Phase 2 Closure Verification
- Exact code closure HEAD: `654944e059a3438e31e90aa7f4dc90b04b95110f`.
- Required checks on that exact HEAD: `test`, `readiness`, `activation-validation`, `activation-gate`, `production-e2e-contract`, `dependency-audit`, and `final-gate` — all completed successfully.
- Combined commit status was successful.
- Documentation synchronization followed the verified code closure.

## Phase 3 — Telegram Bot
Status: COMPLETE
Evidence: Cross-layer Telegram, tracker, worker/queue, runtime, persistence, provider-capability, startup/shutdown, and production health lifecycle audit completed through TASK-106. Final synchronized engineering-document HEAD requires the seven required GitHub Actions checks to succeed.

### TASK-090 — Telegram Surface Contract Hardening
Status: VERIFIED

Repository-backed gaps identified and corrected:
- Callback payloads are allowlisted and invalid settings requests fail closed.
- `/settings` reports actual authenticated-user settings.
- `/signal` enforces canonical `OPEN/CLOSED/STALE/NO_DATA` before executable analysis/tracking.
- Tracking accepts the complete executable directional contract: `BUY`, `SELL`, `STRONG_BUY`, `STRONG_SELL`.
- Dynamic scanner/tracker HTML output is escaped.
- `/status` reports actual configured market-data provider readiness.
- Regression coverage was added in `tests/test_telegram_surface_contract.py`.
- Exact-head verification: `45a4bd5bb892181cb6a30c75f8b0340ecccaacc7`; all seven required checks succeeded.

### TASK-091 — Durable Telegram User State Across Restarts
Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION

Repository-backed gap:
- `TelegramUserState` previously lived only in the process-local `USER_STATES` dictionary. Language, selected market/timeframe, analysis mode, risk level, notification preference, and current menu were therefore lost on application restart.

Correction:
- Added `services/telegram/state_store.py` with atomic JSON persistence and corruption fail-closed behavior.
- `services/telegram/state.py` now restores persisted user state and automatically persists language, menu, and settings mutations.
- Added regression coverage for restart restoration and corrupted-state rejection.
- Implementation commits: `cd735888107076079f234143fecb08d1310d0041`, `21b7987c2216ca8e5f45d8d1e7f31155149b8d8a`, `e73faf2b0a47017bf22ea3e37baa56de924232f1`.
- Regression commit: `00693506e9f7ee4fd13bfdbbd99e38719fd5b28c`.
- Exact-head CI is required before marking TASK-091 VERIFIED.

### Phase 3 Closure Verification
- Concrete remaining gaps found and corrected through TASK-105 and TASK-106.
- Regression coverage exists for tracker atomic persistence and all persistent Telegram settings mutation paths.
- Final synchronized engineering state is subject to exact-head verification by the seven required checks: test, readiness, activation-validation, activation-gate, production-e2e-contract, dependency-audit, and final-gate.

## Phase 4 — Market/Data Layer
Status: PARTIALLY_COMPLETE

## Phase 5 — Analysis Engine
Status: PARTIALLY_COMPLETE

## Phase 6 — AI/ML
Status: PARTIALLY_COMPLETE
Evidence: Existing `ai/` scaffolding is dormant/unwired and intentionally not treated as active production functionality. Future activation remains a later-phase task.

## Phase 7 — PC Worker / Heavy Processing
Status: PARTIALLY_COMPLETE

## Phase 8 — Trading / Decision Engine
Status: PARTIALLY_COMPLETE

## Phase 9 — Backtesting / Simulation
Status: NOT_STARTED

## Phase 10 — Security / Production Hardening
Status: IN_PROGRESS
Evidence: Dependency security audit and production runtime verification are complete; broader security hardening remains a later roadmap phase/task. Worker endpoint hardening was handled as evidence-backed work.

## Phase 11 — Testing
Status: IN_PROGRESS
Evidence: Required CI verification gates were green on the Phase-2 closure HEAD and TASK-090 exact-head verification. TASK-091 is awaiting fresh exact-head verification.

## Phase 12 — Deployment
Status: COMPLETE
Evidence: Railway live health and restart/recovery verification completed for the intentional Railway-connected fork.

## Phase 13 — Final Production Audit
Status: NOT_STARTED

## Roadmap Rule
Work phases sequentially. Phase 2 is closed. Phase 3 is the active audit frontier. Later phases must not be treated as complete merely because related cross-phase hardening was performed earlier. Temporary cross-phase checks remain allowed only when backed by a concrete dependency or regression.


## Phase 4 — Market/Data Layer
Status: COMPLETE
Evidence: The Phase-4 market/data audit was completed through TASK-109. Concrete gaps in the canonical symbol/timeframe boundary and direct OANDA provider boundary were corrected in TASK-107/108. The full audited surface had no further repository-backed correctness gap requiring code changes. Exact-head GitHub Actions verification on closure HEAD `944d7b3176d201e6cf29c921d2bd27886b86a81d` shows all seven required checks completed successfully.
