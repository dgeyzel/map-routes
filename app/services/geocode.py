"""Geocode waypoint strings to coordinates (Nominatim or optional Google)."""

import asyncio
# from typing import Any

import httpx

from app.config import (
    GOOGLE_MAPS_API_KEY,
    NOMINATIM_BASE_URL,
    NOMINATIM_DELAY_SECONDS,
    NOMINATIM_USER_AGENT,
)


async def _geocode_nominatim(
    client: httpx.AsyncClient,
    query: str
) -> tuple[float, float]:
    """Geocode a single query using Nominatim. Returns (lat, lng)."""
    url = f"{NOMINATIM_BASE_URL.rstrip('/')}/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": NOMINATIM_USER_AGENT}
    resp = await client.get(url, params=params, headers=headers, timeout=15.0)
    resp.raise_for_status()
    data = resp.json()
    if not data or not isinstance(data, list):
        raise ValueError(f"No result from Nominatim for: {query!r}")
    first = data[0]
    lat = float(first.get("lat"))
    lon = float(first.get("lon"))
    return (lat, lon)


# Bounds for Bay Area / Peninsula / Santa Cruz (viewport bias so intersection
# queries like "Skyline Blvd and CA-17" resolve to the correct junction).
_GOOGLE_GEOCODE_BOUNDS = "36.85,-122.55|37.65,-121.75"  # SW|NE


async def _geocode_google(
    client: httpx.AsyncClient,
    query: str
) -> tuple[float, float]:
    """Geocode a single query using Google Geocoding API.
    Returns (lat, lng)."""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": query,
        "key": GOOGLE_MAPS_API_KEY,
        "bounds": _GOOGLE_GEOCODE_BOUNDS,
    }
    resp = await client.get(url, params=params, timeout=15.0)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError(f"No result from Google Geocoding for: {query!r}")
    loc = data["results"][0]["geometry"]["location"]
    return (loc["lat"], loc["lng"])


async def geocode_waypoints(
    waypoint_strings: list[str]
) -> list[tuple[str, float, float]]:
    """
    Geocode an ordered list of waypoint strings to (name, lat, lng).

    Uses Google Geocoding if GOOGLE_MAPS_API_KEY is set, otherwise Nominatim.
    For Nominatim, respects rate limit with a delay between requests.

    Args:
        waypoint_strings: Ordered list of place/address strings.

    Returns:
        List of (name, lat, lng) in the same order.

    Raises:
        ValueError: If any waypoint cannot be geocoded.
        httpx.HTTPStatusError: On HTTP errors from the geocoding service.
    """
    if not waypoint_strings:
        return []

    use_google = bool(GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY.strip())
    geocode_one = _geocode_google if use_google else _geocode_nominatim

    result: list[tuple[str, float, float]] = []
    async with httpx.AsyncClient() as client:
        for i, q in enumerate(waypoint_strings):
            if not use_google and i > 0:
                await asyncio.sleep(NOMINATIM_DELAY_SECONDS)
            lat, lng = await geocode_one(client, q)
            result.append((q, lat, lng))
    return result
