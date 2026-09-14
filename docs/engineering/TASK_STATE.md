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
- Implementation commits: `d8880ee51b8cfb975b629c1e69b74cba4eb75f1b` and `7101d6e121bb0e71b5517221ef55d460b9bef10f`.
- Regression commits: `9703fff13d0064dcb4631ec388fc19ee268587a1`, `9da8a791c872a278bfef350600173d0332be362f`, and corrected fixture `2a6fd7f3e874d0cda92b16b7eec04661e931d43c`.

## TASK-070
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Risk-Policy Upper-Bound and Currency-Context Hardening
Implementation Status: VERIFIED
Evidence:
- Standalone PositionSizing and RiskEngine accepted risk policies above 100%.
- RiskEngine account_currency could defer malformed values into later sizing failures.
- PositionSizing and RiskEngine now enforce `0 < risk_percent <= 100` and validate account currency at the boundary.
- Implementation commits: `39464db41d3b3478ec79322e455bf188607f7743` and `6d3eb873f6beb664ffe135002a9f976a3`.
- Regression commits: `917c8690331083a2cebc8d806b9c3849ec431322` and `24350c2eaf3de319d55a1dfd440e5daa3a16b901`.

## TASK-071
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Timestamp and Provider Timing Boundary Hardening
Implementation Status: VERIFIED
Evidence:
- `Candle` now requires both `tzinfo` and a non-None `utcoffset()`.
- ProviderManager now requires finite, non-negative retry delay and cooldown values.
- Regression coverage covers invalid custom timezone objects, NaN/Infinity timing values, and valid zero-delay/zero-cooldown behavior.
- Implementation commits: `df70c0bbab22432541fbfcd05de99519fb35fdae` and `7c1eae02d920f4a15f47ef57bbe2d3fd6a3089f9`.
- Regression commits: `8a857af7a87c68566425a4ec34416b4ad68d1f35` and `89bbdf16c010de7de0ca333b332a6da21fd168f9`.

## TASK-072
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Weekend Gap Detection Boundary Hardening
Implementation Status: VERIFIED
Evidence:
- DataQuality now limits the weekend closure exception to a genuine Friday-to-Monday transition within the existing maximum weekend window.
- Regression coverage verifies genuine Friday→Monday closure while large intraday Friday/Monday gaps remain invalid.
- Implementation commit: `7a322723e8bd1154ae7aaab5a8d8f48bf2790f3f`.
- Regression test commit: `32815e720c22197248b817a1d45f01182ed096eb`.

## TASK-073
Phase: Phase 3 — Telegram / Scanner / Tracker Reliability
Title: Tracker Risk-Plan Synchronization
Implementation Status: VERIFIED
Evidence:
- Tracker refresh now synchronizes the complete executable risk plan on tradable direction changes.
- WAIT/NO_TRADE clears executable levels and marks the tracked item INVALIDATED.
- Regression coverage verifies BUY→SELL synchronization and NO_TRADE clearing.
- Implementation commit: `1b3a9cf1b80ac7daae5afd3c55f86d83419ce2fd`.
- Regression test commit: `4288ee926365af25d593d06b683e2d2bbaf1e8e6`.

## TASK-074
Phase: Phase 2/3 — Multi-Asset Market and Risk Architecture
Title: Remove Forex-Only Assumptions from Market-Aware Risk Path
Implementation Status: VERIFIED
Evidence:
- Central configuration explicitly supports Forex, Crypto, Stocks, Indices, and Commodities.
- MarketAwareAnalysisEngine and RiskEngine no longer force every symbol through Forex-only currency parsing.
- Added asset-aware quote currency and contract-size metadata; Forex uses 100000 while the current spot-like non-Forex universe defaults to 1.0.
- CurrencyConversion supports the repository's explicit USDT/USDC equivalent policy and supported bridging while failing closed for unsupported conversions.
- Regression coverage covers quote/contract metadata and stablecoin conversion.

## TASK-075 through TASK-089
Implementation Status: VERIFIED
Evidence: Persistent engineering history records the previously verified Worker/Queue, Provider, Analysis/Risk, Market Status, Tracker, Output Escaping, and Telegram Access Control hardening through exact-head CI verification on the Phase-2 closure baseline `654944e059a3438e31e90aa7f4dc90b04b95110f`.

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
- Exact-head verification: commit `45a4bd5bb892181cb6a30c75f8b0340ecccaacc7`; all seven required checks succeeded.

