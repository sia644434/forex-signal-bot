# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `a9dbd5a4822580a6a2795531a8a74b332355279d`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-033 — Decision/Risk/Strategy Architecture Ownership Audit
- Last Completed Task: TASK-033 — Decision/Risk/Strategy Architecture Ownership Audit
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Phase 2 still has remaining evidence-backed architecture work before later phases are selected.
- Broken Tests: None known.
- CI Status: TASK-033 Final Integration Gate `34715036954`, job `103610652082`, completed successfully.
- Deployment Status: Commit `a9dbd5a4822580a6a2795531a8a74b332355279d` has successful Railway deployment status. Previously verified live production health/restart evidence remains valid for the deployed path.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, heartbeat freshness, minimal public health, authenticated job-request hardening, readiness-gated dispatch, Telegram ownership consolidation, and Decision/Risk ownership consolidation are verified. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed Railway deployment path. TASK-033 itself is CI-verified and has successful Railway commit status.
- Last Checkpoint: `a9dbd5a4822580a6a2795531a8a74b332355279d` — TASK-033 implementation and architecture documentation checkpoint.
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

## Next Task Selection
Select the next task only from concrete repository evidence after TASK-033. Do not invent a task merely to increment the task number. Continue Phase 2 until its evidence-backed core-architecture scope is complete.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
