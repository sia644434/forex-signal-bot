# Production Observability

This directory is the durable, assistant-readable observability surface for the production trading platform.

The central observability pipeline normalizes:
- Application runtime logs emitted through the central JSON logger.
- Railway deploy/runtime logs.
- Railway build logs.
- Railway HTTP, network-flow and DNS logs.
- GitHub Actions workflow and job status.
- GitHub Actions raw job logs, archived as artifacts.
- Redacted errors and warnings extracted from GitHub job logs.

Application logs are emitted to stdout/stderr in structured JSON so Railway can capture them. External Railway and GitHub telemetry is then collected by the scheduled observability workflow and normalized into the same `Event` schema.

Files:
- `latest/system-status.json`: unified normalized view and recent errors/events.
- `latest/railway-status.json`: Railway collection status and counts.
- `latest/github-actions.json`: GitHub workflow/job telemetry.
- `latest/incident-status.json`: centralized incident state.
- `raw/`: high-volume raw Railway/GitHub data, uploaded as GitHub Actions artifacts instead of committed every cycle.

Required GitHub Actions configuration:
- Secret `RAILWAY_TOKEN` or `RAILWAY_API_TOKEN`.
- Variable `RAILWAY_PROJECT_ID`.
- Variable `RAILWAY_ENVIRONMENT_ID`.
- Optional variable `RAILWAY_SERVICE_ID`.
- Optional variable `RAILWAY_DEPLOYMENT_ID`; if omitted, the collector automatically discovers the latest deployment.
- Optional variables `RAILWAY_LOG_LINES` and `RAILWAY_BUILD_LOG_LINES`.

Secrets are redacted before normalized files are written. Raw GitHub/Railway logs are retained only as workflow artifacts according to the configured artifact retention.
