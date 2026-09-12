# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `85a6999042b687583268e3bea542d86406e741d6`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-024 — PC Worker Authenticated Heartbeat Contract
- Last Completed Task: TASK-023 — Verify and harden the real heavy-Forex workload routing boundary
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. TASK-024 is CI-pending and has not been marked verified.
- Broken Tests: None known; the new heartbeat test is awaiting GitHub Actions completion.
- CI Status: Commit `32ed161e6ae03f41c03de75db56c225d3db10f88` has the seven push workflows running; the Production Readiness run `34706978390` was still `in_progress` at the last check.
- Deployment Status: Prior Railway live health and restart/recovery remain verified for the previously deployed path. The heartbeat changes have not been independently claimed as live production deployed.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. The durable queue, timeout-aware crash recovery, central queue configuration, and application composition boundary are verified. TASK-023 confirmed there is currently no real heavy-Forex domain caller to wire because Phase 9 Backtesting / Simulation is not started; no speculative caller was introduced. TASK-024 adds the next concrete worker transport reliability boundary: authenticated readiness heartbeat.
- Production Readiness: `VERIFIED` for the previously observed deployment path; current TASK-024 changes are CI-pending and not independently live-production-verified.
- Last Checkpoint: `85a6999042b687583268e3bea542d86406e741d6` — recorded TASK-023 audit completion and TASK-024 heartbeat implementation state.
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
Remove Residual Non-Forex Worker Workload. Final-gate run `34704118418`, job `103580948161`, completed successfully with compile, runtime safety tests, full suite, and production Docker build passing.

### TASK-018 — VERIFIED
Durable Forex Worker Processing Queue Contract. SQLite-backed queue, lifecycle states, idempotency, priority ordering, persistence, and dispatcher integration verified by the queue/integration gates.

### TASK-019 — VERIFIED
Forex Worker Queue Crash-Recovery Contract. Stale `RUNNING` recovery and deterministic regression coverage verified on current head.

### TASK-020 — VERIFIED
Activate Forex Worker Queue Crash Recovery. Per-job-timeout-aware recovery is activated at dispatcher initialization and verified by current-head CI.

### TASK-021 — VERIFIED
Forex Worker Queue Persistence Configuration Boundary. Central queue path/recovery-grace configuration and dispatcher construction are verified by current-head CI.

### TASK-022 — VERIFIED
Wire Heavy Forex Worker Through the Application Service Boundary. The application composes an optional non-critical worker processing service backed by the queue-aware dispatcher and centrally configured worker transport. Commit `7a96afddaa46aefe9bb5aa990f40522905754572` passed all seven push workflows.

### TASK-023 — VERIFIED
Verify and harden the real heavy-Forex workload routing boundary. Repository evidence shows worker-owned heavy Forex executors/contracts, but no real Forex domain caller currently submits `JobRequest` through `WorkerProcessingService`. Phase 9 — Backtesting / Simulation is `NOT_STARTED`, so no speculative caller was created. The generic worker boundary is therefore retained for the future real Phase 9 integration.

### TASK-024 — IN PROGRESS
PC Worker Authenticated Heartbeat Contract. Added authenticated `POST /heartbeat`, a matching `PCWorkerClient.heartbeat()` method, and regression coverage for valid and invalid authentication. GitHub Actions is still running for the implementation commit and must pass before this task is marked verified.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
