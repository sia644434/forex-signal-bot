# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `ae2a0d4112447626bf0e3a45d69db937b09bb050`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-028 — next evidence-backed Phase 2 gap selection
- Last Completed Task: TASK-027 — PC Worker Heartbeat Freshness Contract
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Current source-head CI has seven completed push workflow runs for `316391aa4440d8ca2d31a0d11887bfa2482070b4`; the explicitly inspected Production E2E Contract Gate and Production Activation Validation are successful.
- Broken Tests: None known.
- CI Status: TASK-027 verification completed at current-head CI level; commit `316391aa4440d8ca2d31a0d11887bfa2482070b4` has seven completed push workflow runs, including successful Production E2E Contract Gate `34709726285` and Production Activation Validation `34709726258`.
- Deployment Status: The commit `316391aa4440d8ca2d31a0d11887bfa2482070b4` has a successful Railway deployment status. Prior live health and restart/recovery evidence remains valid for the verified deployment path.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, and heartbeat freshness are verified. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed deployment path. TASK-027 is CI-verified; its Railway status is successful. A fresh manual live smoke is only required again when a later change materially affects runtime health/deployment behavior.
- Last Checkpoint: `ae2a0d4112447626bf0e3a45d69db937b09bb050` — synchronized engineering state through TASK-027.
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

## Next Task Selection
TASK-028 must be selected only after repository evidence identifies a concrete remaining Phase 2 correctness, reliability, security, observability, deployment, or recovery gap. Do not invent a task merely to increment the task number.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
