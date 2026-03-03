"""Get route geometry and summary (OSRM or optional Google Directions)."""

# from typing import Any

import httpx

from app.config import GOOGLE_MAPS_API_KEY, OSRM_BASE_URL


def _decode_google_polyline(encoded: str) -> list[list[float]]:
    """Decode Google's encoded polyline to list of [lat, lng] \
        (we'll use [lng, lat] for GeoJSON)."""
    # Standard polyline decoding
    points = []
    index = 0
    lat = 0.0
    lng = 0.0
    while index < len(encoded):
        b = 0
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat / 1e5
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else result >> 1
        lng += dlng / 1e5
        points.append([lng, lat])  # GeoJSON order: [lng, lat]
    return points


async def _route_osrm(
    client: httpx.AsyncClient,
    coords: list[tuple[float, float]],
) -> tuple[list[list[float]], float, float]:
    """Get route from OSRM. \
        Returns (polyline as [lng,lat] list, distance_m, duration_s)."""
    if len(coords) < 2:
        raise ValueError("At least two points required for routing")
    # OSRM: lon,lat;lon,lat;...
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in coords)
    url = f"{OSRM_BASE_URL.rstrip('/')}/route/v1/driving/{coord_str}"
    params = {"overview": "full", "geometries": "geojson"}
    resp = await client.get(url, params=params, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("OSRM could not find a route")
    route = data["routes"][0]
    geometry = route["geometry"]
    if geometry.get("type") == "LineString":
        coords_geojson = geometry["coordinates"]  # already [lng, lat]
    else:
        coords_geojson = []
    distance_m = float(route.get("distance", 0))
    duration_s = float(route.get("duration", 0))
    return (coords_geojson, distance_m, duration_s)


async def _route_google(
    client: httpx.AsyncClient,
    coords: list[tuple[float, float]],
) -> tuple[list[list[float]], float, float]:
    """Get route from Google Directions. \
        Returns (polyline as [lng,lat] list, distance_m, duration_s)."""
    if len(coords) < 2:
        raise ValueError("At least two points required for routing")
    origin = f"{coords[0][0]},{coords[0][1]}"
    destination = f"{coords[-1][0]},{coords[-1][1]}"
    waypoints = ""
    if len(coords) > 2:
        waypoints = "|".join(f"{lat},{lng}" for lat, lng in coords[1:-1])
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": GOOGLE_MAPS_API_KEY,
        "mode": "driving",
    }
    if waypoints:
        params["waypoints"] = waypoints
    resp = await client.get(url, params=params, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK" or not data.get("routes"):
        raise ValueError("Google Directions could not find a route")
    route = data["routes"][0]
    # leg = route.get("legs", [{}])[0]
    distance_m = sum(
        leg.get("distance", {}).get("value", 0)
        for leg in route.get("legs", [])
    )
    duration_s = sum(
        leg.get("duration", {}).get("value", 0)
        for leg in route.get("legs", [])
    )
    enc = route.get("overview_polyline", {}).get("points", "")
    if not enc:
        raise ValueError("Google Directions returned no polyline")
    polyline = _decode_google_polyline(enc)
    return (polyline, float(distance_m), float(duration_s))


async def get_route(
    coords: list[tuple[float, float]],
) -> tuple[list[list[float]], float, float, str | None]:
    """
    Get driving route geometry and summary.

    Uses Google Directions if GOOGLE_MAPS_API_KEY is set, otherwise OSRM.

    Args:
        coords: Ordered list of (lat, lng) for each waypoint.

    Returns:
        (polyline as list of \
            [lng, lat], distance_meters, duration_seconds, via_road or None).
    """
    use_google = bool(GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY.strip())
    async with httpx.AsyncClient() as client:
        if use_google:
            polyline, distance_m, duration_s = await _route_google(client, coords)  # noqa: E501
            via = None  # Could parse from route["legs"] if needed
        else:
            polyline, distance_m, duration_s = await _route_osrm(client, coords)  # noqa: E501
            via = None  # OSRM can provide road names; optional enhancement
    return (polyline, distance_m, duration_s, via)
