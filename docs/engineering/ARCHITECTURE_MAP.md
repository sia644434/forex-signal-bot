# Architecture Map — Multi-Asset Trading Intelligence Platform

## System Overview
The repository is a Python multi-asset trading-intelligence application with a Telegram interface, market-data/provider layer, modular analysis engines, risk/decision components, a dormant/unwired AI/ML package reserved for its later roadmap phase, a PC worker for heavy application processing, a durable worker processing queue, and deployment/CI infrastructure.

## Entry Points
- `main.py`: async process entry point.
- `app.py`: thin application factory wrapper.
- `core/application.py`: application composition root.
- `worker/main.py`: worker-side entry point for heavy application workloads.

## Telegram Layer
Canonical production ownership: `services/telegram/`.
`core/application.py` registers `TelegramService`; the production Telegram path composes the canonical `services/telegram/` router/handlers. TASK-032 removed the previously overlapping legacy Telegram trees.

## Application / Service Layer
- `core/application.py`: lifecycle and composition.
- `core/service.py`: registration, startup/shutdown, health, and degraded-mode handling.
- `services/market_data/service.py`: canonical market-data application facade.
- `services/worker/service.py`: optional non-critical application boundary for heavy processing.

## Market Data / Providers
Canonical application flow: `Multi-Asset caller → MarketDataService → MarketDataEngine → ProviderManager → provider(s)`.
`MarketDataEngine` owns final candle quality/freshness gates; `ProviderManager` owns provider routing/fallback/retry/cooldown behavior. Scanner may retain an explicitly selected ProviderManager for provider-readiness semantics but does not construct MarketDataEngine directly.
TASK-036 through TASK-044 established canonical market-data ownership and lifecycle boundaries. TASK-071 hardened timestamp/provider timing boundaries. TASK-072 and TASK-077 hardened market-closure gap semantics. TASK-076 restored list/tuple provider-result compatibility. TASK-081 aligned DataQuality with centralized symbol normalization. TASK-082 made provider reconfiguration lifecycle-isolated.

## Analysis Layer
`analysis/` contains the production modular analysis pipeline. `analysis/full_engine.py` remains canonical.

## AI / ML Layer
The `ai/` package is dormant and not part of production application composition. TASK-035 established it as future Phase 6 capability. It must not bypass canonical analysis → decision → risk flow.

## Symbol / Asset Metadata
`config/symbols.py` is the central symbol normalization and asset-family classification boundary. The repository explicitly represents Forex, Crypto, Stocks, Indices, and Commodities. Risk/data-quality paths must consume centralized normalization/classification rather than embedding local Forex-only parsing.
`analysis/currency.py` derives quote currency and default contract size from that asset classification. Forex currently uses contract size `100000`; the current spot-like non-Forex universe uses `1.0` unless an explicit provider/broker-specific override is supplied.

## Currency Conversion
`analysis/currency.py` provides quote-currency and contract-size metadata. `services/market_data/currency_conversion.py` owns conversion resolution. The conversion boundary supports direct/inverse supported FX pairs and the repository's explicit USDT/USDC equivalent policy, including stablecoin↔USD bridging. Missing, invalid, or unsupported conversion data must fail closed rather than inventing a rate.

## Decision / Risk Ownership
Canonical production risk owner: `analysis/risk_engine.py`.
Canonical production decision owner: `analysis/decision_engine.py`.
The ownership boundary is: analysis engines produce analytical inputs → DecisionEngine produces the decision → RiskEngine applies the risk layer → FullAnalysisEngine assembles the final report.
RiskEngine derives asset contract size when none is explicitly supplied and applies configured `risk_percent` as the ceiling for dynamic risk selection.

## Position Sizing
`analysis/position_sizing.py` is the executable sizing boundary. It preserves account/quote currency units, validates finite positive inputs, supports the explicit USDT/USDC currency policy, and converts account risk into quantity using contract size and quote-to-account conversion. Precision/rounding and asset-specific quantity semantics remain part of the active audit frontier and must be evidence-backed before changing.

