# Recovery State

## Current Status

- Container restart policy is configured in `railway.toml` with `ON_FAILURE` and retry limits.
- Docker healthcheck and Railway `/health` healthcheck are configured.
- The application health contract now rejects degraded critical-service states through the health endpoint.
- Actual Railway restart/recovery behavior has now been verified with live evidence.

## Verified Recovery Evidence

- Initial Production Live Smoke run `34697840749`, job `103564290648`: success.
- A controlled Railway restart/redeploy was then performed manually by the user.
- Post-restart Production Live Smoke run `34698134769`, job `103565063400`: success.
- Post-restart live health reported `application.status=ok` and `services.telegram.status=ok` with `critical=true`.
- Post-restart verification checked out deployed commit `8bf2a77840b72add70b98cbf1a3b2187f85763f2`.

## Verification Rule

The configured restart policy and healthchecks are mechanisms; the successful live restart/recovery observation is the evidence. The current Railway deployment path has satisfied that evidence requirement.


## Current Engineering Handoff — 2026-09-19
- CURRENT_PHASE: Phase 14 — Advanced Intelligence Foundation
- CURRENT_TASK: TASK-129
- LAST_COMPLETED_TASK: TASK-128
- LAST_VERIFIED_COMMIT: 7e978faa986ed6088511c0aee3a1fa4510a02408
- CURRENT_BRANCH: main
- IN_PROGRESS: exact-head CI verification and continued capability implementation
- REMAINING: portfolio/correlation/stress; strategy lifecycle; opportunity/heatmap; paper/shadow/replay; news/macro; final security/performance/regression; Railway final gate
- NEXT_ACTION: continue implementation from TASK-129 without repeating a full repository audit unless state becomes inconsistent or a cross-cutting dependency requires it.


## Current Handoff Update — 2026-09-19
- CURRENT_PHASE: Phase 20 capability expansion is being developed after the historical Phase-13 audit.
- CURRENT_TASK: TASK-132
- LAST_VERIFIED_COMMIT: 7e978faa986ed6088511c0aee3a1fa4510a02408
- NEW_UNVERIFIED_COMMITS: TASK-129 through TASK-132
- IN_PROGRESS: exact-head CI verification remains pending; capability implementation continues from the Master Prompt roadmap.
- REMAINING: Time Machine orchestration; strategy lifecycle/DNA/champion-challenger; news/macro real providers; advanced stress/sensitivity robustness; alert/report completion; final security/performance/regression; Railway final gate.
- NEXT_ACTION: continue with missing roadmap capabilities; do not treat Railway as the next development task.


## Current Handoff Update — TASK-133 — 2026-09-19
- CURRENT_PHASE: Phase 20 capability expansion.
- CURRENT_TASK: TASK-133.
- LAST_VERIFIED_COMMIT: 7e978faa986ed6088511c0aee3a1fa4510a02408.
- NEW_UNVERIFIED_COMMITS: TASK-129 through TASK-133.
- IN_PROGRESS: exact-head CI verification remains pending; Time Machine foundation is implemented and the roadmap continues.
- REMAINING: strategy lifecycle/DNA/champion-challenger; news/macro real providers; advanced stress/sensitivity robustness; alert/report completion; final security/performance/regression; Railway final gate.
- NEXT_ACTION: continue with the next missing roadmap capability; do not repeat a full repository audit unless persistent state becomes inconsistent or a cross-cutting dependency requires it.


## Current Handoff Update — TASK-134 — 2026-09-19
- CURRENT_PHASE: Phase 18 / 20 capability expansion.
- CURRENT_TASK: TASK-134.
- LAST_VERIFIED_COMMIT: 7e978faa986ed6088511c0aee3a1fa4510a02408.
- NEW_UNVERIFIED_COMMITS: TASK-129 through TASK-134.
- IN_PROGRESS: exact-head CI verification remains pending; strategy intelligence foundation is implemented.
- REMAINING: deeper strategy adaptation/continuous evaluation; news/macro real providers; advanced stress/sensitivity robustness; alert/report completion; final security/performance/regression; Railway final gate.
- NEXT_ACTION: continue with the next large missing capability while preserving state-first incremental inspection.


## Current Handoff Update — TASK-136 — 2026-09-19
- CURRENT_PHASE: Phase 17/18 capability expansion.
- CURRENT_TASK: TASK-136.
- LAST_VERIFIED_COMMIT: 7e978faa986ed6088511c0aee3a1fa4510a02408.
- NEW_UNVERIFIED_COMMITS: strategy lifecycle fix/expansion through robustness research implementation.
- IN_PROGRESS: exact-head CI verification for the current code frontier.
- COMPLETED_CURRENT: strategy adaptation, weakness detection, continuous evaluation, rollback/audit trail, robustness matrix, temporal leakage detection, and PC Worker robustness workload.
- REMAINING: news/macro real providers, alert/report completion, richer OOS/overfitting research, final security/performance/regression, Railway final gate.
- NEXT_ACTION: verify current-head CI, fix any regressions, then continue with the next large missing capability without repeating a full repository audit.


