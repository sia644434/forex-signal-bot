# Test State

## Current Verification State
- Current `main` HEAD: `1aec001ff4769bb47171513ad1bdb7da5bb88c73`.
- Historical phase closure checks remain preserved at their recorded exact heads.
- The current combined GitHub status is **not green** because the Railway deployment status `lavish-energy - forex-signal-bot` is failing.
- The current commit has no PR-triggered workflow runs returned by the workflow-run lookup.
- Therefore historical seven-workflow closure evidence must not be represented as fresh current-HEAD verification.
- No local execution is claimed.

## Verification Contract
Before marking any reopened task or phase VERIFIED:
1. Inspect the exact current `main` HEAD.
2. Run/inspect the complete required workflow set for the resulting HEAD.
3. Inspect combined commit status.
4. For deployment changes, require fresh deployment health/recovery evidence.
5. Re-run focused regressions and dependent cross-layer checks.
6. Update engineering state only after all evidence agrees.

## Historical Verification
The repository retains historical exact-head evidence for Phases 1–11, including the seven-check closure sets documented in `PHASE_STATE.md` and `TASK_STATE.md`. Historical evidence remains useful but is not a substitute for current-HEAD verification.

## Current Frontier
Phase 12 deployment re-verification and the cross-phase integrity audit are the current verification frontier. Phase 13 is blocked until that frontier is resolved.

## New-chat Rule
Repository inspection/modification uses GitHub Connector only. Do not invent test success, deployment success, live-smoke evidence, or phase completion.