# Architecture Map — Multi-Asset Trading Intelligence Platform

## System Overview
Python multi-asset trading-intelligence application with Telegram interface, market-data/provider layer, modular analysis, decision/risk components, dormant/unwired AI/ML capability, PC Worker for heavy application processing, durable processing queue, and deployment/CI infrastructure.

## Canonical Boundaries
- Telegram: `services/telegram/`
- Market-data facade: `services/market_data/service.py`
- Market-data engine: `data/market_data.py`
- Provider routing/fallback: `ProviderManager`
- Analysis: `analysis/full_engine.py`
- Decision: `analysis/decision_engine.py`
- Risk: `analysis/risk_engine.py`
- Portfolio: `analysis/portfolio_engine.py`
- Position sizing: `analysis/position_sizing.py`
- Currency conversion: `services/market_data/currency_conversion.py`
- Heavy processing: `worker/`

## Multi-Asset Contract
The platform supports Forex, Crypto, Stocks, Indices, and Commodities through centralized symbol/asset metadata. Market-specific quote currency, contract size, session, provider capability, and conversion requirements must be explicit. Unsupported or unavailable conditions fail closed.

## Market Data
Canonical flow:
`Multi-Asset caller → MarketDataService → MarketDataEngine → ProviderManager → provider(s)`.
MarketDataEngine owns candle quality/freshness gates. ProviderManager owns provider routing/fallback/retry/cooldown. Provider capability mismatches fail closed instead of being treated as transient outages.

## Analysis / Decision / Risk
`analysis/full_engine.py` is the production analysis orchestrator.
Analysis produces analytical inputs → DecisionEngine produces the decision → RiskEngine applies risk policy → PositionSizing/CurrencyConversion provide sizing where required.
The dormant `ai/` package is not in canonical production scoring.

## Worker / Queue
`worker/` provides the PC Worker runtime, authenticated HTTP boundary, dispatcher, durable queue, and heavy executors. The worker is an application-processing component, not a local coding/model orchestration layer.

## Market Status
Canonical states are `OPEN`, `CLOSED`, `STALE`, and `NO_DATA`. Future/invalid timestamps and stale data fail closed; weekend closure is asset-aware and does not incorrectly treat Crypto as a non-24/7 market.

## Persistence
Worker queue and Telegram persistence boundaries are durable and fail closed on corruption/invalid state according to their established contracts.

## Security / Deployment
Production configuration, worker authentication/input validation, Docker non-root execution, secret/build-context exclusion, CI permissions, and dependency auditing were covered by the historical Phase-10 closure. Railway is an infrastructure target, not a core architecture dependency.

## Testing / CI
Current verification must always use the exact current `main` HEAD. Historical closure SHAs are evidence of prior states, not proof of current state.

## Current Integrity Status
- Historical Phases 1–11: closure evidence preserved.
- Phase 12: **reverification required** because the current HEAD has a failing Railway deployment status.
- Phase 13: blocked until Phase 12 and cross-phase integrity are resolved.

## Audit Rule
When concrete evidence reopens a phase, audit the full phase surface and dependent boundaries, not only the old task list. Fix related concrete defects together, add regression coverage, run the required verification set, and only then restore the phase to current-HEAD verified status.