# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `88e8c683ff802adc93d5f2f0cb4e4d4566d99269`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-043 — Next evidence-backed architecture audit
- Last Completed Task: TASK-042 — Market Data Service Construction Boundary Hardening
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Phase 2 still has remaining evidence-backed architecture work before later phases are selected.
- Broken Tests: None known for the verified TASK-042 implementation head.
- CI Status: TASK-042 final implementation head `e2f7f189b84d611e2806bc050ebe347766f77f4a` completed the observed Test, Production Activation Validation, Production E2E Contract Gate, and Production Readiness gates successfully.
- Deployment Status: No new live production smoke is claimed solely from the TASK-042 implementation or documentation synchronization commits. The previously verified Railway path remains the production deployment evidence.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, heartbeat freshness, minimal public health, authenticated job-request hardening, readiness-gated dispatch, Telegram ownership consolidation, Decision/Risk ownership consolidation, Analysis ownership consolidation, AI ownership auditing, market-data application-boundary consolidation, dormant direct OANDA price-surface removal, lower-level market-data facade removal, provider-specific adapter removal, ProviderManager lifecycle contract hardening, MarketDataEngine output-surface compatibility audit, and MarketDataService construction-boundary hardening are recorded. The `ai/` package is dormant/unwired and reserved for Phase 6; it is not part of the active production trading flow. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed Railway deployment path. No new live smoke is claimed for documentation-only synchronization commits.
- Last Checkpoint: `e2f7f189b84d611e2806bc050ebe347766f77f4a` — TASK-042 verified implementation checkpoint.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### Completed
TASK-004 through TASK-042 are verified according to the persistent engineering state, except TASK-016 which remains removed from the roadmap.

### TASK-041 — VERIFIED
MarketDataEngine Output-Surface and Compatibility Audit. The canonical application path remains `MarketDataService → MarketDataEngine → ProviderManager` through `get_candles_list()`. The DataFrame-returning `MarketDataEngine.get_candles()` surface remains because focused contract tests cover it and repository evidence did not justify removal. `analysis.market_structure` performs its own internal candle-to-DataFrame conversion, while `analysis/candle.py` resolves to the canonical `data.models.Candle` model.

### TASK-042 — VERIFIED
Market Data Service Construction Boundary Hardening. Scanner no longer constructs `MarketDataEngine` directly; it injects the explicit `ProviderManager` into `MarketDataService`. The service preserves direct-engine compatibility construction and rejects simultaneous `engine` and `provider_manager` injection. Focused regression coverage was added. Implementation follow-up commit `e2f7f189b84d611e2806bc050ebe347766f77f4a` passed the observed Actions gates.

## Next Task Selection
TASK-043 — perform the next evidence-backed Phase 2 architecture audit. Start from concrete repository references and contracts; prioritize correctness, reliability, security, observability, deployment, and recovery. Do not introduce speculative feature work or any local coding-agent/Ollama architecture.

## Repository Mapping Decision
- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
