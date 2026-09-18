# Engineering Decisions

## ADR-001 — Persistent repository memory
Date: 2026-09-12
Problem: Chat history is not a reliable persistence mechanism for a multi-session engineering mission.
Options:
1. Rely on chat history.
2. Maintain external notes only.
3. Store concise, versioned engineering state inside the repository.
Chosen Solution: Option 3.
Reason: The repository is the authoritative engineering artifact and survives conversation resets.
Trade-offs: Adds documentation maintenance overhead; mitigated by concise structured state and checkpoint discipline.
Affected Components: `docs/engineering/*`, future engineering workflow.

## ADR-002 — High-level architecture mapping before refactoring
Date: 2026-09-12
Problem: The repository contains overlapping/legacy-looking areas (notably Telegram, decision/risk, and strategy paths).
Chosen Solution: Map actual ownership and contracts first; avoid mass rewrites until concrete production problems are evidenced.
Reason: Prevents unnecessary architectural churn and protects working behavior.
Trade-offs: Short-term duplication may remain while contracts are verified.
Affected Components: Telegram, analysis, decision/risk, strategy.

## ADR-003 — PC Worker is for Trading Intelligence Platform workloads, not local coding-agent infrastructure
Date: 2026-09-12
Problem: The worker runtime had an accidental `coding_agent` workload and an Ollama bootstrap path that were unrelated to the platform's heavy application-processing responsibility.
Chosen Solution: Keep the worker focused on genuine platform workloads and remove the local coding-agent path from the active runtime.
Reason: A local coding agent is not part of the trading platform architecture and would create an unnecessary runtime/configuration dependency.
Affected Components: worker runtime, worker configuration, architecture documentation.

## ADR-004 — Do not carry forward non-application worker tasks
Date: 2026-09-12
Problem: A residual worker task remained after the accidental coding-agent/Ollama architecture was removed.
Chosen Solution: Remove it from the active roadmap without implementing speculative retry-specific architecture. Future retry/failure work must be introduced only when a concrete application, Processing Queue, or Heavy Worker requirement is evidenced.
Reason: Avoids architecture driven by a removed workload.

## ADR-005 — Engineering state must be synchronized with every verified task checkpoint
Date: 2026-09-12
Problem: Implementation work had advanced while persistent state documents still referenced older checkpoints.
Chosen Solution: After each verified task or state-changing checkpoint, update the authoritative engineering state documents before selecting the next task.
Reason: Prevents contradictory task selection and improves recoverability.
Affected Components: `docs/engineering/*`.

## ADR-006 — Keep public worker liveness minimal
Date: 2026-09-12
Problem: The PC Worker's unauthenticated `GET /health` endpoint exposed detailed runtime metadata.
Chosen Solution: Keep `/health` unauthenticated for simple liveness and return only `{"status":"READY"}`. Retain detailed readiness behind authenticated heartbeat transport.
Reason: Least-privilege information exposure.
Affected Components: worker health/heartbeat boundary.

## ADR-007 — Canonical application-facing market-data boundary
Date: 2026-09-12
Problem: Production Telegram callers directly constructed/used MarketDataEngine.
Chosen Solution: Use `services/market_data/service.py` (`MarketDataService`) as the canonical application-facing facade while preserving MarketDataEngine quality/freshness gates and ProviderManager routing/fallback.
Reason: Consolidates ownership without bypassing safety-critical validation.
Affected Components: market-data service and production callers.

## ADR-008 — Application-scoped market-data service lifetime
Date: 2026-09-13
Problem: Per-request MarketDataService construction discarded ProviderManager provider reuse and cooldown state.
Chosen Solution: Create one MarketDataService at Telegram application composition and retain scanner-specific provider selection only where readiness semantics require it.
Reason: Preserves lifecycle-owned provider state without a process-global singleton.
Affected Components: market-data service and Telegram/scanner paths.

