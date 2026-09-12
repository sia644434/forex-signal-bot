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
