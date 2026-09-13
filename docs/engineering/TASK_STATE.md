# Task State

## PRE-TASK-004 — AUDITED
Phase: Phase 2 — Repository/Core Architecture
Title: Phase 2 scope that existed before TASK-004
Implementation Status: AUDITED / NO SEPARATE HISTORICAL TASK CONTRACT RECOVERED
Evidence: TASK-004 is the first explicitly recorded Phase 2 implementation task after TASK-003. No independent pre-TASK-004 task specification was recoverable from persistent engineering state. The current architecture audit therefore treats the Master Prompt's explicit core-architecture requirements as the governing scope rather than inventing historical work.
Concrete gaps identified by the audit are tracked as normal evidence-backed Phase 2 tasks.

## TASK-001
Phase: Phase 1 — Repository Audit
Implementation Status: COMPLETE

## TASK-002
Phase: Phase 1 — Baseline Stabilization
Implementation Status: COMPLETE

## TASK-003
Phase: Phase 1 — Production Verification / Reliability Hardening
Implementation Status: COMPLETE
Test Status: PASS — live health and restart/recovery evidence verified.

## TASK-004 through TASK-013
Phase: Phase 2 — Core Architecture
Implementation Status: COMPLETE
Test Status: PASS via GitHub Actions.

## TASK-014
Phase: Phase 2 — Core Architecture
Title: PC Worker Scope and Configuration Boundary Hardening
Implementation Status: VERIFIED

## TASK-015
Phase: Phase 2 — Core Architecture
Title: Worker Job Lifecycle Reliability
Implementation Status: VERIFIED

## TASK-016 — REMOVED
Phase: Phase 2 — Core Architecture
Title: Worker Retry and Failure Lifecycle
Status: REMOVED FROM ROADMAP
Reason: Carried forward from the previous planning path and not independently required by the final Forex-only Master Prompt. No implementation was performed.
Checkpoint: Removed 2026-09-12.

## TASK-017
Phase: Phase 2 — Core Architecture
Title: Remove Residual Non-Forex Worker Workload
Implementation Status: VERIFIED

## TASK-018
Phase: Phase 2 — Core Architecture
Title: Durable Forex Worker Processing Queue Contract
Implementation Status: VERIFIED

## TASK-019
Phase: Phase 2 — Core Architecture
Title: Forex Worker Queue Crash-Recovery Contract
Implementation Status: VERIFIED

## TASK-020
Phase: Phase 2 — Core Architecture
Title: Activate Forex Worker Queue Crash Recovery
Implementation Status: VERIFIED

## TASK-021
Phase: Phase 2 — Core Architecture
Title: Forex Worker Queue Persistence Configuration Boundary
Implementation Status: VERIFIED

## TASK-022
Phase: Phase 2 — Core Architecture
Title: Wire Heavy Forex Worker Through the Application Service Boundary
Implementation Status: VERIFIED

## TASK-023
Phase: Phase 2 — Core Architecture
Title: Verify and harden the real heavy-Forex workload routing boundary
Implementation Status: VERIFIED — AUDIT COMPLETE
Evidence: Repository search found worker-owned heavy Forex executors/contracts but no real Forex domain caller submitting `JobRequest` through `WorkerProcessingService`. Phase 9 Backtesting / Simulation remains `NOT_STARTED`, so no speculative caller was introduced.

## TASK-024
Phase: Phase 2 — Core Architecture
Title: PC Worker Authenticated Heartbeat Contract
Implementation Status: VERIFIED

## TASK-025
Phase: Phase 2 — Core Architecture
Title: Worker Processing Health/Readiness Contract
Implementation Status: VERIFIED

## TASK-026
Phase: Phase 2 — Core Architecture
Title: Worker Heartbeat Observability
Implementation Status: VERIFIED

## TASK-027
Phase: Phase 2 — Core Architecture
Title: PC Worker Heartbeat Freshness Contract
Implementation Status: VERIFIED

## TASK-028
Phase: Phase 2 — Core Architecture / Security Hardening
Title: Minimize Unauthenticated PC Worker Health Information Exposure
Implementation Status: VERIFIED

## TASK-029
Phase: Phase 2 — Core Architecture / Security Hardening
Title: PC Worker Authenticated Job Request Boundary Hardening
Implementation Status: VERIFIED

