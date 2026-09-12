# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `bb0e9c181fb8f4ec0cc7525b480a341d44cb5468`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-014 — PC Worker Scope and Configuration Boundary Hardening
- Last Completed Task: TASK-013 — Configuration Boundary Consistency Hardening
- Next Task: Verify TASK-014 CI and, if green, begin TASK-015 — PC Worker Reliability Contract Hardening.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. The current worker-scope change has not yet received fresh live production verification.
- Broken Tests: None known; TASK-014 CI is in progress.
- CI Status: Implementation head `957a156761638aa711b9518476cbb72c2bcbe89c` passed Test and Security Audit; cleanup head `bb0e9c181fb8f4ec0cc7525b480a341d44cb5468` has production/test workflows in progress.
- Deployment Status: Railway live deployment health and restart/recovery remain verified for the previously deployed commit. Current worker-scope changes are not yet production-verified.
- Architecture Status: Phase 2 active. The PC Worker is explicitly for heavy Trading Intelligence Platform processing; local coding-agent/Ollama infrastructure has been removed from the repository.
- Production Readiness: `VERIFIED` for the previously observed deployment path; current runtime-affecting changes are not yet re-verified in production.
- Last Checkpoint: Worker architecture correction commit `bb0e9c181fb8f4ec0cc7525b480a341d44cb5468`.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### Pre-TASK-004 Scope — UNKNOWN
The Phase 2 section that existed before TASK-004 was skipped during the sequential implementation pass. It is intentionally recorded as `UNKNOWN / NOT YET AUDITED`, not `COMPLETE`. It must be revisited and verified later before Phase 2 is declared complete.

### TASK-004 through TASK-013
Verified and closed through repository evidence and GitHub Actions. TASK-013 centralized application/health/logger configuration boundaries and its head `382d3461f2a95a3135fa074297a5e4c0a99f6c94` has a successful combined status.

### TASK-014 — IN_PROGRESS
PC Worker Scope and Configuration Boundary Hardening.

Current evidence:
- `worker/executors.py` contains real application workloads such as backtesting, market scans, feature engineering, model training, evaluation, and multi-timeframe analysis.
- `worker/contracts.py` no longer exposes `coding_agent` as a worker workload.
- `worker/main.py` no longer bootstraps a local coding agent or Ollama runtime and consumes centralized `Settings.load().log_level` for worker logging.
- `worker/handlers.py` no longer exposes coding-agent registration.
- The legacy `worker/models/*` local-agent/Ollama implementation, `tests/test_local_coding_agent.py`, and `scripts/setup_pc_agent.ps1` were removed in atomic commit `bb0e9c181fb8f4ec0cc7525b480a341d44cb5468` after reference inspection.
- `docs/engineering/ARCHITECTURE_MAP.md` now records the corrected worker boundary.

Implementation commits:
- `d71ac4bb771580ce421a76139c66aa2080ab9f96` — `fix: keep PC worker focused on application workloads`
- `43588c36a65b724342f8aeaa18ce4930f8fa8c4d` — `fix: remove coding-agent handler from PC worker`
- `9aaa89c0191fc0106a295189331574314b31b189` — `fix: remove coding-agent workload from worker contract`
- `957a156761638aa711b9518476cbb72c2bcbe89c` — `test: enforce application-only PC worker workloads`
- `bb0e9c181fb8f4ec0cc7525b480a341d44cb5468` — `refactor: remove local coding-agent and Ollama subsystem`

Verification:
- Test workflow `34701517686` / job `103574003447` on implementation head `957a156...`: success, including full test suite and syntax checks.
- Security Audit `34701517670` on implementation head `957a156...`: success.
- Cleanup head `bb0e9c...`: production/test workflows are currently in progress.

Next exact action: verify the cleanup-head CI results. If green, close TASK-014 and activate TASK-015 for worker reliability contracts.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites.
