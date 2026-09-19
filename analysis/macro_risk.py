from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any


class MacroProviderError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MacroEvent:
    provider: str
    event_id: str
    title: str
    timestamp: datetime | None
    impact: str
    category: str
    url: str | None = None
    source: str | None = None


def _get_json(url: str, *, timeout: float = 10.0) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "forex-signal-bot/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise MacroProviderError(str(exc)) from exc
    if not isinstance(payload, dict):
        raise MacroProviderError("provider returned a non-object payload")
    return payload


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class NewsAPIProvider:
    name = "newsapi"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("NEWSAPI_API_KEY")

    def available(self) -> bool:
        return bool(self.api_key)

    def fetch(self, *, query: str = "economy OR inflation OR interest rates", page_size: int = 20) -> list[MacroEvent]:
        if not self.api_key:
            raise MacroProviderError("NEWSAPI_API_KEY is not configured")
        params = urlencode({"q": query, "pageSize": min(max(int(page_size), 1), 100), "apiKey": self.api_key, "language": "en", "sortBy": "publishedAt"})
        payload = _get_json("https://newsapi.org/v2/everything?" + params)
        if payload.get("status") != "ok":
            raise MacroProviderError(str(payload.get("message", "NewsAPI request failed")))
        events = []
        for article in payload.get("articles", []):
            if not isinstance(article, dict):
                continue
            title = str(article.get("title") or "").strip()
            if not title:
                continue
            text = f"{title} {article.get('description') or ''}".lower()
            impact = "HIGH" if any(k in text for k in ("rate", "inflation", "cpi", "fed", "ecb", "recession", "payroll", "employment")) else "MEDIUM"
            events.append(MacroEvent(
                provider=self.name,
                event_id=str(article.get("url") or title),
                title=title,
                timestamp=_timestamp(article.get("publishedAt")),
                impact=impact,
                category="NEWS",
                url=article.get("url"),
                source=(article.get("source") or {}).get("name") if isinstance(article.get("source"), dict) else None,
            ))
        return events


class FREDProvider:
    name = "fred"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("FRED_API_KEY")

    def available(self) -> bool:
        return bool(self.api_key)

    def fetch_series(self, series_id: str, *, limit: int = 20) -> list[MacroEvent]:
        if not self.api_key:
            raise MacroProviderError("FRED_API_KEY is not configured")
        if not series_id or not series_id.strip():
            raise ValueError("series_id is required")
        params = urlencode({
            "series_id": series_id.strip().upper(),
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": min(max(int(limit), 1), 100),
        })
        payload = _get_json("https://api.stlouisfed.org/fred/series/observations?" + params)
        observations = payload.get("observations", [])
        events = []
        for item in observations:
            if not isinstance(item, dict):
                continue
            date = _timestamp(str(item.get("date")) + "T00:00:00+00:00")
            value = str(item.get("value", ""))
            if value in {"", "."}:
                continue
            events.append(MacroEvent(
                provider=self.name,
                event_id=f"{series_id}:{item.get('date')}",
                title=f"FRED {series_id.upper()} = {value}",
                timestamp=date,
                impact="HIGH",
                category="MACRO_SERIES",
                source="Federal Reserve Bank of St. Louis",
            ))
        return events


class MacroRiskEngine:
    def __init__(self, providers: list[Any] | None = None) -> None:
        self.providers = providers or [NewsAPIProvider(), FREDProvider()]

    def collect(self, *, query: str = "economy OR inflation OR interest rates", series_ids: list[str] | None = None) -> dict[str, Any]:
        events: list[MacroEvent] = []
        diagnostics: list[dict[str, str]] = []
        for provider in self.providers:
            try:
                if isinstance(provider, FREDProvider):
                    for series_id in series_ids or []:
                        events.extend(provider.fetch_series(series_id))
                else:
                    events.extend(provider.fetch(query=query))
            except MacroProviderError as exc:
                diagnostics.append({"provider": provider.name, "status": "EXTERNAL_DEPENDENCY", "error": str(exc)})
            except Exception as exc:
                diagnostics.append({"provider": getattr(provider, "name", "unknown"), "status": "DEGRADED", "error": str(exc)})
        events.sort(key=lambda item: item.timestamp or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return {
            "events": [self._serialize(event) for event in events],
            "count": len(events),
            "status": "OK" if events else ("EXTERNAL_DEPENDENCY" if diagnostics else "NO_DATA"),
            "diagnostics": diagnostics,
        }

    @staticmethod
    def _serialize(event: MacroEvent) -> dict[str, Any]:
        return {
            "provider": event.provider, "event_id": event.event_id, "title": event.title,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "impact": event.impact, "category": event.category, "url": event.url, "source": event.source,
        }


__all__ = ["MacroEvent", "MacroProviderError", "NewsAPIProvider", "FREDProvider", "MacroRiskEngine"]
