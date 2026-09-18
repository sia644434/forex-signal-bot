# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: See `main` branch head; this field intentionally avoids a self-referential commit SHA because this file is itself committed as part of the synchronization.
- Overall Status: `PRODUCTION_VERIFIED / PHASE_10_SECURITY_HARDENING_IN_PROGRESS`
- Current Phase: Phase 10 — Security / Production Hardening — audit frontier
- Current Task Frontier: Phase 10 is active through TASK-126. Continue only from concrete repository-backed security/production-hardening gaps.
- Last Verified Task: TASK-126 — Worker HTTP and Production Container Security Hardening, exact-head verified on `b92aae52828e7737402da30ec5d513df4c8b0dad` with all seven required checks successful.
- Known Blockers: No known blocker for the previously verified Railway deployment path. Current audit commits must not be treated as live-production verified until their exact `main` HEAD passes the required GitHub Actions gates.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Current audit changes remain unverified until exact-head CI evidence exists.
- Broken Tests: None identified on the latest exact-head verification.
- CI Status: Exact-head verification is green for TASK-126 audit HEAD `b92aae52828e7737402da30ec5d513df4c8b0dad`; all seven required checks completed successfully.
- Deployment Status: No new live-production smoke is claimed from TASK-091 through TASK-100. The previously verified Railway path remains historical deployment evidence.
- Architecture Status: Canonical production flow remains `MarketDataService → MarketDataEngine → ProviderManager → FullAnalysisEngine → DecisionEngine → ConfidenceEngine → RiskEngine → PositionSizing/CurrencyConversion` where applicable. The PC Worker is restricted to heavy application processing. The `ai/` package remains dormant/unwired future Phase 6 capability and is not active production trading architecture. No local coding-agent/Ollama architecture is part of the active worker path.
- Production Readiness: `VERIFIED` for the previously observed Railway deployment path; current audit commits are not claimed as fresh production verification.
- Last State Update: 2026-09-19

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
Phases 3–9 are closed according to their recorded closure checkpoints. Phase 10 — Security / Production Hardening — is active through TASK-126. Do not add speculative tasks; continue only from concrete repository evidence.

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


## Phase 4 Closure Checkpoint
- TASK-107: OANDA direct-provider symbol boundary hardened and verified.
- TASK-108: centralized symbol/timeframe contract enforced at MarketDataEngine boundary and verified.
- TASK-109: full Phase-4 cross-layer audit completed with no additional repository-backed gap.
- Closure code HEAD before documentation synchronization: `944d7b3176d201e6cf29c921d2bd27886b86a81d`.
- Required checks on that exact HEAD: final-gate, readiness, activation-gate, production-e2e-contract, test, dependency-audit, activation-validation — all `completed/success`.
- Documentation synchronization is a new commit and must itself pass the same seven-check contract before Phase 4 is treated as fully synchronized.

## Phase 5 Closure Checkpoint
- TASK-110 through TASK-114 complete the Phase-5 analysis audit.
- Final code HEAD before documentation synchronization: `963abbaee6bfac940944fae3b92f28b5f02dd6b4`.
- Required checks on that exact HEAD: final-gate, readiness, activation-gate, production-e2e-contract, test, dependency-audit, activation-validation — all `completed/success`.
- Documentation synchronization is a new commit and must itself pass the same seven-check contract.

## Phase 6 Closure Checkpoint
- AI/ML remains a dormant, explicitly opt-in capability.
- The canonical production scoring path contains no AI component.
- Final code HEAD: `91a59421cbd82043cec59bc9f5fe883796a1a8da`.
- All seven required checks on that exact HEAD: `completed/success`.
- Documentation synchronization is the final Phase-6 commit and must itself pass the same seven-check contract.


## Phase 7 Closure Checkpoint
- TASK-119, TASK-120, TASK-121, and TASK-122 are verified.
- Closure HEAD: `d34a8836ff5a2e1c8820540dd1d6cc5bff473f8a`; all seven required checks completed successfully.
- No fresh live-production smoke is claimed from this audit; historical Railway verification remains separate evidence.


## Phase 8 Closure Checkpoint
- TASK-123 corrected the MarketAwareAnalysisEngine boundary for candle identity and freshness propagation while preserving legacy candle-like compatibility.
- TASK-124 completed the full Phase-8 Trading / Decision Engine cross-layer closure audit with no additional repository-backed correctness gap.
- Code closure HEAD: `1edbf5126c86bcde45c32cf91e365d22e20e4037`.
- All seven required checks on that exact code HEAD completed successfully.
- No live-production smoke is claimed from this audit; historical Railway evidence remains separate.
- Next audit frontier: Phase 9 — Backtesting / Simulation.


## Phase 9 Closure Checkpoint
- TASK-125 completed the full Backtesting / Simulation cross-layer closure audit.
- Concrete gaps corrected: deterministic/finite simulation inputs, positive close-price validation, bounded simulation parameters, walk-forward train/test separation, and seeded Monte Carlo determinism.
- Code closure HEAD: `d616df74377af7de1aaf798c7b876fe8acecee60`; all seven required checks completed successfully.
- No live-production smoke verification is claimed from this audit.
- Next audit frontier: Phase 10 — Security / Production Hardening.


## Phase 10 Security Hardening Checkpoint
- TASK-126 corrected concrete WorkerHTTPServer request-boundary validation gaps, added regression coverage, hardened the production container to run as non-root, and restricted production CI workflow permissions.
- Exact audit HEAD: `b92aae52828e7737402da30ec5d513df4c8b0dad`.
- All seven required GitHub Actions checks completed successfully on that exact HEAD.
- No live-production smoke verification is claimed from this audit batch.
