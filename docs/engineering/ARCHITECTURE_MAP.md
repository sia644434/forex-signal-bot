# Architecture Map — Forex Platform

## System Overview

The repository is a Python Forex trading-intelligence application with a Telegram interface, market-data/provider layer, modular Forex analysis engines, risk/decision components, a dormant/unwired AI/ML package reserved for its later roadmap phase, a PC worker for heavy Forex processing, a durable worker processing queue, and deployment/CI infrastructure.

## Entry Points

- `main.py`: async process entry point; creates the application, installs shutdown handling, starts services, waits, then stops services.
- `app.py`: thin application factory wrapper.
- `core/application.py`: application composition root; registers `TelegramService` and the optional non-critical `WorkerProcessingService`.
- `worker/main.py`: worker-side entry point for heavy Forex application workloads.

## Telegram Layer

Canonical production ownership: `services/telegram/`.

`core/application.py` registers `TelegramService`; `TelegramService` creates `TelegramClient`; `TelegramClient` imports `services.telegram.router.register_routes`; and the router registers the command/callback handlers under `services/telegram/handlers/`. This is the only Telegram runtime path composed by the production application entry point.

TASK-032 audited the previously overlapping Telegram trees. The legacy `bot/`, `telegram_bot`, and top-level `handlers/` trees were not referenced by the production composition root or `main.py`; their remaining references were limited to legacy tests/CI imports and to each other. They were removed, and the tests/CI import checks were migrated to the canonical `services/telegram/` path. This establishes a single Telegram ownership boundary and avoids parallel handler registration paths.

## Application / Service Layer

- `core/application.py`: lifecycle and composition.
- `core/service.py`: registration, startup/shutdown, health, and degraded-mode handling.
- `services/base.py`: service contract.
- `services/market_data/service.py`: market-data application service.
- `services/worker/service.py`: optional non-critical application boundary for heavy Forex processing; builds the queue-aware `WorkerDispatcher` from central settings and returns controlled `WORKER_OFFLINE` results when PC-worker transport is not configured or not ready.

## Market Data / Providers

Primary locations: `data/` and `services/market_data/`.

Observed components include `MarketDataProvider` contracts, provider managers/factories, fallback logic, freshness and quality logic, and OANDA/Finnhub/AlphaVantage providers plus provider clients.

Important production concerns: provider routing centralization, freshness classification, market state, rate limits, timeout/retry behavior, data contracts, and safe degradation.

## Analysis Layer

`analysis/` contains the production modular analysis pipeline including indicators, ATR, candlestick, market structure/regime, price action, Elliott, harmonic, Wyckoff, supply/demand, SMC, scoring, confidence, decision, risk, and full-engine/report components.

TASK-034 audited the previous alternate analysis architecture. `analysis/adapters.py`, `analysis/contracts.py`, `analysis/registry.py`, and `analysis/orchestrator.py` had no production-active callers; `analysis/contracts.py` also duplicated analysis-context ownership represented elsewhere. Those modules and their obsolete architecture test were removed. `analysis/full_engine.py` remains the canonical production analysis composition and `analysis/__init__.py` exposes only canonical analysis contracts/engines.

## AI / ML Layer

The `ai/` package is currently **dormant and not part of the production application composition**. TASK-035 audited its ownership boundary and found no production or test callers constructing `AIOrchestrator`, `AIProviderManager`, `AIContextBuilder`, `OpenAIProvider`, or the parser/prompt pipeline. The package therefore remains preserved as a future Phase 6 capability rather than being treated as an active runtime dependency or as a second production decision path.

Active application composition in `core/application.py` does not register an AI service; the production Telegram path directly uses the canonical Forex analysis/report components. AI-related settings and production-readiness checks remain configuration scaffolding for the later AI/ML phase and must not be interpreted as evidence that AI currently participates in trading decisions.

The dormant AI package must not control, override, or bypass the canonical analysis → decision → risk flow. Any future activation requires an explicit evidence-backed phase task with production callers, contracts, failure isolation, security review, and tests.

## Decision / Risk Ownership

TASK-033 audited the previously overlapping decision/risk/strategy area against repository-wide references and the production composition path.

- **Canonical production risk owner:** `analysis/risk_engine.py`. `analysis/full_engine.py` constructs `RiskEngine` and uses it to calculate the production risk layer before building `AnalysisReport`.
- **Canonical production decision owner:** `analysis/decision_engine.py`. `analysis/full_engine.py` constructs `DecisionEngine` and uses its decision output in the production analysis pipeline.
- `analysis/risk_manager.py` was an unused duplicate risk implementation with no repository import/call sites and has been removed.
- `risk/manager.py` and the `signal_engine/` package formed an isolated legacy signal/risk path. Repository-wide searches found no production or test callers for that path; it has been removed rather than maintained as a parallel ownership tree.
- The `strategy/` package (`contracts.py`, `registry.py`, `orchestrator.py`) was likewise self-contained with no external runtime callers. It has been removed as dead parallel architecture rather than introducing an unnecessary adapter or duplicate strategy layer.

The resulting ownership boundary is intentionally simple: analysis engines produce analytical inputs → `DecisionEngine` produces the decision → `RiskEngine` applies the risk layer → `FullAnalysisEngine` assembles the final report. No separate legacy risk manager, signal engine, or strategy orchestration path remains.

