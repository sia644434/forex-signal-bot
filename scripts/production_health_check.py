from __future__ import annotations

import argparse
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class HealthCheckError(RuntimeError):
    """Raised when live production health cannot be verified."""


def check_health(base_url: str, *, attempts: int = 3, timeout: float = 10.0) -> dict:
    url = base_url.rstrip("/") + "/health"
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers={"Accept": "application/json"}, method="GET")
            with urlopen(request, timeout=timeout) as response:  # nosec B310 - URL is operator-supplied
                status = int(response.status)
                body = response.read().decode("utf-8")
            if status < 200 or status >= 300:
                raise HealthCheckError(f"health endpoint returned HTTP {status}")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as exc:
                raise HealthCheckError("health endpoint returned invalid JSON") from exc
            if not isinstance(payload, dict):
                raise HealthCheckError("health endpoint returned a non-object JSON payload")
            return payload
        except (HTTPError, URLError, TimeoutError, OSError, HealthCheckError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 4))

    raise HealthCheckError(f"live production health verification failed: {last_error}") from last_error


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a live deployment /health endpoint.")
    parser.add_argument("--base-url", default=os.getenv("PRODUCTION_BASE_URL"))
    args = parser.parse_args()

    if not args.base_url:
        print("PRODUCTION_BASE_URL is not configured; live production verification cannot run.", file=sys.stderr)
        return 2

    try:
        payload = check_health(args.base_url)
    except HealthCheckError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps({"verified": True, "health": payload}, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
