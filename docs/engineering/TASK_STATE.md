# Task State

## TASK-001 through TASK-064
Phase 1/2 reliability and architecture tasks through DecisionEngine Supply/Demand consumption remain VERIFIED according to the persistent engineering history.

## TASK-065
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: ConfidenceEngine Numeric Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING

## TASK-066
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: FullAnalysisEngine Numeric Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING

## TASK-067
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: PositionSizing Decimal Numeric-Range Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Float-level finite validation was followed by Decimal quantization that could leak DecimalException for finite values exceeding active Decimal precision.
- PositionSizing converts that numeric-range failure to the public fail-closed ValueError contract.
- Regression coverage was added for the oversized-but-finite case.
- Implementation commit: `5967f1741e6e381fa83328d93f4f1b65d871b5dd`.
- Regression test commit: `307576dfddc63c079bed0c1fdeed16595fd7ad54`.

## TASK-068
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: RiskEngine Directional Price-Level Safety
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Deeper inspection of `RiskEngine → PositionSizing → CurrencyConversion → MarketAwareAnalysisEngine` found that finite risk distances could still produce economically invalid trade levels.
- A BUY setup could produce a zero/negative stop-loss when risk distance crossed the entry price; a SELL setup could produce non-positive take-profit levels.
- The output contract now rejects non-positive risk levels and enforces directional ordering for BUY and SELL plans before position sizing output is emitted.
- The validator preserves the existing custom risk-reward contract where TP2 and TP3 may legitimately coincide at a 3R target.
- Regression coverage added for zero-crossing, non-positive SELL targets, overflow, and normal directional ordering.
- Implementation commit: `b11d6429698aa749c1263f9fe65e6b4a0bac42dd`.
- Regression test commit: `131f0a656c694a9b6e4e88e4b1f7326032f91074`.

## TASK-069
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Explicit Account-Balance Wiring and Settings Numeric Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Production MarketAwareAnalysisEngine was constructing RiskEngine without the configured account balance.
- Settings now validates account balance/risk/currency policy and MarketAwareAnalysisEngine passes the configured balance explicitly.
- Regression coverage verifies the configured balance changes executable sizing and rejects malformed numeric/currency settings.
- Implementation commits: `d8880ee51cfb8b975b629c1e69b74cba4eb75f1b` and `7101d6e121bb0e71b5517221ef55d460b9bef10f`.
- Regression commits: `9703fff13d0064dcb4631ec388fc19ee268587a1` and `9da8a791c872a278bfef350600173d0332be362f`.
- Corrected fixture commit: `2a6fd7f3e874d0cda92b16b7eec04661e931d43c`.

## TASK-070
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Risk-Policy Upper-Bound and Currency-Context Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Standalone PositionSizing and RiskEngine accepted risk policies above 100%.
- RiskEngine account_currency could defer malformed values into later sizing failures.
- PositionSizing and RiskEngine now enforce `0 < risk_percent <= 100` and validate account currency at the boundary.
- Implementation commits: `39464db41d3b3478ec79322e455bf188607f7743` and `6d3eb873f6beb664ffe135002a9f976a3`.
- Regression commits: `917c8690331083a2cebc8d806b9c3849ec431322` and `24350c2eaf3de319d55a1dfd440e5daa3a16b901`.

