# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: See `main` branch head; this field intentionally avoids a self-referential commit SHA because this file is itself committed as part of the synchronization.
- Overall Status: `PRODUCTION_VERIFIED / PHASE_3_CLOSURE_VERIFICATION`
- Current Phase: Phase 3 — Telegram / Worker / Cross-Layer Reliability — closure verification
- Current Task Frontier: TASK-105/106 are the final concrete Phase-3 hardening tasks; no further repository-backed Phase-3 gap is currently open.
- Last Verified Task: TASK-106 — Complete Persistent Settings Mutation Contract, exact-head verified on `dd97c74c19827c2147b763b2814de35b82e2366c` with all seven required checks successful. TASK-105 is also verified on that exact HEAD.
- Known Blockers: No known blocker for the previously verified Railway deployment path. Current audit commits must not be treated as live-production verified until their exact `main` HEAD passes the required GitHub Actions gates.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Current audit changes remain unverified until exact-head CI evidence exists.
- Broken Tests: None identified on the latest exact-head verification.
- CI Status: Fresh seven-workflow verification is still required for the current audit HEAD. No green state is claimed until exact-head evidence exists.
- Deployment Status: No new live-production smoke is claimed from TASK-091 through TASK-100. The previously verified Railway path remains historical deployment evidence.
- Architecture Status: Canonical production flow remains `MarketDataService → MarketDataEngine → ProviderManager → FullAnalysisEngine → DecisionEngine → ConfidenceEngine → RiskEngine → PositionSizing/CurrencyConversion` where applicable. The PC Worker is restricted to heavy application processing. The `ai/` package remains dormant/unwired future Phase 6 capability and is not active production trading architecture. No local coding-agent/Ollama architecture is part of the active worker path.
- Production Readiness: `VERIFIED` for the previously observed Railway deployment path; current audit commits are not claimed as fresh production verification.
- Last State Update: 2026-09-18

## Current Audit Checkpoint

### Verified prior contracts
- TASK-001 through TASK-090 retain their historical verification state documented in the engineering history.
- Phase 2 Core Architecture was formally completed on the previously verified baseline.
- Telegram surface trust boundaries, canonical market-status gating, tracker executable-signal handling, output escaping, and authorization were verified at TASK-090.
- The project remains explicitly Multi-Asset: Forex, Crypto, Stocks, Indices, and Commodities are supported through centralized symbol metadata.

### Latest concrete audit work
- TASK-091: durable Telegram user state with atomic persistence and corruption fail-closed behavior.
- TASK-092: durable active tracker state across restarts.
- TASK-093: registered tracker refresh loop with persisted notification preference.
- TASK-094: exact-identity untrack callbacks.
- TASK-095: multi-asset scanner universe with bounded environment override.
- TASK-096: queue claim-token fencing against stale worker completions.
- TASK-097: renewable worker queue leases to prevent legitimate long-running jobs from being recovered while still active.
- TASK-098: synchronous worker timeout fencing so `to_thread` work remains tracked until the underlying thread finishes.
- TASK-099: Telegram startup dependency preflight before application runtime start.
- TASK-100: explicit provider symbol capability boundaries and fail-closed diagnostics for unsupported market/provider combinations.

### Current concrete frontier
The Phase-3 concrete audit frontier is closed after TASK-105/106. Do not add speculative Phase-3 tasks. The next work item is Phase 4 only after the synchronized engineering state passes the final seven-check verification.

## Multi-Asset Contract
The project is a **Multi-Asset Trading Intelligence Platform**, not a Forex-only bot. Supported families are Forex, Crypto, Stocks, Indices, and Commodities. Market-specific semantics such as quote currency, contract size, session, provider support, and conversion requirements must be explicit and fail closed when unavailable.

## New-chat continuation rule
A new conversation must begin by reading these engineering state files before making repository changes:
1. `docs/engineering/PROJECT_STATE.md`
2. `docs/engineering/PHASE_STATE.md`
3. `docs/engineering/TASK_STATE.md`
4. `docs/engineering/TEST_STATE.md`
5. `docs/engineering/ARCHITECTURE_MAP.md`
6. `docs/engineering/DECISIONS.md`
7. `docs/engineering/CHANGELOG_ENGINEERING.md`

Then inspect the exact current `main` HEAD and GitHub Actions status. Do not repeat completed work. Continue from the first unresolved audit frontier recorded above. For this repository use GitHub Connector only for repository inspection/modification; do not introduce Data Analysis, local coding-agent/Ollama architecture, speculative features, or unrelated agent architecture.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this repository.
