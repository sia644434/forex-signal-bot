# Production Observability

This directory is the durable, assistant-readable observability surface for the production trading platform.

The central pipeline normalizes:
- Application runtime logs emitted through the central JSON logger.
- GitHub Actions workflow and job status.
- Sanitized GitHub Actions job logs.
- Railway deploy/runtime/build/HTTP/network/DNS logs when optional Railway credentials are configured.

## Architecture

GitHub Actions is the always-on central collector.

Railway integration is optional:
- Without a Railway token, the pipeline continues with GitHub and application CI telemetry. Railway logs remain available in Railway Log Explorer/CLI.
- With a Railway token, the same collector additionally imports Railway telemetry into the unified event schema.
- Missing Railway credentials are not an incident and do not fail the workflow.

No paid Railway plan is required by the observability pipeline itself.

## Files

- `latest/system-status.json`: unified normalized view and recent errors/events.
- `latest/railway-status.json`: Railway integration state and counts.
- `latest/github-actions.json`: GitHub workflow/job telemetry.
- `latest/incident-status.json`: centralized incident state.
- `raw/`: sanitized high-volume Railway/GitHub data, uploaded as GitHub Actions artifacts instead of committed every cycle.

## Optional Railway configuration

Only required if Railway telemetry should also be imported centrally:
- Secret `RAILWAY_TOKEN` or `RAILWAY_API_TOKEN`.
- Variable `RAILWAY_PROJECT_ID`.
- Variable `RAILWAY_ENVIRONMENT_ID`.
- Optional `RAILWAY_SERVICE_ID`.
- Optional `RAILWAY_DEPLOYMENT_ID`; if omitted, the collector discovers the latest deployment.
- Optional `RAILWAY_LOG_LINES` and `RAILWAY_BUILD_LOG_LINES`.

No Railway configuration is required for the GitHub-side observability pipeline.

## Security

Normalized events are redacted before persistence. Raw log files are also sanitized before they are uploaded as workflow artifacts, so the artifact path is not an unredacted log dump.
