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
