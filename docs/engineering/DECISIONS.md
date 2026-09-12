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
Options:
1. Keep coding-agent/Ollama execution inside the worker.
2. Make the worker a general-purpose local AI/coding host.
3. Keep the worker focused on genuine platform workloads and remove the local coding-agent path from the active runtime.
Chosen Solution: Option 3.
Reason: The repository already contains real worker executors for backtesting, market scans, feature engineering, model training/evaluation, and other heavy application workloads. A local coding agent is not part of the trading platform architecture and would create an unnecessary runtime/configuration dependency.
Trade-offs: Legacy local-agent files may remain temporarily as cleanup debt; they are not part of the active worker path.
Affected Components: `worker/main.py`, `worker/handlers.py`, `worker/contracts.py`, worker configuration, future cleanup of `worker/models/*`.
