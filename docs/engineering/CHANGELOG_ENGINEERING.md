# Engineering Changelog

## 2026-09-13 — TASK-064
- Fixed a concrete DecisionEngine contract gap: the Supply/Demand decision component was reading `trend_score` instead of the explicit `supply_demand_score` produced by the production analysis pipeline.
- Added regression coverage proving that explicit Supply/Demand score changes affect the final decision score independently of `trend_score`.
- Verification commit `6b21d82f04a4a7deab2865ffe1bc86a066c8fca5` passed Test run `34778972992` and Production Activation Gate run `34778972997`.
- Test run job `103782342868` completed successfully, including lifecycle/persistence tests, full suite, application health, Telegram imports, signal lifecycle imports, and syntax checks.
- Production Activation Gate job `103782342960` completed successfully, including compile, activation tests, and full test suite.
- TASK-064 is VERIFIED. No local execution is claimed.

## 2026-09-13 — TASK-063
- Wired the actual SupplyDemandEngine score into the AnalysisResult confidence contract.
- Added full-pipeline regression coverage and verified the final main head with the Production E2E Contract Gate.

## 2026-09-13 — TASK-062
- Fixed ConfidenceEngine supply-demand score aliasing by using the explicit `supply_demand_score` contract.
- Added regression coverage for neutral fallback and explicit supply-demand scoring.

## 2026-09-13
- TASK-060: identified a concrete FullAnalysisEngine score-contract gap: DecisionEngine emits a 0..100 score centered on neutral 50, while FullAnalysisEngine used `abs(decision.score)` when calculating trade quality.
- TASK-060: this made equivalent bearish and bullish score strengths receive different trade-quality contributions.
- TASK-060: introduced neutral-centered directional strength `abs((score - 50) * 2)` at the FullAnalysisEngine trade-quality boundary.
- TASK-060: added regression coverage for symmetric score pairs 0/100, 25/75, and neutral 50.
- TASK-060: implementation commit `17335d61eaca21614b50de963e7b08d3a655a063`.
- TASK-060: regression test commit `cf3787509e951755eb082a783ddf531f164febda`.
- TASK-060: verification trigger commit `5e91e0e5771f6d81cec2f421dc51c8e51e8cd9e6` completed the required 7-workflow GitHub Actions gate set successfully.
- TASK-060: Railway commit status for the verification trigger commit is successful.
- TASK-060: persistent engineering state was synchronized before final temporary-trigger cleanup.
- TASK-059: identified a concrete RiskEngine score-contract gap: DecisionEngine emits a 0..100 score centered on neutral 50, while RiskEngine used `abs(score)` as though the score were centered on zero.
- TASK-059: introduced symmetric directional strength `abs((score - 50) * 2)` so equivalent bullish/bearish scores receive equivalent risk treatment.
- TASK-059: applied the normalized strength consistently to dynamic risk percentage, risk level, and trade-quality calculations.
- TASK-059: added regression coverage for symmetric score pairs and neutral-score behavior.
- TASK-059: implementation commit `a98411053c3433fe219b82abf82575547efc98b3`.
- TASK-059: required 7-workflow GitHub Actions verification completed successfully after a push-based CI trigger sequence; final verification commit on `main` was `bb1e4464f0177fd612eeff2240aa096447275b2c`.
- TASK-059: Railway commit status for the final verified `main` head is successful.
- TASK-059: temporary CI trigger file was removed after verification.
- TASK-058: verified the FreshnessPolicy explicit-zero threshold fix across the required CI gate set and Railway deployment/status path.
- Synchronized persistent engineering state after TASK-058, TASK-059, and TASK-060 verification. Phase 2 remains active for continued evidence-backed analysis/reliability auditing.
