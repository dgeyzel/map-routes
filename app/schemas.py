"""Pydantic request/response models for the route API."""

from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    """Request body for POST /api/route."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language route description",
    )


class Waypoint(BaseModel):
    """A single waypoint with name and coordinates."""

    name: str = Field(
        ...,
        description="Display name or address of the waypoint",
    )
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")


class RouteSummary(BaseModel):
    """Total distance and duration for the route."""

    distance_miles: float = Field(..., description="Total distance in miles")
    duration_minutes: float = Field(
        ...,
        description="Total drive time in minutes",
    )


class RouteResponse(BaseModel):
    """Response for a successfully resolved route."""

    waypoints: list[Waypoint] = Field(
        ...,
        description="Ordered list of waypoints"
    )
    summary: RouteSummary = Field(
        ...,
        description="Total distance and duration"
    )
    polyline: list[list[float]] = Field(
        ...,
        description="Route geometry as list of \
            [lng, lat] pairs (GeoJSON-style)",
    )
    via_road: str | None = Field(
        default=None,
        description="Primary road name if available (e.g. 'via CA-35')",
    )
