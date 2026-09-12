# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `e72194018956998f42b16034e40a26a3a9d9732d`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-018 — Durable Forex Worker Processing Queue Contract
- Last Completed Task: TASK-017 — Remove Residual Non-Forex Worker Workload
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Current TASK-018 queue changes are not yet production-verified.
- Broken Tests: None known; current queue changes are awaiting current-head GitHub Actions verification.
- CI Status: TASK-017 final-gate run `34704118418`, job `103580948161`, completed successfully. TASK-018 current head requires fresh CI verification.
- Deployment Status: Prior Railway live health and restart/recovery remain verified for the previously deployed path. Current queue changes have not been promoted through the documented production verification path.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. A durable/idempotent worker processing queue contract now exists; distributed transport integration and deployment-grade recovery remain unverified.
- Production Readiness: `VERIFIED` for the previously observed deployment path; TASK-018 has not yet changed the production verification status.
- Last Checkpoint: `e72194018956998f42b16034e40a26a3a9d9732d` — TASK-018 testing checkpoint.
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

### TASK-018 — TESTING
Durable Forex Worker Processing Queue Contract. `worker/queue.py` provides SQLite-backed persistence and explicit queue lifecycle states; `tests/test_worker_queue.py` covers idempotency, priority ordering, terminal states, cancellation/timeout, and persistence across connections. Current-head CI verification is pending.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
