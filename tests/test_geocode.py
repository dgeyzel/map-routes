"""Unit tests for geocoding service (mocked HTTP)."""

import pytest
import respx
from httpx import Response

from app.services.geocode import geocode_waypoints


@respx.mock
@pytest.mark.asyncio
async def test_geocode_waypoints_nominatim():
    """geocode_waypoints uses Nominatim when Google key is not set."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr("app.services.geocode.GOOGLE_MAPS_API_KEY", None)
        respx.get("https://nominatim.openstreetmap.org/search").mock(
            side_effect=[
                Response(
                    200,
                    json=[
                        {"lat": "37.45", "lon": "-122.35", "display_name": "Skyline at 92"},  # noqa: E501
                    ],
                ),
                Response(
                    200,
                    json=[
                        {"lat": "37.22", "lon": "-122.02", "display_name": "Skyline at 17"},  # noqa: E501
                    ],
                ),
            ]
        )
        result = await geocode_waypoints(["Skyline at 92", "Skyline at 17"])
    assert len(result) == 2
    assert result[0] == ("Skyline at 92", 37.45, -122.35)
    assert result[1] == ("Skyline at 17", 37.22, -122.02)


@respx.mock
@pytest.mark.asyncio
async def test_geocode_waypoints_empty_list():
    """geocode_waypoints returns empty list for empty input."""
    result = await geocode_waypoints([])
    assert result == []


@respx.mock
@pytest.mark.asyncio
async def test_geocode_waypoints_nominatim_no_result_raises():
    """geocode_waypoints raises ValueError \
        when Nominatim returns no results."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr("app.services.geocode.GOOGLE_MAPS_API_KEY", None)
        respx.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=Response(200, json=[])
        )
        with pytest.raises(ValueError, match="No result"):
            await geocode_waypoints(["Unknown Place XYZ 999"])
