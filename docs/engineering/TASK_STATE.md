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
- Regression commits: `9703fff13d0064dcb4631ec388fc19ee268587a1`, `9da8a791c872a278bfef350600173d0332be362f`, and corrected fixture `2a6fd7f3e874d0cda92b16b7eec04661e931d43c`.

## TASK-070
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Risk-Policy Upper-Bound and Currency-Context Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Standalone PositionSizing and RiskEngine accepted risk policies above 100%.
- RiskEngine account_currency could defer malformed values into later sizing failures.
- PositionSizing and RiskEngine now enforce `0 < risk_percent <= 100` and validate account currency at the boundary.
- Implementation commits: `39464db41d3b3478ec79322e455bf1886077f7743` and `6d3eb873f6beb664ffe135002a9f976a3`.
- Regression commits: `917c8690331083a2cebc8d806b9c3849ec431322` and `24350c2eaf3de319d55a1dfd440e5daa3a16b901`.

## TASK-071
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Timestamp and Provider Timing Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- `Candle` now requires both `tzinfo` and a non-None `utcoffset()`.
- ProviderManager now requires finite, non-negative retry delay and cooldown values.
- Regression coverage covers invalid custom timezone objects, NaN/Infinity timing values, and valid zero-delay/zero-cooldown behavior.
- Implementation commits: `df70c0bbab22432541fbfcd05de99519fb35fdae` and `7c1eae02d920f4a15f47ef57bbe2d3fd6a3089f9`.
- Regression commits: `8a857af7a87c68566425a4ec34416b4ad68d1f35` and `89bbdf16c010de7de0ca333b332a6da21fd168f9`.

## TASK-072
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Weekend Gap Detection Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- DataQuality now limits the weekend closure exception to a genuine Friday-to-Monday transition within the existing maximum weekend window.
- Regression coverage verifies genuine Friday→Monday closure while large intraday Friday/Monday gaps remain invalid.
- Implementation commit: `7a322723e8bd1154ae7aaab5a8d8f48bf2790f3f`.
- Regression test commit: `32815e720c22197248b817a1d45f01182ed096eb`.

## TASK-073
Phase: Phase 3 — Telegram / Scanner / Tracker Reliability
Title: Tracker Risk-Plan Synchronization
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Tracker refresh now synchronizes the complete executable risk plan on tradable direction changes.
- WAIT/NO_TRADE clears executable levels and marks the tracked item INVALIDATED.
- Regression coverage verifies BUY→SELL synchronization and NO_TRADE clearing.
- Implementation commits include `1b3a9cf1b80ac7daae5afd3c55f86d83419ce2fd`.
- Regression test commit: `4288ee926365af25d593d06b683e2d2bbaf1e8e6`.

## TASK-074
Phase: Phase 2/3 — Multi-Asset Market and Risk Architecture
Title: Remove Forex-Only Assumptions from Market-Aware Risk Path
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Central configuration explicitly supports Forex, Crypto, Stocks, Indices, and Commodities.
- MarketAwareAnalysisEngine and RiskEngine no longer force every symbol through Forex-only currency parsing.
- Added asset-aware quote currency and contract-size metadata; Forex uses 100000 while the current spot-like non-Forex universe defaults to 1.0.
- CurrencyConversion supports the repository's explicit USDT/USDC equivalent policy and supported bridging while failing closed for unsupported conversions.
- Regression coverage covers quote/contract metadata and stablecoin conversion.
- Implementation commits: `094038f857f7d9f00cf492b071a540872f18b85d`, `33a070bbe4ffed6f1ad33eae60b37a24cb109732`, `c5cf2c9628dc3049cc3d071a8f18aaacf4deab17`, `d999fe3aef82fa11e1082792df3106a4eba74080`.
- Regression commits: `a10de135f2d9d4fd1a3c387e4b167525f5733832` and `fa77800d52d22578914630235a1d3cec777ff48f`.

