# Task State

## TASK-001 through TASK-064
Phase 1/2 reliability and architecture tasks through DecisionEngine Supply/Demand consumption remain VERIFIED according to the persistent engineering history.

## TASK-065
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: ConfidenceEngine Numeric Boundary Hardening
Implementation Status: VERIFIED

## TASK-066
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: FullAnalysisEngine Numeric Boundary Hardening
Implementation Status: VERIFIED

## TASK-067
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: PositionSizing Decimal Numeric-Range Hardening
Implementation Status: VERIFIED

## TASK-068
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: RiskEngine Directional Price-Level Safety
Implementation Status: VERIFIED

## TASK-069
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Explicit Account-Balance Wiring and Settings Numeric Hardening
Implementation Status: VERIFIED

## TASK-070
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Risk-Policy Upper-Bound and Currency-Context Hardening
Implementation Status: VERIFIED

## TASK-071
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Timestamp and Provider Timing Boundary Hardening
Implementation Status: VERIFIED

## TASK-072
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Weekend Gap Detection Boundary Hardening
Implementation Status: VERIFIED

## TASK-073
Phase: Phase 3 — Telegram / Scanner / Tracker Reliability
Title: Tracker Risk-Plan Synchronization
Implementation Status: VERIFIED

## TASK-074
Phase: Phase 2/3 — Multi-Asset Market and Risk Architecture
Title: Remove Forex-Only Assumptions from Market-Aware Risk Path
Implementation Status: VERIFIED

## TASK-075 through TASK-089
Implementation Status: VERIFIED
Evidence: Persistent engineering history records the previously verified Worker/Queue, Provider, Analysis/Risk, Market Status, Tracker, Output Escaping, and Telegram Access Control hardening through exact-head CI verification on the Phase-2 closure baseline `654944e059a3438e31e90aa7f4dc90b04b95110f`.

## TASK-090
Phase: Phase 3 — Telegram / Scanner / Tracker / Callback Reliability
Title: Telegram Surface Contract Hardening
Implementation Status: VERIFIED
Evidence: Exact-head verification on `45a4bd5bb892181cb6a30c75f8b0340ecccaacc7`; all seven required checks succeeded.

## TASK-091
Phase: Phase 3 — Telegram / User-State Reliability
Title: Durable Telegram User State Across Restarts
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION

## TASK-092
Phase: Phase 3 — Telegram / Tracker Reliability
Title: Durable Active Tracker State Across Restarts
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION

## TASK-093
Phase: Phase 3 — Telegram / Tracker Execution Reliability
Title: Activate Tracker Refresh Loop and Honor Notification Preference
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION

## TASK-094
Phase: Phase 3 — Telegram / Callback Reliability
Title: Exact-Identity Untrack Callbacks
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION

## TASK-095
Phase: Phase 3 — Telegram / Multi-Asset Scanner Reliability
Title: Multi-Asset Scanner Universe
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION

## TASK-096
Phase: Phase 3 — Worker / Queue / Recovery Reliability
Title: Lease Fencing for Stale Worker Completions
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete recovery race: an expired `RUNNING` job could be recovered to `PENDING`, re-claimed, and then have its original stale worker overwrite the newer execution.
- Queue claims now receive unique `claim_token` values; recovery clears the old token and terminal dispatcher transitions are fenced by the current token.
- SQLite uses bounded connection/busy timeouts.
- Regression coverage verifies stale-worker completion is rejected after recovery/re-claim.

## TASK-097
Phase: Phase 3 — Worker / Queue / Recovery Reliability
Title: Renewable Worker Queue Leases
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- A legitimate long-running dispatcher claim could expire because `claimed_at` was never renewed while the worker was still executing.
- `WorkerQueue.renew_lease()` now refreshes only the matching `job_id + claim_token` pair.
- `WorkerDispatcher` runs a bounded heartbeat (maximum 30 seconds, approximately one-third of the requested timeout) while the worker submission is in flight.
- A failed heartbeat cannot overwrite a newer claim because terminal transitions remain token-fenced.
- Regression coverage verifies lease renewal and rejection of a stale token after re-claim.

## TASK-098
Phase: Phase 3 — Worker / Runtime Reliability
Title: Synchronous Worker Timeout Fencing
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- `asyncio.wait_for(asyncio.to_thread(...))` cannot terminate the underlying OS thread. A timed-out synchronous handler could therefore continue after the runtime had forgotten it was active.
- Timed-out synchronous jobs now keep their underlying thread task tracked until it actually finishes.
- A duplicate request with the same job ID returns `RUNNING` while the original thread is in flight, then receives the cached completed result exactly once when it finishes.
- Regression coverage verifies no duplicate execution after a synchronous timeout.

