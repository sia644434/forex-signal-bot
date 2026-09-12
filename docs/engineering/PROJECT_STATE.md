# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-006 — Shutdown Lifecycle Contract Hardening
- Last Completed Task: TASK-005 — Application Lifecycle Contract Hardening
- Next Task: Verify TASK-006 CI, then continue Phase 2 architecture mapping.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository.
- Broken Tests: None known for TASK-005; TASK-006 CI verification is pending.
- CI Status: TASK-005 is green across test, activation, readiness, dependency-audit, and final-gate workflows. TASK-006 has been committed and is awaiting CI evidence.
- Deployment Status: Railway live deployment health and restart/recovery remain verified for the previously deployed commit.
- Architecture Status: Phase 2 active; ServiceManager and Application lifecycle contracts are closed, and ShutdownManager lifecycle contracts are now the active boundary.
- Production Readiness: `VERIFIED` for the previously observed deployment path; future runtime-affecting changes must repeat appropriate live gates.
- Last Checkpoint: Phase 2 TASK-006 implementation checkpoint.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### TASK-004 — COMPLETE
ServiceManager lifecycle contracts were added and verified. The contract suite covers registration uniqueness, startup rollback, non-critical startup degradation, reverse-order shutdown, shutdown-failure isolation, and health-failure isolation.

Implementation:
- `2e38e857dbed219c41c8b4339434bb3deae66d6ce` — `test: add service manager lifecycle contracts`
- Added `tests/test_service_manager_contract.py` with six focused contract tests.
- GitHub Actions `34698627396` / job `103566339790`: success.

### TASK-005 — COMPLETE
Application lifecycle contract hardening is verified and closed.

Implementation:
- `79b14578f69254c4748c58e2a9ce4672bf850aeb` — initial lifecycle contract tests.
- `926fc1a63307107fcfd2b4bd2b487c696838d18d` — isolated lifecycle fixtures after a real-socket test leak was detected.
- Added `tests/test_application_lifecycle_contract.py` with six focused contract tests.

Verification:
- GitHub Actions Test `34698909805` / job `103567089476`: success, 366 tests passed.
- Production Activation Gate `34698909862` / job `103567089666`: success.
- Production Readiness `34698909828` / job `103567089616`: success.
- Dependency Audit `34698909815` / job `103567089540`: success.
- Final Gate `34698909812` / job `103567089502`: success, including production Docker build.
- No local execution is claimed.

### TASK-006 — IN_PROGRESS
Shutdown lifecycle contract hardening is the active Phase 2 task.

Implementation:
- `2db7c75fcfc94cf1b44de76c6a279c1c45bc1686` — `test: add shutdown manager lifecycle contracts`
- Added `tests/test_shutdown_contract.py` with four focused tests covering SIGINT/SIGTERM registration, trigger behavior, wait/unblock behavior, and idempotent triggering.

Current verification status:
- CI verification is pending for TASK-006.
- No local execution is claimed.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites.
