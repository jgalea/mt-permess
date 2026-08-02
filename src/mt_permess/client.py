"""HTTP client for the permess.mt public API."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE = "https://permess.mt"
USER_AGENT = "mt-permess/0.1 (+https://github.com/jgalea/mt-permess)"


class PermessError(Exception):
    """Raised when the permess API returns an error."""


class PermessClient:
    def __init__(self, base_url: str = DEFAULT_BASE, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._ctx = ssl.create_default_context()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query: list[tuple[str, str]] = []
        if params:
            for key, value in params.items():
                if value is None:
                    continue
                if isinstance(value, (list, tuple)):
                    for item in value:
                        query.append((key, str(item)))
                else:
                    query.append((key, str(value)))
        qs = urllib.parse.urlencode(query)
        url = f"{self.base_url}{path}"
        if qs:
            url = f"{url}?{qs}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                body = resp.read()
                if not body:
                    raise PermessError(f"Empty response from {url}")
                return json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read()[:400].decode("utf-8", errors="replace")
            raise PermessError(f"HTTP {e.code} for {url}: {detail}") from e
        except urllib.error.URLError as e:
            raise PermessError(f"Request failed for {url}: {e.reason}") from e
        except json.JSONDecodeError as e:
            raise PermessError(f"Invalid JSON from {url}: {e}") from e

    def stats(
        self,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
        villages: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/api/stats",
            {
                "start_year": start_year,
                "end_year": end_year,
                "villages": villages,
            },
        )

    def radius(
        self,
        *,
        lat: float,
        lon: float,
        radius: float,
    ) -> dict[str, Any]:
        return self._get(
            "/api/permits/radius",
            {"lat": lat, "lon": lon, "radius": radius},
        )

    def area(
        self,
        *,
        nw_lon_lat: str,
        se_lon_lat: str,
        start_year: int | None = None,
        end_year: int | None = None,
        year: int | None = None,
        permit_type: str | None = None,
        villages: list[str] | None = None,
        ai_category: str | None = None,
        ai_value: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/api/permits/area",
            {
                "nw_lon_lat": nw_lon_lat,
                "se_lon_lat": se_lon_lat,
                "start_year": start_year,
                "end_year": end_year,
                "year": year,
                "permit_type": permit_type,
                "villages": villages,
                "ai_category": ai_category,
                "ai_value": ai_value,
            },
        )

    def heatmap(
        self,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
        permit_type: str | None = None,
        villages: list[str] | None = None,
        ai_category: str | None = None,
        ai_value: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/api/permits/heatmap",
            {
                "start_year": start_year,
                "end_year": end_year,
                "permit_type": permit_type,
                "villages": villages,
                "ai_category": ai_category,
                "ai_value": ai_value,
            },
        )

    def weekly_area(
        self,
        *,
        nw_lon_lat: str,
        se_lon_lat: str,
        year: int | None = None,
        permit_type: str | None = None,
        ai_category: str | None = None,
        ai_value: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/api/stats/weekly/area",
            {
                "nw_lon_lat": nw_lon_lat,
                "se_lon_lat": se_lon_lat,
                "year": year,
                "permit_type": permit_type,
                "ai_category": ai_category,
                "ai_value": ai_value,
            },
        )

    def ai_filters(self) -> list[dict[str, Any]]:
        return self._get("/api/ai/filters")

    def geocode(self, query: str) -> Any:
        """POST /api/geocode — best-effort place lookup."""
        url = f"{self.base_url}/api/geocode"
        body = json.dumps({"query": query}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read()[:400].decode("utf-8", errors="replace")
            raise PermessError(f"HTTP {e.code} for geocode: {detail}") from e
        except urllib.error.URLError as e:
            raise PermessError(f"Geocode failed: {e.reason}") from e
