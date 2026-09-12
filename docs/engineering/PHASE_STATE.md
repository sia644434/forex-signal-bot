# Phase State

## Phase 1 — Baseline Stabilization / Reliability Hardening
Status: COMPLETE
Evidence: Baseline contract regressions were fixed and production verification was completed through live health and restart/recovery evidence.

## Phase 2 — Core Architecture
Status: IN_PROGRESS
Active Task: TASK-038 — Market Data Lower-Level Facade / Alternate Ownership Audit
Objective: Complete only architecture work that directly supports the Forex platform and its heavy Forex processing path.

### Completed Evidence
- TASK-004 through TASK-013 were verified and closed through GitHub Actions.
- TASK-014 removed the accidental local coding-agent/Ollama worker architecture and verified the application-only worker boundary.
- TASK-015 hardened worker job lifecycle validation, timeout, cancellation, active-job tracking, and completed-job idempotency.
- TASK-017 removed the residual `multi_agent_analysis` workload, executor, tests, and documentation references.
- TASK-018 through TASK-023 established durable Forex worker queue, crash recovery, persistence configuration, application service composition, and the real heavy-Forex routing boundary without speculative callers.
- TASK-024 through TASK-031 established authenticated heartbeat, readiness, freshness, least-privilege health exposure, authenticated job requests, readiness-gated dispatch, and worker observability.
- TASK-032 consolidated Telegram ownership under `services/telegram/`.
- TASK-033 consolidated Decision/Risk ownership under canonical `analysis/` engines.
- TASK-034 removed the unused alternate analysis adapter/registry/orchestrator/contracts architecture.
- TASK-035 audited the `ai/` package and established that it is dormant/unwired future Phase 6 capability and not an active trading architecture.
- TASK-036 consolidated production Telegram market-data candle retrieval behind `MarketDataService` while preserving `MarketDataEngine` quality/freshness gates and `ProviderManager` routing.
- TASK-037 removed the dormant direct OANDA price surface after repository-wide reference inspection found no production caller. CI and Railway status were successful for the verified implementation commit.

### TASK-037 — VERIFIED
Dormant Direct OANDA Price Surface Audit.
Evidence:
- `get_latest_oanda_price` had no production caller.
- The direct OANDA price method and its now-unused factory dependency were removed.
- The canonical OANDA candle path remains intact.
- GitHub Actions run `34719290035` completed successfully for commit `65ea6150fa23895ad5655e59dbc9349945e67f96`.
- Railway commit status for that commit is `success`.

### TASK-038 — IN PROGRESS
Market Data Lower-Level Facade / Alternate Ownership Audit.
Objective: Verify whether `DataManager`, `ExplicitProviderManager`, and their compatibility paths are still required now that `MarketDataService` is the canonical application-facing boundary.
Evidence:
- `DataManager(` repository search found construction only in tests.
- `ExplicitProviderManager` is referenced by `DataManager` and focused tests, with no production caller found.
- `MarketDataService` still supports a lower-level `DataManager` path that production callers do not use.
Constraint: Do not delete compatibility contracts until repository references, tests, and externally meaningful behavior are fully checked.

## Phase 3 — Telegram Bot
Status: PARTIALLY_COMPLETE

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
Evidence: Dependency security audit and production runtime verification are complete; broader security hardening remains a later roadmap phase/task. Worker endpoint hardening was handled as evidence-backed Phase 2 work.

## Phase 11 — Testing
Status: IN_PROGRESS
Evidence: Existing CI and production verification gates are green for verified implementation heads. TASK-037's full test workflow completed successfully.

## Phase 12 — Deployment
Status: COMPLETE
Evidence: Railway live health and restart/recovery verification completed for the intentional Railway-connected fork.

## Phase 13 — Final Production Audit
Status: NOT_STARTED

## Roadmap Rule
Work phases sequentially. Completing Phase 1 does not skip directly to Phase 12 or Phase 13. Phase 2 must be completed before Phase 3, and so on, unless an explicit evidence-backed dependency requires a temporary cross-phase check.