## TASK-099
Phase: Phase 3 — Telegram / Startup Reliability
Title: Preflight Background-Service Dependencies Before Runtime Start
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Tracker scheduling and updater availability were previously validated after `Application.start()`, allowing partial startup on dependency failure.
- Startup now validates the updater and schedules the durable tracker job before the runtime is marked started.

## TASK-100
Phase: Phase 3 — Market Data / Provider Reliability
Title: Explicit Provider Symbol Capability Boundaries
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- The multi-asset scanner includes Crypto, Stocks, Indices, and Commodities, while the currently registered Finnhub and Alpha Vantage implementations are explicitly Forex-only and OANDA has a narrower instrument map.
- Before this change, ProviderManager attempted every configured provider for every symbol, turning known capability mismatches into generic provider failures and unnecessary retries/cooldowns.
- Providers now expose `supports_symbol`; OANDA, Finnhub, and Alpha Vantage declare their real symbol boundaries, while duck-typed custom providers remain backward-compatible.
- ProviderManager skips unsupported providers without making network requests and records an explicit `UnsupportedSymbol` diagnostic. This makes multi-asset capability gaps fail closed instead of looking like transient provider outages.
- Regression coverage verifies capability-based provider skipping and diagnostics.

## Multi-Asset Architecture Contract
The project is a **Multi-Asset Trading Intelligence Platform**, not a Forex-only bot. Supported market families are represented centrally in `config/symbols.py`: Forex, Crypto, Stocks, Indices, and Commodities. A symbol must not be rejected merely because it is not Forex. Market-specific semantics such as quote currency, contract size, trading session, provider support, and conversion requirements must be explicit and must fail closed when unavailable.

## Current Audit Frontier
Phase 3 remains active. TASK-090 is verified. TASK-091 through TASK-101 are implemented and pending exact-head CI verification. TASK-102 addresses the concrete worker HTTP/runtime-loop lifecycle gap. Remaining frontier after TASK-102 is queue/runtime shutdown and persistence recovery, production health, and final end-to-end lifecycle. Do not create a task merely to advance the roadmap; create the next task only after a concrete repository-backed gap is demonstrated.

## New-chat Continuation Contract
When a new chat starts work on this repository, first read:
- `docs/engineering/PROJECT_STATE.md`
- `docs/engineering/PHASE_STATE.md`
- `docs/engineering/TASK_STATE.md`
- `docs/engineering/TEST_STATE.md`
- `docs/engineering/ARCHITECTURE_MAP.md`
- `docs/engineering/DECISIONS.md`
- `docs/engineering/CHANGELOG_ENGINEERING.md`


## TASK-101
Phase: Phase 3 — Telegram / Multi-Asset Settings Reliability
Title: Multi-Asset Telegram Settings Consistency
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: the centralized symbol registry defined Forex, Crypto, Stocks, Indices, and Commodities, and the scanner had a multi-asset universe, but Telegram Settings exposed only four Forex symbols.
- Settings now exposes market families and dynamically renders the canonical symbols from config/symbols.py.
- Symbol callbacks are bounded to the centralized supported-symbol registry and fail closed for unknown values.
- Regression coverage verifies all market families and representative multi-asset selections.


## TASK-102
Phase: Phase 3 — Worker / Runtime / HTTP Reliability
Title: Persistent Worker Runtime Loop Across HTTP Requests
Implementation Status: IMPLEMENTED — PENDING EXACT-HEAD CI VERIFICATION
Evidence:
- Concrete gap: `WorkerHTTPServer` previously called `asyncio.run(runtime.execute(...))` for every HTTP request. WorkerRuntime timeout fencing depends on an underlying synchronous thread task remaining alive after timeout; closing the per-request event loop could therefore destroy the task lifecycle before its completion callback could finalize and cache the result.
- The HTTP server now owns one persistent asyncio event loop in a dedicated runtime thread and dispatches every `WorkerRuntime.execute()` call onto that loop with `run_coroutine_threadsafe`.
- Regression coverage verifies a timed-out synchronous job remains `RUNNING` for duplicate requests and later becomes `COMPLETED` after the underlying thread releases.
