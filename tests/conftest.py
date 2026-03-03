"""Pytest fixtures for route map app tests."""

import pytest
# from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_llm_waypoints():
    """Sample waypoint strings returned by LLM."""
    return ["Skyline Blvd at CA-92", "Skyline Blvd at CA-17"]


@pytest.fixture
def mock_geocoded():
    """Sample geocoded (name, lat, lng) list."""
    return [
        ("Skyline Blvd at CA-92", 37.45, -122.35),
        ("Skyline Blvd at CA-17", 37.22, -122.02),
    ]


@pytest.fixture
def mock_route_result():
    """Sample routing result: (polyline, distance_m, duration_s, via)."""
    polyline = [[-122.35, 37.45], [-122.3, 37.4], [-122.02, 37.22]]
    return (polyline, 60_000.0, 4200.0, "via CA-35")
