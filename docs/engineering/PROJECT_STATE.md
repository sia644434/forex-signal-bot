# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `d3bc5157a60032eacf8866a810c1d3edf98edd41`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-028 — Minimize Unauthenticated PC Worker Health Information Exposure
- Last Completed Task: TASK-027 — PC Worker Heartbeat Freshness Contract
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. TASK-028 changes the worker's unauthenticated health response and therefore requires current-head CI before verification is claimed.
- Broken Tests: None known; current TASK-028 CI is pending.
- CI Status: TASK-027 verification is complete. TASK-028 implementation commits are pushed; current-head verification is pending.
- Deployment Status: The previously verified Railway deployment path remains healthy. TASK-028 has not yet been promoted/independently live-verified.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, and heartbeat freshness are verified. TASK-028 now minimizes unauthenticated worker health exposure while retaining authenticated detailed heartbeat data. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the previously observed deployment path. TASK-028 is implementation-complete but not yet CI-verified or separately live-verified.
- Last Checkpoint: `d3bc5157a60032eacf8866a810c1d3edf98edd41` — synchronized engineering state through TASK-028 implementation.
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
Durable Forex Worker Processing Queue Contract. SQLite-backed queue, lifecycle states, idempotency, priority ordering, persistence, and dispatcher integration verified.

### TASK-019 — VERIFIED
Forex Worker Queue Crash-Recovery Contract. Stale `RUNNING` recovery and deterministic regression coverage verified.

### TASK-020 — VERIFIED
Activate Forex Worker Queue Crash Recovery. Per-job-timeout-aware recovery is activated at dispatcher initialization and verified.

### TASK-021 — VERIFIED
Forex Worker Queue Persistence Configuration Boundary. Central queue path/recovery-grace configuration and dispatcher construction are verified.

### TASK-022 — VERIFIED
Wire Heavy Forex Worker Through the Application Service Boundary. Optional non-critical worker processing service is backed by the queue-aware dispatcher and centrally configured worker transport.

### TASK-023 — VERIFIED
Verify and harden the real heavy-Forex workload routing boundary. No real Forex domain caller currently submits heavy jobs because Phase 9 Backtesting / Simulation is not started; no speculative caller was introduced.

### TASK-024 — VERIFIED
PC Worker Authenticated Heartbeat Contract. Authenticated heartbeat endpoint/client contract and valid/invalid authentication coverage are complete.

### TASK-025 — VERIFIED
Worker Processing Health/Readiness Contract. Worker readiness states are exposed through the application boundary and covered by regression tests.

### TASK-026 — VERIFIED
Worker Heartbeat Observability. Worker identity/timestamp observability is exposed through worker processing health.

### TASK-027 — VERIFIED
PC Worker Heartbeat Freshness Contract. Configurable maximum heartbeat age is enforced dynamically; expired, malformed, or timestamp-missing READY heartbeats become `STALE`. Current-head CI and Railway status are successful.

### TASK-028 — IMPLEMENTED / VERIFICATION PENDING
Minimize Unauthenticated PC Worker Health Information Exposure. The public `/health` endpoint now returns only `{"status":"READY"}` while detailed worker identity/runtime metadata remains behind authenticated heartbeat transport. Regression coverage was added. Current-head CI is pending.

## Next Task Selection
After TASK-028 CI verification, select the next task only from concrete repository evidence. Do not invent a task merely to increment the task number.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
