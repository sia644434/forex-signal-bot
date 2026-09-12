# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-005 — Application Lifecycle Contract Hardening
- Last Completed Task: TASK-004 — Service Lifecycle Contract Hardening
- Next Task: Complete TASK-005 CI verification, then continue Phase 2 architecture mapping.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository.
- Broken Tests: None known; TASK-005 full regression suite is currently running in GitHub Actions.
- CI Status: TASK-004 is green. TASK-005 Test workflow `34698829433` / job `103566877894` is currently in progress; lifecycle/persistence tests have passed and the full suite is running.
- Deployment Status: Railway live deployment health and restart/recovery remain verified for the previously deployed commit.
- Architecture Status: Phase 2 active; ServiceManager lifecycle contracts are closed and Application lifecycle/composition contracts are now the active boundary.
- Production Readiness: `VERIFIED` for the previously observed deployment path; future runtime-affecting changes must repeat appropriate live gates.
- Last Checkpoint: Phase 2 TASK-005 implementation checkpoint.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### TASK-004 — COMPLETE
ServiceManager lifecycle contracts were added and verified. The contract suite covers registration uniqueness, startup rollback, non-critical startup degradation, reverse-order shutdown, shutdown-failure isolation, and health-failure isolation.

Implementation:
- `2e38e857dbed219c41c8b4339434bb61a372f040` — `test: add service manager lifecycle contracts`
- Added `tests/test_service_manager_contract.py` with six focused contract tests.
- GitHub Actions `34698627396` / job `103566339790`: success.

### TASK-005 — IN_PROGRESS
Application lifecycle contract hardening is the active Phase 2 task.

Implementation:
- `79b14578f69254c4748c58e2a9ce4672bf850aeb` — `test: add application lifecycle contracts`
- Added `tests/test_application_lifecycle_contract.py` with six focused contract tests covering service/health-server ordering, critical health degradation, healthy health preservation, Telegram composition-root registration, and the `app.py` factory wrapper.

Current verification status:
- GitHub Actions Test workflow `34698829433` / job `103566877894` is in progress.
- The dedicated lifecycle/persistence test step has passed; the full test suite is still running.
- No local execution is claimed.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites.
