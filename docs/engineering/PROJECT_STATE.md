# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: See `main` branch head; this field intentionally avoids a self-referential commit SHA because this file is itself committed as part of the synchronization.
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-065/TASK-066 numeric-contract hardening across Risk/Position Sizing and FullAnalysis boundaries; continue evidence-backed audit only.
- Last Completed Task: TASK-066 — FullAnalysis Numeric Boundary Hardening (implementation completed; CI verification pending)
- Known Blockers: None known for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Current numeric-contract changes require final GitHub Actions verification before being marked VERIFIED.
- Broken Tests: None confirmed at the time of this state update; latest relevant workflow runs are still in progress.
- CI Status: Latest audit commits triggered the required GitHub Actions workflows; final conclusion remains `IN_PROGRESS` until those runs finish.
- Deployment Status: No new live production smoke is claimed solely from the current audit commits. The previously verified Railway path remains the production deployment evidence.
- Architecture Status: Phase 2 active. Canonical production flow remains `MarketDataService → MarketDataEngine → ProviderManager → FullAnalysisEngine → DecisionEngine → ConfidenceEngine → RiskEngine → PositionSizing/CurrencyConversion` where applicable. The PC Worker is restricted to heavy Forex application processing. The `ai/` package remains dormant/unwired future Phase 6 capability and is not active production trading architecture. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the previously observed Railway deployment path; current audit commits are not yet claimed as live production verification.
- Last Checkpoint: `8781f69e6372433d2367956be4c55a4e645a8d4c` — FullAnalysis numeric boundary regression checkpoint; subsequent documentation/state synchronization follows the audit.
- Last State Update: 2026-09-14

## Current Audit Checkpoint

### Verified prior contracts
- TASK-058 through TASK-064 remain verified according to persistent engineering state.
- DecisionEngine 0..100 score is neutral-centered at 50.
- ConfidenceEngine uses the signed-score contract consistently.
- Supply/Demand has an explicit score field and DecisionEngine consumes it directly.
- RiskEngine and PositionSizing use explicit currency/risk-distance contracts and fail closed on invalid numeric inputs.

### Current audit work
- ConfidenceEngine numeric hardening was implemented with regression coverage; final verification is pending.
- FullAnalysisEngine numeric boundary hardening was implemented with regression coverage; final verification is pending.
- PositionSizing/CurrencyConversion/Risk integration is the next audit frontier: verify that account currency, quote currency, conversion rate, risk amount, risk-per-unit, lot size, and executable position size preserve units and finite/positive contracts end-to-end.

## New-chat continuation rule

A new conversation must begin by reading these engineering state files before making repository changes:
1. `docs/engineering/PROJECT_STATE.md`
2. `docs/engineering/PHASE_STATE.md`
3. `docs/engineering/TASK_STATE.md`
4. `docs/engineering/TEST_STATE.md`
5. `docs/engineering/ARCHITECTURE_MAP.md`
6. `docs/engineering/DECISIONS.md`
7. `docs/engineering/CHANGELOG_ENGINEERING.md`

Then inspect the exact current `main` HEAD and GitHub Actions status. Do not repeat completed work. Continue from the first unresolved audit frontier recorded above. Only create a new task when a concrete repository-backed gap is demonstrated. For this repository use GitHub Connector only for repository inspection/modification; do not introduce Data Analysis, local coding-agent/Ollama architecture, speculative features, or unrelated agent architecture.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
