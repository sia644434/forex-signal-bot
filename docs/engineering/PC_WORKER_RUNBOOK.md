# PC Worker Connection Runbook

## Architecture

- Railway runs the Telegram/control plane and the durable SQLite-backed worker queue.
- The Windows PC runs the PC Worker process.
- Railway reaches the PC Worker through an HTTPS endpoint.
- The PC Worker endpoint requires the shared PC_WORKER_TOKEN.
- Worker availability is optional: when the worker is offline, heavy jobs remain PENDING and are retried after an authenticated worker heartbeat reports READY.

## Windows PC setup

From the repository root:

1. Install the project Python dependencies.
2. Create a strong random worker token and keep it out of Git:
   ~~~powershell
   $env:PC_WORKER_TOKEN = [Convert]::ToHexString((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
   ~~~
3. Start the worker:
   ~~~powershell
   $env:PC_WORKER_HOST = "127.0.0.1"
   $env:PC_WORKER_PORT = "8765"
   python -m worker.main
   ~~~
4. In another PowerShell window, verify locally:
   ~~~powershell
   Invoke-WebRequest http://127.0.0.1:8765/health
   ~~~
   The response must report READY.

## HTTPS endpoint

For Railway to reach a home PC without port forwarding, Tailscale Funnel can proxy the local worker over HTTPS. Keep the worker itself bound to 127.0.0.1; Funnel terminates public TLS and proxies to localhost.

Example:

~~~powershell
tailscale funnel 8765
tailscale funnel status
~~~

Copy the HTTPS *.ts.net URL shown by Tailscale.

## Railway variables

Configure:

- PC_WORKER_URL=https://<your-worker>.ts.net
- PC_WORKER_TOKEN=<same-secret-token>
- PC_WORKER_TIMEOUT=30
- PC_WORKER_HEARTBEAT_MAX_AGE=120
- WORKER_QUEUE_DATABASE_PATH=worker_queue.sqlite3

After Railway starts, the worker service performs an authenticated heartbeat and keeps checking readiness. Heavy jobs are dispatched only when the worker is READY.

## Security

- Never expose the worker without PC_WORKER_TOKEN.
- Never put the token in Git, workflow files, logs, Telegram messages, or screenshots.
- Funnel makes the endpoint reachable from the public internet, so the bearer token is the application-level access control.
- If the token is ever exposed, rotate it on both the PC Worker and Railway immediately.

## Connection verification

Expected sequence:

1. PC Worker starts and logs ready.
2. Tailscale Funnel reports the public HTTPS endpoint.
3. Railway has matching PC_WORKER_URL and PC_WORKER_TOKEN.
4. Railway worker service health changes to READY.
5. A profile backtest submitted from Telegram is accepted by the PC Worker.
6. The queue record reaches COMPLETED.
7. If the PC is stopped, new heavy jobs remain PENDING.
8. When the PC Worker returns and heartbeat becomes READY, pending jobs are retried automatically.
