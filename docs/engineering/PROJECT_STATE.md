# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `ecd5bc11188238ad7205c1a043e74a1ce6d5fdfe`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: Next evidence-backed Phase 2 task selection after TASK-044
- Last Completed Task: TASK-044 — Scanner ProviderManager Lifetime and Readiness Boundary Audit
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Phase 2 still has remaining evidence-backed architecture work before later phases are selected.
- Broken Tests: None known for the verified TASK-044 implementation head.
- CI Status: TASK-044 implementation commits `680fc4cd447d770fb7013563d0d538a04e8cc4d2`, `99dc8679680590d96641e574b00716f637b4988d`, and `7180828f4c3b12e7bb30588b614941cc662c0154` completed Final Integration Gate `34721606858`, Production Activation Validation `34721606855`, and Production E2E Contract Gate `34721606841` successfully. Engineering state is now synchronized through the documentation commits.
- Deployment Status: No new live production smoke is claimed solely from TASK-044 or the documentation synchronization commits. The previously verified Railway path remains the production deployment evidence.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, heartbeat freshness, minimal public health, authenticated job-request hardening, readiness-gated dispatch, Telegram ownership consolidation, Decision/Risk ownership consolidation, Analysis ownership consolidation, AI ownership auditing, market-data application-boundary consolidation, dormant direct OANDA price-surface removal, lower-level market-data facade removal, provider-specific adapter removal, ProviderManager lifecycle contract hardening, MarketDataEngine output-surface compatibility audit, MarketDataService construction-boundary hardening, application-scoped MarketDataService lifetime hardening, and application-scoped scanner ProviderManager lifetime hardening are recorded. The `ai/` package is dormant/unwired and reserved for Phase 6; it is not part of the active production trading flow. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed Railway deployment path. No new live smoke is claimed for TASK-044 or documentation-only synchronization commits.
- Last Checkpoint: `7180828f4c3b12e7bb30588b614941cc662c0154` — TASK-044 verified implementation checkpoint.
- Last State Update: 2026-09-13

## Phase 2 — Core Architecture

### Completed
TASK-004 through TASK-044 are verified according to the persistent engineering state, except TASK-016 which remains removed from the roadmap.

### TASK-043 — VERIFIED
MarketDataService Lifetime and Application Composition Hardening. Telegram signal, callback, and tracker paths reuse one application-scoped `MarketDataService`, preserving provider manager/cache/cooldown/failure state across application calls. Scanner was intentionally separate because its explicit provider-readiness selection was a distinct contract. Regression coverage was added. Implementation head `abe8e0db1d98e3c7ac3d6ffd09330604463656d9` passed Production Readiness, Production Activation Validation, and Production E2E Contract Gate.

### TASK-044 — VERIFIED
Scanner ProviderManager Lifetime and Readiness Boundary Audit. The scanner now retains its ProviderManager in `Application.bot_data` so repeated Telegram scans preserve provider instances, cooldowns, and failure state without introducing process-global state. Provider readiness is recalculated on every retrieval and the retained manager is refreshed through `set_providers()`. Regression coverage verifies reuse and readiness changes. Implementation commits `680fc4cd447d770fb7013563d0d538a04e8cc4d2`, `99dc8679680590d96641e574b00716f637b4988d`, and `7180828f4c3b12e7bb30588b614941cc662c0154` passed the recorded CI/activation/E2E gates.

## Next Task Selection
Phase 2 remains active. Select the next task only after a fresh evidence-backed repository audit identifies a concrete correctness, reliability, security, observability, deployment, or recovery gap. Do not invent speculative feature work or skip ahead to Phase 3.

## Repository Mapping Decision
- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
