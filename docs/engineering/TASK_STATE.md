# Task State

## TASK-001 through TASK-064
Phase 1/2 reliability and architecture tasks through DecisionEngine Supply/Demand consumption remain VERIFIED according to the persistent engineering history.

## TASK-065
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: ConfidenceEngine Numeric Boundary Hardening
Implementation Status: VERIFIED

## TASK-066
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: FullAnalysisEngine Numeric Boundary Hardening
Implementation Status: VERIFIED

## TASK-067
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: PositionSizing Decimal Numeric-Range Hardening
Implementation Status: VERIFIED
Evidence:
- Float-level finite validation was followed by Decimal quantization that could leak DecimalException for finite values exceeding active Decimal precision.
- PositionSizing converts that numeric-range failure to the public fail-closed ValueError contract.
- Regression coverage was added for the oversized-but-finite case.
- Implementation commit: `5967f1741e6e381fa83328d93f4f1b65d871b5dd`.
- Regression test commit: `307576dfddc63c079bed0c1fdeed16595fd7ad54`.

## TASK-068
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: RiskEngine Directional Price-Level Safety
Implementation Status: VERIFIED
Evidence:
- Deeper inspection of `RiskEngine → PositionSizing → CurrencyConversion → MarketAwareAnalysisEngine` found that finite risk distances could still produce economically invalid trade levels.
- A BUY setup could produce a zero/negative stop-loss when risk distance crossed the entry price; a SELL setup could produce non-positive take-profit levels.
- The output contract now rejects non-positive risk levels and enforces directional ordering for BUY and SELL plans before position sizing output is emitted.
- Regression coverage added for zero-crossing, non-positive SELL targets, overflow, and normal directional ordering.
- Implementation commit: `b11d6429698aa749c1263f9fe65e6b4a0bac42dd`.
- Regression test commit: `131f0a656c694a9b6e4e88e4b1f7326032f91074`.

## TASK-069
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Explicit Account-Balance Wiring and Settings Numeric Hardening
Implementation Status: VERIFIED
Evidence:
- Production MarketAwareAnalysisEngine was constructing RiskEngine without the configured account balance.
- Settings now validates account balance/risk/currency policy and MarketAwareAnalysisEngine passes the configured balance explicitly.
- Regression coverage verifies the configured balance changes executable sizing and rejects malformed numeric/currency settings.
- Implementation commits: `d8880ee51b8cf...`.

## TASK-070 through TASK-089
Implementation Status: VERIFIED
Evidence: Persistent engineering history records the previously verified reliability hardening through exact-head CI verification on the Phase-2 closure baseline `654944e059a3438e31e90aa7f4dc90b04b95110f`.

## TASK-090
Phase: Phase 3 — Telegram / Scanner / Tracker / Callback Reliability
Title: Telegram Surface Contract Hardening
Implementation Status: VERIFIED
Evidence:
- Callback payloads are allowlisted and invalid settings values fail closed.
- `/settings` reports actual per-user settings rather than hard-coded values.
- `/signal` enforces `OPEN/CLOSED/STALE/NO_DATA` before executable analysis/tracking.
- Executable tracking covers BUY, SELL, STRONG_BUY, and STRONG_SELL.
- Dynamic scanner/tracker HTML is escaped and `/status` reports actual provider readiness.
- Regression coverage added in `tests/test_telegram_surface_contract.py`.
- Implementation commits: `abea95fdd36e8fde1de9108d4659481f0bca2e60`, `f744c8d44c1e6262d7acf0531910e39d97b9745f`, `03918668250a2bbea716f302c4382894a1bf5ac3`, `5936b2aa42441bd8f181a836fe5d7043d88f933c`, `cf5ab1e0cbadb4e59897002590d498558226e80e`.
- Regression commit: `4a9481ffa43cc98d387c0425e222486f6a955281`.
- Exact-head verification: commit `45a4bd5bb892181cb6a30c75f8b0340ecccaacc7`; all seven required checks succeeded.

## TASK-091
Phase: Phase 3 — Telegram / User-State Reliability
Title: Durable Telegram User State Across Restarts
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: `TelegramUserState` was held only in the process-local `USER_STATES` dictionary, so language, settings, and menu state were lost on process restart.
- Added `TelegramStateStore` with atomic JSON replacement and corruption fail-closed behavior.
- User state now loads from durable storage and automatically persists language, menu, and settings mutations.
- Added `tests/test_telegram_state_contract.py` coverage for restart restoration and corrupted-state fail-closed behavior.
- Implementation commits: `cd735888107076079f234143fecb08d1310d0041`, `21b7987c2216ca8e5f45d8d1e7f31155149b8d8a`, `e73faf2b0a47017bf22ea3e37baa56de924232f1`.
- Regression commit: `00693506e9f7ee4fd13bfdbbd99e38719fd5b28c`.
- Current verification target is the latest repository HEAD after this task; Phase 3 remains open until all required CI checks succeed on that exact HEAD.

## TASK-092
Phase: Phase 3 — Telegram / Tracker Reliability
Title: Durable Active Tracker State Across Restarts
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: active tracked signals were held only in the process-local `ACTIVE_TRACKS` dictionary. A service restart discarded every ongoing tracker even though the user had explicitly requested tracking.
- Added `TrackerStore` with atomic JSON replacement, configurable `TELEGRAM_TRACKER_FILE`, and corruption fail-closed behavior.
- Active tracker records are restored at module initialization and persisted on create, stop, refresh, target/stop completion, and signal-plan updates.
- Stored tracker identity is validated against its key to prevent mismatched records from being silently accepted.
- Added `tests/test_telegram_tracker_persistence.py` covering restart restoration, removal persistence, corruption rejection, and identity mismatch rejection.
- Implementation commits: `6765a4d022c84b90f01e34b379026670a03f1ecf`, `aee7e0b02a883ed283f4f8177ff70197f523c872`.
- Regression commit: `e96075b80d7fb8ea104b1584a71fe6118220ef7a`.
- Exact-head CI verification is still required before this task can be marked VERIFIED.

## Multi-Asset Architecture Contract
The project is a **Multi-Asset Trading Intelligence Platform**, not a Forex-only bot. Supported market families are represented centrally in `config/symbols.py`: Forex, Crypto, Stocks, Indices, and Commodities. A symbol must not be rejected merely because it is not Forex. Market-specific semantics such as quote currency, contract size, trading session, provider support, and conversion requirements must be explicit and must fail closed when unavailable.

## Current Audit Frontier
Phase 3 remains active. TASK-090 is verified. TASK-091 and TASK-092 are implemented and pending exact-head CI verification. Continue auditing Telegram/Scanner/Tracker/Callbacks for concrete gaps only, then proceed to Worker/Queue/Persistence and later phases according to the roadmap.

Do not create another task merely to advance the roadmap. Create the next task only after a concrete repository-backed gap is demonstrated.

## New-chat Continuation Contract
When a new chat starts work on this repository, first read:
- `docs/engineering/PROJECT_STATE.md`
- `docs/engineering/PHASE_STATE.md`
- `docs/engineering/TASK_STATE.md`
- `docs/engineering/TEST_STATE.md`
- `docs/engineering/ARCHITECTURE_MAP.md`
- `docs/engineering/DECISIONS.md`
- `docs/engineering/CHANGELOG_ENGINEERING.md`
