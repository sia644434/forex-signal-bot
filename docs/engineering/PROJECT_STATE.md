# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: See `main` branch head; this field intentionally avoids a self-referential commit SHA because this file is itself committed as part of the synchronization.
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-083 — Configured Risk Policy Ceiling for Dynamic Sizing; verification must be confirmed on the exact resulting `main` HEAD before marking the latest audit checkpoint VERIFIED.
- Last Completed Task: TASK-083 implementation and regression coverage completed; GitHub Actions verification is the remaining checkpoint.
- Known Blockers: None known for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Current audit changes must not be treated as live-production verified until their exact `main` HEAD passes the required GitHub Actions gates.
- Broken Tests: A previous ProviderManager lifecycle regression expectation was corrected to match the intentional replacement contract. No new failure is claimed without exact-head workflow evidence.
- CI Status: Latest audit changes triggered the required GitHub Actions workflows. The latest verification checkpoint must remain `IN_PROGRESS/PENDING` until the exact resulting `main` HEAD has all required gates completed successfully.
- Deployment Status: No new live production smoke is claimed solely from the current audit commits. The previously verified Railway path remains the production deployment evidence.
- Architecture Status: Phase 2 active. Canonical production flow remains `MarketDataService → MarketDataEngine → ProviderManager → FullAnalysisEngine → DecisionEngine → ConfidenceEngine → RiskEngine → PositionSizing/CurrencyConversion` where applicable. The PC Worker is restricted to heavy application processing. The `ai/` package remains dormant/unwired future Phase 6 capability and is not active production trading architecture. No local coding-agent/Ollama architecture is part of the active worker path.
- Production Readiness: `VERIFIED` for the previously observed Railway deployment path; current audit commits are not yet claimed as fresh live-production verification.
- Last Checkpoint: TASK-083 implementation `d9c427b7f44a56db2c4f6c98b37e249a6df8af82`, regression `cbc09a3fefa6b5d97d77119cb8196f1d21da7604`; documentation synchronization follows the audit.
- Last State Update: 2026-09-14

## Current Audit Checkpoint

### Verified prior contracts
- TASK-058 through TASK-064 remain verified according to persistent engineering history.
- DecisionEngine 0..100 score is neutral-centered at 50.
- ConfidenceEngine uses the signed-score contract consistently.
- Supply/Demand has an explicit score field and DecisionEngine consumes it directly.
- RiskEngine and PositionSizing use explicit currency/risk-distance contracts and fail closed on invalid numeric inputs.
- ProviderManager accepts list/tuple provider results, normalizes equivalent symbol forms at its validation boundary, isolates failure diagnostics per request, and now replaces/prunes provider lifecycle state on reconfiguration.
- Market-aware risk state is isolated per analysis rather than mutating the shared FullAnalysisEngine risk component.
- The project remains explicitly Multi-Asset: Forex, Crypto, Stocks, Indices, and Commodities are supported through centralized symbol metadata.

### Latest concrete audit work
- TASK-079 established a consistent USDT/USDC currency boundary across PositionSizing, Settings, RiskEngine, and CurrencyConversion.
- TASK-080 removed the Forex `100000` contract-size default from direct non-Forex RiskEngine calls by deriving the contract size from centralized asset metadata when no explicit override is supplied.
- TASK-081 made DataQuality use the canonical symbol normalization layer.
- TASK-082 made ProviderManager reconfiguration replace the injected registry and prune removed provider instances/cooldowns while preserving active factory cache state.
- TASK-083 made configured `risk_percent` an account-level ceiling for dynamic risk selection, preventing confidence/score heuristics from silently exceeding production risk policy.

### Current audit frontier
Continue from:
`ProviderManager → MarketDataService → Freshness/DataQuality → Symbol/Asset Metadata → CurrencyConversion → MarketAwareAnalysisEngine → RiskEngine → PositionSizing`
then proceed outward into Telegram/Scanner/Tracker/Callbacks and Worker/Queue/Persistence, Security/Production, and the final E2E audit.

Prioritize concrete gaps in freshness propagation, market-session semantics, conversion freshness/direction, quantity/contract semantics, precision/rounding, risk-budget enforcement, and end-to-end fail-closed behavior. Do not add speculative features.

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
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this repository.
