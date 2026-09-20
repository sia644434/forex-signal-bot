from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from observability.redaction import redact_value
from observability.report import build_summary, parse_json_lines, write_json
from observability.schema import Event

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "observability" / "latest"
RAW = ROOT / "observability" / "raw"
REPO = os.environ.get("GITHUB_REPOSITORY", "siasoltoon/forex-signal-bot")


def run(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str, str]:
    process = subprocess.run(cmd, text=True, capture_output=True, env=env)
    return process.returncode, process.stdout, process.stderr


def railway_base_args(project: str, environment: str, service: str | None) -> list[str]:
    args = ["npx", "-y", "@railway/cli", "--project", project, "--environment", environment]
    if service:
        args += ["--service", service]
    return args


def discover_latest_deployment(
    project: str, environment: str, service: str | None, env: dict[str, str]
) -> str | None:
    command = railway_base_args(project, environment, service)
    command += ["deployment", "list", "--json", "--limit", "1"]
    code, output, _ = run(command, env)
    if code:
        return None
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return None

    deployments: list[dict[str, Any]]
    if isinstance(data, list):
        deployments = [item for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        raw = data.get("deployments") or data.get("data") or []
        deployments = [item for item in raw if isinstance(item, dict)]
    else:
        deployments = []

    return str(deployments[0].get("id")) if deployments and deployments[0].get("id") else None


def _write_raw(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact_value(text), encoding="utf-8")


def collect_railway() -> list[Event]:
    token = os.environ.get("RAILWAY_TOKEN") or os.environ.get("RAILWAY_API_TOKEN")
    project = os.environ.get("RAILWAY_PROJECT_ID")
    environment = os.environ.get("RAILWAY_ENVIRONMENT_ID")
    service = os.environ.get("RAILWAY_SERVICE_ID")

    # Railway telemetry is optional. The central pipeline remains healthy when
    # no Railway token is available; Railway's own dashboard/CLI remains the
    # authoritative UI for Railway logs in that mode.
    if not token:
        write_json(
            OUT / "railway-status.json",
            {
                "status": "optional_not_configured",
                "enabled": False,
                "reason": "No Railway API/project token is configured.",
                "central_observability": "github_only",
            },
        )
        return []

    if not project or not environment:
        write_json(
            OUT / "railway-status.json",
            {
                "status": "misconfigured",
                "enabled": False,
                "reason": "Railway token exists but project/environment IDs are missing.",
                "required_when_enabled": [
                    "RAILWAY_PROJECT_ID",
                    "RAILWAY_ENVIRONMENT_ID",
                ],
            },
        )
        return []

    env = os.environ.copy()
    env["RAILWAY_TOKEN"] = token
    lines = os.environ.get("RAILWAY_LOG_LINES") or "500"
    build_lines = os.environ.get("RAILWAY_BUILD_LOG_LINES") or "1000"
    deployment = os.environ.get("RAILWAY_DEPLOYMENT_ID") or discover_latest_deployment(
        project, environment, service, env
    )

    events: list[Event] = []
    raw_dir = RAW / "railway"
    raw_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    base = railway_base_args(project, environment, service)

    def collect(kind: str, extra: list[str], filename: str) -> None:
        command = base + ["logs", "--json", "--lines", lines] + extra
        if kind in {"runtime", "http"}:
            command.append("--latest")
        code, output, error = run(command, env)
        if code:
            _write_raw(raw_dir / f"{filename}-error.txt", error[-4000:])
            counts[kind] = 0
            return
        parsed = parse_json_lines(output, "railway", kind)
        counts[kind] = len(parsed)
        _write_raw(
            raw_dir / f"{filename}.jsonl",
            "\n".join(event.to_json() for event in parsed) + ("\n" if parsed else ""),
        )
        events.extend(parsed)

    collect("runtime", [], "runtime")
    collect("http", ["--http"], "http")
    collect("network", ["--network"], "network")
    collect("dns", ["--dns"], "dns")

    if deployment:
        command = base + [
            "logs",
            deployment,
            "--build",
            "--json",
            "--lines",
            build_lines,
        ]
        code, output, error = run(command, env)
        if code:
            _write_raw(raw_dir / "build-error.txt", error[-4000:])
            counts["build"] = 0
        else:
            parsed = parse_json_lines(output, "railway", "build")
            counts["build"] = len(parsed)
            _write_raw(
                raw_dir / "build.jsonl",
                "\n".join(event.to_json() for event in parsed)
                + ("\n" if parsed else ""),
            )
            events.extend(parsed)
    else:
        counts["build"] = 0

    write_json(
        OUT / "railway-status.json",
        {
            "status": "ok",
            "enabled": True,
            "event_count": len(events),
            "counts": counts,
            "project_id": project,
            "environment_id": environment,
            "service_id": service,
            "deployment_id": deployment,
        },
    )
    return events


def collect_github() -> list[Event]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/runs?per_page=30",
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        runs = json.load(response).get("workflow_runs", [])

    events: list[Event] = []
    raw_dir = RAW / "github"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for run_data in runs:
        conclusion = run_data.get("conclusion")
        level = (
            "INFO"
            if conclusion == "success"
            else "ERROR"
            if conclusion in {"failure", "timed_out", "startup_failure"}
            else "WARN"
        )
        events.append(
            Event(
                timestamp=run_data.get("updated_at") or run_data.get("created_at"),
                source="github",
                service="actions",
                level=level,
                event="workflow_run",
                message=f'{run_data.get("name")} => {run_data.get("status")}/{conclusion}',
                commit_sha=run_data.get("head_sha"),
                metadata={
                    "run_id": run_data.get("id"),
                    "workflow": run_data.get("name"),
                    "html_url": run_data.get("html_url"),
                },
            )
        )

        run_id = run_data.get("id")
        if not run_id:
            continue

        try:
            jobs_request = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100",
                headers=headers,
            )
            with urllib.request.urlopen(jobs_request, timeout=30) as response:
                jobs = json.load(response).get("jobs", [])

            for job in jobs:
                job_id = job.get("id")
                if not job_id:
                    continue

                job_conclusion = job.get("conclusion")
                job_level = (
                    "INFO"
                    if job_conclusion == "success"
                    else "ERROR"
                    if job_conclusion in {"failure", "timed_out", "startup_failure"}
                    else "WARN"
                )
                events.append(
                    Event(
                        timestamp=job.get("completed_at")
                        or job.get("started_at")
                        or run_data.get("updated_at"),
                        source="github",
                        service="actions",
                        level=job_level,
                        event="workflow_job",
                        message=f'{job.get("name")} => {job.get("status")}/{job_conclusion}',
                        commit_sha=run_data.get("head_sha"),
                        metadata={
                            "run_id": run_id,
                            "job_id": job_id,
                            "workflow": run_data.get("name"),
                            "job": job.get("name"),
                            "html_url": job.get("html_url"),
                        },
                    )
                )

                log_request = urllib.request.Request(
                    f"https://api.github.com/repos/{REPO}/actions/jobs/{job_id}/logs",
                    headers=headers,
                )
                try:
                    with urllib.request.urlopen(log_request, timeout=30) as response:
                        raw = response.read().decode("utf-8", "replace")
                    _write_raw(raw_dir / f"{run_id}-{job_id}.log", raw)

                    for line in raw.splitlines():
                        stripped = line.strip()
                        if "##[error]" in stripped:
                            events.append(
                                Event(
                                    timestamp=job.get("completed_at")
                                    or job.get("started_at")
                                    or run_data.get("updated_at"),
                                    source="github",
                                    service="actions",
                                    level="ERROR",
                                    event="workflow_log_error",
                                    message=stripped.split("##[error]", 1)[-1].strip(),
                                    commit_sha=run_data.get("head_sha"),
                                    metadata={
                                        "run_id": run_id,
                                        "job_id": job_id,
                                        "workflow": run_data.get("name"),
                                        "job": job.get("name"),
                                    },
                                )
                            )
                        elif "##[warning]" in stripped:
                            events.append(
                                Event(
                                    timestamp=job.get("completed_at")
                                    or job.get("started_at")
                                    or run_data.get("updated_at"),
                                    source="github",
                                    service="actions",
                                    level="WARN",
                                    event="workflow_log_warning",
                                    message=stripped.split("##[warning]", 1)[-1].strip(),
                                    commit_sha=run_data.get("head_sha"),
                                    metadata={
                                        "run_id": run_id,
                                        "job_id": job_id,
                                        "workflow": run_data.get("name"),
                                        "job": job.get("name"),
                                    },
                                )
                            )
                except urllib.error.HTTPError as exc:
                    _write_raw(
                        raw_dir / f"{run_id}-{job_id}.error.txt",
                        f"HTTP {exc.code}: {exc.reason}",
                    )
        except Exception as exc:
            _write_raw(raw_dir / f"{run_id}-jobs.error.txt", str(exc))

    write_json(
        OUT / "github-actions.json",
        {
            "status": "ok",
            "run_count": len(runs),
            "event_count": len(events),
            "runs": [event.to_dict() for event in events],
        },
    )
    return events


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        railway = collect_railway()
        github = collect_github()
        events = railway + github
        summary = build_summary(events, commit_sha=os.environ.get("GITHUB_SHA"))
        write_json(OUT / "system-status.json", summary)
        write_json(
            OUT / "incident-status.json",
            {
                "status": "incident" if summary["errors"] else "healthy",
                "error_count": len(summary["errors"]),
                "latest_errors": summary["errors"][-20:],
            },
        )
        print(
            json.dumps(
                {
                    "events": len(events),
                    "railway": len(railway),
                    "github_actions": len(github),
                    "errors": len(summary["errors"]),
                }
            )
        )
        return 0
    except Exception as exc:
        write_json(
            OUT / "system-status.json",
            {
                "status": "collector_error",
                "error": str(exc),
                "commit_sha": os.environ.get("GITHUB_SHA"),
            },
        )
        write_json(
            OUT / "incident-status.json",
            {
                "status": "collector_error",
                "error_count": 1,
                "latest_errors": [
                    {
                        "level": "CRITICAL",
                        "event": "collector_failure",
                        "message": str(exc),
                    }
                ],
            },
        )
        print(f"Observability collector error captured: {exc}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
