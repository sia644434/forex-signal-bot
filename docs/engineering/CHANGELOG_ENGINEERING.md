# Engineering Changelog

## 2026-09-13
- TASK-044: completed the scanner `ProviderManager` lifetime and readiness boundary audit.
- TASK-044: confirmed the Telegram callback is the real application caller of `scan_market()` in the current code path; no scheduler/background scanner lifecycle was found that justified a separate manager design.
- TASK-044: changed scanner manager lifetime from per-scan construction to application-scoped storage in `Application.bot_data`, preserving provider instances, cooldowns, and failure state without introducing process-global state.
- TASK-044: preserved dynamic provider-readiness semantics by recalculating readiness on each manager retrieval and refreshing provider priority through `set_providers()`.
- TASK-044: retained `_build_provider_manager()` as the direct/non-application fallback for `scan_market()`.
- TASK-044: added regression coverage for application-scoped manager reuse and readiness changes.
- TASK-044: implementation commits `680fc4cd447d770fb7013563d0d538a04e8cc4d2`, `99dc8679680590d96641e574b00716f637b4988d`, and `7180828f4c3b12e7bb30588b614941cc662c0154` passed Final Integration Gate `34721606858`, Production Activation Validation `34721606855`, and Production E2E Contract Gate `34721606841`.
- Synchronized persistent engineering state after TASK-044 verification. Phase 2 remains active pending selection of the next evidence-backed architecture/reliability gap.

## 2026-09-12
- Established the first persistent engineering-memory checkpoint for the repository.
- Added baseline architecture/state tracking under `docs/engineering/`.
- Recorded repository/CI evidence without claiming production readiness.
- Preserved the current implementation; no mass architectural rewrite performed during baseline setup.
- Corrected the PC Worker boundary: active worker runtime is dedicated to heavy Forex workloads and no longer initializes a local coding agent/Ollama runtime.
- Removed `coding_agent` from the declared worker workload contract and added regression coverage preventing its reintroduction.
- Removed the residual `multi_agent_analysis` worker workload, executor, tests, and documentation references.
- Audited the skipped pre-TASK-004 Phase 2 scope without inventing a missing historical task contract.
- Added the durable SQLite-backed Forex worker queue, crash recovery, persistence configuration, application service composition, and heavy-Forex routing boundary without speculative callers.
- Added authenticated PC Worker heartbeat transport, readiness states, heartbeat observability, freshness semantics, least-privilege public health, authenticated job requests, readiness-gated dispatch, and operational observability.
- Consolidated Telegram ownership under `services/telegram/`.
- Removed duplicate decision/risk/strategy architecture and documented canonical `analysis/decision_engine.py` and `analysis/risk_engine.py` ownership.
- Removed the unused alternate analysis adapter/registry/orchestrator/contracts architecture and aligned canonical analysis exports.
- Audited the `ai/` package and classified it as dormant/unwired future Phase 6 capability. No production AI caller or AI service composition was introduced.
- Consolidated production Telegram candle retrieval behind `services/market_data/service.py` (`MarketDataService`) while preserving `MarketDataEngine` quality/freshness gates and `ProviderManager` routing/fallback behavior.
- Migrated signal, tracker, scanner, and callback candle retrieval to the service boundary. Scanner retains explicit provider-manager selection only to preserve provider-readiness semantics and injects it into the engine used by the service.
- Verified TASK-036 implementation head `6174463174d8c6c4ad513896ad7ff96847e85edc` through completed CI gates and successful Railway commit status.
- Added ADR-007 documenting the canonical application-facing market-data boundary.
- TASK-037: repository-wide inspection found the dormant `get_latest_oanda_price` surface in `data/market_data.py` with no production caller.
- TASK-037: removed the dormant direct OANDA price surface and its now-unused dependency while preserving the canonical OANDA candle path.
- TASK-037: implementation commit `65ea6150fa23895ad5655e59dbc9349945e67f96` passed GitHub Actions run `34719290035`; Railway commit status was successful.
- TASK-038: removed the unused lower-level `DataManager` / `ExplicitProviderManager` compatibility architecture after repository-wide reference inspection and successful CI verification.
- TASK-039: removed unused provider-specific market-data adapter methods after repository-wide caller inspection.
- TASK-040: verified ProviderManager lifecycle/state semantics and added regression coverage for injected provider retention and rebinding.
- TASK-041: verified the MarketDataEngine output/compatibility surface and retained the tested DataFrame contract because repository evidence did not justify removal.
- TASK-042: hardened the MarketDataService construction boundary so scanner no longer directly constructs MarketDataEngine; focused compatibility coverage and production gates passed.
- TASK-043: audited Telegram market-data service lifetime and found repeated service construction would discard ProviderManager cache/cooldown/failure state between application calls.
- TASK-043: changed Telegram signal, callback, and tracker paths to reuse one application-scoped MarketDataService while intentionally keeping scanner provider-readiness composition separate.
- TASK-043: added application-lifetime/state regression coverage and recorded the decision in ADR-008.
- TASK-043: implementation head `abe8e0db1d98e3c7ac3d6ffd09330604463656d9` passed Production Readiness run `34721145994`, Production Activation Validation run `34721150684`, and Production E2E Contract Gate run `34721147175`.
- TASK-044: selected the next evidence-backed Phase 2 audit: scanner `ProviderManager` lifetime and provider-readiness boundary. No implementation is assumed until all `scan_market()` callers, lifecycle/configuration behavior, and ProviderManager state contracts are inspected.
- Synchronized engineering state through TASK-044 selection.
