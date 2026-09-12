# Production Verification Runbook

## Purpose

This runbook defines the final evidence required before production readiness can be marked verified.

## 1. Live Health Smoke

Use the GitHub Actions workflow `Production Live Smoke`.

Prerequisite:

- Repository secret `PRODUCTION_BASE_URL` must contain the deployed application's base URL.

Expected evidence:

- Workflow completes successfully.
- `GET /health` returns HTTP 2xx.
- The response is valid JSON.
- Application readiness is healthy.
- No critical service is reported as failed/degraded.

A green CI test suite without this live run does not satisfy the live-production gate.

## 2. Restart / Recovery Verification

After a successful live health smoke:

1. Trigger a controlled Railway restart/redeploy of the production service.
2. Observe the service transition through restart.
3. Confirm the service becomes healthy again without manual code changes.
4. Confirm Railway's `/health` healthcheck passes after recovery.
5. Run `Production Live Smoke` again and retain the successful run as evidence.

Do not treat the configured `ON_FAILURE` restart policy or Docker/Railway healthchecks as proof that recovery works. Configuration is only the recovery mechanism; the successful live observation is the evidence.

## 3. Final Readiness Rule

Production readiness may be marked verified only when all of the following are evidenced:

- Full automated test suite is green.
- Production Docker build is green.
- Dependency security audit is green.
- Production activation/readiness gates are green.
- Live `/health` smoke is green against the actual deployed URL.
- Restart/recovery is observed successfully in the deployed environment.

Until the final two live checks exist, the project remains `NOT LIVE-VERIFIED`.
