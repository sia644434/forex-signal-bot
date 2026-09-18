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