## TASK-030
Phase: Phase 2 — Core Architecture / Reliability Hardening
Title: PC Worker Readiness Enforcement at Job-Dispatch Boundary
Implementation Status: VERIFIED

## TASK-031
Phase: Phase 2 — Core Architecture / Observability
Title: Worker Observability and Operational Contract Audit
Implementation Status: VERIFIED

## TASK-032
Phase: Phase 2 — Core Architecture
Title: Telegram Architecture Ownership Audit / Consolidation
Implementation Status: VERIFIED
Evidence: Canonical Telegram ownership is under `services/telegram/`; inactive legacy Telegram trees were removed after repository-wide reference audit. Final Gate `34714087357`, job `103607956046`: success.

## TASK-033
Phase: Phase 2 — Core Architecture
Title: Decision/Risk/Strategy Architecture Ownership Audit
Implementation Status: VERIFIED
Evidence: Canonical ownership is `analysis/decision_engine.py` for decision logic and `analysis/risk_engine.py` for risk logic. Unused overlapping `analysis/risk_manager.py`, `risk/manager.py`, `signal_engine/`, and `strategy/` trees were removed after repository-wide reference/call-site inspection. Final Integration Gate `34715036954`, job `103610652082`: success.

## TASK-034
Phase: Phase 2 — Core Architecture
Title: Analysis Architecture Ownership Audit
Implementation Status: VERIFIED
Evidence: Unused alternate analysis architecture was removed and `analysis/full_engine.py` remains canonical. Current verified checkpoint had completed CI evidence.
Checkpoint: Verified 2026-09-12.

## TASK-035
Phase: Phase 2 — Core Architecture
Title: AI Architecture Ownership Audit
Implementation Status: VERIFIED — DORMANT / UNWIRED
Evidence: Repository-wide searches found no production/test caller constructing `AIOrchestrator`, `AIProviderManager`, `AIContextBuilder`, or `OpenAIProvider`. The `ai/` package remains dormant future Phase 6 capability and is not part of the active trading path.
Checkpoint: Verified 2026-09-12.

## TASK-036
Phase: Phase 2 — Core Architecture
Title: Market Data Ownership Consolidation
Implementation Status: VERIFIED
Evidence: Production Telegram candle retrieval routes through `MarketDataService`, preserving `MarketDataEngine` quality/freshness gates and `ProviderManager` routing. Scanner keeps explicit provider-manager selection only for its provider-readiness semantics. Implementation head `6174463174d8c6c4ad513896ad7ff96847e85edc` has completed CI gates and successful Railway status.
Checkpoint: Verified 2026-09-12.

## TASK-037
Phase: Phase 2 — Core Architecture
Title: Dormant Direct OANDA Price Surface Audit
Implementation Status: VERIFIED
Test Status: PASS — GitHub Actions run `34719290035` completed successfully for commit `65ea6150fa23895ad5655e59dbc9349945e67f96`.
Evidence:
- Repository-wide inspection found `get_latest_oanda_price` only in `data/market_data.py` with no production caller.
- The direct OANDA price surface was removed.
- The canonical OANDA candle path remains through `MarketDataEngine` / `ProviderManager`.
- Railway commit status for `65ea6150fa23895ad5655e59dbc9349945e67f96` is `success`.
Checkpoint: Verified 2026-09-12.

## TASK-038
Phase: Phase 2 — Core Architecture
Title: Market Data Lower-Level Facade / Alternate Ownership Audit
Implementation Status: VERIFIED
Test Status: PASS — GitHub Actions gates completed successfully for implementation commit `c2b772e1d37c0f06524da42f735b9913888234e4`.
Evidence:
- `DataManager(` construction existed only in tests; no production caller was found.
- `ExplicitProviderManager` had no production caller outside the dormant DataManager path.
- `data/manager.py`, `data/explicit_provider_manager.py`, and their focused tests were removed.
- `MarketDataService` was reduced to the canonical `MarketDataEngine` delegation contract.
Checkpoint: Verified 2026-09-12.

