# Multi-Layer Production Audit Batch — 2026-09-14

This document records the concrete repository-backed fixes applied during the cross-layer audit. Verification is tied to the exact resulting `main` HEAD and must not be inferred from implementation success alone.

## TASK-079 — Stablecoin Currency Boundary Consistency

- PositionSizing previously required every currency context to be exactly three letters.
- The repository already has an explicit USDT/USDC conversion policy, so BTCUSDT risk sizing could still fail at the final PositionSizing boundary.
- PositionSizing now accepts ordinary three-letter ISO-style codes plus the explicitly supported stablecoins USDT and USDC.
- Settings now accepts USDT/USDC as account currencies and normalizes them to uppercase.
- RiskEngine now accepts the same explicit stablecoin account-currency policy.
- Regression coverage verifies USDT identity sizing, USDT→USD sizing, malformed currency rejection, and Settings normalization.

Implementation commits:
- `75b08aa971f5074db72bfff3850cfb9d9739f46c`
- `ffbe2c4d8448e555481cf0a50ce6eeaafa358b3e`
- `6f4e28a36338810a4ecb97bbe6b0bb08e9df0e92`

Regression commits:
- `3ea3828a5ff065944f901cd7fcfcff0d45952d01`
- `4441b4b14e4f35db36f42f4cef25f06290d5346f`
- `761e7666b846a69d3e1b5cc07604a4747e738f3f`

## TASK-080 — Asset-Derived Risk Contract Size

- RiskEngine previously defaulted to Forex contract size `100000` even when called directly with a non-Forex symbol and no explicit contract size.
- This could produce materially incorrect crypto/stock/index/commodity sizing outside the MarketAware path.
- `RiskEngine.contract_size` is now optional. When omitted, it derives contract size from centralized instrument metadata.
- Forex retains `100000`, while the current spot-like non-Forex universe uses its explicit metadata default of `1.0`.
- An explicitly supplied contract size remains authoritative for broker/provider-specific overrides.
- Regression coverage verifies BTCUSDT sizing uses the asset-derived unit and USDT→USD conversion can be supplied explicitly.

Implementation commit:
- `6f4e28a36338810a4ecb97bbe6b0bb08e9df0e92`

Regression commit:
- `761e7666b846a69d3e1b5cc07604a4747e738f3f`

## TASK-081 — Central Symbol Normalization at Data-Quality Boundary

- DataQuality used a local normalization implementation that removed `_` only.
- The canonical symbol layer already supports `/`, `_`, and `-`, so equivalent symbols could disagree at the data-quality boundary.
- DataQuality now delegates symbol normalization to `config.symbols.normalize_symbol()`.
- Regression coverage verifies `eur/usd` and `EUR_USD` are treated as the same symbol.

Implementation commit:
- `a3c6f43bf76e0ab10b0cb721fdd0e18a20e04ddd`

Regression commit:
- `0cbe8b40c62fb6a0b561d0d94d72de10436dbaa5`

## TASK-082 — Provider Reconfiguration Lifecycle Isolation

- `ProviderManager.set_providers()` previously updated the injected-provider registry instead of replacing it.
- A removed injected provider could therefore remain reachable after reconfiguration and later be silently resurrected when the same provider name was configured as a string.
- Factory-created provider instances for removed providers could also remain cached outside the active provider set.
- Reconfiguration now replaces the injected registry and prunes factory-instance caches and cooldown state to the active provider set while preserving the cache for providers that remain active.
- Regression coverage verifies removed injected providers disappear, removed objects cannot be resurrected, and active factory caches remain stable.

Implementation commit:
- `46ba02295ddbc2629cca371ebbdafaba47a6a715`

Regression commits:
- `03cace1b483d1980c3db074bae1be240f487f53c`
- `54dfaa6591b90ebf9e99906cf14a10c73a30ea37`

## TASK-083 — Configured Risk Policy Ceiling for Dynamic Sizing

- `RiskEngine` accepted a configured `risk_percent`, but `_dynamic_risk_percent()` selected hard-coded candidates up to `2.0%` without considering the configured policy.
- A production configuration such as `risk_percent=0.25` could therefore be silently exceeded by a high-confidence/high-strength signal, creating a direct risk-budget bypass.
- Dynamic sizing now treats configured `risk_percent` as the account-level ceiling: confidence/score heuristics may select a lower percentage but can never silently exceed the configured maximum.
- An explicit `calculate(..., risk_percent=...)` override remains validated and authoritative for that call.
- Regression coverage verifies restrictive and non-restrictive ceilings and symmetric directional scoring.

Implementation commit:
- `d9c427b7f44a56db2c4f6c98b37e249a6df8af82`

Regression commit:
- `cbc09a3fefa6b5d97d77119cb8196f1d21da7604`

## ProviderManager CI Regression Synchronization

- The CI suite exposed a stale regression expectation for `set_providers()` after TASK-082 intentionally changed lifecycle semantics from merge/update to replacement.
- The regression test was synchronized with the new contract: removed injected providers must disappear from the active registry and cannot remain reachable through stale injection state.
- This is a test-contract correction, not a relaxation of the lifecycle safety behavior.

## Verification State

- The latest audit implementation and documentation checkpoints are present on `main`.
- Required GitHub Actions verification must always be evaluated against the exact final `main` HEAD after documentation synchronization.
- Until all required gates complete successfully, the latest audit batch remains `VERIFICATION PENDING`.
- Existing historical Railway/live verification remains valid only for the previously verified deployment checkpoint and must not be conflated with the current audit batch.

## Next Frontier

Continue the remaining cross-layer audit in this order:

`ProviderManager → MarketDataService → Freshness/DataQuality → Symbol/Asset Metadata → CurrencyConversion → MarketAwareAnalysisEngine → RiskEngine → PositionSizing → Telegram/Scanner/Tracker/Callbacks → Worker/Queue/Persistence → Security/Production → Final E2E`

Priorities:
- freshness/staleness propagation and fail-closed behavior
- provider retry/cooldown overflow and concurrency boundaries
- market-specific session/closure semantics
- symbol/asset metadata consistency
- conversion rate direction, freshness, and unavailable-data handling
- quantity/contract/lot semantics and precision/rounding
- account risk-budget preservation end-to-end
- Telegram and worker lifecycle/recovery contracts
- security and production hardening

Do not create a new task until a concrete repository-backed gap is demonstrated.
