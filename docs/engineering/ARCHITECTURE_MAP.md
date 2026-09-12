# Architecture Map — Forex Platform

## System Overview

The repository is a Python Forex trading-intelligence application with a Telegram interface, market-data/provider layer, modular Forex analysis engines, application AI/ML functionality, risk/decision components, a PC worker for heavy Forex processing, a durable worker processing queue, and deployment/CI infrastructure.

## Entry Points

- `main.py`: async process entry point; creates the application, installs shutdown handling, starts services, waits, then stops services.
- `app.py`: thin application factory wrapper.
- `core/application.py`: application composition root; registers `TelegramService` and the optional non-critical `WorkerProcessingService`.
- `worker/main.py`: worker-side entry point for heavy Forex application workloads.

## Telegram Layer

Primary locations: `services/telegram/`, `bot/`, `telegram_bot/`, and legacy/top-level `handlers/`.

The newer service-oriented path includes client, router, state, i18n, scanner, journal, tracker, market-session handling, and command/callback handlers. Multiple Telegram-related trees exist, so consolidation/ownership must be verified before architectural cleanup.

## Application / Service Layer

- `core/application.py`: lifecycle and composition.
- `core/service.py`: registration, startup/shutdown, health, and degraded-mode handling.
- `services/base.py`: service contract.
- `services/market_data/service.py`: market-data application service.
- `services/worker/service.py`: optional non-critical application boundary for heavy Forex processing; builds the queue-aware `WorkerDispatcher` from central settings and returns controlled `WORKER_OFFLINE` results when PC-worker transport is not configured.

## Market Data / Providers

Primary locations: `data/` and `services/market_data/`.

Observed components include `MarketDataProvider` contracts, provider managers/factories, fallback logic, freshness and quality logic, and OANDA/Finnhub/AlphaVantage providers plus provider clients.

Important production concerns: provider routing centralization, freshness classification, market state, rate limits, timeout/retry behavior, data contracts, and safe degradation.

## Analysis Layer

`analysis/` contains a large modular engine set including indicators, ATR, candlestick, market structure/regime, price action, Elliott, harmonic, Wyckoff, supply/demand, SMC, scoring, confidence, risk-related analysis, registry, orchestration, and full-engine/report components.

`analysis/registry.py` and `analysis/orchestrator.py` indicate a registry/orchestration pattern. Exact runtime composition and failure semantics require targeted verification.

## AI/ML Application Layer

`ai/` provides context, prompt construction, parsing, provider abstraction, orchestration, and an OpenAI provider.

AI/ML components must represent genuine Forex Trading Intelligence Platform functionality and remain separate from the PC Worker's heavy-processing boundary.

## Decision / Risk / Strategy

- `analysis/decision_engine.py`, `analysis/risk_engine.py`, `analysis/risk_manager.py`
- `risk/manager.py`
- `strategy/` contracts, registry, and orchestrator
- `signal_engine/engine.py`

These overlapping areas require contract-level mapping before refactoring. The final architecture must keep analysis, decision, risk, and execution concerns separated.

## Worker / Heavy Processing

`worker/` provides the PC Worker runtime, HTTP boundary, job contracts, dispatcher, handlers, and real executors for heavy Forex application workloads.

Verified application workloads include backtesting, walk-forward processing, Monte Carlo simulation, feature engineering, dataset building, market scanning, multi-timeframe analysis, model training/evaluation, and bounded computational analysis.

The worker boundary contains only workloads that directly support the Forex platform. Worker-specific network/auth/resource configuration remains a worker concern; genuinely global configuration such as `LOG_LEVEL` uses centralized settings.

The application-facing path is now:

`Forex domain caller → WorkerProcessingService → WorkerDispatcher → durable queue and/or PCWorkerClient → PC Worker`

`WorkerProcessingService` is optional and non-critical. When PC-worker transport is absent, submission fails in a controlled `WORKER_OFFLINE` result instead of blocking application startup.

Required next verification: identify actual heavy-Forex domain call sites and confirm that backtesting, historical-data processing, simulation, batch calculations, and other expensive workloads use this boundary where required by the Master Prompt. Do not assume that exposing the service alone constitutes full workload routing.

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

`tests/` includes unit/contract/integration-style coverage for providers, freshness, market data, analysis, decision logic, worker, Telegram, lifecycle, and production readiness. Worker workload tests enforce that only supported Forex application workloads are registered. `tests/test_worker_queue.py` covers queue idempotency, priority ordering, lifecycle transitions, terminal-state idempotency, cancellation/timeout, crash recovery, and persistence across connections. `tests/test_worker_service.py` covers the application-facing worker boundary and controlled offline behavior.

## CI/CD

CI status must always be verified against the relevant commit rather than inferred from documentation. The TASK-022 verification head `7a96afddaa46aefe9bb5aa990f40522905754572` passed Test, Final Integration Gate, Production Readiness, Production Activation Gate, Production Activation Validation, Production E2E Contract Gate, and Security Audit.

## Security Boundaries

Primary boundaries are Telegram input, external market-data providers, AI provider calls, worker API/network boundary, environment secrets, and deployment runtime. Security review is not yet complete.

## Data Flow — Baseline Hypothesis to Verify

Telegram request → Telegram handlers/router → application/service layer → market data → analysis/orchestration → decision/risk → safe result/NO TRADE → Telegram response.

Heavy Forex application workloads should use:

Forex heavy operation → `WorkerProcessingService` → `WorkerDispatcher` → queue/PC Worker → result → calling Forex service.

The concrete domain call sites for this second flow are the next Phase 2 verification target.

## Failure Flow — Target

Invalid/stale market data → safe degraded state / NO TRADE.
Provider failure → centralized fallback/failover → quality/freshness validation.
Optional analysis failure → isolate failure and preserve valid analyses where safe.
Risk failure → fail closed.
Queue/worker timeout/failure → explicit lifecycle state + bounded recovery behavior where required.
Missing worker transport → controlled `WORKER_OFFLINE` result for optional heavy processing.
External/AI failure → bounded degradation without unsafe decisions.

## Status

The PC Worker is restricted to heavy Forex application processing. Residual non-Forex workload definitions were removed. The durable queue, timeout-aware crash recovery, central queue configuration, and application composition boundary are verified. The next architectural task is to audit real heavy-Forex domain call sites and harden any missing routing through the worker boundary; no speculative architecture should be added.
