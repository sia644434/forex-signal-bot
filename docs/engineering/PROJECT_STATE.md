# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `a15098d9660779f0968705b5e3ef67fc052c80f6`
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: TASK-038 — Market Data Lower-Level Facade / Alternate Ownership Audit
- Last Completed Task: TASK-037 — Dormant Direct OANDA Price Surface Audit
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Phase 2 still has remaining evidence-backed architecture work before later phases are selected.
- Broken Tests: None known for the verified TASK-037 implementation head.
- CI Status: TASK-037 implementation commit `65ea6150fa23895ad5655e59dbc9349945e67f96` has successful completed GitHub Actions and successful Railway commit status. Current HEAD contains documentation synchronization after that verified implementation.
- Deployment Status: TASK-037 implementation commit has successful Railway commit status. No new live production smoke is claimed solely from later documentation commits.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, heartbeat freshness, minimal public health, authenticated job-request hardening, readiness-gated dispatch, Telegram ownership consolidation, Decision/Risk ownership consolidation, Analysis ownership consolidation, AI ownership auditing, market-data application-boundary consolidation, and dormant direct OANDA price-surface removal are recorded. The `ai/` package is dormant/unwired and reserved for Phase 6; it is not part of the active production trading flow. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed Railway deployment path. No new live smoke is claimed for documentation-only synchronization commits.
- Last Checkpoint: `65ea6150fa23895ad5655e59dbc9349945e67f96` — TASK-037 verified implementation checkpoint.
- Last State Update: 2026-09-12

## Phase 2 — Core Architecture

### Completed
TASK-004 through TASK-013, TASK-014, TASK-015, TASK-017 through TASK-036 are verified according to the persistent engineering state. TASK-016 remains removed from the roadmap.

### TASK-037 — VERIFIED
Dormant Direct OANDA Price Surface Audit. The repository-wide audit found no production caller for `get_latest_oanda_price`; the dormant direct price surface was removed while the canonical OANDA candle path remained intact. CI run `34719290035` completed successfully and Railway commit status is successful for implementation commit `65ea6150fa23895ad5655e59dbc9349945e67f96`.

### TASK-038 — IN PROGRESS
Market Data Lower-Level Facade / Alternate Ownership Audit. Repository-wide inspection found `DataManager(` construction only in tests, while `ExplicitProviderManager` is referenced by `DataManager` and focused tests with no production caller found. `MarketDataService` still supports a lower-level `DataManager` compatibility path even though production callers use the canonical engine path. The next step is to verify all remaining references and tests before any removal or consolidation.

## Next Task Selection
Continue TASK-038 by auditing the complete lower-level market-data compatibility surface. Preserve behavior unless repository evidence proves it is dormant and safe to remove. Do not invent a replacement caller or parallel market-data path.

## Repository Mapping Decision
- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
