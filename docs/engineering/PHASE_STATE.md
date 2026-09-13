# Phase State

## Phase 1 — Baseline Stabilization / Reliability Hardening
Status: COMPLETE
Evidence: Baseline contract regressions were fixed and production verification was completed through live health and restart/recovery evidence.

## Phase 2 — Core Architecture
Status: IN_PROGRESS
Active Work: TASK-060 is verified; continue the evidence-backed analysis/reliability audit and create a new task only when a concrete repository-backed gap is demonstrated.
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
- TASK-036 consolidated production Telegram candle retrieval behind `MarketDataService` while preserving `MarketDataEngine` quality/freshness gates and `ProviderManager` routing.
- TASK-037 removed the dormant direct OANDA price surface after repository-wide reference inspection found no production caller.
- TASK-038 removed the unused lower-level `DataManager` / `ExplicitProviderManager` compatibility architecture.
- TASK-039 removed unused provider-specific market-data adapter methods while preserving the provider-neutral canonical path.
- TASK-040 verified ProviderManager lifecycle and retained-injected-provider semantics with regression coverage.
- TASK-041 verified the MarketDataEngine output surface and retained the DataFrame compatibility contract because focused tests still cover it.
- TASK-042 hardened the MarketDataService construction boundary so scanner no longer constructs MarketDataEngine directly.
- TASK-043 established application-scoped MarketDataService lifetime for Telegram signal, callback, and tracker paths.
- TASK-044 established application-scoped scanner ProviderManager lifetime while preserving dynamic provider-readiness refresh.
- TASK-045 added focused Telegram tracker lifecycle/behavior regression coverage.
- TASK-046 added focused Telegram user-state contract coverage.
- TASK-047 corrected Telegram journal ordering and persistence/index semantics.
- TASK-048 made Telegram journal mutations atomic across the full read-modify-write boundary and added concurrency regression coverage.
- TASK-049 made Telegram journal storage fail closed on unreadable/corrupt persisted JSON and added corruption regression coverage.
- TASK-050 added structural validation for syntactically valid but invalid Telegram journal JSON and regression coverage preserving the original file on rejection.
- TASK-051 added entry-level journal schema validation and regression coverage for invalid persisted entry shapes and legacy optional-field compatibility.
- TASK-052 through TASK-054 hardened partial-start cleanup, started-service shutdown tracking, and failed-cleanup retry semantics.
- TASK-055 closed the Worker Queue resource lifecycle gap by releasing the durable queue during service shutdown.
- TASK-056 isolated ProviderManager failure diagnostics per concurrent request with `ContextVar` and request-local failure tracking.
- TASK-057 fixed stale ProviderManager cooldown state surviving removal and later re-addition of providers during configuration/readiness refresh; regression coverage was added and the required gate set passed.
- TASK-058 fixed explicit-zero FreshnessPolicy threshold handling so omitted thresholds use defaults while supplied zero thresholds reach validation and are rejected; required verification passed.
- TASK-059 fixed RiskEngine asymmetry caused by interpreting the DecisionEngine's 0..100 score as zero-centered; directional strength is now symmetric around neutral score 50 and required verification passed.
- TASK-060 fixed the same score-contract asymmetry at the FullAnalysisEngine trade-quality boundary; symmetric score-pair regression coverage was added and the required verification set passed.

### Current Audit
- TASK-058 is VERIFIED.
- TASK-059 is VERIFIED.
- TASK-060 is VERIFIED.
- Continue the evidence-backed analysis/reliability audit.
- No new task is created unless a concrete repository-backed correctness, reliability, security, observability, deployment, or recovery gap is demonstrated.

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
Evidence: Existing CI and production verification gates are green for verified implementation heads. Reliability regression coverage is added only when a concrete Phase 2 defect is confirmed.

## Phase 12 — Deployment
Status: COMPLETE
Evidence: Railway live health and restart/recovery verification completed for the intentional Railway-connected fork.

## Phase 13 — Final Production Audit
Status: NOT_STARTED

## Roadmap Rule
Work phases sequentially. Completing Phase 1 does not skip directly to Phase 12 or Phase 13. Phase 2 must be completed before Phase 3, and so on, unless an explicit evidence-backed dependency requires a temporary cross-phase check.

- TASK-061 fixed the ConfidenceEngine/DecisionEngine score-contract mismatch: signed analysis component scores are normalized around neutral 50 before confidence voting, while volatility remains a separate ratio contract. Required verification passed.
