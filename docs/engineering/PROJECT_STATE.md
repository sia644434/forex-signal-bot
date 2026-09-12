# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-011 — Application Error Contract Hardening
- Last Completed Task: TASK-010 — Main Entrypoint Lifecycle Contract Hardening
- Next Task: Verify TASK-011 CI, then continue Phase 2 from repository evidence.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository.
- Broken Tests: None known; TASK-011 CI is pending.
- CI Status: TASK-010 is green across Test, Final Integration Gate, and Production Activation Validation. TASK-011 has been committed and is awaiting CI evidence.
- Deployment Status: Railway live deployment health and restart/recovery remain verified for the previously deployed commit.
- Architecture Status: Phase 2 active; ServiceManager, Application lifecycle, ShutdownManager, startup rollback, shutdown cleanup, HealthServer lifecycle, and main entrypoint lifecycle contracts are covered. Error contract coverage is now the active boundary.
- Production Readiness: `VERIFIED` for the previously observed deployment path; future runtime-affecting changes must repeat appropriate live gates.
- Last Checkpoint: Phase 2 TASK-010 verification; TASK-011 implementation started.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### Pre-TASK-004 Scope — UNKNOWN
The Phase 2 section that existed before TASK-004 was skipped during the sequential implementation pass. It is intentionally recorded as `UNKNOWN / NOT YET AUDITED`, not `COMPLETE`. It must be revisited and verified later before Phase 2 is declared complete.

### TASK-004 — COMPLETE
ServiceManager lifecycle contracts were added and verified. The contract suite covers registration uniqueness, startup rollback, non-critical startup degradation, reverse-order shutdown, shutdown-failure isolation, and health-failure isolation.

### TASK-005 — COMPLETE
Application lifecycle contract hardening is verified and closed, including startup/shutdown ordering, health aggregation, composition-root registration, and isolated lifecycle fixtures.

### TASK-006 — COMPLETE
Shutdown lifecycle contract hardening is verified and closed, covering SIGINT/SIGTERM registration, trigger behavior, wait/unblock behavior, and idempotent triggering.

### TASK-007 — COMPLETE
Application startup rollback contract hardening is verified and closed. Services are rolled back if `HealthServer.start()` fails after service startup.

### TASK-008 — COMPLETE
Application shutdown cleanup guarantee is verified and closed. `Application.stop()` guarantees service cleanup through `finally` if `HealthServer.stop()` raises.

Verification:
- Final-gate `34699763599` / job `103569325433`: success.
- Activation-gate `34699763592` / job `103569325284`: success.
- Readiness `34699763622` / job `103569325273`: success.
- Dependency-audit `34699763583` / job `103569325266`: success.
- Activation-validation `34699763626` / job `103569325282`: success.

### TASK-009 — COMPLETE
HealthServer lifecycle contract hardening is verified and closed. Focused coverage was added for start/stop idempotence, invalid ports, malformed health payloads, and existing HTTP health behavior.

Verification:
- The same green gate set above ran on head `086b872bfbe06cd00c5af0e0e7ab361e34a17e7f`, which included TASK-009.

### TASK-010 — COMPLETE
Main entrypoint lifecycle contract hardening is verified and closed.

Implementation:
- `b90c31c694034838f8752e375fb8fc222c61fba4` — `test: add main lifecycle integration contracts`
- Added `tests/test_main_lifecycle_contract.py` covering normal lifecycle ordering and startup-failure behavior.

Verification:
- Test workflow `34699973369` / job `103569881919`: success, including lifecycle/persistence tests, full test suite, application health, imports, and syntax checks.
- Final Integration Gate `34699973444` / job `103569882107`: success, including compile, runtime safety tests, full suite, and production Docker build.
- Production Activation Validation `34699973428` / job `103569882020`: success.
- No local execution claimed.

### TASK-011 — IN_PROGRESS
Application Error Contract Hardening.

Evidence:
- `core/errors.py` defines the application/domain error hierarchy, stable error codes, details payload, and centralized `handle_exception()` boundary.
- Prior repository search did not show focused contract coverage for this boundary.
- `44aac8eaab94e99bb340500cce473b1350abd183` — `test: add application error contracts`
- Added `tests/test_error_contract.py` covering message/details preservation, stable hierarchy/codes, requested log level routing, and fallback logging behavior.

Current verification:
- CI pending for TASK-011.
- No local execution claimed.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites.
