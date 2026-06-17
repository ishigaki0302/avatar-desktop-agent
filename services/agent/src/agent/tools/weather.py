"""Weather tool via wttr.in (Phase: reliable factual answers).

Generic web search returns only links and page scraping is too noisy/JS-heavy to
read live forecasts. wttr.in returns structured current conditions (and geolocates
by IP when no location is given), so the agent can actually state the weather.
"""

from __future__ import annotations

import ssl

import httpx
import truststore

from agent.tools.base import ToolError

# Verify TLS against the OS trust store (corporate MITM proxies use a self-signed CA).
_VERIFY = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
_TIMEOUT_S = 15.0


def parse_wttr(data: dict[str, object]) -> dict[str, object]:
    """Extract concise current-condition fields from a wttr.in j1 response."""
    conditions = data["current_condition"]
    if not isinstance(conditions, list) or not conditions:
        raise ToolError("unexpected weather response")
    current = conditions[0]
    areas = data.get("nearest_area")
    location = ""
    if isinstance(areas, list) and areas:
        names = areas[0].get("areaName")
        if isinstance(names, list) and names:
            location = names[0].get("value", "")
    return {
        "location": location,
        "temp_c": current.get("temp_C"),
        "feels_like_c": current.get("FeelsLikeC"),
        "humidity": current.get("humidity"),
        "description": current.get("weatherDesc", [{}])[0].get("value", ""),
    }


def get_weather(location: str = "") -> dict[str, object]:
    """Fetch current weather for `location` (empty = IP-based current location)."""
    try:
        res = httpx.get(
            f"https://wttr.in/{location}?format=j1&lang=ja",
            timeout=_TIMEOUT_S,
            verify=_VERIFY,
            headers={"User-Agent": "curl/8"},
        )
        res.raise_for_status()
        return parse_wttr(res.json())
    except (httpx.HTTPError, KeyError, IndexError, OSError) as exc:
        raise ToolError(f"weather lookup failed: {exc}") from exc
