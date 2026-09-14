# Engineering Changelog

## 2026-09-14 — TASK-084 Market Status Contract Hardening
- Exact `main` HEAD `48b015525daf99b60294c8591cb8ed1c0fee2c35` was verified before starting the next audit step: Test, Production Readiness, Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, and Final Integration Gate all succeeded; combined status is successful.
- TASK-084 identified a concrete Telegram market-status contract gap: the helper emitted `STALE_DATA` rather than canonical `STALE`, ignored its timeframe argument for a fixed 180-minute threshold, treated naive timestamps as UTC, and applied weekend closure globally.
- TASK-084 changed market status to canonical `OPEN/CLOSED/STALE/NO_DATA`, scales stale detection to six timeframe intervals, rejects invalid/naive/future timestamps, and applies weekend closure only to non-crypto markets.
- Scanner now passes symbol context into market-status evaluation and consumes the canonical `STALE` state.
- Added focused regression coverage in `tests/test_market_session.py` for no-data, timestamp safety, future timestamps, timeframe-scaled staleness, weekday OPEN, Forex weekend closure, Crypto weekend behavior, and invalid reference time.
- TASK-084 implementation commit `a0caef5d41e598dc9ce54c31b68d2529c1438c5d`.
- TASK-084 scanner integration commit `ad0ae2ed332ed1007302cfe008587e9cfb8a6c10`.
- TASK-084 regression commit `3e3f17dac93f2f20e13c804a0b89195fdf239587`.
- TASK-084 post-change exact-head verification is pending; no green or live-production claim is made yet.

## 2026-09-14 — Audit synchronization through TASK-083
- TASK-083: identified a concrete RiskEngine policy gap where `_dynamic_risk_percent()` could select up to `2.0%` without respecting a more restrictive configured `risk_percent`.
- TASK-083: changed dynamic sizing so configured `risk_percent` is the account-level ceiling; the dynamic heuristic may reduce risk but cannot silently exceed policy.
- TASK-083: added focused regression coverage for restrictive/non-restrictive ceilings and symmetric directional scoring.
- TASK-083: implementation commit `d9c427b7f44a56db2c4f6c98b37e249a6df8af82`.
- TASK-083: regression commit `cbc09a3fefa6b5d97d77119cb8196f1d21da7604`.
- ProviderManager lifecycle regression expectation was synchronized with the intentional `set_providers()` replacement contract after the CI suite exposed the stale test assumption.
- TASK-082: reconfiguration now replaces the injected provider registry and prunes removed instances/cooldowns while preserving active factory cache state.
- TASK-081: DataQuality now delegates symbol normalization to the canonical symbol layer.
- TASK-080: RiskEngine derives contract size from centralized asset metadata when no explicit override is supplied.
- TASK-079: PositionSizing, Settings, and RiskEngine now share the explicit USDT/USDC currency policy already supported by CurrencyConversion.
- TASK-065 through TASK-083 were subsequently verified together on exact `main` HEAD `48b015525daf99b60294c8591cb8ed1c0fee2c35`; all seven required workflows succeeded and combined status is successful.

## 2026-09-14 — TASK-079 through TASK-082
- TASK-082: identified a ProviderManager reconfiguration lifecycle gap where removed injected providers and stale cached state could remain reachable after `set_providers()`.
- TASK-082: replaced the injected-provider registry on reconfiguration and pruned inactive provider instances/cooldowns while preserving active factory cache state.
- TASK-082: added regression coverage for removal, stale cooldown cleanup, re-addition, and same-name instance rebinding.
- TASK-082 implementation commit `46ba02295ddbc2629cca371ebbdafaba47a6a715`.
- TASK-082 regression commits `03cace1b483d1980c3db074bae1be240f487f53c` and `54dfaa6591b90ebf9e99906cf14a10c73a30ea37`.
- TASK-081: aligned DataQuality symbol normalization with `config.symbols.normalize_symbol()` and added slash/underscore regression coverage.
- TASK-081 implementation commit `a3c6f43bf76e0ab10b0cb721fdd0e18a20e04ddd`.
- TASK-081 regression commit `0cbe8b40c62fb6a0b561d0d94d72de10436dbaa5`.
- TASK-080: removed the Forex contract-size default from direct non-Forex RiskEngine calls by deriving asset metadata when no explicit override exists.
- TASK-080 regression commit `761e7666b846a69d3e1b5cc07604a4747e738f3f`.
- TASK-079: made the stablecoin currency boundary consistent across PositionSizing, Settings, RiskEngine, and CurrencyConversion.

## 2026-09-13 — TASK-065 and prior verified checkpoints
- TASK-065: identified a concrete RiskEngine configuration gap: `risk_reward_target` was accepted as a constructor parameter but TP2 and reported risk/reward remained hardcoded at `2.0`.
- TASK-065: wired `risk_reward_target` into BUY/SELL TP2 and `RiskResult.risk_reward`, added validation, and regression coverage.
- Historical TASK-058 through TASK-064 verification evidence remains preserved in repository history.
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
