# Production Observability

This directory is the durable, assistant-readable observability surface for the production trading platform.

It collects Railway runtime, HTTP, network, DNS and (when RAILWAY_DEPLOYMENT_ID is supplied) build logs (including scanner/provider/Telegram/application output), GitHub Actions status, normalized events, and redacted incident summaries.

Files: latest/system-status.json, latest/railway-status.json, latest/github-actions.json, latest/incident-status.json. High-volume raw history is uploaded as GitHub Actions artifacts instead of being committed every cycle.

Required GitHub Actions configuration: secret RAILWAY_TOKEN; variables RAILWAY_PROJECT_ID, RAILWAY_ENVIRONMENT_ID; optional RAILWAY_SERVICE_ID, RAILWAY_DEPLOYMENT_ID, RAILWAY_LOG_LINES and RAILWAY_BUILD_LOG_LINES. Use a Railway project token scoped to the production environment. Never commit credentials.

Railway logs have finite retention, so the workflow archives the collected raw batch as an artifact. Secrets are redacted before normalized files are written.
