# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `6fcd36d12cd8f4052a78e7fab302f29dd6c6575d`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-044 — Scanner ProviderManager Lifetime and Readiness Boundary Audit
- Last Completed Task: TASK-043 — MarketDataService Lifetime and Application Composition Hardening
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Phase 2 still has remaining evidence-backed architecture work before later phases are selected.
- Broken Tests: None known for the verified TASK-043 implementation head.
- CI Status: TASK-043 implementation head `abe8e0db1d98e3c7ac3d6ffd09330604463656d9` completed Production Readiness run `34721145994`, Production Activation Validation run `34721150684`, and Production E2E Contract Gate run `34721147175` successfully. Documentation state is synchronized through the current head.
- Deployment Status: No new live production smoke is claimed solely from the TASK-043 implementation or documentation synchronization commits. The previously verified Railway path remains the production deployment evidence.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, heartbeat freshness, minimal public health, authenticated job-request hardening, readiness-gated dispatch, Telegram ownership consolidation, Decision/Risk ownership consolidation, Analysis ownership consolidation, AI ownership auditing, market-data application-boundary consolidation, dormant direct OANDA price-surface removal, lower-level market-data facade removal, provider-specific adapter removal, ProviderManager lifecycle contract hardening, MarketDataEngine output-surface compatibility audit, MarketDataService construction-boundary hardening, and application-scoped MarketDataService lifetime hardening are recorded. The `ai/` package is dormant/unwired and reserved for Phase 6; it is not part of the active production trading flow. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed Railway deployment path. No new live smoke is claimed for documentation-only synchronization commits.
- Last Checkpoint: `abe8e0db1d98e3c7ac3d6ffd09330604463656d9` — TASK-043 verified implementation checkpoint.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### Completed
TASK-004 through TASK-043 are verified according to the persistent engineering state, except TASK-016 which remains removed from the roadmap.

### TASK-042 — VERIFIED
Market Data Service Construction Boundary Hardening. Scanner no longer constructs `MarketDataEngine` directly; it injects the explicit `ProviderManager` into `MarketDataService`. The service preserves direct-engine compatibility construction and rejects simultaneous `engine` and `provider_manager` injection. Focused regression coverage was added. Implementation follow-up commit `e2f7f189b84d611e2806bc050ebe347766f77f4a` passed the observed Actions gates.

### TASK-043 — VERIFIED
MarketDataService Lifetime and Application Composition Hardening. Telegram signal, callback, and tracker paths now reuse one application-scoped `MarketDataService`, preserving provider manager/cache/cooldown/failure state across application calls. Scanner remains intentionally separate because its explicit provider-readiness selection is a distinct contract. Regression coverage was added. Implementation head `abe8e0db1d98e3c7ac3d6ffd09330604463656d9` passed Production Readiness, Production Activation Validation, and Production E2E Contract Gate.

## Next Task Selection
TASK-044 — audit scanner `ProviderManager` lifetime and readiness semantics. Start with all `scan_market()` callers and scanner lifecycle/configuration behavior. Do not assume a shared manager is correct; preserve dynamic provider-readiness behavior unless repository evidence justifies a change. Do not introduce speculative feature work or any local coding-agent/Ollama architecture.

## Repository Mapping Decision
- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
