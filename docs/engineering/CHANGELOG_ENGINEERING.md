# Engineering Changelog

## 2026-09-12
- Established the first persistent engineering-memory checkpoint for the repository.
- Added baseline architecture/state tracking under `docs/engineering/`.
- Recorded repository/CI evidence without claiming production readiness.
- Preserved the current implementation; no mass architectural rewrite performed during baseline setup.
- Corrected the PC Worker boundary: active worker runtime is dedicated to heavy Trading Intelligence Platform / Forex workloads and no longer initializes a local coding agent/Ollama runtime.
- Removed `coding_agent` from the declared worker workload contract and added regression coverage preventing its reintroduction.
- Removed the residual `multi_agent_analysis` worker workload, executor, tests, and documentation references; TASK-017 final CI gate passed.
- Audited the skipped pre-TASK-004 Phase 2 scope without inventing a missing historical task contract.
- Added `worker/queue.py`, a dependency-free SQLite-backed durable processing queue for heavy Forex jobs with idempotent enqueue and explicit lifecycle states.
- Added queue regression coverage for priority ordering, lifecycle transitions, idempotency, cancellation/timeout, and persistence across file-backed connections.
- Added queue crash recovery and activated timeout-aware dispatcher recovery.
- Centralized queue persistence/recovery configuration and wired the optional non-critical worker processing service through the application boundary.
- Audited the real heavy-Forex routing boundary and deliberately avoided a speculative Phase 9 caller because Backtesting / Simulation is not started.
- Added authenticated PC Worker heartbeat transport and application-boundary heartbeat handling.
- Added worker readiness states and heartbeat identity/timestamp observability.
- Added configurable PC Worker heartbeat freshness with `PC_WORKER_HEARTBEAT_MAX_AGE`; stale READY heartbeats now report `STALE` dynamically.
- Corrected the unconfigured worker readiness regression contract in `316391aa4440d8ca2d31a0d11887bfa2482070b4`.
- Verified the current-head CI path for TASK-027: seven completed push workflow runs are registered, with Production E2E Contract Gate `34709726285` and Production Activation Validation `34709726258` explicitly successful.
- Synchronized `TASK_STATE.md`, `PROJECT_STATE.md`, `PHASE_STATE.md`, and `TEST_STATE.md` through TASK-027.
- Added ADR-005 requiring engineering state synchronization after every verified task/state-changing checkpoint.
- TASK-028: identified that unauthenticated worker `/health` exposed detailed runtime metadata.
- TASK-028: changed public `/health` to the minimal `{"status":"READY"}` liveness contract in `c092704fc8fb924a16556ef85686021965662264`.
- TASK-028: added focused regression coverage in `8160737a2a13ec066c3eb9e9e48f5adce662b099`.
- TASK-028: retained detailed worker identity/readiness behind authenticated `/heartbeat` and recorded ADR-006 for the least-privilege boundary.
- Synchronized `TASK_STATE.md`, `PROJECT_STATE.md`, `PHASE_STATE.md`, and `TEST_STATE.md` to record TASK-028 as implementation-complete with CI verification pending.
