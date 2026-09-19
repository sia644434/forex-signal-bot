# Project State

- Project: `siasoltoon/forex-signal-bot`
- Branch: `main`
- Current HEAD: `6024a5dfbc7d1e6f13632fa83ea9c8a4f2f5266b`
- Product: **Multi-Asset Trading Intelligence Platform**
- Supported market families: Forex, Crypto, Stocks, Indices, Commodities
- Historical phase closures: Phases 1–11 have recorded closure evidence at their respective exact code heads.
- Current operational state: **Phase 13 active code audit; Railway verification deferred to the final external gate**.
- Current unresolved production signal: the combined status for current HEAD contains a failing Railway deployment status (`lavish-energy - forex-signal-bot`).
- Phase 13 is active for code/test/CI/cross-phase auditing; it cannot be finally closed until the code audit is complete and the deferred Railway verification is performed on the resulting HEAD.
- No current code defect is declared solely from the Railway failure; the failure is an evidence-backed production-verification blocker that must be investigated.
- Historical Railway/live-smoke evidence remains valid only for the deployment state and commit for which it was observed; it must not be conflated with current-HEAD verification.

## Current Audit Contract
A phase is current-HEAD verified only when implementation, focused regression tests, required CI checks, deployment evidence where applicable, and synchronized engineering documentation agree.

The audit must:
- inspect the entire phase surface, not just the original task checklist;
- identify functional, reliability, security, data, testing, CI/CD, deployment, observability, and documentation gaps;
- fix related concrete gaps together;
- add regression coverage for corrected behavior;
- verify the resulting exact HEAD;
- re-audit dependent boundaries before closure;
- avoid speculative rewrites and unsupported features.

## Multi-Asset Contract
The repository is not Forex-only. Centralized symbol/asset metadata and market-specific semantics must remain intact. Unsupported provider/market combinations, unavailable conversion data, stale/future market data, and invalid risk inputs must fail closed.

## Architecture Constraints
The PC Worker is for heavy application processing. The dormant `ai/` package is not part of canonical production scoring. No local coding-agent/Ollama/model-orchestration architecture is part of the active worker path.

## New-chat continuation
Before repository changes, read:
1. `docs/engineering/PROJECT_STATE.md`
2. `docs/engineering/PHASE_STATE.md`
3. `docs/engineering/TASK_STATE.md`
4. `docs/engineering/TEST_STATE.md`
5. `docs/engineering/ARCHITECTURE_MAP.md`
6. `docs/engineering/DECISIONS.md`
7. `docs/engineering/CHANGELOG_ENGINEERING.md`

Then inspect the exact current `main` HEAD and current CI/deployment status.