## TASK-071
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Timestamp and Provider Timing Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- `Candle` previously treated `tzinfo is not None` as sufficient timezone awareness. A custom `tzinfo` can still return None from `utcoffset()`, leaving an effectively naive timestamp that can fail later during market-data timestamp arithmetic.
- The canonical Candle boundary now requires both `tzinfo` and a non-None `utcoffset()`.
- ProviderManager timing configuration previously accepted NaN/Infinity because ordinary non-negative comparisons do not reject non-finite floats. NaN could silently disable retry/cooldown timing checks and Infinity could create an effectively permanent cooldown.
- ProviderManager now requires finite, non-negative retry delay and cooldown values.
- Regression coverage added for invalid custom timezone objects and NaN/+Infinity/-Infinity provider timing configuration, while preserving zero-delay/zero-cooldown behavior.
- Implementation commits: `df70c0bbab22432541fbfcd05de99519fb35fdae` and `7c1eae02d920f4a15f47ef57bbe2d3fd6a3089f9`.
- Regression commits: `8a857af7a87c68566425a4ec34416b4ad68d1f35` and `89bbdf16c010de7de0ca333b332a6da21fd168f9`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## TASK-072
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Weekend Gap Detection Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- `DataQuality._is_expected_market_closure_gap()` treated any gap whose previous candle was Friday or whose current candle was Monday as a normal Forex closure.
- This could incorrectly mark large intraday Friday/Monday gaps as acceptable and suppress a real missing-data signal.
- The closure exception is now limited to an actual Friday-to-Monday date transition within the existing maximum weekend window.
- Focused regression coverage verifies a genuine Friday→Monday closure remains valid while large intraday Friday and Monday gaps remain invalid.
- Implementation commit: `7a322723e8bd1154ae7aaab5a8d8f48bf2790f3f`.
- Regression test commit: `32815e720c22197248b817a1d45f01182ed096eb`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## TASK-073
Phase: Phase 3 — Telegram / Scanner / Tracker Reliability
Title: Tracker Risk-Plan Synchronization
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Tracker refresh previously changed only `last_signal` when analysis flipped direction. Persisted signal, entry, stop-loss, and take-profit levels could therefore remain from the old direction.
- Tracker refresh now synchronizes the complete executable risk plan whenever the new analysis remains tradable. `WAIT`/`NO_TRADE` clears executable levels and marks the tracked item `INVALIDATED`.
- Regression coverage verifies BUY→SELL risk-plan synchronization and clearing executable levels on `NO_TRADE`.
- Implementation commits: `1b3a9cf1b80ac7daae5afd3c55f86d83419ce2fd` and related Telegram changes from the same audit step.
- Regression test commit: `4288ee926365af25d593d06b683e2d2bbaf1e8e6`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## TASK-074
Phase: Phase 2/3 — Multi-Asset Market and Risk Architecture
Title: Remove Forex-Only Assumptions from Market-Aware Risk Path
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Repository configuration already defines Forex, Crypto, Stocks, Indices, and Commodities, but `MarketAwareAnalysisEngine` and `RiskEngine` still called `get_forex_currency_pair()` for every symbol.
- This made supported non-Forex instruments such as `XAUUSD`, `BTCUSDT`, `AAPL`, and `SPX` fail before risk sizing even though they were explicitly declared supported markets.
- Added asset-aware quote-currency metadata and default contract-size metadata. Forex retains 100,000 base units; the current spot-like crypto/stock/index/commodity universe uses one underlying unit by default, preventing the Forex lot-size default from leaking into unrelated assets.
- MarketAwareAnalysisEngine now obtains quote currency and contract size from instrument metadata and passes the contract size into RiskEngine.
- RiskEngine now uses generic quote-currency metadata instead of Forex-only parsing.
- CurrencyConversionService now supports the repository's USDT-quoted crypto universe through an explicit USDT/USDC-to-USD equivalent policy and can bridge that quote to supported FX account currencies. Other unsupported conversions continue to fail closed.
- Regression coverage added for quote currency and contract-size metadata plus stablecoin conversion and bridging.
- Implementation commits: `094038f857f7d9f00cf492b071a540872f18b85d`, `33a070bbe4ffed6f1ad33eae60b37a24cb109732`, `c5cf2c9628dc3049cc3d071a8f18aaacf4deab17`, `d999fe3aef82fa11e1082792df3106a4eba74080`.
- Regression commits: `a10de135f2d9d4fd1a3c387e4b167525f5733832` and `fa77800d52d22578914630235a1d3cec777ff48f`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## TASK-075
Phase: Phase 7 — Worker / Queue / Persistence Reliability
Title: Targeted Queue Claims and Cancellation Recovery
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- `WorkerDispatcher.submit()` enqueued a request and then called `claim_next()`. Under concurrent submissions, the scheduler could allow another request to claim the highest-priority pending job, causing the original caller to return `PENDING` for work it had already submitted and creating a dispatch race around priority ordering.
- The durable queue now exposes an atomic targeted `claim(job_id)` operation while preserving `claim_next()` for generic consumers.
- Dispatcher submission now claims the exact request it enqueued, eliminating cross-request claim stealing.
- Dispatcher cancellation now transitions the claimed durable job to `CANCELLED` instead of re-raising `CancelledError` while leaving the SQLite record `RUNNING` until later crash recovery.
- Regression coverage verifies targeted claim semantics, concurrent dispatches completing their own jobs, and cancellation not stranding a running queue record.
- Implementation commits: `64f833d72903d1142273ec6db034ee1946e715e3` and `cc068e5d5fbab53175c67c25682bcf2e8863a286`.
- Regression commits: `04d870ed8bac9e198427516c474c609b5a46e5d8` and `2e20055af86a31160a323a9656bb49b26fa3146a`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## TASK-076
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Provider Result Compatibility Boundary
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- The ProviderManager rewrite narrowed `_validate_result()` from the previously supported `list`/`tuple` provider-result contract to `list` only.
- That was a behavioral regression at the provider boundary because adapters and direct callers may legitimately return tuples before canonicalization.
- `_validate_result()` now accepts both list and tuple results and canonicalizes the validated result to a list before downstream normalization.
- Regression coverage verifies both the asynchronous manager path and direct `_validate_result()` compatibility.
- Implementation commit: `b495c9ddbdc42881542df190cacbdc660bf72f0b`.
- Regression test commit: `f8721317fa34a3551bf89ebaa70f1a3fdd4a520e`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## TASK-077
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Asset-Aware Weekend Gap Semantics
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- The weekend-gap exception in `DataQuality` was globally applied even though the repository explicitly supports Crypto alongside weekend-closed markets.
- Crypto markets are 24/7, so a Friday→Monday gap cannot be assumed to be an expected closure and must remain a detectable data-quality gap.
- The gap policy now receives an explicit market type. Weekend closure handling remains available for Forex, Stocks, Indices, and Commodities, while Crypto is fail-closed for the same Friday→Monday gap.
- `MarketDataEngine` propagates the symbol's centralized asset classification into `DataQuality`, making the production path use the correct policy instead of relying on a Forex default.
- Regression coverage verifies Crypto Friday→Monday gaps are invalid while the existing Forex closure contract remains valid.
- Implementation commits: `228a613a5452521574b1204bbaf4699e070f2d4e` and `866ca9e30473b75ddd6d628cfbcc1ebd5b97282d`.
- Regression test commit: `c3d885443271ab6c9b9066cfc1757ff3960cfe40`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## TASK-078
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Market-Aware Risk State Isolation
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- `MarketAwareAnalysisEngine.analyze()` previously replaced the shared `FullAnalysisEngine.risk_engine` instance on every tradable analysis.
- A long-lived MarketAwareAnalysisEngine can be reused by Telegram/scanner/worker paths, so mutating that shared field creates cross-request state coupling and a race hazard when analyses overlap.
- RiskEngine is now created as a local per-analysis dependency and is used directly for the calculation, leaving the shared FullAnalysisEngine risk component untouched.
- Regression coverage verifies the shared risk-engine reference is not mutated by market-aware analysis.
- Implementation commit: `355ecc083c62e525af687e9478e469b66b27bb84`.
- Regression test commit: `137990c2337ed2015ab349e1d871a78d338fec36`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## Multi-Asset Architecture Contract
The project is a **Multi-Asset Trading Intelligence Platform**, not a Forex-only bot. Supported market families are represented centrally in `config/symbols.py`: Forex, Crypto, Stocks, Indices, and Commodities. A symbol must not be rejected merely because it is not Forex. Market-specific semantics such as quote currency, contract size, trading session, provider support, and conversion requirements must be explicit and must fail closed when unavailable.

