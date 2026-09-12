# Engineering Decisions

## ADR-001 — Persistent repository memory
Date: 2026-09-12
Problem: Chat history is not a reliable persistence mechanism for a multi-session engineering mission.
Options:
1. Rely on chat history.
2. Maintain external notes only.
3. Store concise, versioned engineering state inside the repository.
Chosen Solution: Option 3.
Reason: The repository is the authoritative engineering artifact and survives conversation resets.
Trade-offs: Adds documentation maintenance overhead; mitigated by concise structured state and checkpoint discipline.
Affected Components: `docs/engineering/*`, future engineering workflow.

## ADR-002 — High-level architecture mapping before refactoring
Date: 2026-09-12
Problem: The repository contains overlapping/legacy-looking areas (notably Telegram, decision/risk, and strategy paths).
Chosen Solution: Map actual ownership and contracts first; avoid mass rewrites until concrete production problems are evidenced.
Reason: Prevents unnecessary architectural churn and protects working behavior.
Trade-offs: Short-term duplication may remain while contracts are verified.
Affected Components: Telegram, analysis, decision/risk, strategy.

## ADR-003 — PC Worker is for Trading Intelligence Platform workloads, not local coding-agent infrastructure
Date: 2026-09-12
Problem: The worker runtime had an accidental `coding_agent` workload and an Ollama bootstrap path that were unrelated to the platform's heavy application-processing responsibility.
Chosen Solution: Keep the worker focused on genuine Forex platform workloads and remove the local coding-agent path from the active runtime.
Reason: A local coding agent is not part of the trading platform architecture and would create an unnecessary runtime/configuration dependency.
Trade-offs: Legacy local-agent files may remain temporarily as cleanup debt; they are not part of the active worker path.
Affected Components: worker runtime, worker configuration, architecture documentation.

## ADR-004 — Do not carry forward non-Forex worker tasks
Date: 2026-09-12
Problem: `TASK-016 — Worker Retry and Failure Lifecycle` remained in the task roadmap after the worker's accidental coding-agent/Ollama architecture was removed.
Chosen Solution: Remove TASK-016 from the active roadmap without implementing it. Future retry/failure work must be introduced only when a concrete Forex application, Processing Queue, or Heavy Forex Worker requirement is evidenced by the repository.
Reason: The final product architecture is strictly Forex-focused.
Consequences: No retry-specific code is added solely for TASK-016. Evidence-backed retry requirements may still be addressed later as properly scoped Forex tasks.
Affected Components: `docs/engineering/*`.

## ADR-005 — Engineering state must be synchronized with every verified task checkpoint
Date: 2026-09-12
Problem: Implementation work had advanced through TASK-027 while persistent state documents still referenced TASK-024 and older commits.
Chosen Solution: After each verified task or state-changing checkpoint, update the authoritative engineering state documents in the repository before selecting the next task.
Reason: Prevents `TASK_STATE.md`, `PROJECT_STATE.md`, `PHASE_STATE.md`, `TEST_STATE.md`, and the engineering changelog from becoming stale relative to code and CI evidence.
Trade-offs: Adds small documentation commits after implementation/verification checkpoints, but substantially improves recoverability and prevents contradictory task selection.
Affected Components: `docs/engineering/*`.

## ADR-006 — Keep public worker liveness minimal
Date: 2026-09-12
Problem: The PC Worker's unauthenticated `GET /health` endpoint exposed detailed runtime metadata including worker identity, host/platform information, Python version, capabilities, registered jobs, and active jobs.
Chosen Solution: Keep `/health` unauthenticated for simple liveness checks but return only `{"status":"READY"}`. Retain detailed worker identity/readiness information behind the authenticated `/heartbeat` transport.
Reason: This preserves compatibility with simple health probes while applying least-privilege information exposure.
Consequences: Consumers needing worker identity or detailed readiness must use the authenticated heartbeat contract.
Affected Components: `worker/server.py`, `tests/test_pc_worker_health_security.py`, worker monitoring/integration consumers.

## ADR-007 — Canonical application-facing market-data boundary
Date: 2026-09-12
Problem: Production Telegram callers were directly constructing/using `MarketDataEngine`, creating an application-level ownership leak even though the engine contains important provider routing, data-quality, and freshness gates.
Chosen Solution: Use `services/market_data/service.py` (`MarketDataService`) as the canonical application-facing market-data facade and route production candle retrieval through it. Preserve `MarketDataEngine` as the quality/freshness execution layer and `ProviderManager` as the provider routing/fallback owner.
Reason: Consolidates application ownership without bypassing safety-critical market-data validation or provider failover behavior.
Consequences: Application callers should not directly retrieve candles from `MarketDataEngine`. Scanner may retain explicit `ProviderManager` selection only when necessary for provider-readiness semantics, injecting it into the engine used by the service.
Affected Components: `services/market_data/service.py`, `services/telegram/handlers/signal.py`, `services/telegram/tracker.py`, `services/telegram/scanner.py`, `services/telegram/handlers/callbacks.py`, market-data architecture documentation.
