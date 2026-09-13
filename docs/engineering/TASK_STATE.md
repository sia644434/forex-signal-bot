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
- The journal boundary validates required fields, optional/defaulted fields, accepted scalar types, and rejects unknown entry fields before constructing `JournalEntry`.
- Persisted invalid entry shapes fail closed with controlled `JournalStoreError` behavior instead of leaking `TypeError`/`AttributeError` from dataclass construction or later journal operations.
- Legacy entries that omit optional fields continue to use the dataclass defaults.
- Regression coverage verifies missing required fields, invalid numeric types, unknown fields, and legacy optional-field compatibility.
- Implementation head `210922f91584c6d713d67bed192fa7b4f6796de1` passed all 7 required GitHub Actions workflows.
- Railway commit status for the exact head is `success`.
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
- `ServiceManager.stop_all()` now targets only successfully started services and retains failed stops for retry.
- Regression coverage verifies reverse-order shutdown, no shutdown of never-started services, and retry after stop failure.
- Exact final implementation/docs head `15a85e37d866e2f4f6bf75e5c427ca394f3b3cd2` passed all 7 required GitHub Actions workflows and Railway commit status was `success`.
- No local execution is claimed.

## TASK-054
Phase: Phase 2 — Core Architecture / Application Lifecycle Reliability
Title: Failed-Start Cleanup Retry Tracking
Implementation Status: VERIFIED
Evidence:
- Failed-start services remain lifecycle-tracked when their cleanup also fails, allowing later `stop_all()` retry.
- Regression coverage verifies retryable cleanup after failed startup.
- Final docs head `4208e6d17fdbca79bdf30b5434d17607857ee7ad` passed all 7 required GitHub Actions checks successfully.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-055
Phase: Phase 2 — Core Architecture / Worker Lifecycle Reliability
Title: Worker Queue Resource Lifecycle
Implementation Status: VERIFIED
Evidence:
- `WorkerDispatcher.close()` now closes/releases its owned durable queue and `WorkerProcessingService.stop()` delegates to that boundary.
- Regression coverage verifies shutdown releases the queue and dispatcher close is idempotent.
- Descendant exact head `d904bd4bbb37e0970fc9579b07e56bf6cddd2e95` passed all 7 required GitHub Actions workflows and has successful Railway commit status.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-056
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: ProviderManager Concurrent Failure-State Isolation
Implementation Status: VERIFIED
Evidence:
- Audit found that `_last_failures` was a shared mutable list reset at the start of every `get_candles()` request, so overlapping asyncio requests could overwrite or mix failure diagnostics belonging to different requests.
- `ProviderManager` now stores `last_failures` in an asyncio task/context-local `ContextVar` and `_request_with_retry()` appends to a request-local failure list.
- The final `ApplicationError.details["failures"]` is built from the same request-local list, so concurrent requests cannot report another request's failures.
- Regression coverage overlaps two failing provider requests and verifies that each request retains only its own failure diagnostics.
- Exact head `d904bd4bbb37e0970fc9579b07e56bf6cddd2e95` passed all 7 required GitHub Actions workflows and Railway commit status was `success`.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-057
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: ProviderManager Cooldown State Consistency Across Reconfiguration
Implementation Status: VERIFIED
Evidence:
- The scanner retains an application-scoped `ProviderManager` but recalculates configured provider readiness on every scan and calls `set_providers()` with the current configured provider set.
- A provider that fails is placed into cooldown. `set_providers()` previously retained that cooldown even after the provider was removed from the active configuration.
- If the provider later became configured again, the stale cooldown could cause the newly re-enabled provider to be skipped until the old cooldown expired, delaying recovery after configuration/readiness changes.
- The fix retains cooldowns only for provider names that remain in the active configuration and removes cooldown state for providers removed by reconfiguration.
- Existing injected-provider retention/rebinding semantics are unchanged.
- Regression coverage verifies cooldown removal on provider removal and immediate usable recovery when the provider is re-added.
- Implementation commit: `705531c2f1e00a7fafbbca795a6844051c3b2235`.
- Regression test commit: `3282aa0053e3b82e5434ca8906c7804d8beca5a5c`.
- Final docs head `df7db987dfbe0a29529675aa1c8a528af52ef05b` passed the required 7-workflow GitHub Actions set successfully and Railway commit status is `success`.
- No local execution is claimed.

## TASK-058
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: FreshnessPolicy Explicit Zero-Threshold Validation
Implementation Status: VERIFIED
Evidence:
- Audit found that `FreshnessPolicy.assess()` used `warning_after or default`, `stale_after or default`, and `reject_after or default`.
- Because `timedelta(0)` is falsy, an explicitly supplied zero threshold silently became the default threshold instead of reaching `_validate_duration()` and being rejected as invalid.
- Fixed by using explicit `is not None` defaulting so only omitted thresholds receive defaults; explicitly supplied zero values now reach validation and raise `ValueError`.
- Regression coverage verifies zero is rejected independently for warning, stale, and reject thresholds.
- Implementation commit: `497076047e9b421ede7df2e80c89f61034d529fb`.
- Regression test commit: `d2ca6aec69a8329f762211e06b101126c6bac148`.
- Exact-head GitHub Actions verification completed successfully across the required 7-workflow gate set.
- Railway commit status for the verified implementation head is `success`.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## TASK-059
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: RiskEngine Decision-Score Symmetry
Implementation Status: VERIFIED
Evidence:
- Audit found that `DecisionEngine` emits a 0..100 score where 50 is neutral, but `RiskEngine` treated the score as if it were centered around zero by using `abs(score)`.
- This made bullish scores strong while equivalent bearish scores were treated as weak, affecting dynamic risk percentage, risk level, and trade-quality grading.
- Added a single symmetric directional-strength conversion: `abs((score - 50) * 2)`, mapping 0/100 to 100, 25/75 to 50, and 50 to 0.
- Applied the normalized strength consistently to dynamic risk percentage, risk level, and trade-quality calculations.
- Added regression coverage for symmetric score pairs and neutral-score behavior.
- Implementation commit: `a98411053c3433fe219b82abf82575547efc98b3`.
- Required 7-workflow GitHub Actions verification completed successfully after the CI trigger sequence; the final verification commit on `main` is `bb1e4464f0177fd612eeff2240aa096447275b2c`.
- Railway commit status for the final verified `main` head is `success`.
- The temporary CI trigger file was created only to activate push-based verification and was removed afterward.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## Current Phase 2 Audit State
TASK-059 is VERIFIED. Continue the evidence-backed analysis/reliability audit. Do not create another task unless a concrete correctness, reliability, security, observability, deployment, or recovery gap is demonstrated.

## Deferred Roadmap Issues
- #44 — PC Worker request hardening and endpoint contract audit — implemented as TASK-029 and closed.
- #45 — PC Worker readiness enforcement at job-dispatch boundary — implemented as TASK-030.
- #46 — Worker observability and operational contract audit — implemented as TASK-031.
- #47 — Canonical market-data application boundary — implemented as TASK-036.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
