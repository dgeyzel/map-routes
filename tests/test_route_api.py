"""Integration tests for POST /api/route with mocked services."""

import pytest
from unittest.mock import AsyncMock, patch


def test_post_route_success(
    client,
    mock_llm_waypoints,
    mock_geocoded,
    mock_route_result
):
    """POST /api/route returns 200 and route data \
        when services return valid data."""
    with (
        patch(
            "app.routes.route_api.parse_route_query",
            return_value=mock_llm_waypoints
        ),
        patch(
            "app.routes.route_api.geocode_waypoints",
            new_callable=AsyncMock,
            return_value=mock_geocoded
        ),
        patch(
            "app.routes.route_api.get_route",
            new_callable=AsyncMock,
            return_value=mock_route_result
        ),
    ):
        response = client.post(
            "/api/route",
            json={"query": "Skyline Blvd from 92 to 17"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "waypoints" in data
    assert len(data["waypoints"]) == 2
    assert data["waypoints"][0]["name"] == "Skyline Blvd at CA-92"
    assert data["waypoints"][0]["lat"] == 37.45
    assert data["waypoints"][0]["lng"] == -122.35
    assert "summary" in data
    assert data["summary"]["distance_miles"] == pytest.approx(37.3, rel=0.1)
    assert data["summary"]["duration_minutes"] == pytest.approx(70.0, rel=0.1)
    assert "polyline" in data
    assert len(data["polyline"]) >= 2


def test_post_route_empty_query(client):
    """POST /api/route with empty query returns 422."""
    response = client.post("/api/route", json={"query": ""})
    assert response.status_code == 422


def test_post_route_missing_query(client):
    """POST /api/route without query key returns 422."""
    response = client.post("/api/route", json={})
    assert response.status_code == 422


def test_post_route_llm_returns_empty(
    client,
    mock_geocoded,
    mock_route_result
):
    """POST /api/route returns 422 when LLM returns no waypoints."""
    with (
        patch("app.routes.route_api.parse_route_query", return_value=[]),
        patch(
            "app.routes.route_api.geocode_waypoints",
            new_callable=AsyncMock
        ),
        patch("app.routes.route_api.get_route", new_callable=AsyncMock),
    ):
        response = client.post("/api/route", json={"query": "gibberish xyz"})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_route_llm_raises(client):
    """POST /api/route returns 503 when \
        LLM raises a non-ValueError (e.g. service failure)."""
    with patch(
        "app.routes.route_api.parse_route_query",
        side_effect=RuntimeError("API unavailable")
    ):
        response = client.post(
            "/api/route",
            json={"query": "Skyline from 92 to 17"}
        )
    assert response.status_code == 503
    assert "detail" in response.json()
