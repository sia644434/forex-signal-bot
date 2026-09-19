# Project State

- Project: `siasoltoon/forex-signal-bot`
- Branch: `main`
- Current HEAD: `7e978faa986ed6088511c0aee3a1fa4510a02408`
- Product: **Multi-Asset Trading Intelligence Platform**
- Supported market families: Forex, Crypto, Stocks, Indices, Commodities
- Historical phase closures: Phases 1–11 retain their recorded closure evidence.
- Current operational state: **Phase 13 code audit VERIFIED; final Railway gate pending**.
- Current-head GitHub Actions: all seven required workflows completed successfully on the exact HEAD.
- Current external Railway status: still failing for `lavish-energy - forex-signal-bot`; this is deferred for final deployment verification and is not treated as proof of a code defect.
- Phase 12 remains `REVERIFICATION_REQUIRED` until Railway is synchronized to this HEAD and fresh health/recovery evidence exists.
- Phase 13 code/test/CI/cross-phase audit is verified at this exact HEAD; final production closure requires the external Railway gate.

## Current Audit Contract
A phase is current-HEAD verified only when implementation, focused regression tests, required CI checks, deployment evidence where applicable, and synchronized engineering documentation agree.

The audit:
- inspected the full relevant phase surface rather than only the original checklist;
- fixed concrete lifecycle, CI/security, and terminology issues together;
- added/updated focused regression coverage for corrected startup behavior;
- verified the resulting exact HEAD with the complete seven-workflow CI set;
- re-audited dependent boundaries;
- avoided speculative rewrites and unsupported features.

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