## TASK-091
Phase: Phase 3 — Telegram / User-State Reliability
Title: Durable Telegram User State Across Restarts
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: `TelegramUserState` was held only in the process-local `USER_STATES` dictionary, so language, settings, and menu state were lost on process restart.
- Added `TelegramStateStore` with atomic JSON replacement and corruption fail-closed behavior.
- User state now loads from durable storage and automatically persists language, menu, and settings mutations.
- Regression coverage added in `tests/test_telegram_state_contract.py`.
- Implementation commits: `cd735888107076079f234143fecb08d1310d0041`, `21b7987c2216ca8e5f45d8d1e7f31155149b8d8a`, `e73faf2b0a47017bf22ea3e37baa56de924232f1`.
- Regression commit: `00693506e9f7ee4fd13bfdbbd99e38719fd5b28c`.

## TASK-092
Phase: Phase 3 — Telegram / Tracker Reliability
Title: Durable Active Tracker State Across Restarts
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: active tracked signals were held only in the process-local `ACTIVE_TRACKS` dictionary. A service restart discarded every ongoing tracker.
- Added `TrackerStore` with atomic JSON replacement, configurable `TELEGRAM_TRACKER_FILE`, and corruption fail-closed behavior.
- Active tracker records are restored at module initialization and persisted on create, stop, refresh, target/stop completion, and signal-plan updates.
- Stored tracker identity is validated against its key.
- Regression coverage added in `tests/test_telegram_tracker_persistence.py`.
- Implementation commits: `6765a4d022c84b90f01e34b379026670a03f1ecf`, `aee7e0b02a883ed283f4f8177ff70197f523c872`.
- Regression commit: `e96075b80d7fb8ea104b1584a71fe6118220ef7a`.

## TASK-093
Phase: Phase 3 — Telegram / Tracker Execution Reliability
Title: Activate Tracker Refresh Loop and Honor Notification Preference
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: `refresh_all_tracked_signals()` existed but had no registration in the Telegram application, so persisted active trackers were never automatically refreshed after deployment/startup.
- Concrete gap: the user's persisted `notifications_enabled` setting was not consulted by the tracker job; notifications were always sent.
- Added a scheduled JobQueue refresh loop with a bounded configurable `TELEGRAM_TRACKER_INTERVAL_SECONDS` (minimum 5 seconds, default 60).
- Startup now fails explicitly if Telegram JobQueue is unavailable because active tracking cannot operate without it.
- Tracker notifications now respect the user's persisted notification preference, defaulting to enabled for backward compatibility.
- Regression coverage added in `tests/test_telegram_tracker_job_contract.py`.
- Implementation commits: `d2b5fd1e4e3bd95829707f369638b2d9c2e2e2fd`, `61ed687e94a912dd8f455a76cd4845df2abdf0c9`.
- Regression commit: `a9e15adeedacd95e573b5f23fb2f038c880432a7`.

## TASK-094
Phase: Phase 3 — Telegram / Callback Reliability
Title: Exact-Identity Untrack Callbacks
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: the single `signal_untrack` callback used the user's current settings rather than the specific tracked signal represented by the Tracking screen.
- If multiple signals were tracked and the user changed market/timeframe settings, pressing Stop could stop the wrong signal or fail to stop the displayed one.
- Tracking buttons now encode the exact symbol/timeframe identity and the handler validates ownership against the user's current tracked set before stopping it.
- Regression coverage added in `tests/test_telegram_callback_tracking_contract.py`.
- Implementation commit: `f5528c87a598f17bbb033e16b7b3985be336840f`.
- Regression commit: `bd374520a7c5dae78cef2d79043d1f80188593b4`.

## TASK-095
Phase: Phase 3 — Telegram / Multi-Asset Scanner Reliability
Title: Multi-Asset Scanner Universe
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: despite the platform's explicit multi-asset architecture, the Telegram scanner default universe contained only four Forex pairs.
- Scanner now uses a bounded representative universe spanning Forex, Crypto, Stocks, Indices, and Commodities.
- `TELEGRAM_SCANNER_SYMBOLS` provides an explicit normalized override with a maximum of 20 symbols to prevent uncontrolled scan fan-out.
- Regression coverage verifies multi-asset defaults, normalization/deduplication, and the hard bound.
- Implementation commit: `8201797322700ef0f4ac85fb7b01aa76fba8189a`.
- Regression commit: `f26c454d2ecd5cd0c424f64f21b93a4005ab119e`.

## Multi-Asset Architecture Contract
The project is a **Multi-Asset Trading Intelligence Platform**, not a Forex-only bot. Supported market families are represented centrally in `config/symbols.py`: Forex, Crypto, Stocks, Indices, and Commodities. A symbol must not be rejected merely because it is not Forex. Market-specific semantics such as quote currency, contract size, trading session, provider support, and conversion requirements must be explicit and must fail closed when unavailable.

## Current Audit Frontier
Phase 3 remains active. TASK-090 is verified. TASK-091 through TASK-095 are implemented and pending exact-head CI verification. Continue auditing Telegram/Scanner/Tracker/Callbacks for concrete gaps only, then proceed to Worker/Queue/Persistence and later phases according to the roadmap.

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
