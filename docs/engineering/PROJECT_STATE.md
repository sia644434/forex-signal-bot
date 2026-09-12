# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main` (repository default branch; connector does not expose a separate local working tree)
- Current Commit: `0cd1b6f476a9ee0e1ec2ae6c91801a0e8d638408`
- Overall Status: `IN_PROGRESS`
- Current Phase: Phase 1 — Repository Audit
- Current Task: TASK-001 — Establish persistent engineering memory and baseline architecture map
- Last Completed Task: Repository reconnaissance through GitHub Connector
- Next Task: Verify baseline behavior and prioritize the highest-risk correctness/reliability gap after persistent state is committed
- Known Blockers: No local working-tree state is exposed by the GitHub Connector; deployment/runtime verification requiring private environment credentials is not yet established
- Known Risks: Production readiness is NOT verified; CI currently has at least one reported successful commit status, but this is not equivalent to all production gates passing
- Broken Tests: Not established in this audit; tests are present but have not been executed locally in this session
- CI Status: Latest combined commit status reports one successful status context (`lavish-energy - forex-signal-bot`); full workflow/job inventory requires targeted verification
- Deployment Status: Railway configuration exists; deployment health is not independently verified as production-ready
- Architecture Status: Baseline mapped at a high level; targeted subsystem verification remains
- Production Readiness: `NOT_READY / NOT_VERIFIED`
- Last Checkpoint: Initial baseline audit checkpoint
- Last State Update: 2026-09-12

## Evidence

The repository default branch is `main`. The latest commit is `0cd1b6f...`, whose message is `test(agent): add local coding agent smoke tests`. The tree contains dedicated `ai`, `analysis`, `config`, `core`, `data`, `risk`, `services`, `signal_engine`, `strategy`, `telegram_bot`, `tests`, and `worker` areas, plus Railway/Docker deployment configuration.

The application entry path is `main.py` → `app.py` → `core.application.create_app()`. The application currently registers `TelegramService` through `ServiceManager`.

The repository contains provider/freshness abstractions and tests for OANDA, Finnhub, AlphaVantage, provider contracts, freshness, market-data services, analysis, decision logic, Telegram, worker contracts/runtime, and production gates.

## Checkpoint

What was done: repository identity, branch/default branch, latest commit, tree, dependencies, entrypoints, major architecture areas, tests, workflows, and CI status were inspected; no `docs/engineering/` persistent memory directory exists yet.

What remains: commit the persistent memory files, then continue with targeted baseline verification rather than rescanning the repository.
