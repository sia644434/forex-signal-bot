# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `f06a6424fa20af665919da9e72618c227c7839f7`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-023 — Verify and harden the real heavy-Forex workload routing boundary
- Last Completed Task: TASK-022 — Wire Heavy Forex Worker Through the Application Service Boundary
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. TASK-023 is an evidence-gathering/hardening task and must not be marked complete until an actual heavy-Forex operation is shown to route through the application worker boundary or a concrete repository gap is identified.
- Broken Tests: None known on the verified TASK-022 head.
- CI Status: TASK-022 head `7a96afddaa46aefe9bb5aa990f40522905754572` passed Test, Final Integration Gate, Production Readiness, Production Activation Gate, Production Activation Validation, Production E2E Contract Gate, and Security Audit.
- Deployment Status: Prior Railway live health and restart/recovery remain verified for the previously deployed path. TASK-022 was verified by CI but has not been independently claimed as a live production deployment.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. The durable queue, timeout-aware crash recovery, central queue configuration, and application composition boundary are verified. The next architectural check is whether real heavy-Forex domain operations actually use this boundary rather than only exposing a generic service.
- Production Readiness: `VERIFIED` for the previously observed deployment path; current TASK-022 changes are CI-verified but not independently live-production-verified.
- Last Checkpoint: `f06a6424fa20af665919da9e72618c227c7839f7` — verified TASK-022 and corrected engineering state evidence.
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
Wire Heavy Forex Worker Through the Application Service Boundary. The application composes an optional non-critical worker processing service backed by the queue-aware dispatcher and centrally configured worker transport. Commit `7a96afddaa46aefe9bb5aa990f40522905754572` passed all seven push workflows: Test, Final Integration Gate, Production Readiness, Production Activation Gate, Production Activation Validation, Production E2E Contract Gate, and Security Audit.

### TASK-023 — IN_PROGRESS
Verify and harden the real heavy-Forex workload routing boundary. Inspect the actual backtesting, historical-data, simulation, batch-calculation, scanning, and other expensive Forex paths and determine which must route through `WorkerProcessingService`/`WorkerDispatcher`. Implement only an evidence-backed missing integration; do not create speculative wrappers or unrelated architecture.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
