# Architecture Map — Verified Phase 2 Corrections

## System Overview

The repository is a Python trading-intelligence application with a Telegram interface, market-data/provider layer, modular analysis engines, application AI integration, risk/decision components, a PC worker for heavy application processing, and deployment/CI infrastructure.

## Entry Points

- `main.py`: async process entry point; creates the application, installs shutdown handling, starts services, waits, then stops services.
- `app.py`: thin application factory wrapper.
- `core/application.py`: application composition root; currently registers `TelegramService` in `ServiceManager`.
- `worker/main.py`: worker-side entry point for heavy application workloads.

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

## AI/ML Application Layer

`ai/` provides context, prompt construction, parsing, provider abstraction, orchestration, and an OpenAI provider.

AI/ML components must represent genuine Trading Intelligence Platform functionality. The PC worker is not a general coding-agent host and is not architecturally coupled to local Ollama/model tooling.

## Decision / Risk / Strategy

- `analysis/decision_engine.py`, `analysis/risk_engine.py`, `analysis/risk_manager.py`
- `risk/manager.py`
- `strategy/` contracts, registry, and orchestrator
- `signal_engine/engine.py`

These overlapping areas require contract-level mapping before refactoring. The final architecture must keep analysis, decision, risk, and execution concerns separated.

## Worker / Heavy Processing

`worker/` provides the PC Worker runtime, HTTP boundary, job contracts, dispatcher, handlers, and real executors for heavy application workloads.

Verified application workloads include backtesting, walk-forward processing, Monte Carlo simulation, feature engineering, dataset building, market scanning, multi-timeframe analysis, model training/evaluation, and bounded computational analysis.

The active worker entrypoint does not initialize a local coding agent or Ollama runtime. `coding_agent` is not a declared worker workload. Worker-specific network/auth/resource configuration remains a worker concern; genuinely global configuration such as `LOG_LEVEL` uses centralized settings.

The legacy local-agent/Ollama implementation and its setup/test artifacts were removed after repository reference inspection confirmed they were not part of the active application worker path.

Required future verification: worker authentication, registration/heartbeat, lifecycle, idempotency, retries, timeouts, cancellation, resource limits, and restart recovery.

## Queue

A dedicated queue implementation is not obvious from the baseline tree. Worker dispatcher/task lifecycle may provide part of this behavior. A persistent/idempotent queue model must be confirmed or introduced only where justified.

## Persistence / Storage

No obvious dedicated database/migration directory was identified in the baseline tree. `services/telegram/journal_store.py` and data/model layers exist. Persistence, retention, concurrency, and recovery require targeted inspection.

## Configuration

`config/` contains environment/settings/symbol configuration; `settings/` also contains AI settings. `.env.example` exists. Core application, health-server, and logger boundaries consume centralized settings. Worker-specific values such as worker host/port/token/identity/capabilities remain candidates for a worker-local configuration boundary rather than being forced into global application settings.

## External Services / Deployment

- `Dockerfile`
- `railway.toml`
- `.github/workflows/` with testing, provider-contract, integration, production-readiness/activation, E2E, and automation runner workflows.

Railway is an infrastructure target, not a core architecture dependency.

## Testing

`tests/` includes unit/contract/integration-style coverage for providers, freshness, market data, analysis, decision logic, worker, Telegram, lifecycle, and production readiness. Worker-scope regression coverage explicitly prevents `coding_agent` from returning as an application worker workload.

## CI/CD

CI status must always be verified against the relevant commit rather than inferred from documentation. Existing workflows cover testing, provider contracts, integration/production gates, E2E, security audit, and automation runner behavior.

## Security Boundaries

Primary boundaries are Telegram input, external market-data providers, AI provider calls, worker API/network boundary, environment secrets, and deployment runtime. Security review is not yet complete.

## Data Flow — Baseline Hypothesis to Verify

Telegram request → Telegram handlers/router → application/service layer → market data → analysis/orchestration → decision/risk → safe result/NO TRADE → Telegram response.

Heavy application workloads may be dispatched separately through the PC Worker contracts/runtime. Local coding-agent/Ollama execution is not part of this platform data flow.

## Failure Flow — Target

Invalid/stale market data → safe degraded state / NO TRADE.
Provider failure → centralized fallback/failover → quality/freshness validation.
Optional analysis failure → isolate failure and preserve valid analyses where safe.
Risk failure → fail closed.
Worker timeout/failure → explicit lifecycle state + retry/dead-letter behavior where required.
External/AI failure → bounded degradation without unsafe decisions.

## Status

Phase 2 worker boundary is corrected and the accidental local coding-agent/Ollama subsystem has been removed. Remaining worker work is reliability, lifecycle, authentication, idempotency, timeout/recovery, and resource-boundary verification.
