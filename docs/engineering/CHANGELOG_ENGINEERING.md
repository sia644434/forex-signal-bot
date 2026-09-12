# Engineering Changelog

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
- TASK-038: started an evidence-backed audit of the lower-level `DataManager` / `ExplicitProviderManager` compatibility surface. Repository-wide searches found no production construction/caller; compatibility paths remain under review before any removal.
- Synchronized engineering state through TASK-038 selection.
