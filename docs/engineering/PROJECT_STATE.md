# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-004 — Service Lifecycle Contract Hardening
- Last Completed Task: TASK-003 — Establish deployment and runtime verification evidence
- Next Task: Verify lifecycle contracts through GitHub Actions, then continue Phase 2 architecture mapping.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository.
- Broken Tests: None known; TASK-004 tests are newly added and awaiting CI execution.
- CI Status: Previous production/integration/security/live verification gates are green; the new TASK-004 commit has not yet produced a workflow result.
- Deployment Status: Railway live deployment health and restart/recovery remain verified for the previously deployed commit.
- Architecture Status: Phase 2 active; application composition and ServiceManager lifecycle contracts are the first targeted architecture boundary.
- Production Readiness: `VERIFIED` for the previously observed deployment path; future runtime-affecting changes must repeat appropriate live gates.
- Last Checkpoint: Phase 2 TASK-004 implementation checkpoint.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

TASK-004 targets the concrete lifecycle boundary in `core/service.py`: registration uniqueness, startup failure semantics, rollback of already-started services, non-critical degradation, reverse-order shutdown, shutdown-failure isolation, and health-failure isolation.

Implementation:
- `2e38e857dbed219c41c8b4339434bb61a372f040` — `test: add service manager lifecycle contracts`
- Added `tests/test_service_manager_contract.py` with six focused contract tests.

Current verification status:
- Code/test change committed successfully.
- GitHub Actions execution is pending/not yet evidenced for this commit.
- No local execution is claimed.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites.
