# Task State

## TASK-001 through TASK-064
Phase 1/2 reliability and architecture tasks through DecisionEngine Supply/Demand consumption remain VERIFIED according to the persistent engineering history.

## TASK-065
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: ConfidenceEngine Numeric Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Hardened ConfidenceEngine normalization, weights, data-quality, uncertainty, and present-invalid field handling against non-finite values.
- Regression coverage was added for NaN/Inf, invalid weights, missing fields, and bounded finite output behavior.
- Final verification remains pending on the current moving `main` head.

## TASK-066
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: FullAnalysisEngine Numeric Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Hardened FullAnalysisEngine numeric boundaries so invalid ATR/analysis values cannot silently enter downstream calculations.
- Preserved the legacy price-list and canonical Candle input contracts.
- Regression coverage was added for numeric boundary failures and downstream finite behavior.
- The first verification run exposed two genuine test-contract issues: legitimate `None` NO-TRADE risk outputs were being rejected, and the ATR regression fixture omitted the required `volatility` field. Both were corrected.
- Final verification remains pending on the current moving `main` head.

## TASK-067
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: PositionSizing Decimal Numeric-Range Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Audit of `RiskEngine → PositionSizing → CurrencyConversion` found that float-level finite checks were present, but the later Decimal quantization step could still raise a raw `DecimalException` for values that were finite as Python floats but exceeded the active Decimal precision during quantization.
- This leaked a lower-level numeric exception instead of preserving the public fail-closed `ValueError` contract expected by the position-sizing boundary and RiskEngine's error handling.
- Position sizing now catches `DecimalException` around Decimal risk/lot calculations and converts it to a controlled `ValueError`.
- Regression coverage verifies the oversized-but-finite numeric-range case.
- Implementation commit: `5967f1741e6e381fa83328d93f4f1b65d871b5dd`.
- Regression test commit: `307576dfddc63c079bed0c1fdeed16595fd7ad54`.
- Current required GitHub Actions verification is pending.
- No local execution is claimed.

## Current Phase 2 Audit Frontier
After TASK-065 through TASK-067 verification, continue the evidence-backed audit of:
`RiskEngine → PositionSizing → CurrencyConversion → MarketAwareAnalysisEngine`.

Required checks:
- account-currency versus quote-currency unit semantics
- conversion-rate direction and pair orientation
- configured risk policy versus effective dynamic risk percentage
- risk amount versus risk-per-unit units
- lot-size and contract-size semantics
- rounding/precision behavior
- finite/positive/overflow/underflow boundaries
- fail-closed behavior when conversion data is missing, stale, invalid, or unavailable
- whether configured `RISK_PER_TRADE` actually influences effective risk
- end-to-end consistency between MarketAwareEngine, RiskEngine, PositionSizing, and CurrencyConversionService

Do not create another task until a concrete repository-backed gap is demonstrated.

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
1. Determine the exact current `main` HEAD.
2. Inspect GitHub Actions for that exact HEAD.
3. Resolve every pending or failed verification before moving deeper.
4. Do not repeat TASK-058 through TASK-067 unless their verification evidence is missing or contradicted.
5. Continue from the first unresolved audit frontier recorded above.
6. Inspect more architecture than the previous step and only implement concrete repository-backed gaps.
7. Add focused regression coverage for every confirmed defect.
8. Verify the required GitHub Actions gate set before marking a task VERIFIED.
9. Keep the repository Forex-only; do not introduce Data Analysis, local coding-agent/Ollama architecture, speculative features, or unrelated agent architecture.
10. Use GitHub Connector only for repository inspection and modification.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites.
