# Architecture Map — Baseline

## System Overview

The repository is a Python trading-intelligence application with a Telegram interface, market-data/provider layer, modular analysis engines, AI integration, risk/decision components, a PC worker subsystem, and deployment/CI infrastructure.

## Entry Points

- `main.py`: async process entry point; creates the application, installs shutdown handling, starts services, waits, then stops services.
- `app.py`: thin application factory wrapper.
- `core/application.py`: application composition root; currently registers `TelegramService` in `ServiceManager`.
- `worker/main.py`: worker-side entry point.

## Telegram Layer

Primary locations: `services/telegram/`, `bot/`, `telegram_bot/`, and legacy/top-level `handlers/`.

The newer service-oriented path includes client, router, state, i18n, scanner, journal, tracker, market-session handling, and command/callback handlers. Multiple Telegram-related trees exist, so consolidation/ownership must be verified before architectural cleanup.

## Application / Service Layer

- `core/application.py`: lifecycle and composition.
- `core/service.py`: registration, startup/shutdown, health, and degraded-mode handling.
- `services/base.py`: service contract.
- `services/market_data/service.py`: market-data application service.

## Market Data / Providers

Primary locations: `data/` and `services/market_data/`.

Observed components include `MarketDataProvider` contracts, provider managers/factories, fallback logic, freshness and quality logic, and OANDA/Finnhub/AlphaVantage providers plus provider clients.

Important production concerns: provider routing centralization, freshness classification, market state, rate limits, timeout/retry behavior, data contracts, and safe degradation.

## Analysis Layer

`analysis/` contains a large modular engine set including indicators, ATR, candlestick, market structure/regime, price action, Elliott, harmonic, Wyckoff, supply/demand, SMC, scoring, confidence, risk-related analysis, registry/orchestrator, and full-engine/report components.

`analysis/registry.py` and `analysis/orchestrator.py` indicate a registry/orchestration pattern. Exact runtime composition and failure semantics require targeted verification.

## AI/ML

`ai/` provides context, prompt construction, parsing, provider abstraction, orchestration, and an OpenAI provider. `worker/models/` additionally contains local-agent/Ollama runtime and model registry/bootstrap tooling.

AI must remain advisory/failure-tolerant and must not bypass deterministic safety/risk gates.

## Decision / Risk / Strategy

- `analysis/decision_engine.py`, `analysis/risk_engine.py`, `analysis/risk_manager.py`
- `risk/manager.py`
- `strategy/` contracts, registry, and orchestrator
- `signal_engine/engine.py`

These overlapping areas require contract-level mapping before refactoring. The final architecture must keep analysis, decision, risk, and execution concerns separated.

## Worker / Heavy Processing

`worker/` includes contracts, client, dispatcher, executors, handlers, runtime, server, and model/agent integration. Tests exist for worker contracts, executors, integration, and runtime.

Required future verification: authentication, registration/heartbeat, lifecycle, idempotency, retries, timeouts, cancellation, resource limits, and restart recovery.

## Queue

A dedicated queue implementation is not obvious from the baseline tree. Worker dispatcher/task lifecycle may provide part of this behavior. A persistent/idempotent queue model must be confirmed or introduced only where justified.

## Persistence / Storage

No obvious dedicated database/migration directory was identified in the baseline tree. `services/telegram/journal_store.py` and data/model layers exist. Persistence, retention, concurrency, and recovery require targeted inspection.

## Configuration

`config/` contains environment/settings/symbol configuration; `settings/` also contains AI settings. `.env.example` exists. Configuration ownership and validation should be unified where practical without breaking existing contracts.

## External Services / Deployment

- `Dockerfile`
- `railway.toml`
- `.github/workflows/` with testing, provider-contract, integration, production-readiness/activation, E2E, and automation-runner workflows.

Railway is an infrastructure target, not a core architecture dependency.

## Testing

`tests/` includes unit/contract/integration-style coverage for providers, freshness, market data, analysis, decision logic, worker, Telegram, lifecycle, and production readiness. Exact passing status has not been established by execution in this session.

## CI/CD

The baseline contains 9 workflow files, including `test.yml`, provider contract runners, integration/production gates, E2E, and automation runner workflows. The latest combined commit status returned one successful status context; all relevant workflow jobs still require evidence-based verification.

## Security Boundaries

Primary boundaries are Telegram input, external market-data providers, AI provider calls, worker API/network boundary, environment secrets, and deployment runtime. Security review is not yet complete.

## Data Flow — Baseline Hypothesis to Verify

Telegram request → Telegram handlers/router → application/service layer → market data → analysis/orchestration → decision/risk → safe result/NO TRADE → Telegram response.

Worker workloads are separately dispatched through worker contracts/runtime and may support AI/ML/heavy computation.

This flow is an initial map, not a claim that every runtime path currently follows it.

## Failure Flow — Target

Invalid/stale market data → safe degraded state / NO TRADE.
Provider failure → centralized fallback/failover → quality/freshness validation.
Optional analysis failure → isolate failure and preserve valid analyses where safe.
Risk failure → fail closed.
Worker timeout/failure → explicit lifecycle state + retry/dead-letter behavior where required.
External/AI failure → bounded degradation without unsafe decisions.

## Status

Baseline architecture map established from repository tree and targeted entrypoint inspection. Detailed contracts remain to be verified only when their subsystem becomes active work.
