"""Route API: POST /route for natural-language route resolution."""

import asyncio

from fastapi import APIRouter, HTTPException

from app.schemas import RouteRequest, RouteResponse, RouteSummary, Waypoint
from app.services.geocode import geocode_waypoints
from app.services.llm import parse_route_query
from app.services.routing import get_route

router = APIRouter()


@router.post("/route", response_model=RouteResponse)
async def post_route(request: RouteRequest) -> RouteResponse:
    """
    Parse a natural-language route query, geocode waypoints, compute the route,
    and return geometry plus summary (distance and duration).
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Run sync Gemini call in thread pool to avoid blocking
    try:
        waypoint_strings = await asyncio.to_thread(parse_route_query, query)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Route parsing failed: {e!s}"
        ) from e

    if not waypoint_strings:
        raise HTTPException(
            status_code=422,
            detail="No waypoints could be parsed from the query"
        )

    try:
        geocoded = await geocode_waypoints(waypoint_strings)
    except (ValueError, Exception) as e:
        raise HTTPException(
            status_code=503,
            detail=f"Geocoding failed: {e!s}"
        ) from e

    if not geocoded:
        raise HTTPException(
            status_code=422,
            detail="No coordinates found for waypoints"
        )

    coords = [(lat, lng) for _name, lat, lng in geocoded]

    try:
        polyline, distance_m, duration_s, via_road = await get_route(coords)
    except (ValueError, Exception) as e:
        raise HTTPException(
            status_code=503,
            detail=f"Routing failed: {e!s}"
        ) from e

    if not polyline:
        raise HTTPException(
            status_code=422,
            detail="No route geometry returned"
        )

    waypoints = [
        Waypoint(name=name, lat=lat, lng=lng)
        for (name, lat, lng) in geocoded
    ]
    distance_miles = distance_m / 1609.344
    duration_minutes = duration_s / 60.0
    summary = RouteSummary(
        distance_miles=round(distance_miles, 1),
        duration_minutes=round(duration_minutes, 1)
    )

    return RouteResponse(
        waypoints=waypoints,
        summary=summary,
        polyline=polyline,
        via_road=via_road,
    )
