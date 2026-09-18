# Engineering Changelog

## 2026-09-19 — Phase 6 AI/ML boundary closure
- TASK-115 changed the example AI configuration to explicit opt-in by setting `AI_ENABLED=false`.
- TASK-115 changed production readiness so missing AI credentials are warned about only when AI is explicitly enabled.
- TASK-116 removed the dormant AI component from `AnalysisScorer`; legacy `ai_score` no longer influences canonical production scoring.
- TASK-117 hardened AI configuration and response boundaries against non-finite values.
- TASK-118 completed the repository-wide AI/ML boundary audit.
- Existing `ai/` capability remains isolated and dormant; it was not activated.
- No Ollama, coding-agent, autonomous-agent, or model-orchestration architecture was introduced.
- Final Phase-6 code HEAD: `91a59421cbd82043cec59bc9f5fe883796a1a8da`; all seven required checks completed successfully.



## 2026-09-19 — Multi-Asset closure audit continuation
- Corrected engineering scope documentation to explicitly preserve Forex, Crypto, Stocks, Indices, and Commodities.
- TASK-119 hardened PC Worker readiness against stale/future/malformed heartbeats and reflected degraded readiness in health.
- TASK-120 hardened Telegram scanner environment overrides against unsupported symbols.
- Added focused regression coverage for both production-boundary fixes.
- Updated phase/task/test engineering state; exact-head CI verification remains required before marking the new tasks VERIFIED.


## 2026-09-19 — Phase 7 PC Worker / Heavy Processing closure
- Verified TASK-119, TASK-120, and TASK-121 on exact closure HEAD `d34a8836ff5a2e1c8820540dd1d6cc5bff473f8a`.
- TASK-122 completed the full Phase-7 cross-layer audit across WorkerRuntime, WorkerHTTPServer, PCWorkerClient, WorkerDispatcher, WorkerQueue, application readiness, recovery, shutdown, and security boundaries.
- No additional repository-backed Phase-7 correctness gap requiring code changes was identified.
- All seven required GitHub Actions workflows completed successfully on the exact closure HEAD.
- Phase 7 is now COMPLETE; Phase 8 — Trading / Decision Engine — is the next audit frontier.


## 2026-09-19 — Phase 8 Trading / Decision Engine closure
- TASK-123 hardened `MarketAwareAnalysisEngine` against mismatched candle symbols and stale/future market inputs before decision/risk evaluation.
- Preserved the existing compatibility contract for legacy candle-like inputs that do not expose market metadata.
- Added regression coverage for symbol mismatch, stale input, and future-dated input.
- TASK-124 completed the full Phase-8 cross-layer audit across DecisionEngine, ConfidenceEngine, RiskEngine, PositionSizing, CurrencyConversionService, and MarketAwareAnalysisEngine.
- No additional repository-backed Phase-8 correctness gap was identified.
- Code closure HEAD: `1edbf5126c86bcde45c32cf91e365d22e20e4037`; all seven required GitHub Actions checks completed successfully.
- Phase 8 is now COMPLETE; Phase 9 — Backtesting / Simulation — is the next audit frontier.


## Phase 9 — Backtesting / Simulation Closure
- TASK-125 completed the full Phase-9 cross-layer closure audit.
- Hardened backtest inputs against missing, non-numeric, non-finite, and non-positive close prices.
- Added validation for non-negative signal thresholds, bounded fees, simulation counts, and simulation horizons.
- Corrected walk-forward evaluation so the training history is available for the first test signal while only the test segment contributes to reported performance.
- Added deterministic seeded Monte Carlo regression coverage and fail-closed invalid-input coverage.
- Code closure HEAD: `d616df74377af7de1aaf798c7b876fe8acecee60`; all seven required GitHub Actions checks completed successfully.
- Phase 9 is COMPLETE; Phase 10 — Security / Production Hardening — is the next audit frontier.


## 2026-09-19 — Phase 10 Security / Production Hardening checkpoint
- TASK-126 hardened `WorkerHTTPServer` request validation against malformed JSON shapes, invalid timeout/priority values, oversized identifiers, and non-object payloads.
- Added regression coverage in `tests/test_pc_worker_health_security.py`.
- Hardened the production Docker image to run as a dedicated non-root user.
- Restricted production CI workflow permissions to `contents: read` where write access is unnecessary.
- Exact audit HEAD: `b92aae52828e7737402da30ec5d513df4c8b0dad`; all seven required GitHub Actions checks completed successfully.
- Phase 10 remains open for additional concrete security/production-hardening audit work.
