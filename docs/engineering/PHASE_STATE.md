# Phase State

## Phase 1 — Baseline Stabilization / Reliability Hardening
Status: COMPLETE
Evidence: Baseline contract regressions were fixed and production verification was completed through live health and restart/recovery evidence.

## Phase 2 — Core Architecture
Status: IN_PROGRESS
Active Task: TASK-044 — Scanner ProviderManager Lifetime and Readiness Boundary Audit
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
- TASK-038 removed the unused lower-level `DataManager` / `ExplicitProviderManager` compatibility architecture after repository-wide reference inspection.
- TASK-039 removed unused provider-specific market-data adapter methods while preserving the provider-neutral canonical path.
- TASK-040 verified ProviderManager lifecycle and retained-injected-provider semantics with regression coverage.
- TASK-041 verified the MarketDataEngine output surface and retained the DataFrame compatibility contract because focused tests still cover it.
- TASK-042 hardened the MarketDataService construction boundary so scanner no longer constructs MarketDataEngine directly.
- TASK-043 established application-scoped MarketDataService lifetime for Telegram signal, callback, and tracker paths so ProviderManager state is preserved across calls.

### TASK-043 — VERIFIED
MarketDataService Lifetime and Application Composition Hardening.
Evidence:
- Repeated application-level `MarketDataService()` construction was identified as a state-lifetime reliability risk because it recreates the engine/manager state.
- Telegram signal, callback, and tracker paths were changed to reuse the application-scoped service.
- Scanner was intentionally kept separate because its provider-readiness selection is a distinct contract.
- Regression coverage was added for application-scoped lifetime/state reuse.
- Production Readiness run `34721145994`, Production Activation Validation run `34721150684`, and Production E2E Contract Gate run `34721147175` all completed successfully for implementation head `abe8e0db1d98e3c7ac3d6ffd09330604463656d9`.

### TASK-044 — IN PROGRESS
Scanner ProviderManager Lifetime and Readiness Boundary Audit.
Objective: Determine whether the scanner's per-invocation `ProviderManager` construction is intentional and correct, or whether repeated scans unnecessarily discard provider cache/cooldown/failure state. Preserve runtime provider-readiness semantics and do not introduce shared state until repository evidence justifies it.
Initial evidence:
- `scan_market()` currently builds a fresh provider manager on each invocation.
- `_build_provider_manager()` derives the configured provider list dynamically through `ProviderFactory`.
- `callbacks.py` directly invokes `scan_market()`, so repeated user scans can create fresh manager state.
- The audit must inspect all current callers, any scheduler/background lifecycle, provider configuration-change behavior, and existing ProviderManager cooldown/cache tests before implementation.

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
Evidence: Existing CI and production verification gates are green for verified implementation heads. TASK-043 lifecycle regression, readiness, activation, and E2E contract gates completed successfully.

## Phase 12 — Deployment
Status: COMPLETE
Evidence: Railway live health and restart/recovery verification completed for the intentional Railway-connected fork.

## Phase 13 — Final Production Audit
Status: NOT_STARTED

## Roadmap Rule
Work phases sequentially. Completing Phase 1 does not skip directly to Phase 12 or Phase 13. Phase 2 must be completed before Phase 3, and so on, unless an explicit evidence-backed dependency requires a temporary cross-phase check.
