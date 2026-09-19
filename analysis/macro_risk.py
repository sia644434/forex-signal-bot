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
    def __init__(self, providers: list[Any] | None = None, *, cache_ttl_seconds: int = 300) -> None:
        if cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")
        self.providers = providers or [NewsAPIProvider(), FREDProvider()]
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}


    @staticmethod
    def assess(events: list[MacroEvent], *, now: datetime | None = None, proximity_minutes: int = 120) -> dict[str, Any]:
        if proximity_minutes < 0:
            raise ValueError("proximity_minutes must be non-negative")
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        relevant = []
        for event in events:
            if event.timestamp is None:
                continue
            delta = abs((event.timestamp - current).total_seconds()) / 60.0
            if delta <= proximity_minutes:
                relevant.append(event)
        high = sum(event.impact == "HIGH" for event in relevant)
        medium = sum(event.impact == "MEDIUM" for event in relevant)
        if high:
            level = "CRISIS" if high >= 2 else "ELEVATED"
        elif medium:
            level = "ELEVATED"
        else:
            level = "NORMAL"
        return {
            "status": "OK" if relevant else "NO_DATA",
            "risk_level": level,
            "high_impact_count": high,
            "medium_impact_count": medium,
            "events": [MacroRiskEngine._serialize(event) for event in relevant],
            "proximity_minutes": proximity_minutes,
        }

    def collect(self, *, query: str = "economy OR inflation OR interest rates", series_ids: list[str] | None = None, now: datetime | None = None) -> dict[str, Any]:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        cache_key = json.dumps({"query": query, "series_ids": series_ids or []}, sort_keys=True)
        cached = self._cache.get(cache_key)
        if cached is not None and self.cache_ttl_seconds > 0:
            age = (current - cached[0]).total_seconds()
            if 0 <= age <= self.cache_ttl_seconds:
                result = dict(cached[1])
                result["status"] = "CACHED"
                result["cache_age_seconds"] = round(age, 3)
                return result

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
        result = {
            "events": [self._serialize(event) for event in events],
            "count": len(events),
            "status": "OK" if events else ("EXTERNAL_DEPENDENCY" if diagnostics else "NO_DATA"),
            "diagnostics": diagnostics,
            "cache_age_seconds": 0.0,
        }
        self._cache[cache_key] = (current, result)
        return result

    def collect_and_assess(
        self,
        *,
        query: str = "economy OR inflation OR interest rates",
        series_ids: list[str] | None = None,
        now: datetime | None = None,
        proximity_minutes: int = 120,
    ) -> dict[str, Any]:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        collected = self.collect(query=query, series_ids=series_ids, now=current)
        events = []
        for item in collected["events"]:
            timestamp = _timestamp(item.get("timestamp"))
            if timestamp is not None:
                events.append(MacroEvent(
                    provider=str(item["provider"]),
                    event_id=str(item["event_id"]),
                    title=str(item["title"]),
                    timestamp=timestamp,
                    impact=str(item["impact"]),
                    category=str(item["category"]),
                    url=item.get("url"),
                    source=item.get("source"),
                ))
        assessed = self.assess(events, now=current, proximity_minutes=proximity_minutes)
        assessed["provider_status"] = collected["status"]
        assessed["provider_diagnostics"] = collected["diagnostics"]
        assessed["collected_count"] = collected["count"]
        return assessed

    @staticmethod
    def _serialize(event: MacroEvent) -> dict[str, Any]:
        return {
            "provider": event.provider, "event_id": event.event_id, "title": event.title,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "impact": event.impact, "category": event.category, "url": event.url, "source": event.source,
        }


__all__ = ["MacroEvent", "MacroProviderError", "NewsAPIProvider", "FREDProvider", "MacroRiskEngine"]
