# Task State

## TASK-001 through TASK-064
Phase 1/2 reliability and architecture tasks through DecisionEngine Supply/Demand consumption remain VERIFIED according to the persistent engineering history.

## TASK-065
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: ConfidenceEngine Numeric Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING

## TASK-066
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: FullAnalysisEngine Numeric Boundary Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING

## TASK-067
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: PositionSizing Decimal Numeric-Range Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Float-level finite validation was followed by Decimal quantization that could leak DecimalException for finite values exceeding active Decimal precision.
- PositionSizing converts that numeric-range failure to the public fail-closed ValueError contract.
- Regression coverage was added for the oversized-but-finite case.
- Implementation commit: `5967f1741e6e381fa83328d93f4f1b65d871b5dd`.
- Regression test commit: `307576dfddc63c079bed0c1fdeed16595fd7ad54`.

## TASK-068
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: RiskEngine Directional Price-Level Safety
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Deeper audit of `RiskEngine → PositionSizing → CurrencyConversion → MarketAwareAnalysisEngine` found that finite risk distances could still produce economically invalid trade levels.
- A BUY setup could produce a zero/negative stop-loss when risk distance crossed the entry price; a SELL setup could produce non-positive take-profit levels.
- The output contract now rejects non-positive risk levels and enforces directional ordering for BUY and SELL plans before position sizing output is emitted.
- The validator preserves the existing custom risk-reward contract where TP2 and TP3 may legitimately coincide at a 3R target.
- Regression coverage added for zero-crossing, non-positive SELL targets, overflow, and normal directional ordering.
- Implementation commit: `b11d6429698aa749c1263f9fe65e6b4a0bac42dd`.
- Regression test commit: `131f0a656c694a9b6e4e88e4b1f7326032f91074`.
- The first gate exposed an overly strict TP2/TP3 ordering assertion and a test fixture that incorrectly expected a BUY failure where only SELL could cross zero. Both were corrected before final verification.

## TASK-069
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Explicit Account-Balance Wiring and Settings Numeric Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- The production `MarketAwareAnalysisEngine` was constructing `RiskEngine` without an account balance, so executable position sizing always used RiskEngine's hard-coded default balance of 1000 instead of the configured trading account balance.
- `Settings` now exposes `ACCOUNT_BALANCE`, validates it as finite and strictly positive, and MarketAwareAnalysisEngine passes it explicitly into RiskEngine.
- `Settings.RISK_PER_TRADE` previously allowed `NaN`/`Infinity` through because ordinary range comparisons do not reject non-finite floats; it is now explicitly finite before range validation.
- `ACCOUNT_CURRENCY` is now normalized and validated as a three-letter alphabetic currency code.
- `.env.example` documents `ACCOUNT_BALANCE` and the explicit account-balance/risk policy relationship.
- Regression coverage verifies configured account balance changes risk amount and executable position size, rejects non-finite account balance/risk values, and rejects malformed account currencies.
- Implementation commits: `d8880ee51cfb8b975b629c1e69b74cba4eb75f1b` and `7101d6e121bb0e71b5517221ef55d460b9bef10f`.
- Regression commits: `9703fff13d0064dcb4631ec388fc19ee268587a1` and `9da8a791c872a278bfef350600173d0332be362f`.
- A first GitHub Test run exposed an incorrect expected position-size fixture; the implementation was correct and the fixture was corrected in `2a6fd7f3e874d0cda92b16b7eec04661e931d43c`.
- Verification for the corrected head is currently in progress; no green claim is made until the required gates finish.

## TASK-070
Phase: Phase 2 — Core Architecture / Analysis/Risk Reliability
Title: Risk-Policy Upper-Bound and Currency-Context Hardening
Implementation Status: IMPLEMENTED — VERIFICATION PENDING
Evidence:
- Deeper inspection of the completed account-balance/risk-sizing path found that standalone `PositionSizing` accepted a risk percentage greater than 100%, which could request a risk budget larger than the entire account balance.
- `RiskEngine` also accepted constructor and per-call risk policies above 100%, even though production `Settings` already caps the configured fraction at 1.0.
- `PositionSizing` now enforces `0 < risk_percent <= 100`.
- `RiskEngine` now enforces the same upper bound for its constructor policy and explicit per-call override.
- `RiskEngine.account_currency` now fails closed on malformed non-empty currency contexts instead of deferring the invalid value into a later sizing failure.
- Regression coverage verifies rejection above 100%, acceptance at exactly 100%, malformed account-currency rejection, and override-bound enforcement.
- Implementation commits: `39464db41d3b3478ec79322e455bf188607f7743` and `6d3eb873f6beb664ffe135002a9fba7a91f976a3`.
- Regression commits: `917c8690331083a2cebc8d806b9c3849ec431322` and `24350c2eaf3de319d55a1dfd440e5daa3a16b901`.
- Verification is pending on the resulting head; no green claim is made until the required gates finish.

## Current Phase 2 Audit Frontier
After TASK-065 through TASK-070 verification, continue the evidence-backed audit of:
`RiskEngine → PositionSizing → CurrencyConversion → MarketAwareAnalysisEngine`
then proceed outward into the Telegram/Scanner/Tracker/Callbacks and Worker/Queue/Persistence paths.

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
4. Do not repeat TASK-058 through TASK-070 unless their verification evidence is missing or contradicted.
5. Continue from the first unresolved audit frontier recorded above.
6. Inspect more architecture than the previous step and only implement concrete repository-backed gaps.
7. Add focused regression coverage for every confirmed defect.
8. Verify the required GitHub Actions gate set before marking a task VERIFIED.
9. Keep the repository Forex-only; do not introduce Data Analysis, local coding-agent/Ollama architecture, speculative features, or unrelated agent architecture.
10. Use GitHub Connector only for repository inspection and modification.

## Active Task Selection Rule
Prioritize concrete correctness, reliability, security, observability, deployment, and recovery gaps evidenced by repository code, tests, or deployment configuration. Avoid speculative rewrites.
