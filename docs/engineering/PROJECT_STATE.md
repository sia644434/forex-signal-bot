# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `c795ec81279e1e03565a7393c46a349d6030319f`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-022 — Wire Heavy Forex Worker Through the Application Service Boundary
- Last Completed Task: TASK-021 — Forex Worker Queue Persistence Configuration Boundary
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. TASK-022 changes are not yet production-verified.
- Broken Tests: None known; TASK-022 current-head GitHub Actions verification is pending.
- CI Status: TASK-019 through TASK-021 were verified on current head `923d586b07cce1941723daa7faf20c330a435423`; TASK-022 has a new head and requires fresh CI verification.
- Deployment Status: Prior Railway live health and restart/recovery remain verified for the previously deployed path. Current TASK-022 changes have not been promoted through the documented production verification path.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. The durable queue, timeout-aware crash recovery, and central queue configuration are verified. TASK-022 adds the missing application composition boundary for heavy-worker processing; production transport deployment remains unverified.
- Production Readiness: `VERIFIED` for the previously observed deployment path; current TASK-022 changes have not yet been production-verified.
- Last Checkpoint: `c795ec81279e1e03565a7393c46a349d6030319f` — TASK-022 implementation checkpoint.
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

### TASK-022 — IMPLEMENTED / TESTING
Wire Heavy Forex Worker Through the Application Service Boundary. The application now composes an optional non-critical worker processing service backed by the queue-aware dispatcher and centrally configured worker transport. Current-head CI verification is pending.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