## Current Audit Frontier
Continue the evidence-backed audit from:
`ProviderManager → MarketDataService → Freshness/DataQuality → Symbol/Asset Metadata → CurrencyConversion → MarketAwareAnalysisEngine → RiskEngine → PositionSizing`
then proceed outward into Telegram/Scanner/Tracker/Callbacks and Worker/Queue/Persistence.

Required checks:
- provider result validation and normalization
- retry/cooldown finite and overflow boundaries
- concurrency isolation of provider state and failure diagnostics
- freshness and stale-data fail-closed behavior
- market-specific session/closure semantics
- symbol normalization and asset classification
- quote-currency and contract-size metadata
- account-currency versus quote-currency unit semantics
- conversion-rate direction and pair orientation
- configured risk policy versus effective dynamic risk percentage
- risk amount versus risk-per-unit units
- lot/contract semantics per asset class
- rounding/precision behavior
- finite/positive/overflow/underflow boundaries
- missing/invalid/stale/unavailable conversion data
- end-to-end consistency between MarketDataService, CurrencyConversionService, MarketAwareAnalysisEngine, RiskEngine, and PositionSizing

Do not create another task until a concrete repository-backed gap is demonstrated.

## New-chat Continuation Contract
When a new chat starts work on this repository, first read:
- `docs/engineering/PROJECT_STATE.md`
- `docs/engineering/PHASE_STATE.md`
- `docs/engineering/TASK_STATE.md`
- `docs/engineering/TEST_STATE.md`
- `docs/engineering/ARCHITECTURE_MAP.md`
- `docs/engineering/DECISIONS.md`
- `docs/engineering/CHANGELOG_ENGINEERING.md`

Then:
1. Determine the exact current `main` HEAD.
2. Inspect GitHub Actions for that exact HEAD.
3. Resolve every pending or failed verification before moving deeper.
4. Do not repeat TASK-058 through TASK-078 unless verification evidence is missing or contradicted.
5. Continue from the first unresolved audit frontier recorded above.
6. Inspect more architecture than the previous step and only implement concrete repository-backed gaps.
7. Add focused regression coverage for every confirmed defect.
8. Verify the required GitHub Actions gate set before marking a task VERIFIED.
9. Treat the repository as a Multi-Asset Trading Intelligence Platform; do not reintroduce Forex-only assumptions. Do not introduce Data Analysis, local coding-agent/Ollama architecture, speculative features, or unrelated agent architecture.
10. Use GitHub Connector only for repository inspection and modification.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites.
