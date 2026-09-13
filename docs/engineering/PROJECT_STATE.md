# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: See `main` branch head; this field intentionally avoids a self-referential commit SHA because this file is itself committed as part of the synchronization.
- Overall Status: `PRODUCTION_VERIFIED`
- Current Phase: Phase 2 — Core Architecture
- Current Task: Next evidence-backed Phase 2 task selection after TASK-050
- Last Completed Task: TASK-050 — Telegram Journal Storage Structure Validation
- Removed Task: TASK-016 — Worker Retry and Failure Lifecycle; removed because it was inherited from the previous planning path and is not independently required by the final Forex-only Master Prompt.
- Known Blockers: None for the verified Railway deployment path; GitHub Connector does not expose a local working tree/runtime.
- Known Risks: Production verification applies to the intentional Railway-connected fork `sia644434/forex-signal-bot`, synchronized by the user from this source repository. Phase 2 still has remaining evidence-backed architecture work before later phases are selected.
- Broken Tests: None known for the verified TASK-050 implementation head.
- CI Status: TASK-050 implementation head `b1415472efa6ebffcbea6bba86535597c28501bb` completed 7 successful GitHub Actions workflow runs. Railway commit status is also `success`.
- Deployment Status: No new live production smoke is claimed solely from TASK-050 or documentation synchronization. The previously verified Railway path remains the production deployment evidence.
- Architecture Status: Phase 2 active. The PC Worker is restricted to heavy Forex application processing. Durable queue, timeout-aware crash recovery, central queue configuration, application composition, authenticated heartbeat, readiness, observability, heartbeat freshness, minimal public health, authenticated job-request hardening, readiness-gated dispatch, Telegram ownership consolidation, Decision/Risk ownership consolidation, Analysis ownership consolidation, AI architecture auditing, market-data application-boundary consolidation, dormant direct OANDA price-surface removal, lower-level market-data facade removal, provider-specific adapter removal, ProviderManager lifecycle contract hardening, MarketDataEngine output-surface compatibility audit, MarketDataService construction-boundary hardening, application-scoped MarketDataService lifetime hardening, application-scoped scanner ProviderManager lifetime hardening, Telegram tracker contract coverage, Telegram user-state contract coverage, journal ordering/persistence contract hardening, journal mutation atomicity, journal corruption fail-closed handling, and journal storage structure validation are recorded. The `ai/` package is dormant/unwired and reserved for Phase 6; it is not part of the active production trading flow. No local coding-agent/Ollama architecture is part of the active Forex worker path.
- Production Readiness: `VERIFIED` for the observed Railway deployment path. No new live smoke is claimed for TASK-050 or documentation-only synchronization.
- Last Checkpoint: `b1415472efa6ebffcbea6bba86535597c28501bb` — TASK-050 verified implementation checkpoint.
- Last State Update: 2026-09-13

## Phase 2 — Core Architecture

### Completed
TASK-004 through TASK-050 are verified according to the persistent engineering state, except TASK-016 which remains removed from the roadmap.

### TASK-047 — VERIFIED
Telegram Journal Ordering and Persistence Contract Audit. The journal module was aligned with the `JournalStore` chronological persistence representation and newest-first public listing/index semantics. Regression coverage verified add/reload ordering, close-by-index behavior, and invalid-index handling. Final implementation head `2e6bef7ec971501cd3573b21544c22f721253f99` passed the required CI/security/activation/readiness/E2E/deployment gates.

### TASK-048 — VERIFIED
Telegram Journal Mutation Atomicity. Repository audit found that journal `add_entry()` and `close_entry()` performed read-modify-write across separate `JournalStore` lock scopes, allowing overlapping async/threaded callbacks to lose updates. `JournalStore.add()` was used for atomic append, and `JournalStore.update_at()` was added for atomic indexed mutation under one lock. Regression coverage added concurrent multi-threaded journal additions and verified that all submitted entries survive. Implementation head `b9157db60e52fb975c634f6f0abb2585f7f36de4` passed seven successful Actions workflows and Railway commit status.

### TASK-049 — VERIFIED
Telegram Journal Corruption Fail-Closed Contract. Repository audit found that `JournalStore._read()` converted filesystem/JSON read failures into `{}`, allowing a subsequent append to treat a corrupted store as empty and risk discarding persisted journal data. The store now raises `JournalStoreError` on read/parse failure, and regression coverage verifies that malformed JSON is rejected by both list and append paths without overwriting the original corrupt file. Implementation head `87dd8a5e827f6db30cbdec6f925be2ea091eed38` passed the required GitHub Actions workflow set and Railway commit status.

### TASK-050 — VERIFIED
Telegram Journal Storage Structure Validation. Repository audit found that syntactically valid but structurally invalid journal JSON could reach journal code and produce uncontrolled `AttributeError`/`TypeError` behavior. `JournalStore._read()` now validates the root mapping, user-entry lists, and entry dictionaries, raising `JournalStoreError` on invalid structure. Regression coverage verifies representative invalid structures and confirms the original persisted file remains unchanged. Implementation head `b1415472efa6ebffcbea6bba86535597c28501bb` passed the required 7-workflow GitHub Actions set and Railway commit status.

## Next Task Selection
Phase 2 remains active. Select the next task only after a fresh evidence-backed repository audit identifies a concrete correctness, reliability, security, observability, deployment, or recovery gap. Do not invent speculative feature work or skip ahead to Phase 3.

## Repository Mapping Decision
- `siasoltoon/forex-signal-bot` remains the source repository.
- `sia644434/forex-signal-bot` is the intentional Railway-connected fork synchronized by the user.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