## ADR-009 — Multi-Asset risk metadata must not inherit Forex defaults
Date: 2026-09-14
Problem: The repository explicitly supports Forex, Crypto, Stocks, Indices, and Commodities, but risk paths could force non-Forex symbols through Forex-only parsing and a Forex contract-size default.
Chosen Solution: Centralize symbol normalization/classification and derive quote currency and default contract size from asset metadata. Forex remains `100000`; the current spot-like non-Forex universe defaults to `1.0` unless an explicit override is supplied.
Reason: Prevents materially incorrect sizing and avoids rejecting supported non-Forex instruments.
Consequences: Provider/broker-specific contract specifications remain explicit overrides rather than being guessed globally.
Affected Components: `config/symbols.py`, `analysis/currency.py`, `analysis/risk_engine.py`, `analysis/position_sizing.py`, MarketAwareAnalysisEngine.

## ADR-010 — Explicit stablecoin currency boundary
Date: 2026-09-14
Problem: CurrencyConversion explicitly supported USDT/USDC while some downstream sizing/settings boundaries accepted only three-letter currencies.
Chosen Solution: Treat USDT and USDC as explicit supported stablecoin currencies across Settings, RiskEngine, PositionSizing, and CurrencyConversion, with unsupported four-letter currencies still rejected.
Reason: Keeps BTCUSDT/other supported crypto flows internally consistent without broadening the currency universe speculatively.
Affected Components: settings, currency conversion, risk, position sizing.

## ADR-011 — Provider reconfiguration is replacement, not merge
Date: 2026-09-14
Problem: `ProviderManager.set_providers()` could leave removed injected instances and stale lifecycle state reachable after reconfiguration.
Chosen Solution: Reconfiguration replaces the injected registry and prunes removed provider instances/cooldowns while preserving active factory cache state.
Reason: A removed provider must not be silently resurrected by name after configuration/readiness refresh.
Affected Components: `data/provider_manager.py`, provider lifecycle tests.

## ADR-012 — Configured risk policy is the ceiling for dynamic sizing
Date: 2026-09-14
Problem: Dynamic risk selection could choose up to `2.0%` without respecting a more restrictive configured `risk_percent`, allowing a production risk budget to be silently exceeded.
Chosen Solution: Treat configured `risk_percent` as an account-level ceiling for dynamic candidates. Dynamic logic may reduce risk but never silently exceed policy; explicit per-call overrides remain separately validated and authoritative.
Reason: Risk policy must be enforceable at the production boundary, not merely advisory to a heuristic.
Affected Components: `analysis/risk_engine.py`, risk sizing regression tests.

## ADR-013 — Canonical Telegram market-status contract
Date: 2026-09-14
Problem: The Telegram market-session helper emitted `STALE_DATA` instead of the platform's canonical `STALE` state, used a fixed stale threshold despite receiving a timeframe, assumed naive timestamps were UTC, and applied weekend closure globally.
Chosen Solution: Keep market status limited to `OPEN`, `CLOSED`, `STALE`, and `NO_DATA`; scale stale detection to six timeframe intervals; require timezone-aware timestamps and reject future timestamps; apply weekend closure only to non-crypto markets; pass symbol context from Scanner.
Reason: Status is a safety boundary for scan decisions and must remain consistent with the canonical market-data freshness model and centralized asset semantics.
Consequences: Invalid timestamp input fails closed as `NO_DATA`; scanner maps stale data through the canonical `STALE` status; 24/7 Crypto is not closed solely by calendar weekend.
Affected Components: `services/telegram/market_session.py`, `services/telegram/scanner.py`, `tests/test_market_session.py`.

## TASK-061 — Analysis Score Contract Boundary
The analysis layer's directional component scores are signed (`-100..100`), while DecisionEngine consumes a normalized `0..100` representation centered on neutral `50`. ConfidenceEngine must normalize directional analysis components at its input boundary using the same mapping. `volatility_score` is explicitly excluded because it is a non-directional ratio.

## Current Decision Guardrails
- Do not reintroduce Forex-only assumptions into a multi-asset repository.
- Do not invent contract size, conversion rates, session rules, or quantity precision where repository evidence does not establish them.
- Missing or unsupported conversion data must fail closed.
- Configured account risk is a hard ceiling for dynamic risk selection.
- Provider lifecycle state must reflect only the active provider configuration.
- Market status uses canonical `OPEN/CLOSED/STALE/NO_DATA` semantics.
- Exact-head GitHub Actions evidence is required before marking implementation checkpoints VERIFIED.


