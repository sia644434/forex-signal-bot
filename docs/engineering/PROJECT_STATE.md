# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-014 — PC Worker Scope and Configuration Boundary Hardening
- Last Completed Task: TASK-013 — Configuration Boundary Consistency Hardening
- Next Task: Complete TASK-014 by verifying CI, reviewing the worker diff, and then audit/remove any remaining out-of-scope local-agent artifacts if repository evidence confirms they are unused.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. The repository still contains legacy `worker/models/*` local-agent/Ollama artifacts that are no longer part of the active PC Worker runtime path and require a separate cleanup decision.
- Broken Tests: None known; current TASK-014 CI is in progress.
- CI Status: Head `957a156761638aa711b9518476cbb72c2bcbe89c` has GitHub Actions runs in progress.
- Deployment Status: Railway live deployment health and restart/recovery remain verified for the previously deployed commit. Current worker-scope changes are not yet production-verified.
- Architecture Status: Phase 2 active. Core lifecycle/error/configuration contracts are verified; PC Worker is being explicitly constrained to application heavy-processing workloads rather than local coding-agent/Ollama execution.
- Production Readiness: `VERIFIED` for the previously observed deployment path; current runtime-affecting changes are not yet re-verified in production.
- Last Checkpoint: TASK-014 implementation checkpoint at head `957a156761638aa711b9518476cbb72c2bcbe89c`.
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
- `worker/contracts.py` previously exposed `coding_agent` alongside application workloads; it has now been removed.
- `worker/main.py` previously bootstrapped a local coding agent through Ollama; that runtime path has now been removed.
- `worker/handlers.py` no longer exposes a coding-agent registration path.
- `worker/main.py` now consumes centralized `Settings.load().log_level` for worker logging.
- Legacy `worker/models/*` local-agent/Ollama files still exist in the repository but are no longer imported by the active worker entrypoint; cleanup remains a separate evidence-based task.

Current implementation commits:
- `d71ac4bb771580ce421a76139c66aa2080ab9f96` — `fix: keep PC worker focused on application workloads`
- `43588c36a65b724342f8aeaa18ce4930f8fa8c4d` — `fix: remove coding-agent handler from PC worker`
- `9aaa89c0191fc0106a295189331574314b31b189` — `fix: remove coding-agent workload from worker contract`
- `957a156761638aa711b9518476cbb72c2bcbe89c` — `test: enforce application-only PC worker workloads`

Verification: GitHub Actions is currently in progress for head `957a156761638aa711b9518476cbb72c2bcbe89c`.

## Repository Mapping Decision

- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, CI, or deployment configuration. Avoid speculative feature work and broad rewrites.
