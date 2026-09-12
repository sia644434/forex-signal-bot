# Recovery State

## Current Status

- Container restart policy is configured in `railway.toml` with `ON_FAILURE` and retry limits.
- Docker healthcheck and Railway `/health` healthcheck are configured.
- The application health contract now rejects degraded critical-service states through the health endpoint.
- Actual Railway restart/recovery behavior remains unverified until live runtime evidence is available.

## Verification Rule

Do not claim restart recovery is production-verified from configuration alone. A successful live deployment smoke/recovery observation is required.
