# Multi-Layer Production Audit Batch — 2026-09-14

This document records the concrete repository-backed fixes applied during the cross-layer audit. Verification remains pending until the required GitHub Actions gates for the resulting `main` HEAD finish.

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
- Forex therefore retains `100000`, while the current spot-like non-Forex universe uses its explicit metadata default of `1.0`.
- An explicitly supplied contract size remains authoritative for broker/provider-specific overrides.
- Regression coverage verifies BTCUSDT sizing uses the asset-derived unit and that USDT→USD conversion can be supplied explicitly.

Implementation commit:
- `6f4e28a36338810a4ecb97bbe6b0bb08e9df0e92`

Regression commit:
- `761e7666b846a69d3e1b5cc07604a4747e738f3f`

## TASK-081 — Central Symbol Normalization at Data-Quality Boundary

- DataQuality used a local normalization implementation that removed `_` only.
- The canonical symbol layer already supports `/`, `_`, and `-` forms, so equivalent symbols could disagree at the data-quality boundary.
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

- `RiskEngine` accepted a configured `risk_percent`, but when `calculate()` was called without an explicit per-call override, `_dynamic_risk_percent()` selected hard-coded values up to `2.0%` without considering the configured policy.
- This meant a production configuration such as `risk_percent=0.25` could be silently exceeded by a high-confidence signal, creating a direct risk-budget bypass.
- Dynamic sizing now treats configured `risk_percent` as the account-level ceiling: the confidence/score policy can select a lower percentage, but can never exceed the configured maximum.
- An explicit `calculate(..., risk_percent=...)` override remains validated and authoritative for that call.
- Regression coverage verifies symmetry, a restrictive configured ceiling, and behavior when the configured ceiling is above the dynamic candidate.

Implementation commit:
- `d9c427b7f44a56db2c4f6c98b37e249a6df8af82`

Regression commit:
- `cbc09a3fefa6b5d97d77119cb8196f1d21da7604`

## Verification

Resulting `main` HEAD:
- `cbc09a3fefa6b5d97d77119cb8196f1d21da7604`

GitHub Actions are running for the latest exact HEAD. No green/verified claim is made until the required gates complete.

## Next Frontier

After verification, continue with the remaining cross-layer audit:

`ProviderManager → MarketDataService → Freshness/DataQuality → Symbol/Asset Metadata → CurrencyConversion → MarketAwareAnalysisEngine → RiskEngine → PositionSizing → Telegram/Scanner/Tracker/Callbacks → Worker/Queue/Persistence → Security/Production → Final E2E`

Prioritize unit/contract semantics, conversion freshness/direction, provider concurrency isolation, and end-to-end consistency before adding speculative features.
