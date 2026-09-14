# Engineering Changelog

## 2026-09-15 — Phase 3 Telegram state persistence hardening
- TASK-091 identified a concrete Telegram reliability gap: `TelegramUserState` existed only in the process-local `USER_STATES` dictionary, so user language, selected market/timeframe, analysis mode, risk level, notification preference, and menu state were lost after an application restart.
- Added `services/telegram/state_store.py` with atomic JSON replacement and fail-closed handling for corrupted persisted state.
- `services/telegram/state.py` now restores durable user state and automatically persists language, menu, and settings mutations.
- Added regression coverage for restart restoration and corrupted-state rejection in `tests/test_telegram_state_contract.py`.
- Implementation commits: `cd735888107076079f234143fecb08d1310d0041`, `21b7987c2216ca8e5f45d8d1e7f31155149b8d8a`, `e73faf2b0a47017bf22ea3e37baa56de924232f1`.
- Regression commit: `00693506e9f7ee4fd13bfdbbd99e38719fd5b28c`.
- TASK-091 remains pending exact-head CI verification; Phase 3 remains IN_PROGRESS.

## 2026-09-14 — Phase 3 Telegram surface contract hardening
- TASK-090 identified and corrected a callback trust-boundary gap: arbitrary callback payloads could previously be interpreted as settings values. Callback handling now accepts only canonical values emitted by repository keyboards, and invalid settings payloads fail closed.
- `/settings` now reports actual authenticated-user state instead of hard-coded values.
- `/signal` now enforces canonical `OPEN/CLOSED/STALE/NO_DATA` market status before executable analysis/tracking.
- Executable tracking recognizes `BUY`, `SELL`, `STRONG_BUY`, and `STRONG_SELL`.
- Dynamic Telegram scanner/tracker output is HTML-escaped and `/status` reports actual provider readiness.
- Regression coverage added in `tests/test_telegram_surface_contract.py`.
- TASK-090 implementation commits: `abea95fdd36e8fde1de9108d4659481f0bca2e60`, `f744c8d44c1e6262d7acf0531910e39d97b9745f`, `03918668250a2bbea716f302c4382894a1bf5ac3`, `5936b2aa42441bd8f181a836fe5d7043d88f933c`, `cf5ab1e0cbadb4e59897002590d498558226e80e`.
- TASK-090 regression commit: `4a9481ffa43cc98d387c0425e222486f6a955281`.
- Exact-head CI verification on `45a4bd5bb892181cb6a30c75f8b0340ecccaacc7`: all seven required checks succeeded.

## 2026-09-14 — Phase 2 closure verification
- TASK-084 through TASK-089 are now marked VERIFIED after exact-head CI verification.
- Code closure HEAD: `654944e059a3438e31e90aa7f4dc90b04b95110f`.
- On that exact code HEAD, all seven required workflows/checks succeeded: Test, Readiness, Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, and Final Integration Gate.
- Phase 2 Core Architecture is formally COMPLETE; no additional repository-backed Phase-2 gap was identified during the closure audit.
- Engineering state documents were synchronized in follow-up documentation commits.

## 2026-09-14 — Post-TASK-084 cross-layer reliability audit
- TASK-085: ProviderManager no longer sorts/deduplicates provider candles before downstream quality validation. Provider candle sequences must now already be strictly chronological with unique timestamps; malformed ordering/duplicates fail and can trigger provider failover instead of being silently repaired.
- TASK-086: WorkerRuntime timeout enforcement now covers synchronous heavy executors without blocking the event loop; invalid timeout values are rejected and completed-job cache growth is bounded.
- TASK-087: Tracker refresh re-analyzes the latest market state before TP/SL evaluation and escapes dynamic HTML notifications.
- TASK-088: Telegram signal output escapes dynamic fields and tracker registration accepts only executable directional decisions.
- TASK-089: Centralized Telegram access control uses `TELEGRAM_ALLOWED_USER_IDS`; production with missing/invalid allowlist fails closed and command/callback routes share the same authorization boundary.
- The subsequent regression-only commit `654944e059a3438e31e90aa7f4dc90b04b95110f` preserved the tracker target contract under fresh analysis and was fully verified by the required checks.

## Historical Engineering Checkpoints
- Established persistent engineering-memory state under `docs/engineering/`.
- Corrected the PC Worker boundary and removed the accidental local coding-agent/Ollama runtime from the active architecture.
- Removed the residual `multi_agent_analysis` worker workload.
- Added durable SQLite-backed worker queue, crash recovery, persistence configuration, application service composition, authenticated worker heartbeat/readiness, least-privilege health, authenticated jobs, readiness-gated dispatch, and worker observability.
- Consolidated Telegram ownership under `services/telegram/`.
- Consolidated Decision/Risk ownership under canonical `analysis/` engines and removed the unused alternate analysis architecture.
- Audited `ai/` as dormant/unwired future Phase 6 capability.
- Consolidated production Telegram market-data retrieval behind `MarketDataService` while preserving MarketDataEngine quality/freshness gates and ProviderManager routing.
- Removed the dormant direct OANDA price surface and unused lower-level provider compatibility architecture.
- Verified ProviderManager lifecycle and application-scoped market-data service lifetime.
- Hardened Telegram journal ordering, atomic mutations, corruption fail-closed behavior, structure validation, and entry-schema validation.
- Hardened service startup/shutdown cleanup and worker queue resource lifecycle.