## Worker / Heavy Processing

`worker/` provides the PC Worker runtime, HTTP boundary, job contracts, dispatcher, handlers, and real executors for heavy Forex application workloads.

Verified application workloads include backtesting, walk-forward processing, Monte Carlo simulation, feature engineering, dataset building, market scanning, multi-timeframe analysis, model training/evaluation, and bounded computational analysis.

The worker boundary contains only workloads that directly support the Forex platform. Worker-specific network/auth/resource configuration remains a worker concern; genuinely global configuration such as `LOG_LEVEL` uses centralized settings.

The application-facing path is now:

`Forex domain caller → WorkerProcessingService → WorkerDispatcher → durable queue and/or PCWorkerClient → PC Worker`

`WorkerProcessingService` is optional and non-critical. When PC-worker transport is absent, submission fails in a controlled `WORKER_OFFLINE` result instead of blocking application startup. Configured dispatch is fail-closed unless the authenticated heartbeat is fresh and `READY`.

No concrete Phase 9 heavy-Forex domain caller currently exists because Backtesting / Simulation is not started. No speculative caller was introduced.

## Processing Queue

`worker/queue.py` provides a dependency-free SQLite-backed durable job queue contract for heavy Forex jobs. It persists `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, and `TIMEOUT` states, orders pending jobs by priority, makes enqueue idempotent by `job_id`, and preserves records across process connections when a file-backed database is configured.

Dispatcher initialization performs timeout-aware recovery of expired running jobs using each job's own timeout plus configured grace. The queue remains separate from network transport and worker execution and is not claimed as a production distributed broker.

## Persistence / Storage

`worker/queue.py` is the first explicit durable persistence boundary for worker job lifecycle state. Broader application persistence, retention, concurrency, and recovery remain subject to targeted inspection. `services/telegram/journal_store.py` and other data/model layers also exist.

## Configuration

`config/` contains environment/settings/symbol configuration; `settings/` also contains AI settings. `.env.example` exists. Core application, health-server, logger, queue, and worker-service boundaries consume centralized settings where appropriate. Worker-specific values such as worker host/port/token/identity/capabilities remain worker-local unless they are required by the application transport boundary; `PC_WORKER_URL`, `PC_WORKER_TOKEN`, and `PC_WORKER_TIMEOUT` are now explicitly validated application transport settings.

## External Services / Deployment

- `Dockerfile`
- `railway.toml`
- `.github/workflows/` with testing, provider-contract, integration, production-readiness/activation, E2E, security, and automation runner workflows.

Railway is an infrastructure target, not a core application architecture dependency.

## Testing

`tests/` includes unit/contract/integration-style coverage for providers, freshness, market data, analysis, decision logic, worker, Telegram, lifecycle, and production readiness. Telegram tests and CI import checks target `services/telegram/`, the canonical production-owned path. Worker workload tests enforce that only supported Forex application workloads are registered. `tests/test_worker_queue.py` covers queue idempotency, priority ordering, lifecycle transitions, terminal-state idempotency, cancellation/timeout, crash recovery, and persistence across connections. `tests/test_worker_service.py` covers the application-facing worker boundary and controlled offline behavior.

## CI/CD

CI status must always be verified against the relevant commit rather than inferred from documentation. The architecture audit changes are on the current `main` head and must pass the repository's configured checks before the corresponding task is marked verified.

## Security Boundaries

Primary boundaries are Telegram input, external market-data providers, the dormant AI provider boundary reserved for a later phase, worker API/network boundary, environment secrets, and deployment runtime. Security review is not yet complete.

## Data Flow — Baseline Hypothesis to Verify

Telegram request → canonical `services/telegram/` handlers/router → application/service layer → market data → analysis → decision → risk → safe result/NO TRADE → Telegram response.

The dormant AI package is not in this production data flow.

Heavy Forex application workloads should use:

Forex heavy operation → `WorkerProcessingService` → `WorkerDispatcher` → queue/PC Worker → result → calling Forex service.

The concrete domain call sites for this second flow are deferred until the corresponding Phase 9 heavy-Forex features exist.

## Failure Flow — Target

Invalid/stale market data → safe degraded state / NO TRADE.
Provider failure → centralized fallback/failover → quality/freshness validation.
Optional analysis failure → isolate failure and preserve valid analyses where safe.
Risk failure → fail closed.
Queue/worker timeout/failure → explicit lifecycle state + bounded recovery behavior where required.
Missing/unready worker transport → controlled `WORKER_OFFLINE` result for optional heavy processing.
Future AI provider failure → bounded degradation without unsafe decisions; AI must never bypass canonical decision/risk safety.

## Status

The PC Worker is restricted to heavy Forex application processing. Residual non-Forex workload definitions were removed. The durable queue, timeout-aware crash recovery, central queue configuration, application composition boundary, worker heartbeat/readiness/freshness, worker security boundaries, and observability contracts are verified. Telegram ownership has been consolidated under `services/telegram/`. TASK-033 removed the evidence-backed dead decision/risk/strategy parallel trees and documented `analysis/decision_engine.py` and `analysis/risk_engine.py` as the canonical production owners. TASK-034 removed the unused alternate analysis architecture. TASK-035 established that the existing `ai/` package is dormant/unwired and reserved for Phase 6 rather than an active production architecture.