## TASK-039
Phase: Phase 2 — Core Architecture
Title: Provider-Specific Market Data Adapter Surface Audit
Implementation Status: VERIFIED
Test Status: PASS — implementation commit `044ab88fb83f7f929887fb8823d67a811c67e8a5` has successful Railway commit status; provider-specific market data methods and focused tests were removed and the canonical provider-neutral path remains intact.
Evidence:
- `get_finnhub_candles`, `get_oanda_candles`, and `get_alphavantage_intraday` were found only in `data/market_data.py` and focused contract tests; no production caller was found.
- The canonical path remains provider-neutral: `MarketDataService → MarketDataEngine → ProviderManager`.
- The provider-specific adapter methods and their focused tests were removed in commit `044ab88fb83f7f929887fb8823d67a811c67e8a5`.
Checkpoint: Verified 2026-09-12.

## TASK-040
Phase: Phase 2 — Core Architecture / Reliability
Title: ProviderManager Lifecycle and State Contract Audit
Implementation Status: VERIFIED
Test Status: PASS — commit `b4bfd674bf01c2fd8a1cadce62c13f273fc5d033`; Production Activation Validation and Security Audit completed successfully.
Evidence:
- `set_providers()` explicitly retains injected provider instances by contract; removing those retained objects would have contradicted the documented lifecycle behavior.
- Regression coverage was added for active-priority replacement while preserving injected instances.
- Regression coverage was added for replacing an injected instance when the same canonical provider name is rebound.
Checkpoint: Verified 2026-09-12.

## TASK-041
Phase: Phase 2 — Core Architecture / Reliability
Title: MarketDataEngine Output-Surface and Compatibility Audit
Implementation Status: VERIFIED
Test Status: PASS — implementation was an evidence-backed compatibility audit; the existing DataFrame surface remains intentionally retained because focused contract tests cover it and no safe evidence justified removal.
Evidence:
- Production `MarketDataService` uses the canonical `get_candles_list()` path.
- `MarketDataEngine.get_candles()` remains covered by focused contract tests, so it was not removed merely because no current internal production caller was found.
- `analysis.market_structure` uses its own internal candle-to-DataFrame conversion and is not a duplicate `MarketDataEngine` ownership path.
- The compatibility `analysis/candle.py` module resolves to the canonical `data.models.Candle` model rather than maintaining a second candle dataclass.
Checkpoint: Verified 2026-09-12.

## TASK-042
Phase: Phase 2 — Core Architecture / Reliability
Title: MarketDataService Construction Boundary Hardening
Implementation Status: VERIFIED
Test Status: PASS — GitHub Actions `Test` run `34720757481`, job `103626042716`, completed successfully; Production Activation Validation run `34720757426` and Production E2E Contract Gate run `34720757376` completed successfully.
Evidence:
- `services/telegram/scanner.py` previously constructed `MarketDataEngine` directly, bypassing the application-facing `MarketDataService` boundary.
- `MarketDataService` now supports explicit `ProviderManager` injection while retaining the existing direct-engine compatibility contract and rejecting simultaneous `engine` and `provider_manager` injection.
- Scanner now constructs `MarketDataService(provider_manager=provider_manager)` without directly constructing `MarketDataEngine`.
- Focused tests cover provider-manager construction and mutual-exclusion behavior.
- A follow-up contract-test compatibility fix was committed as `e2f7f189b84d611e2806bc050ebe347766f77f4a`; all observed Actions gates for that head completed successfully.
Checkpoint: Verified 2026-09-12.

## TASK-043
Phase: Phase 2 — Core Architecture / Reliability
Title: MarketDataService Lifetime and Application Composition Hardening
Implementation Status: VERIFIED
Test Status: PASS — Production Readiness run `34721145994`, Production Activation Validation run `34721150684`, and Production E2E Contract Gate run `34721147175` completed successfully for head `abe8e0db1d98e3c7ac3d6ffd09330604463656d9`.
Evidence:
- Telegram callers were audited for repeated `MarketDataService()` construction that recreated `MarketDataEngine` / `ProviderManager` state.
- A single application-scoped `MarketDataService` is now composed and reused by Telegram signal, callback, and tracker paths.
- Scanner remains intentionally separate due to distinct provider-readiness contract.
- Regression coverage was added for application-scoped market-data lifetime/state reuse.
- ADR-008 records the lifetime decision.
Checkpoint: Verified 2026-09-12.