## ADR-014 — Provider Capability and Direct-Call Boundaries Must Agree
Date: 2026-09-18
Problem: A provider can correctly advertise a symbol capability while a lower-level direct request path still accepts a broader input set.
Chosen Solution: Concrete providers must make direct symbol normalization no broader than their declared capability boundary.
Reason: Direct provider callers must fail closed just like ProviderManager callers; otherwise the capability contract is only advisory.
Affected Components: OANDA provider and provider contract tests.

## ADR-015 — Canonical Market-Data Input Contract at the Engine Boundary
Date: 2026-09-18
Problem: The platform has a centralized multi-asset symbol/timeframe contract, but a lower-level application boundary could pass provider-facing identifiers without consistently enforcing that central contract.
Chosen Solution: MarketDataEngine validates the centralized supported-symbol universe and translates canonical internal timeframes explicitly into provider-facing identifiers.
Reason: Keeps application-facing market semantics independent from provider-specific naming and prevents malformed or unsupported market-data requests from reaching providers.
Affected Components: `data/market_data.py`, `config/symbols.py`, provider contract tests.

## ADR-016 — Analysis Numeric Boundaries Must Fail Closed
Date: 2026-09-18
Problem: The canonical indicator and market-structure layers could accept, skip, or neutralize invalid numeric inputs at lower-level boundaries even though the top-level analysis path validated its input.
Chosen Solution: Validate finite numeric inputs at both the canonical orchestration boundary and reusable analysis primitive boundaries; invalid scores must not be converted into neutral defaults.
Reason: Lower-level analysis APIs are independently callable and must not silently manufacture analytical state from invalid data.
Affected Components: `analysis/indicator_engine.py`, `analysis/market_structure/detector.py`, `analysis/indicators/*`.

## ADR-017 — One Effective Implementation per Analysis Helper Contract
Date: 2026-09-18
Problem: `analysis/indicator_engine.py` contained duplicate helper implementations in the same class, allowing later definitions to override earlier behavior without an explicit contract.
Chosen Solution: Remove duplicate helper blocks and keep one effective implementation for each helper.
Reason: Duplicate definitions create silent override risk and can invalidate earlier safety hardening.
Affected Components: `analysis/indicator_engine.py`.

## ADR-018 — Dormant AI Must Be Explicitly Opt-In
Date: 2026-09-19
Problem: The repository contained dormant AI capability while the example environment enabled it by default and readiness assumed enabled state when the variable was absent.
Chosen Solution: Make AI explicitly opt-in and keep it outside the canonical production analysis/scoring path.
Reason: A dormant optional capability must not appear active or influence trading decisions implicitly.
Affected Components: `.env.example`, `core/production_readiness.py`, `analysis/scoring.py`.

## ADR-019 — Non-Finite AI Values Must Fail Closed
Date: 2026-09-19
Problem: NaN/Infinity could bypass ordinary range checks for AI temperature or confidence normalization.
Chosen Solution: Reject non-finite configuration values and normalize non-finite AI confidence to the safe zero-confidence state.
Reason: Invalid numerical state must never be propagated into downstream decision/reporting contracts.
Affected Components: `config/settings.py`, `ai/parser.py`.


## ADR-020 — Market-Aware Analysis Must Preserve Market Identity and Freshness
Date: 2026-09-19
Problem: The canonical MarketDataService path already enforced symbol and freshness gates, but direct MarketAwareAnalysisEngine callers could provide Candle inputs whose symbol differed from the requested market or whose latest timestamp was stale/future-dated. That could cause analysis to be associated with one market while risk sizing used another market's metadata.
Chosen Solution: At the MarketAwareAnalysisEngine boundary, validate Candle identity against the canonical requested symbol and apply the canonical six-candle freshness policy before analysis/risk evaluation. Preserve existing legacy candle-like compatibility when inputs do not expose market metadata.
Reason: The decision/risk boundary must not trust caller-supplied market identity or stale market data merely because the upstream canonical service normally validates it.
Affected Components: `analysis/market_aware_engine.py`, `tests/test_market_aware_engine.py`.
