# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `2b65d94a6f0282f61d541481b335e7fd666b1dea`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-037 — Dormant Direct OANDA Price Surface Audit
- Last Completed Task: TASK-036 — Market Data Ownership Consolidation
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Phase 2 still has remaining evidence-backed architecture work before later phases are selected.
- Broken Tests: None known for the verified TASK-036 head.
- CI Status: TASK-036 implementation head `6174463174d8c6c4ad513896ad7ff96847e85edc` has successful completed CI gates and successful Railway commit status. The current main head is documentation-only synchronization after that verified implementation checkpoint.
- Deployment Status: TASK-036 implementation head has successful Railway commit status. No new production deployment is claimed solely from the documentation synchronization commits.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, heartbeat freshness, minimal public health, authenticated job-request hardening, readiness-gated dispatch, Telegram ownership consolidation, Decision/Risk ownership consolidation, Analysis ownership consolidation, AI ownership auditing, and market-data application-boundary consolidation are recorded. The `ai/` package is dormant/unwired and reserved for Phase 6; it is not part of the active production trading flow. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed Railway deployment path. TASK-036 is CI/deployment-status verified but does not claim a new live smoke solely from the source-repository checkpoint.
- Last Checkpoint: `6174463174d8c6c4ad513896ad7ff96847e85edc` — TASK-036 market-data ownership consolidation implementation checkpoint, followed by documentation synchronization commits.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### Pre-TASK-004 Scope — AUDITED
The repository history contains TASK-004 as the first explicitly recorded Phase 2 implementation task after TASK-003. No separate historical pre-TASK-004 task contract was recoverable from persistent engineering state. The Master Prompt's explicit core-architecture requirements are therefore treated as the governing scope; no historical task was invented.

### TASK-004 through TASK-013
Verified and closed through repository evidence and GitHub Actions.

### TASK-014 — VERIFIED
PC Worker Scope and Configuration Boundary Hardening.

### TASK-015 — VERIFIED
Worker Job Lifecycle Reliability.

### TASK-016 — REMOVED
Worker Retry and Failure Lifecycle. Removed from the roadmap because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.

### TASK-017 — VERIFIED
Remove Residual Non-Forex Worker Workload.

### TASK-018 — VERIFIED
Durable Forex Worker Processing Queue Contract.

### TASK-019 — VERIFIED
Forex Worker Queue Crash-Recovery Contract.

### TASK-020 — VERIFIED
Activate Forex Worker Queue Crash Recovery.

### TASK-021 — VERIFIED
Forex Worker Queue Persistence Configuration Boundary.

### TASK-022 — VERIFIED
Wire Heavy Forex Worker Through the Application Service Boundary.

### TASK-023 — VERIFIED
Verify and harden the real heavy-Forex workload routing boundary. No real Forex domain caller currently submits heavy jobs because Phase 9 Backtesting / Simulation is not started; no speculative caller was introduced.

### TASK-024 — VERIFIED
PC Worker Authenticated Heartbeat Contract.

### TASK-025 — VERIFIED
Worker Processing Health/Readiness Contract.

### TASK-026 — VERIFIED
Worker Heartbeat Observability.

### TASK-027 — VERIFIED
PC Worker Heartbeat Freshness Contract.

### TASK-028 — VERIFIED
Minimize Unauthenticated PC Worker Health Information Exposure.

### TASK-029 — VERIFIED
PC Worker Authenticated Job Request Boundary Hardening.

### TASK-030 — VERIFIED
PC Worker Readiness Enforcement at Job-Dispatch Boundary. Configured heavy-job dispatch is blocked unless the cached authenticated heartbeat is fresh and `READY`; non-ready states fail closed.

### TASK-031 — VERIFIED
Worker Observability and Operational Contract Audit. Queue/dispatcher/service operational metrics were added without exposing sensitive payload/result/error data through the public health endpoint.

### TASK-032 — VERIFIED
Telegram Architecture Ownership Audit / Consolidation. Canonical ownership is under `services/telegram/`; inactive legacy Telegram trees were removed after reference audit.

### TASK-033 — VERIFIED
Decision/Risk/Strategy Architecture Ownership Audit. Canonical ownership is `analysis/decision_engine.py` for decision logic and `analysis/risk_engine.py` for risk logic. Unused overlapping `analysis/risk_manager.py`, `risk/manager.py`, `signal_engine/`, and `strategy/` trees were removed after repository-wide reference/call-site inspection. `ARCHITECTURE_MAP.md` records the canonical ownership.

### TASK-034 — VERIFIED
Analysis Architecture Ownership Audit. The unused alternate `analysis/adapters.py`, `analysis/contracts.py`, `analysis/registry.py`, `analysis/orchestrator.py`, and obsolete `tests/test_analysis_architecture.py` were removed after repository-wide reference inspection. `analysis/full_engine.py` remains the canonical production analysis composition and `analysis/__init__.py` now exports only canonical analysis contracts/engines.

### TASK-035 — VERIFIED
AI Architecture Ownership Audit. Repository-wide reference inspection found the `ai/` package internally self-contained and not wired into the production application composition. No production/test callers construct `AIOrchestrator`, `AIProviderManager`, `AIContextBuilder`, or `OpenAIProvider`. The package is preserved as dormant future Phase 6 capability; no AI path is allowed to bypass the canonical analysis → decision → risk flow. `ARCHITECTURE_MAP.md` records the boundary.

### TASK-036 — VERIFIED
Market Data Ownership Consolidation. `services/market_data/service.py` is the canonical application-facing market-data facade. Production Telegram callers in signal, tracker, scanner, and callbacks now retrieve candles through `MarketDataService` while preserving the canonical `MarketDataEngine` quality/freshness gates. The Scanner may still construct an engine locally only to inject its explicitly selected `ProviderManager`; candle retrieval remains behind the service boundary. Implementation head `6174463174d8c6c4ad513896ad7ff96847e85edc` has successful completed CI gates and successful Railway commit status.

## Next Task Selection
TASK-037 is the evidence-backed audit of the dormant direct OANDA price surface (`get_latest_oanda_price`). Repository-wide reference inspection found no production caller. Before removal, verify all repository references/tests/documentation and ensure no canonical market-data behavior is lost. Do not invent a replacement caller or parallel market-data path.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