## TASK-044
Phase: Phase 2 — Core Architecture / Reliability
Title: Scanner ProviderManager Lifetime and Readiness Boundary Audit
Implementation Status: VERIFIED
Test Status: PASS — Final Integration Gate run `34721606858`, job `103628419256`; Production Activation Validation run `34721606855`, job `103628419303`; Production E2E Contract Gate run `34721606841`, job `103628419217` all completed successfully.
Evidence:
- Repository-wide inspection confirmed the Telegram callback is the real application caller of `scan_market()`; no scheduler/background caller requiring a separate scanner-manager lifecycle was found in the current code path.
- Repeated Telegram scans previously rebuilt `ProviderManager`, discarding provider instances, cooldowns, and failure state.
- Scanner now exposes `get_scanner_provider_manager(application)` and retains the manager in `Application.bot_data`, preserving state without making it process-global.
- Provider readiness is recalculated on every retrieval, and `set_providers()` refreshes the active configured-provider order on the retained manager, preserving dynamic readiness behavior.
- `scan_market()` accepts an optional manager for application composition while retaining `_build_provider_manager()` fallback for direct/non-application callers.
- Regression coverage verifies manager identity reuse and provider-readiness changes across repeated application calls.
- Implementation commits: `680fc4cd447d770fb7013563d0d538a04e8cc4d2`, `99dc8679680590d96641e574b00716f637b4988d`, `7180828f4c3b12e7bb30588b614941cc662c0154`.
Checkpoint: Verified 2026-09-13.

## TASK-045
Phase: Phase 2 — Core Architecture / Telegram Reliability
Title: Telegram Signal Tracker Contract Audit
Implementation Status: VERIFIED
Test Status: PASS — implementation correction commit `276be55c75f54cdffbd82aadbb3e7f53fa97240a` passed the required GitHub Actions gates.
Evidence:
- Focused regression coverage was added for tracker replacement, idempotent stop, BUY stop-loss handling, BUY target handling, and signal-change timestamp/update behavior.
- CI exposed a test-double mismatch around the tracker's asynchronous notification callback; the correction changed the test callback to async without changing production behavior.
- Production Activation Validation run `34742847128`: success.
- Production Activation Gate run `34742847126`: success.
- Production Readiness run `34742847163`: success.
- Production E2E Contract Gate run `34742847216`: success.
- Final Integration Gate run `34742847153`: success.
- Test run `34742847146`: success.
- Security Audit run `34742847130`: success.
Checkpoint: Verified 2026-09-13.

## TASK-046
Phase: Phase 2 — Core Architecture / Telegram Reliability
Title: Telegram User State Contract Coverage
Implementation Status: VERIFIED
Test Status: PASS — implementation commit `2970f7224a12db64353d0e70b9932d65c8e48a6c` passed all observed required GitHub Actions gates.
Evidence:
- Added focused regression coverage for creation/reuse of per-user state, mutation of `current_menu`, and isolation of mutable `settings` between users.
- Production Activation Validation run `34742956007`, job `103685663171`: success.
- Security Audit run `34742955998`, job `103685663261`: success.
- Production E2E Contract Gate run `34742956014`, job `103685663284`: success.
- Test run `34742956032`, job `103685663329`: success; lifecycle/persistence tests, full test suite, application health, Telegram import, signal lifecycle import, and syntax checks all succeeded.
- Production Activation Gate run `34742955996`, job `103685663235`: success.
- Production Readiness run `34742956006`, job `103685663216`: success.
- Final Integration Gate run `34742955999`, job `103685663094`: success; compile, runtime safety, full test suite, and production Docker build succeeded.
- No local execution is claimed.
Checkpoint: Verified 2026-09-13.

## Deferred Roadmap Issues
- #44 — PC Worker request hardening and endpoint contract audit — implemented as TASK-029 and closed.
- #45 — PC Worker readiness enforcement at job-dispatch boundary — implemented as TASK-030.
- #46 — Worker observability and operational contract audit — implemented as TASK-031.
- #47 — Canonical market-data application boundary — implemented as TASK-036.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative feature work and broad rewrites. Never introduce local coding-agent, Ollama, or unrelated agent architecture into this Forex repository.