## Worker / Heavy Processing
`worker/` provides the PC Worker runtime, HTTP boundary, job contracts, dispatcher, handlers, and heavy application executors.
Application-facing path:
`Application caller → WorkerProcessingService → WorkerDispatcher → durable queue and/or PCWorkerClient → PC Worker`
No speculative Phase 9 caller has been introduced.

## Processing Queue
`worker/queue.py` provides the SQLite-backed durable job queue contract. It persists lifecycle states and supports crash-recovery semantics. TASK-075 added targeted atomic claims and cancellation recovery. It is not claimed as a distributed broker.

## Persistence / Storage
Worker queue persistence is durable. `services/telegram/journal_store.py` is the file-backed Telegram journal persistence boundary. TASK-047 through TASK-051 established ordering/index semantics, atomic mutations, corruption fail-closed behavior, root/container structure validation, and entry-schema validation.

## Configuration
`config/` contains environment/settings/symbol configuration. Account balance, risk policy, account currency, and symbol/asset metadata are explicit boundaries. Worker-specific network/auth/resource settings remain worker-local unless required by the application transport boundary.

## External Services / Deployment
- `Dockerfile`
- `railway.toml`
- `.github/workflows/` with testing, integration, production readiness/activation, E2E, security, and automation workflows.
Railway is an infrastructure target, not a core application architecture dependency.

## Testing
`tests/` includes unit/contract/integration-style coverage for providers, market data, analysis, decision/risk logic, worker, Telegram, lifecycle, and production readiness. Recent audit regressions cover provider lifecycle replacement, multi-asset sizing, symbol normalization, stablecoin conversion, and configured risk ceilings.

## CI/CD
CI status must always be verified against the exact relevant commit rather than inferred from documentation. Current audit changes are not considered VERIFIED until the required workflow set for the resulting `main` HEAD completes successfully.

## Security Boundaries
Primary boundaries are Telegram input, external market-data providers, market-data freshness/quality, currency conversion, risk/position sizing, dormant AI provider boundary reserved for a later phase, worker API/network boundary, environment secrets, persistence, and deployment runtime. Security review is not yet complete.

## Data Flow
Telegram request → canonical `services/telegram/` handlers/router → application/service layer → `MarketDataService` → `MarketDataEngine` → analysis → decision → risk → position sizing/currency conversion where required → safe result/NO TRADE → Telegram response.
The dormant AI package is not in this production data flow.

Heavy application operation → `WorkerProcessingService` → `WorkerDispatcher` → queue/PC Worker → result → calling service.

## Failure Flow
Invalid/stale market data → safe degraded state / NO TRADE.
Provider failure → centralized fallback/failover → quality/freshness validation.
Unsupported or invalid conversion → fail-closed sizing/risk result.
Risk failure → fail closed.
Queue/worker timeout/failure → explicit lifecycle state + bounded recovery behavior where required.
Missing/unready worker transport → controlled `WORKER_OFFLINE` result for optional heavy processing.
Telegram journal invalid/corrupt storage → explicit `JournalStoreError` fail-closed behavior.

## Current Audit Frontier
Continue the cross-layer audit through:
`ProviderManager → MarketDataService → Freshness/DataQuality → Symbol/Asset Metadata → CurrencyConversion → MarketAwareAnalysisEngine → RiskEngine → PositionSizing → Telegram/Scanner/Tracker/Callbacks → Worker/Queue/Persistence → Security/Production → Final E2E`.
Focus on concrete repository-backed contract gaps: freshness propagation, conversion freshness/direction, quantity/contract semantics, precision/rounding, finite/overflow boundaries, and end-to-end fail-closed behavior.

## Status
The platform is explicitly Multi-Asset. Telegram ownership, market-data ownership, decision/risk ownership, provider lifecycle, queue lifecycle, and journal persistence boundaries are consolidated. The `ai/` package is dormant/unwired. TASK-079 through TASK-083 extend the market/risk contract hardening without introducing speculative architecture. Phase 2 remains active.