## TASK-075
Phase: Phase 7 — Worker / Queue / Persistence Reliability
Title: Targeted Queue Claims and Cancellation Recovery
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Added atomic targeted queue `claim(job_id)` and changed Dispatcher submission to claim the exact job it enqueued.
- Dispatcher cancellation now marks the durable job CANCELLED instead of stranding a RUNNING record.
- Regression coverage verifies targeted claims, concurrent dispatch ownership, and cancellation recovery.
- Implementation commits: `64f833d72903d1142273ec6db034ee1946e715e3` and `cc068e5d5fbab53175c67c25682bcf2e8863a286`.
- Regression commits: `04d870ed8bac9e198427516c474c609b5a46e5d8` and `2e20055af86a31160a323a9656bb49b26fa3146a`.

## TASK-076
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Provider Result Compatibility Boundary
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- ProviderManager `_validate_result()` now accepts both list and tuple results and canonicalizes them to list.
- Regression coverage verifies asynchronous manager and direct validation compatibility.
- Implementation commit: `b495c9ddbdc42881542df190cacbdc660bf72f0b`.
- Regression test commit: `f8721317fa34a3551bf89ebaa70f1a3fdd4a520e`.

## TASK-077
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Asset-Aware Weekend Gap Semantics
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Weekend-gap semantics now receive explicit market type.
- Forex, Stocks, Indices, and Commodities preserve weekend closure handling; Crypto is fail-closed for the same Friday→Monday gap because it is 24/7.
- MarketDataEngine propagates centralized symbol asset classification into DataQuality.
- Implementation commits: `228a613a5452521574b1204bbaf4699e070f2d4e` and `866ca9e30473b75ddd6d628cfbcc1ebd5b97282d`.
- Regression test commit: `c3d885443271ab6c9b9066cfc1757ff3960cfe40`.

## TASK-078
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Market-Aware Risk State Isolation
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- MarketAwareAnalysisEngine no longer replaces the shared FullAnalysisEngine risk_engine on every analysis.
- RiskEngine is instantiated locally per market-aware analysis, preventing cross-request state coupling.
- Regression coverage verifies the shared risk-engine reference remains unchanged.
- Implementation commit: `355ecc083c62e525af687e9478e469b66b27bb84`.
- Regression test commit: `137990c2337ed2015ab349e1d871a78d338fec36`.

## TASK-079
Phase: Phase 2 — Core Architecture / Market and Risk Reliability
Title: Stablecoin Currency Boundary Consistency
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- PositionSizing previously required exactly three-letter currencies despite explicit USDT/USDC conversion support.
- PositionSizing, Settings, and RiskEngine now share the explicit three-letter-plus-USDT/USDC currency policy.
- Regression coverage verifies USDT identity sizing, USDT→USD sizing, malformed currency rejection, and Settings normalization.
- Implementation commits: `75b08aa971f5074db72bfff3850cfb9d9739f46c`, `ffbe2c4d8448e555481cf0a50ce6eeaafa358b3e`, `6f4e28a36338810a4ecb97bbe6b0bb08e9df0e92`.
- Regression commits: `3ea3828a5ff065944f901cd7fcfcff0d45952d01`, `4441b4b14e4f35db36f42f4cef25f06290d5346f`, `761e7666b846a69d3e1b5cc07604a4747e738f3f`.

## TASK-080
Phase: Phase 2 — Core Architecture / Multi-Asset Risk Reliability
Title: Asset-Derived Risk Contract Size
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- RiskEngine no longer defaults direct non-Forex sizing to Forex contract size 100000.
- Contract size is derived from centralized asset metadata when no explicit override is supplied; explicit overrides remain authoritative.
- Regression coverage verifies BTCUSDT uses the asset-derived unit.
- Implementation commit: `6f4e28a36338810a4ecb97bbe6b0bb08e9df0e92`.
- Regression commit: `761e7666b846a69d3e1b5cc07604a4747e738f3f`.

