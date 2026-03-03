"""Unit tests for routing service (mocked HTTP)."""

import re

import pytest
import respx
from httpx import Response

from app.services.routing import get_route

# OSRM URL includes coords in path: /route/v1/driving/{lng,lat;lng,lat;...}
OSRM_ROUTE_PATTERN = re.compile(
    r"^https://router\.project-osrm\.org/route/v1/driving/"
)


@respx.mock
@pytest.mark.asyncio
async def test_get_route_osrm():
    """get_route uses OSRM and \
        returns polyline, distance_m, duration_s when Google key not set."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr("app.services.routing.GOOGLE_MAPS_API_KEY", None)
        respx.get(OSRM_ROUTE_PATTERN).mock(
            return_value=Response(
                200,
                json={
                    "code": "Ok",
                    "routes": [
                        {
                            "distance": 50000.0,
                            "duration": 3600.0,
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [[-122.35, 37.45], [-122.02, 37.22]],  # noqa: E501
                            },
                        }
                    ],
                },
            )
        )
        coords = [(37.45, -122.35), (37.22, -122.02)]
        polyline, distance_m, duration_s, via = await get_route(coords)
    assert polyline == [[-122.35, 37.45], [-122.02, 37.22]]
    assert distance_m == 50000.0
    assert duration_s == 3600.0
    assert via is None


@respx.mock
@pytest.mark.asyncio
async def test_get_route_osrm_no_route_raises():
    """get_route raises ValueError when OSRM finds no route."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr("app.services.routing.GOOGLE_MAPS_API_KEY", None)
        respx.get(OSRM_ROUTE_PATTERN).mock(
            return_value=Response(200, json={"code": "NoRoute", "routes": []})
        )
        coords = [(37.45, -122.35), (37.22, -122.02)]
        with pytest.raises(ValueError, match="could not find a route"):
            await get_route(coords)


@pytest.mark.asyncio
async def test_get_route_raises_for_single_point():
    """get_route raises ValueError when given fewer than two points."""
    with pytest.raises(ValueError, match="At least two points"):
        await get_route([(37.45, -122.35)])
