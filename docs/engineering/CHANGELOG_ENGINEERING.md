# Engineering Changelog

## 2026-09-12
- Established the first persistent engineering-memory checkpoint for the repository.
- Added baseline architecture/state tracking under `docs/engineering/`.
- Recorded repository/CI evidence without claiming production readiness.
- Preserved the current implementation; no mass architectural rewrite performed during baseline setup.
- Corrected the PC Worker boundary: active worker runtime is dedicated to heavy Trading Intelligence Platform workloads and no longer initializes a local coding agent/Ollama runtime.
- Removed `coding_agent` from the declared worker workload contract and added regression coverage preventing its reintroduction.
- Removed the residual `multi_agent_analysis` worker workload, executor, tests, and documentation references; TASK-017 final CI gate passed.
- Audited the skipped pre-TASK-004 Phase 2 scope without inventing a missing historical task contract.
- Added `worker/queue.py`, a dependency-free SQLite-backed durable processing queue for heavy Forex jobs with idempotent enqueue and explicit lifecycle states.
- Added queue regression coverage for priority ordering, lifecycle transitions, idempotency, cancellation/timeout, and persistence across file-backed connections.
- Documented the queue as a persistence boundary while explicitly leaving distributed transport, shared-storage deployment, and cross-process recovery verification for subsequent evidence-backed work.
