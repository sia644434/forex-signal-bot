# Engineering Changelog

## 2026-09-13
- TASK-048: identified a real Telegram journal concurrency gap: `add_entry()` and `close_entry()` performed read-modify-write across separate `JournalStore` lock scopes, allowing overlapping callbacks to lose updates.
- TASK-048: changed `journal.add_entry()` to use the store's atomic append path and added `JournalStore.update_at()` for atomic indexed mutation under one lock.
- TASK-048: added concurrency regression coverage with 40 simultaneous additions across 8 workers and verified all entries remain present.
- TASK-048: implementation head `b9157db60e52fb975c634f6f0abb2585f7f36de4` passed 7 successful GitHub Actions workflows: Test, Production Readiness, Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, and Final Integration Gate. Railway commit status is successful.
- TASK-047: completed the Telegram journal ordering/persistence contract audit and corrected the chronological storage/public newest-first representation boundary, including close-by-index semantics.
- TASK-047: implementation head `2e6bef7ec971501cd3573b21544c22f721253f99` passed the required CI/security/activation/readiness/E2E/deployment gates.
- Synchronized persistent engineering state after TASK-048 verification. Phase 2 remains active pending selection of the next evidence-backed architecture/reliability gap.

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
- TASK-037 removed the dormant direct OANDA price surface and preserved the canonical OANDA candle path.
- TASK-038 removed the unused lower-level `DataManager` / `ExplicitProviderManager` compatibility architecture.
- TASK-039 removed unused provider-specific market-data adapter methods after repository-wide caller inspection.
- TASK-040 verified ProviderManager lifecycle/state semantics and added regression coverage for injected provider retention and rebinding.
- TASK-041 verified the MarketDataEngine output/compatibility surface and retained the tested DataFrame contract because repository evidence did not justify removal.
- TASK-042 hardened the MarketDataService construction boundary so scanner no longer directly constructs MarketDataEngine.
- TASK-043 changed Telegram signal, callback, and tracker paths to reuse one application-scoped MarketDataService.
- TASK-044 changed scanner ProviderManager lifetime to application-scoped storage while preserving dynamic provider-readiness refresh.
- Synchronized engineering state through TASK-044 selection.
