# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-008 — Application Shutdown Cleanup Guarantee
- Last Completed Task: TASK-007 — Application Startup Rollback Contract Hardening
- Next Task: Verify TASK-008 CI, then continue Phase 2.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository.
- Broken Tests: None known for TASK-007; TASK-008 CI verification is pending.
- CI Status: TASK-007 is green across final-gate, test, readiness, activation-validation, and dependency-audit checks. TASK-008 has been committed and is awaiting CI evidence.
- Deployment Status: Railway live deployment health and restart/recovery remain verified for the previously deployed commit.
- Architecture Status: Phase 2 active; ServiceManager, Application lifecycle, ShutdownManager, and startup rollback contracts are closed. Application shutdown cleanup is now the active boundary.
- Production Readiness: `VERIFIED` for the previously observed deployment path; future runtime-affecting changes must repeat appropriate live gates.
- Last Checkpoint: Phase 2 TASK-008 implementation checkpoint.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### Pre-TASK-004 Scope — UNKNOWN
The Phase 2 section that existed before TASK-004 was skipped during the sequential implementation pass. It is intentionally recorded as `UNKNOWN / NOT YET AUDITED`, not `COMPLETE`. It must be revisited and verified later before Phase 2 is declared complete.

### TASK-004 — COMPLETE
ServiceManager lifecycle contracts were added and verified. The contract suite covers registration uniqueness, startup rollback, non-critical startup degradation, reverse-order shutdown, shutdown-failure isolation, and health-failure isolation.

Implementation:
- `2e38e857dbed219c41c8b4339434bb61a372f040` — `test: add service manager lifecycle contracts`
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

### TASK-006 — COMPLETE
Shutdown lifecycle contract hardening is verified and closed.

Implementation:
- `2db7c75fcfc94cf1b44de76c6a279c1c45bc1686` — `test: add shutdown manager lifecycle contracts`
- Added `tests/test_shutdown_contract.py` with four focused tests covering SIGINT/SIGTERM registration, trigger behavior, wait/unblock behavior, and idempotent triggering.

Verification:
- GitHub Actions check runs for the commit completed successfully.
- Test job `103567612517`: success, including lifecycle/persistence tests, full suite, application health, imports, and syntax checks.
- No local execution is claimed.

### TASK-007 — COMPLETE
Application startup rollback contract hardening is verified and closed.

Implementation:
- `33ae66e70402d140c7ebe4437951fab2db4a98d1` — rollback services when health-server startup fails.
- `1028a219875220d71b012c8a500c9647953f5a59` — regression coverage for startup rollback.
- The contract ensures services are stopped if `HealthServer.start()` fails after service startup.

Verification:
- Final-gate `34699115514` / job `103567612470`: success, including full test suite and production Docker build.
- Test `34699115551` / job `103567612517`: success.
- Readiness `34699115528` / job `103567612438`: success.
- Activation-validation `34699115556` / job `103567612531`: success.
- Dependency-audit `34699115544` / job `103567612573`: success.
- No local execution is claimed.

### TASK-008 — IN_PROGRESS
Application shutdown cleanup guarantee is now the active Phase 2 task.

Implementation:
- `08716e48bb2e3ffcd38e59f027ea3c61ad507615` — guarantee service cleanup during application shutdown.
- `7aafd9f08e1a2423befa9d23d89d429b9b059888` — regression coverage for shutdown cleanup.
- `Application.stop()` guarantees `services.stop_all()` through `finally` if `HealthServer.stop()` raises.

Current verification status:
- CI verification is pending for TASK-008.
- No local execution is claimed.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites.