## 2026-09-19 — TASK-137 Macro / News Risk Expansion
- Added real NewsAPI and FRED adapters with explicit external-dependency diagnostics.
- Added macro event proximity assessment and integrated NORMAL/ELEVATED/CRISIS risk into the full analysis and decision boundary.
- Added regression tests for providers, macro assessment, and full-pipeline gating.
- Exact-head CI verification remains pending; no production verification is claimed for the new commits.


## 2026-09-19 — TASK-138 Advanced Research Validation
- CURRENT_PHASE: Phase 14/17 capability expansion.
- CURRENT_TASK: TASK-138.
- LAST_VERIFIED_COMMIT: historical verified frontier remains unchanged; current research commits are unverified pending CI.
- COMPLETED_CURRENT: OOS validation, rolling walk-forward validation, train/test divergence diagnostics, temporal leakage checks, and PC Worker routing.
- IN_PROGRESS: exact-head CI verification.
- REMAINING: richer robustness scenarios, strategy/research integration, alert/report completion, security/performance/regression, Railway final gate.
- NEXT_ACTION: verify the current head and fix regressions before claiming TASK-138 verified.


## 2026-09-19 — TASK-139 Research-Gated Strategy Lifecycle
- CURRENT_TASK: TASK-139.
- COMPLETED_CURRENT: research evidence is now connected to champion/challenger comparison and Worker evaluation.
- IN_PROGRESS: exact-head Actions verification.
- REMAINING: deeper research/strategy integration, alerts/reports, security/performance, full regression, Railway final gate.
- NEXT_ACTION: verify CI at the resulting head; fix any actual failure before marking verified.


## 2026-09-19 — TASK-140 Research-Gated Strategy Adaptation
- TASK-139 exact-head Actions were verified green on `7a8b864ca82a54218f79d33663cf08472513c5d0`.
- Implemented TASK-140: strategy DNA adaptation is now proposal-first and production mutation requires research validation evidence.
- Current task: TASK-140.
- IN_PROGRESS: exact-head Actions verification for TASK-140.
- NEXT_ACTION: inspect exact-head CI; fix only real failures, then continue to the next large missing capability.


## Recovery Frontier — TASK-141
- Last implemented code commit: 537c018cc979d858f5fb790e516a81de42716d94 (strategy worker regression coverage).
- Scope: version-bound strategy validation + research-backed worker evaluation integration.
- Exact-head CI verification: pending.
- Resume rule: check Actions for the latest main HEAD first; if green, mark TASK-141 VERIFIED. If red, inspect only the failing workflow/job and repair the affected boundary.
- Next development target after verification: deeper continuous strategy evaluation/history and validation-aware lifecycle state transitions.


## Recovery Frontier — TASK-142
- Latest implementation scope: validation-aware continuous strategy evaluation history.
- Exact-head CI verification: pending.
- Resume from the latest main HEAD; inspect only affected strategy-intelligence tests if CI fails.
- After verification, continue with richer lifecycle transitions/history and then broader strategy/research hardening.

## TASK-142 CI Repair
- Exact-head CI exposed a missing StrategyRecord initialization for evaluation_history.
- Fixed in `e89da517d4b9a8d552901e2562cfeee2e54aab72`.
- Recheck Actions on the new HEAD before continuing.

## TASK-143 Recovery Frontier
- Added automatic RobustnessEngine gating to research-backed strategy validation.
- Latest code/test commits: `af993591e329e8e160328ef16298bc4421c17344`, `192143e665b66444b3e789289e5f7ba06f01a1ec`.
- Exact-head Actions verification pending; resume by checking latest main HEAD workflows.


## Recovery Frontier — TASK-144
- Latest implementation head: e602866e50d35cb0f477491bf88fcc1f6a0b038e.
- TASK-143 CI exposed a research test-data issue: the prior linear price fixture produced a legitimate train/test divergence warning; the fixture was corrected to a stable geometric-return series rather than weakening the production gate.
- TASK-144 adds validation-gated challenger state, automatic retirement for persistent negative expectancy/elevated drawdown, and persisted research diagnostics.
- Exact-head Actions verification remains pending for the latest head.
- Resume rule: check all seven required workflows for the latest head; repair only concrete failures, then continue with remaining roadmap capabilities.