## TASK-081
Phase: Phase 2 — Core Architecture / Market Data Reliability
Title: Central Symbol Normalization at Data-Quality Boundary
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- DataQuality now delegates symbol normalization to `config.symbols.normalize_symbol()` instead of maintaining a narrower local implementation.
- Regression coverage verifies `eur/usd` and `EUR_USD` semantic equivalence.
- Implementation commit: `a3c6f43bf76e0ab10b0cb721fdd0e18a20e04ddd`.
- Regression commit: `0cbe8b40c62fb6a0b561d0d94d72de10436dbaa5`.

## TASK-082
Phase: Phase 2 — Core Architecture / Provider Reliability
Title: Provider Reconfiguration Lifecycle Isolation
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- `ProviderManager.set_providers()` now replaces the injected provider registry instead of updating it in place.
- Removed providers are pruned from injected instances, factory caches, and cooldown state; active provider cache state is preserved.
- This prevents removed injected providers from being silently resurrected after reconfiguration.
- Regression coverage verifies removal, re-addition without stale cooldown, and same-name instance rebinding.
- Implementation commit: `46ba02295ddbc2629cca371ebbdafaba47a6a715`.
- Regression commits: `03cace1b483d1980c3db074bae1be240f487f53c` and `54dfaa6591b90ebf9e99906cf14a10c73a30ea37`.

## TASK-083
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Configured Risk Policy Ceiling for Dynamic Sizing
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- `_dynamic_risk_percent()` previously selected hard-coded candidates up to 2.0% without respecting the configured `risk_percent` ceiling.
- A restrictive production policy such as `risk_percent=0.25` could therefore be silently exceeded by a high-confidence/high-strength signal.
- Dynamic risk now uses the configured `risk_percent` as an account-level ceiling: the heuristic can reduce risk but cannot silently increase it above policy.
- Explicit per-call `risk_percent` remains validated and authoritative for that call.
- Regression coverage verifies restrictive and non-restrictive ceilings plus symmetric directional behavior.
- Implementation commit: `d9c427b7f44a56db2c4f6c98b37e249a6df8af82`.
- Regression commit: `cbc09a3fefa6b5d97d77119cb8196f1d21da7604`.

## Multi-Asset Architecture Contract
The project is a **Multi-Asset Trading Intelligence Platform**, not a Forex-only bot. Supported market families are represented centrally in `config/symbols.py`: Forex, Crypto, Stocks, Indices, and Commodities. A symbol must not be rejected merely because it is not Forex. Market-specific semantics such as quote currency, contract size, trading session, provider support, and conversion requirements must be explicit and must fail closed when unavailable.

## Current Audit Frontier
Continue the evidence-backed audit from:
`ProviderManager → MarketDataService → Freshness/DataQuality → Symbol/Asset Metadata → CurrencyConversion → MarketAwareAnalysisEngine → RiskEngine → PositionSizing`
then proceed outward into Telegram/Scanner/Tracker/Callbacks and Worker/Queue/Persistence, Security/Production, and Final E2E.

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
- conversion freshness and missing/invalid data behavior
- configured risk policy versus effective dynamic risk percentage
- risk amount versus risk-per-unit units
- lot/contract semantics per asset class
- rounding/precision behavior
- finite/positive/overflow/underflow boundaries
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
4. Do not repeat completed tasks unless verification evidence is missing or contradicted.
5. Continue from the first unresolved audit frontier recorded above.
6. Inspect more architecture than the previous step and only implement concrete repository-backed gaps.
7. Add focused regression coverage for every confirmed defect.
8. Verify the required GitHub Actions gate set before marking a task VERIFIED.
9. Treat the repository as a Multi-Asset Trading Intelligence Platform; do not reintroduce Forex-only assumptions. Do not introduce Data Analysis, local coding-agent/Ollama architecture, speculative features, or unrelated agent architecture.
