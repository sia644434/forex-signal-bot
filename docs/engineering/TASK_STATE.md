# Task State

## PRE-TASK-004 — AUDITED
Phase 2 scope before TASK-004 was audited from persistent engineering state; no separate historical task contract was invented.

## TASK-001
Phase 1 — Repository Audit
Implementation Status: COMPLETE

## TASK-002
Phase 1 — Baseline Stabilization
Implementation Status: COMPLETE

## TASK-003
Phase 1 — Production Verification / Reliability Hardening
Implementation Status: COMPLETE; live health and restart/recovery evidence verified.

## TASK-004 through TASK-013
Phase 2 — Core Architecture
Implementation Status: COMPLETE; verified through GitHub Actions.

## TASK-014
PC Worker Scope and Configuration Boundary Hardening — VERIFIED.

## TASK-015
Worker Job Lifecycle Reliability — VERIFIED.

## TASK-016 — REMOVED
Worker Retry and Failure Lifecycle — REMOVED FROM ROADMAP. Not independently required by the final Forex-only Master Prompt; no implementation performed.

## TASK-017
Remove Residual Non-Forex Worker Workload — VERIFIED.

## TASK-018
Durable Forex Worker Processing Queue Contract — VERIFIED.

## TASK-019
Forex Worker Queue Crash-Recovery Contract — VERIFIED.

## TASK-020
Activate Forex Worker Queue Crash Recovery — VERIFIED.

## TASK-021
Forex Worker Queue Persistence Configuration Boundary — VERIFIED.

## TASK-022
Wire Heavy Forex Worker Through the Application Service Boundary — VERIFIED.

## TASK-023
Verify and harden the real heavy-Forex workload routing boundary — VERIFIED / AUDIT COMPLETE. No speculative Phase 9 caller introduced.

## TASK-024
PC Worker Authenticated Heartbeat Contract — VERIFIED.

## TASK-025
Worker Processing Health/Readiness Contract — VERIFIED.

## TASK-026
Worker Heartbeat Observability — VERIFIED.

## TASK-027
PC Worker Heartbeat Freshness Contract — VERIFIED.

## TASK-028
Minimize Unauthenticated PC Worker Health Information Exposure — VERIFIED.

## TASK-029
PC Worker Authenticated Job Request Boundary Hardening — VERIFIED.

## TASK-030
PC Worker Readiness Enforcement at Job-Dispatch Boundary — VERIFIED.

## TASK-031
Worker Observability and Operational Contract Audit — VERIFIED.

## TASK-032
Telegram Architecture Ownership Audit / Consolidation — VERIFIED. Canonical ownership is `services/telegram/`.

## TASK-033
Decision/Risk/Strategy Architecture Ownership Audit — VERIFIED. Canonical owners are `analysis/decision_engine.py` and `analysis/risk_engine.py`.

## TASK-034
Analysis Architecture Ownership Audit — VERIFIED. `analysis/full_engine.py` remains canonical.

## TASK-035
AI Architecture Ownership Audit — VERIFIED / DORMANT / UNWIRED. `ai/` remains future Phase 6 capability and is not active production architecture.

## TASK-036
Market Data Ownership Consolidation — VERIFIED. Canonical application flow is `MarketDataService → MarketDataEngine → ProviderManager`.

## TASK-037
Dormant Direct OANDA Price Surface Audit — VERIFIED. `get_latest_oanda_price` was removed after no production caller was found.

## TASK-038
Market Data Lower-Level Facade / Alternate Ownership Audit — VERIFIED. Unused DataManager/ExplicitProviderManager compatibility architecture removed.

## TASK-039
Provider-Specific Market Data Adapter Surface Audit — VERIFIED. Unused provider-specific market-data methods removed.

## TASK-040
ProviderManager Lifecycle and State Contract Audit — VERIFIED. Injected-provider retention/rebinding contracts covered by regression tests.

## TASK-041
MarketDataEngine Output-Surface and Compatibility Audit — VERIFIED. Tested DataFrame compatibility surface intentionally retained.

## TASK-042
MarketDataService Construction Boundary Hardening — VERIFIED. Scanner no longer constructs MarketDataEngine directly.

## TASK-043
MarketDataService Lifetime and Application Composition Hardening — VERIFIED. Telegram signal/callback/tracker paths reuse application-scoped service state.

## TASK-044
Scanner ProviderManager Lifetime and Readiness Boundary Audit — VERIFIED. Manager is application-scoped and readiness is refreshed dynamically.

## TASK-045
Telegram Signal Tracker Contract Audit — VERIFIED. Focused lifecycle/target/signal-change regression coverage passed required gates.

## TASK-046
Telegram User State Contract Coverage — VERIFIED. Per-user state reuse, menu mutation, and settings isolation covered by regression tests.

