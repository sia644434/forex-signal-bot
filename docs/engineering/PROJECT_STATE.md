# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `77119280bc3d9cb857edee017aeeb5bb435bc07c`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-041 — MarketDataEngine Output-Surface and Compatibility Audit
- Last Completed Task: TASK-040 — ProviderManager Lifecycle and State Contract Audit
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Phase 2 still has remaining evidence-backed architecture work before later phases are selected.
- Broken Tests: None known for the verified TASK-040 implementation head.
- CI Status: TASK-040 implementation commit `b4bfd674bf01c2fd8a1cadce62c13f273fc5d033` completed Production Activation Validation and Security Audit successfully. TASK-039 implementation commit `044ab88fb83f7f929887fb8823d67a811c67e8a5` has successful Railway commit status.
- Deployment Status: No new live production smoke is claimed solely from the TASK-040 or documentation synchronization commits. The previously verified Railway path remains the production deployment evidence.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, heartbeat freshness, minimal public health, authenticated job-request hardening, readiness-gated dispatch, Telegram ownership consolidation, Decision/Risk ownership consolidation, Analysis ownership consolidation, AI ownership auditing, market-data application-boundary consolidation, dormant direct OANDA price-surface removal, lower-level market-data facade removal, provider-specific adapter removal, and ProviderManager lifecycle contract hardening are recorded. The `ai/` package is dormant/unwired and reserved for Phase 6; it is not part of the active production trading flow. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed Railway deployment path. No new live smoke is claimed for documentation-only synchronization commits.
- Last Checkpoint: `b4bfd674bf01c2fd8a1cadce62c13f273fc5d033` — TASK-040 verified implementation checkpoint.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### Completed
TASK-004 through TASK-013, TASK-014, TASK-015, TASK-017 through TASK-040 are verified according to the persistent engineering state. TASK-016 remains removed from the roadmap.

### TASK-039 — VERIFIED
Provider-Specific Market Data Adapter Surface Audit. Provider-named compatibility methods were removed after repository evidence showed no production callers and the canonical provider-neutral path remained intact. Implementation commit `044ab88fb83f7f929887fb8823d67a811c67e8a5` has successful Railway commit status.

### TASK-040 — VERIFIED
ProviderManager Lifecycle and State Contract Audit. The documented retention behavior for injected provider instances was preserved, while focused regression coverage was added for active-priority replacement and same-name instance rebinding. Commit `b4bfd674bf01c2fd8a1cadce62c13f273fc5d033` passed Production Activation Validation and Security Audit.

### TASK-041 — IN PROGRESS
MarketDataEngine Output-Surface and Compatibility Audit. Production `MarketDataService` uses `get_candles_list()`, while `MarketDataEngine.get_candles()` remains a DataFrame-returning compatibility surface covered by focused tests. The task is to determine whether this dual surface is intentional and should be retained or whether repository evidence justifies a safe consolidation. No speculative replacement path will be introduced.

## Next Task Selection
Continue TASK-041 by auditing all current references, focused tests, and dependency boundaries around the DataFrame-returning `MarketDataEngine.get_candles()` surface. Preserve it if compatibility evidence justifies it; otherwise remove it only with complete test and import cleanup.

## Repository Mapping Decision
- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
