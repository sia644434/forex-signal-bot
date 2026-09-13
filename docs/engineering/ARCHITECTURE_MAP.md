# Architecture Map — Forex Platform

## System Overview
The repository is a Python Forex trading-intelligence application with a Telegram interface, market-data/provider layer, modular Forex analysis engines, risk/decision components, a dormant/unwired AI/ML package reserved for its later roadmap phase, a PC worker for heavy Forex processing, a durable worker processing queue, and deployment/CI infrastructure.

## Entry Points
- `main.py`: async process entry point.
- `app.py`: thin application factory wrapper.
- `core/application.py`: application composition root.
- `worker/main.py`: worker-side entry point for heavy Forex application workloads.

## Telegram Layer
Canonical production ownership: `services/telegram/`.
`core/application.py` registers `TelegramService`; the production Telegram path composes the canonical `services/telegram/` router/handlers. TASK-032 removed the previously overlapping legacy Telegram trees.

## Application / Service Layer
- `core/application.py`: lifecycle and composition.
- `core/service.py`: registration, startup/shutdown, health, and degraded-mode handling.
- `services/market_data/service.py`: canonical market-data application facade.
- `services/worker/service.py`: optional non-critical application boundary for heavy Forex processing.

## Market Data / Providers
Canonical application flow: `Forex caller → MarketDataService → MarketDataEngine → ProviderManager → provider(s)`.
`MarketDataEngine` owns final candle quality/freshness gates; `ProviderManager` owns provider routing/fallback/retry/cooldown behavior. Scanner may retain an explicitly selected ProviderManager for provider-readiness semantics but does not construct MarketDataEngine directly.
TASK-036 through TASK-044 established the canonical market-data ownership, removed dormant direct/provider-specific alternate surfaces, hardened construction boundaries, and preserved application-scoped service/manager state.
TASK-037's dormant `get_latest_oanda_price` surface was removed; it is no longer an outstanding architecture item.

## Analysis Layer
`analysis/` contains the production modular analysis pipeline. TASK-034 removed the unused alternate analysis architecture. `analysis/full_engine.py` remains canonical.

## AI / ML Layer
The `ai/` package is dormant and not part of production application composition. TASK-035 established it as future Phase 6 capability. It must not bypass canonical analysis → decision → risk flow.

## Decision / Risk Ownership
Canonical production risk owner: `analysis/risk_engine.py`.
Canonical production decision owner: `analysis/decision_engine.py`.
The resulting ownership boundary is: analysis engines produce analytical inputs → DecisionEngine produces the decision → RiskEngine applies the risk layer → FullAnalysisEngine assembles the final report.

## Worker / Heavy Processing
`worker/` provides the PC Worker runtime, HTTP boundary, job contracts, dispatcher, handlers, and heavy Forex application executors. The worker boundary contains only workloads that directly support the Forex platform.

Application-facing path:
`Forex domain caller → WorkerProcessingService → WorkerDispatcher → durable queue and/or PCWorkerClient → PC Worker`
No concrete Phase 9 heavy-Forex domain caller currently exists because Backtesting / Simulation is not started. No speculative caller was introduced.

## Processing Queue
`worker/queue.py` provides the SQLite-backed durable job queue contract. It persists lifecycle states and supports crash-recovery semantics. It is not claimed as a distributed broker.

## Persistence / Storage
Worker queue persistence is durable. `services/telegram/journal_store.py` is the file-backed Telegram journal persistence boundary. TASK-047 corrected its ordering/index contract, and TASK-048 made journal mutations atomic across read-modify-write operations.

## Configuration
`config/` contains environment/settings/symbol configuration. Worker-specific network/auth/resource settings remain worker-local unless required by the application transport boundary.

## External Services / Deployment
- `Dockerfile`
- `railway.toml`
- `.github/workflows/` with testing, integration, production readiness/activation, E2E, security, and automation workflows.
Railway is an infrastructure target, not a core application architecture dependency.

## Testing
`tests/` includes unit/contract/integration-style coverage for providers, market data, analysis, decision logic, worker, Telegram, lifecycle, and production readiness. TASK-048 adds explicit concurrency regression coverage for Telegram journal mutation atomicity.

## CI/CD
CI status must always be verified against the relevant commit rather than inferred from documentation. TASK-048's exact head passed the configured required workflow set.

## Security Boundaries
Primary boundaries are Telegram input, external market-data providers, dormant AI provider boundary reserved for a later phase, worker API/network boundary, environment secrets, and deployment runtime. Security review is not yet complete.

## Data Flow
Telegram request → canonical `services/telegram/` handlers/router → application/service layer → `MarketDataService` → `MarketDataEngine` → analysis → decision → risk → safe result/NO TRADE → Telegram response.
The dormant AI package is not in this production data flow.

Heavy Forex operation → `WorkerProcessingService` → `WorkerDispatcher` → queue/PC Worker → result → calling Forex service.

## Failure Flow
Invalid/stale market data → safe degraded state / NO TRADE.
Provider failure → centralized fallback/failover → quality/freshness validation.
Risk failure → fail closed.
Queue/worker timeout/failure → explicit lifecycle state + bounded recovery behavior where required.
Missing/unready worker transport → controlled `WORKER_OFFLINE` result for optional heavy processing.
Future AI provider failure → bounded degradation without unsafe decisions.
Telegram journal mutation failure/concurrency → atomic store operation or explicit error; no split read-modify-write contract remains in the journal mutation paths.

## Status
The PC Worker is restricted to heavy Forex application processing. Telegram ownership is consolidated under `services/telegram/`. Decision/Risk/Analysis ownership is consolidated. The `ai/` package is dormant/unwired. Market-data candle retrieval is canonical through `MarketDataService → MarketDataEngine → ProviderManager`. TASK-047 and TASK-048 established the Telegram journal ordering/persistence and mutation-atomicity contracts. Phase 2 remains active pending the next evidence-backed architecture/reliability gap.
