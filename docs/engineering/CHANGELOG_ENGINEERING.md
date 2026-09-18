# Engineering Changelog

## 2026-09-18 — Phase 4 Market/Data Layer closure
- TASK-107 closed a direct OANDA boundary inconsistency: `supports_symbol()` rejected unsupported symbols while direct `_normalize_symbol()` still accepted arbitrary six-letter alphabetic instruments. Direct OANDA requests now fail closed outside the explicit instrument map.
- TASK-108 closed a canonical MarketDataEngine boundary gap: the engine now validates the centralized supported-symbol registry and explicitly maps internal timeframes to provider-facing identifiers. This also corrected the `15m -> 15M` provider-boundary normalization defect.
- TASK-109 completed the Phase-4 audit across candle contracts, symbol/asset metadata, timeframe normalization, MarketDataService/Engine, ProviderManager, all registered providers, fallback/retry/cooldown, ordering/duplicates/gaps, freshness, DataQuality, DataFrame conversion, currency conversion, multi-asset compatibility, production configuration/readiness, and E2E fail-closed behavior.
- No further repository-backed Phase-4 code gap was identified. Speculative provider expansion, caching, retry-policy redesign, and new market-session behavior were intentionally not introduced without concrete evidence.
- Closure code HEAD: `944d7b3176d201e6cf29c921d2bd27886b86a81d`; all seven required checks completed successfully.

# Engineering Changelog

## 2026-09-15 — Provider capability boundary hardening
- TASK-100 identified a concrete multi-asset reliability gap: the scanner's multi-asset universe includes Crypto, Stocks, Indices, and Commodities, but the registered Finnhub and Alpha Vantage providers are Forex-only and OANDA has a narrower instrument map. ProviderManager previously attempted every configured provider for every symbol, turning known capability mismatches into generic failures/retries/cooldowns.
- Added explicit `supports_symbol()` provider capability boundaries. OANDA now exposes its actual instrument acceptance; Finnhub and Alpha Vantage explicitly declare Forex-only coverage.
- ProviderManager now skips unsupported providers without issuing network requests and records an `UnsupportedSymbol` diagnostic. Duck-typed custom providers remain backward-compatible when they do not expose the optional capability method.
- Added regression coverage for capability-based provider skipping.
- TASK-100 remains pending exact-head CI verification.

## 2026-09-15 — Cross-layer Worker/Queue/Telegram reliability hardening
- TASK-096 identified a concrete recovery race in the durable WorkerQueue: an expired `RUNNING` job could be recovered to `PENDING`, re-claimed by a new execution, and then have the original stale worker overwrite the newer terminal state. Added per-claim `claim_token` fencing and regression coverage.
- TASK-097 found the complementary lease-expiry gap: legitimate long-running jobs had no heartbeat, so `claimed_at` could expire while the worker was still executing. Added token-scoped `renew_lease()` and a bounded dispatcher heartbeat.
- TASK-098 found that `asyncio.wait_for(asyncio.to_thread(...))` does not terminate the underlying synchronous OS thread. Timed-out synchronous worker jobs are now retained as in-flight until the underlying thread actually completes, preventing same-runtime duplicate execution and caching the eventual result once.
- TASK-099 found a Telegram startup ordering gap: updater/JobQueue dependencies were validated after `Application.start()`. Startup now preflights these dependencies and schedules tracker refresh before the runtime is marked started, preventing partial startup on dependency failure.
- Added regression coverage for renewable queue leases and synchronous worker timeout fencing.
- These changes remain pending exact-head CI verification;
- TASK-101 fixed the Telegram multi-asset settings gap by deriving market-family and symbol choices from the centralized symbol registry instead of exposing only four Forex pairs.
- they are not marked VERIFIED until the complete required workflow set succeeds on the exact current HEAD.

## 2026-09-15 — Worker queue recovery/lease fencing hardening
- TASK-096 identified a concrete cross-layer recovery race in the durable WorkerQueue: an expired `RUNNING` job could be recovered to `PENDING`, re-claimed by a new worker execution, and then have its original stale worker overwrite the new execution's terminal state.
- Added per-claim `claim_token` fencing. Recovery clears the old lease token; dispatcher terminal transitions must present the token belonging to their current claim, so stale workers cannot complete or fail a newer execution.
- Added SQLite `busy_timeout`/connection timeout to make the durable queue more resilient to short-lived concurrent connection locks.
- Added regression coverage for stale-worker completion after recovery and re-claim.
- TASK-096 is implemented and pending exact-head CI verification; it is not marked VERIFIED until the complete required workflow set succeeds on the exact current HEAD.

## 2026-09-15 — Phase 3 Telegram state persistence hardening
- TASK-091 identified a concrete Telegram reliability gap: `TelegramUserState` existed only in the process-local `USER_STATES` dictionary, so user language, selected market/timeframe, analysis mode, risk level, notification preference, and menu state were lost after an application restart.
- Added `services/telegram/state_store.py` with atomic JSON replacement and fail-closed handling for corrupted persisted state.
- `services/telegram/state.py` now restores durable user state and automatically persists language, menu, and settings mutations.
- Added regression coverage for restart restoration and corrupted-state rejection in `tests/test_telegram_state_contract.py`.
- TASK-091 remains pending exact-head CI verification; Phase 3 remains IN_PROGRESS.

## 2026-09-14 — Phase 3 Telegram surface contract hardening
- TASK-090 identified and corrected a callback trust-boundary gap: arbitrary callback payloads could previously be interpreted as settings values. Callback handling now accepts only canonical values emitted by repository keyboards, and invalid settings payloads fail closed.
- `/settings` now reports actual authenticated-user state instead of hard-coded values.
- `/signal` now enforces canonical `OPEN/CLOSED/STALE/NO_DATA` market status before executable analysis/tracking.
- Executable tracking recognizes `BUY`, `SELL`, `STRONG_BUY`, and `STRONG_SELL`.
- Dynamic Telegram scanner/tracker output is HTML-escaped and `/status` reports actual provider readiness.
- Regression coverage added in `tests/test_telegram_surface_contract.py`.
- TASK-090 exact-head verification on `45a4bd5bb892181cb6a30c75f8b0340ecccaacc7`: all seven required checks succeeded.

## 2026-09-14 — Phase 2 closure verification
- TASK-084 through TASK-089 are marked VERIFIED after exact-head CI verification on code closure HEAD `654944e059a3438e31e90aa7f4dc90b04b95110f`.
- Phase 2 Core Architecture is formally COMPLETE.

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


## 2026-09-18 — Phase 3 closure hardening
- TASK-105 closed a concrete persistence consistency gap: Telegram TrackerStore used a fixed temporary path and did not fsync before replacement. It now uses unique same-directory temporary files, fsync, atomic replace, and cleanup.
- TASK-106 closed a concrete persistence API gap: the persistent settings wrapper did not explicitly persist setdefault, pop, and popitem. These mutation paths are now covered and regression-tested.
- The full Phase-3 audit was rechecked across Telegram surface/callbacks/settings, tracker persistence/refresh, worker queue fencing/renewal/recovery, synchronous timeout fencing, worker runtime lifecycle, startup/shutdown cleanup, provider capability boundaries, and production health resource lifecycle.
- No additional repository-backed Phase-3 gap was found after TASK-105/106. Phase 3 is ready for final synchronized seven-check verification.
