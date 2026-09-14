# Engineering Changelog

## 2026-09-14 — Phase 2 closure verification
- TASK-084 through TASK-089 are now marked VERIFIED after exact-head CI verification.
- Code closure HEAD: `654944e059a3438e31e90aa7f4dc90b04b95110f`.
- On that exact code HEAD, all seven required workflows/checks succeeded: Test, Readiness, Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, and Final Integration Gate.
- Phase 2 Core Architecture is formally COMPLETE; no additional repository-backed Phase-2 gap was identified during the closure audit.
- Engineering state documents were synchronized in follow-up documentation commits.

## 2026-09-14 — Post-TASK-084 cross-layer reliability audit
- TASK-085: ProviderManager no longer sorts/deduplicates provider candles before downstream quality validation. Provider candle sequences must now already be strictly chronological with unique timestamps; malformed ordering/duplicates fail and can trigger provider failover instead of being silently repaired.
- TASK-085: added regression coverage for non-chronological and duplicate provider responses while preserving tuple compatibility and limit behavior.
- TASK-085 implementation commit `eea607f106cbea57c1fd3b6d3d7b0a783398eb97`; regression commit `a7d181580369fc3f92b851d608a8f406060f49f6`.
- TASK-086: WorkerRuntime now applies the timeout boundary to synchronous heavy executors using an off-event-loop execution path, preventing CPU-bound synchronous handlers from blocking the worker event loop and making the runtime timeout contract effective for both sync and async handlers.
- TASK-086: added regression coverage for synchronous timeout behavior, invalid timeout input, and cancellation cache safety.
- TASK-086 implementation commit `6e22747447de1a545c4f5fe59d80e`; regression commit `f623afee75b8c6fc4c8b5f72605b4a0d8fd11d69`.
- TASK-087: Tracker refresh now re-analyzes the latest market state before evaluating TP/SL, preventing an old BUY/SELL risk plan from incorrectly closing a signal after a same-candle direction change. Tracker notifications also escape dynamic HTML content.
- TASK-087: added regression coverage for direction-flip target ordering.
- TASK-087 implementation commit `c9e9f9417800693cc7e354386dd4189811314503`; regression commits `d32d9478e699263e5ae2bd8264b2f247bb277e6a` and `5582f1179c94a21549a9cc887149cb6c31884ed4`.
- TASK-088: Telegram signal output now HTML-escapes dynamic market/report fields and the tracker accepts only executable BUY/SELL decisions from the signal handler; neutral/unknown results are never registered as active tracked trades.
- TASK-088 implementation commit `320e2d5f2dd1ab7d512d3b6fc02b854daf7cec0e`.
- TASK-089: centralized Telegram access control was added. `TELEGRAM_ALLOWED_USER_IDS` is an explicit allowlist; production with a missing/invalid allowlist fails closed, while development/testing preserve the prior open behavior. All command and callback routes pass through the same authorization boundary.
- TASK-089: added regression coverage for allowlisted users, unauthorized users, invalid configuration, production fail-closed behavior, and development compatibility.
- TASK-089 commits: access boundary `925ba7f48a16cad20c61941d51c891d1a4f5bf8c`, route enforcement `ec6c29e531961c2e57e466be46a31474ec99e7a6`, regression coverage `55284ac27fd54de248941c1f2bf132c00e317655`.
- The subsequent regression-only commit `654944e059a3438e31e90aa7f4dc90b04b95110f` preserved the tracker target contract under fresh analysis and was fully verified by the required checks.

## 2026-09-14 — TASK-084 Market Status Contract Hardening
- Exact code HEAD `48b015525daf99b60294c8591cb8ed1c0fee2c35` was verified before starting the next audit step: Test, Production Readiness, Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, and Final Integration Gate all succeeded; combined status is successful.
- TASK-084 identified a concrete Telegram market-status contract gap: the helper emitted `STALE_DATA` rather than canonical `STALE`, ignored its timeframe argument for a fixed 180-minute threshold, treated naive timestamps as UTC, and applied weekend closure globally.
- TASK-084 changed market status to canonical `OPEN/CLOSED/STALE/NO_DATA`, scales stale detection to six timeframe intervals, rejects invalid/naive/future timestamps, and applies weekend closure only to non-crypto markets.
- Scanner now passes symbol context into market-status evaluation and consumes the canonical `STALE` state.
- Added focused regression coverage in `tests/test_market_session.py` for no-data, timestamp safety, future timestamps, timeframe-scaled staleness, weekday OPEN, Forex weekend closure, Crypto weekend behavior, and invalid reference time.
- TASK-084 implementation commit `a0caef5d41e598dc9ce54c31b68d2529c1438c5d`.
- TASK-084 scanner integration commit `ad0ae2ed332ed1007302cfe008587e9cfb8a6c10`.
- TASK-084 regression commit `3e3f17dac93f2f20e13c804a0b89195fdf239587`.

## 2026-09-14 — Audit synchronization through TASK-083
- TASK-083: identified a concrete RiskEngine policy gap where `_dynamic_risk_percent()` could select up to `2.0%` without respecting a more restrictive configured `risk_percent`.
- TASK-083: changed dynamic sizing so configured `risk_percent` is the account-level ceiling; the dynamic heuristic may reduce risk but cannot silently exceed it.
- TASK-083: added focused regression coverage for restrictive/non-restrictive ceilings and symmetric directional scoring.
- TASK-083: implementation commit `d9c427b7f44a56db2c4f6c98b37e249a6df8af82`.
- TASK-083: regression commit `cbc09a3fefa6b5d97d77119cb8196f1d21da7604`.
- TASK-065 through TASK-083 were subsequently verified together on exact code HEAD `48b015525daf99b60294c8591cb8ed1c0fee2c35`; all seven required workflows succeeded and combined status is successful.

## 2026-09-14 — TASK-079 through TASK-082
- TASK-082: ProviderManager reconfiguration now replaces the injected provider registry and prunes inactive instances/cooldowns while preserving active factory cache state.
- TASK-081: DataQuality now delegates symbol normalization to `config.symbols.normalize_symbol()` and regression coverage verifies slash/underscore equivalence.
- TASK-080: RiskEngine derives contract size from centralized asset metadata when no explicit override is supplied.
- TASK-079: PositionSizing, Settings, and RiskEngine now share the explicit USDT/USDC currency policy already supported by CurrencyConversion.

## 2026-09-13 — TASK-065 and prior verified checkpoints
- TASK-065: `risk_reward_target` is now wired into BUY/SELL TP2 and reported risk/reward with validation and regression coverage.
- Historical TASK-058 through TASK-064 evidence remains preserved in repository history.
- Historical TASK-052 through TASK-057 evidence remains preserved in repository history.

## Historical 2026-09-12 and earlier engineering checkpoints
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
