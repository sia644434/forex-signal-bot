# Task State

## TASK-001 through TASK-060
Phase 1/2 reliability and architecture tasks through FullAnalysis trade-quality symmetry remain VERIFIED according to the persistent engineering history in this file.

## TASK-061
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: ConfidenceEngine Signed Analysis Score Contract Alignment
Implementation Status: VERIFIED
Evidence:
- `ConfidenceEngine` converts signed analysis component scores from `-100..100` to the shared `0..100` directional score contract, preserving `0 -> 50` neutral semantics.
- Required verification passed on the verified implementation head.

## TASK-062
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: ConfidenceEngine Supply-Demand Score Contract
Implementation Status: VERIFIED
Evidence:
- `ConfidenceEngine._collect_engines()` consumes the explicit `supply_demand_score` field rather than `trend_score`.
- Regression coverage verifies the explicit field and neutral missing-field behavior.

## TASK-063
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Supply-Demand Score Wiring into Confidence Contract
Implementation Status: VERIFIED
Evidence:
- `FullAnalysisEngine` passes `supply_demand_result.score` into `AnalysisResult.supply_demand_score`.
- Production E2E Contract Gate and full test suite passed on the verified trigger head.

## TASK-064
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: DecisionEngine Supply-Demand Score Consumption
Implementation Status: VERIFIED
Evidence:
- DecisionEngine reads `supply_demand_score` directly.
- Regression coverage and production verification passed.

## TASK-065
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: ConfidenceEngine Numeric Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Hardened ConfidenceEngine normalization and aggregation boundaries against non-finite values.
- Present-invalid numeric fields are rejected instead of being silently converted to neutral/default values; genuinely missing fields retain intended defaults.
- Weight validation requires finite, non-negative values.
- Data-quality and market-uncertainty calculations reject non-finite inputs.
- Regression coverage was added for NaN/Inf, invalid weights, missing fields, and bounded finite output behavior.
- Implementation/test changes are present on `main`; final required GitHub Actions verification is pending.
- No local execution is claimed.

## TASK-066
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: FullAnalysisEngine Numeric Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Hardened the FullAnalysisEngine boundary so non-finite analysis/ATR values cannot silently enter Decision/Confidence/Risk calculations.
- Preserved the existing legacy price-list and Candle collection contracts.
- Added regression coverage for numeric boundary failures and finite downstream behavior.
- Implementation/test changes are present on `main`; final required GitHub Actions verification is pending.
- No local execution is claimed.

## Current Phase 2 Audit Frontier
The next concrete audit frontier after verification of TASK-065/TASK-066 is:
`RiskEngine → PositionSizing → CurrencyConversion`.

Required checks:
- account-currency versus quote-currency unit semantics
- conversion-rate direction and pair orientation
- risk amount versus risk-per-unit units
- lot-size and contract-size semantics
- rounding/precision behavior
- finite/positive/overflow boundaries
- fail-closed behavior when conversion data is missing, stale, invalid, or unavailable
- end-to-end consistency between MarketAwareEngine, RiskEngine, PositionSizing, and CurrencyConversionService

Do not create the next task until a concrete repository-backed gap is demonstrated.

## New-chat Continuation Contract
When a new chat starts work on this repository, first read:
- `docs/engineering/PROJECT_STATE.md`
- `docs/engineering/PHASE_STATE.md`
- `docs/engineering/TASK_STATE.md`
- `docs/engineering/TEST_STATE.md`
- `docs/engineering/ARCHITECTURE_MAP.md`
- `docs/engineering/DECISIONS.md`
- `docs/engineering/CHANGELOG_ENGINEERING.md`

Then:
1. Determine the exact `main` HEAD.
2. Inspect GitHub Actions for that exact HEAD.
3. Resolve any pending CI failure before starting another audit frontier.
4. Do not repeat TASK-058 through TASK-066 unless their verification evidence is missing or contradicted.
5. Continue from the first unresolved audit frontier recorded above.
6. Inspect more architecture than the previous step and only implement concrete repository-backed gaps.
7. Add focused regression coverage for every confirmed defect.
8. Verify the required GitHub Actions gate set before marking a task VERIFIED.
9. Keep the repository Forex-only; do not introduce Data Analysis, local coding-agent/Ollama architecture, speculative features, or unrelated agent architecture.
10. Use GitHub Connector only for repository inspection and modification.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites.