## TASK-047
Phase: Phase 2 — Core Architecture / Telegram Reliability
Title: Telegram Journal Ordering and Persistence Contract Audit
Implementation Status: VERIFIED
Evidence: Corrected chronological persistence/mutation order versus newest-first public listing/index semantics. Final implementation head `2e6bef7ec971501cd3573b21544c22f721253f99` passed the required CI/security/activation/readiness/E2E/deployment gates.

## TASK-048
Phase: Phase 2 — Core Architecture / Telegram Reliability
Title: Telegram Journal Mutation Atomicity
Implementation Status: VERIFIED
Evidence:
- `JournalStore.add()` is used for atomic append.
- `JournalStore.update_at()` performs indexed read-modify-write under one lock.
- `journal.add_entry()` and `journal.close_entry()` now use atomic store mutation paths.
- Concurrency regression coverage submits 40 additions across 8 workers and verifies all 40 remain present.
- Implementation head `b9157db60e52fb975c634f6f0abb2585f7f36de4` has 7 successful GitHub Actions workflow runs and successful Railway commit status.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-049
Phase: Phase 2 — Core Architecture / Telegram Reliability
Title: Telegram Journal Corruption Fail-Closed Contract
Implementation Status: VERIFIED
Evidence:
- `JournalStore._read()` no longer converts filesystem/JSON read failures into an empty journal.
- Corrupt or unreadable journal storage raises `JournalStoreError` instead of allowing a later write to silently discard persisted data.
- Regression coverage verifies that malformed JSON is rejected by both read/list and append paths and that the original corrupt file is not overwritten.
- Implementation head `87dd8a5e827f6db30cbdec6f925be2ea091eed38` completed the required GitHub Actions workflow set successfully and has successful Railway commit status.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-050
Phase: Phase 2 — Core Architecture / Telegram Reliability
Title: Telegram Journal Storage Structure Validation
Implementation Status: VERIFIED
Evidence:
- `JournalStore._read()` now validates that persisted JSON is a dictionary whose user keys map to lists of entry dictionaries.
- Structurally invalid but syntactically valid JSON is rejected with `JournalStoreError` instead of leaking inconsistent `AttributeError`/`TypeError` behavior into journal operations.
- Regression coverage verifies invalid root/list/null/user-entry structures are rejected and the original file remains unchanged.
- Implementation head `b1415472efa6ebffcbea6bba86535597c28501bb` completed the required 7-workflow GitHub Actions set successfully.
- Railway commit status for the exact implementation head is `success`.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-051
Phase: Phase 2 — Core Architecture / Telegram Reliability
Title: Telegram Journal Entry Schema Validation
Implementation Status: VERIFIED
Evidence:
- The journal boundary now validates required fields, optional/defaulted fields, accepted scalar types, and rejects unknown entry fields before constructing `JournalEntry`.
- Persisted invalid entry shapes fail closed with controlled `JournalStoreError` behavior instead of leaking `TypeError`/`AttributeError` from dataclass construction or later journal operations.
- Legacy entries that omit optional fields continue to use the dataclass defaults.
- Regression coverage verifies missing required fields, invalid numeric types, unknown fields, and legacy optional-field compatibility.
- Implementation head `210922f91584c6d713d67bed192fa7b4f6796de1` passed all 7 required GitHub Actions workflows: Test, Production Readiness, Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, and Final Integration Gate.
- Railway commit status for the exact implementation head is `success`.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-052
Phase: Phase 2 — Core Architecture / Application Lifecycle Reliability
Title: Partial Service Startup Cleanup
Implementation Status: VERIFIED
Evidence:
- `ServiceManager.start_all()` now explicitly invokes the failed service's `stop()` cleanup path before handling already-started services.
- Regression coverage verifies cleanup for both critical and non-critical failed-start services and confirms startup continues for non-critical failures.
- Implementation head `0b97e1487bdb6b1d944f4957b6a4e782dc6713f5` passed the required GitHub Actions gate set successfully.
- No local execution is claimed.

