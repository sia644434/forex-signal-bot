# Project State

- Project: `siasoltoon/forex-signal-bot`
- Current Branch: `main`
- Current Commit: `5573f772477b3bf05fca4cf9e105b64dc054a29b`
- Overall Status: `IN_PROGRESS`
- Current Phase: Phase 1 — Repository Audit / Baseline Stabilization
- Current Task: TASK-002 — Restore failing data-quality and scanner contracts
- Last Completed Task: Persistent repository memory established; CI failures diagnosed; focused fixes implemented
- Next Task: Verify TASK-002 through GitHub Actions and continue with the next highest-risk correctness/reliability gap
- Known Blockers: GitHub Connector does not expose a local working tree; private deployment/runtime credentials are not available for independent production verification
- Known Risks: Production readiness is NOT verified. Baseline CI run failed with five contract regressions; fixes are committed but not yet CI-verified on the latest commit
- Broken Tests: Baseline run `34689171483`: 5 failed, 341 passed
- CI Status: Baseline run failed at full suite; lifecycle tests passed. New commits triggered fresh CI requiring verification.
- Deployment Status: Railway configuration exists; production health remains unverified
- Architecture Status: High-level baseline mapped; targeted subsystem verification is active
- Production Readiness: `NOT_READY / NOT_VERIFIED`
- Last Checkpoint: TASK-002 implementation checkpoint
- Last State Update: 2026-09-12

## Evidence

Baseline CI run `34689171483` installed dependencies successfully and passed `tests/test_lifecycle_features.py` (2/2), then failed the full suite with 5 failures and 341 passes. Failures: two data-gap contract checks, invalid `None` configuration message, scanner exception-name exposure, and scanner localization.

TASK-002 changes:
- `data/quality.py`: explicit `None`/gap-tolerance validation and deterministic large-gap detection.
- `services/telegram/scanner.py`: internal exception names are no longer exposed; scanner output is localized.
- `services/telegram/i18n.py`: scanner title/status/field translations added for Persian and English.

## Checkpoint

What was done: diagnosed all five failures from the actual GitHub Actions log and implemented focused fixes.

Commits:
- `6ccb77d` — fix: enforce market data quality contract
- `7ebb648` — fix: localize and sanitize scanner output
- `5573f77` — fix: complete scanner localization strings

What was tested: corrections were made directly against the failing assertions from CI evidence. No local execution was claimed because the repository connector does not provide a local test runtime.

Next exact action: inspect the newly triggered CI run for `5573f77`; if green, update TASK/TEST/PHASE state and continue. If red, classify and fix the exact failure rather than rerunning blindly.