## TASK-053
Phase: Phase 2 — Core Architecture / Application Lifecycle Reliability
Title: Started-Service Shutdown Tracking
Implementation Status: VERIFIED
Evidence:
- `ServiceManager.stop_all()` previously attempted to stop every registered service, including services that never started or had already failed startup and been cleaned up.
- This violated the lifecycle boundary and could invoke `stop()` on an uninitialized service or perform duplicate cleanup after startup failure.
- `ServiceManager` now tracks successfully started services explicitly and `stop_all()` only targets that lifecycle set.
- Successfully stopped services are removed from the tracked set; services whose `stop()` fails remain tracked so a later shutdown attempt can retry cleanup.
- Regression coverage verifies reverse start-order shutdown, no shutdown of never-started services after critical failure, and retry after stop failure.
- Implementation commits: `b82b5c5a31fc57f2b484849df9e397d67c446a93`, `98db3b8c0f6a0580212dbe93a11a71b346f50f32`.
- Exact final implementation/docs head `15a85e37d866e2f4f6bf75e5c427ca394f3b3cd2` passed all 7 required GitHub Actions workflows: Test, Production Readiness, Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, and Final Integration Gate.
- Railway commit status for the exact head is `success`.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-054
Phase: Phase 2 — Core Architecture / Application Lifecycle Reliability
Title: Failed-Start Cleanup Retry Tracking
Implementation Status: VERIFIED
Evidence:
- Audit found that a service whose `start()` failed was cleaned up once, but if its `stop()` cleanup also failed, it was not retained in `_started_services` and therefore could never be retried by `stop_all()`.
- `ServiceManager.start_all()` now retains a failed-start service in the lifecycle tracking set until its cleanup succeeds.
- Critical-service startup failure still raises after cleanup of previously started services, while the failed service remains retryable if its own cleanup failed.
- Regression coverage verifies a failed non-critical start with failed cleanup is retained and successfully retried during `stop_all()`.
- Implementation commit: `689920a13f6ade3a41bea3d28fc3d1fd40c1a3e3`.
- Test commit: `50d456f1cebd5e2bccc2789254894b683182ae94`.
- Final docs head `4208e6d17fdbca79bdf30b5434d17607857ee7ad` passed all 7 required GitHub Actions checks successfully: `test`, `production-e2e-contract`, `final-gate`, `activation-validation`, `dependency-audit`, `readiness`, and `activation-gate`.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-055
Phase: Phase 2 — Core Architecture / Worker Lifecycle Reliability
Title: Worker Queue Resource Lifecycle
Implementation Status: VERIFIED
Evidence:
- Audit found a concrete resource-lifecycle gap: `WorkerDispatcher.from_settings()` creates a durable `WorkerQueue`, but `WorkerProcessingService.stop()` previously did nothing, so the SQLite connection owned by the application service was not closed during normal application shutdown.
- `WorkerDispatcher.close()` now closes and releases its owned queue resource; `WorkerProcessingService.stop()` delegates to that boundary.
- Regression coverage verifies service shutdown releases the dispatcher queue and that dispatcher close is idempotent.
- No production behavior or worker workload contract was changed; this is application resource cleanup only.
- Implementation commits: `d67a9a3a96c8bafd64978caa46dfa9af044c1a7f`, `4e2c0478284d0077aff587f4978c47eedc561bc2`, `adfc8733105c8adbdc498d8ec8f3bd9f3e11acd3`.
- Descendant exact head `d904bd4bbb37e0970fc9579b07e56bf6cddd2e95` passed all 7 required GitHub Actions workflows and has successful Railway commit status; these gates include the full test suite and production contract gates covering the TASK-055 implementation.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-056
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: ProviderManager Concurrent Failure-State Isolation
Implementation Status: VERIFIED
Evidence:
- Audit found that `_last_failures` was a shared mutable list reset at the start of every `get_candles()` request, so overlapping asyncio requests could overwrite or mix failure diagnostics belonging to different requests.
- Provider retry/fallback/cooldown behavior was otherwise preserved; the fix is limited to request-scoped failure diagnostics.
- `ProviderManager` now stores `last_failures` in an asyncio task/context-local `ContextVar` and `_request_with_retry()` appends to a request-local failure list.
- The final `ApplicationError.details["failures"]` is built from the same request-local list, so concurrent requests cannot report another request's failures.
- Regression coverage in `tests/test_provider_manager_concurrency.py` overlaps two failing provider requests and verifies that each request retains only its own failure diagnostics.
- Implementation commit: `8b74f42d9d5ae3d2ae12a317cc126310458ed396`.
- Regression test commits: `13a5790b72463797ed4ebe2130cd64842c2a44f1`, `a91e8476c8924f229929011474921d4ad3431908`.
- Exact head `d904bd4bbb37e0970fc9579b07e56bf6cddd2e95` passed all 7 required GitHub Actions workflows: Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, Test, Production Readiness, and Final Integration Gate.
- Railway commit status for the exact head is `success`.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## Deferred Roadmap Issues
- #44 — PC Worker request hardening and endpoint contract audit — implemented as TASK-029 and closed.
- #45 — PC Worker readiness enforcement at job-dispatch boundary — implemented as TASK-030.
- #46 — Worker observability and operational contract audit — implemented as TASK-031.
- #47 — Canonical market-data application boundary — implemented as TASK-036.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
