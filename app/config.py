"""Application configuration loaded from environment."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (parent of app/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def _get(key: str, default: str | None = None) -> str | None:
    """Get env var; never log or expose the value."""
    return os.environ.get(key, default)


# Required
GEMINI_API_KEY: str | None = _get("GEMINI_API_KEY")

# Optional: when set, use Google Geocoding + Directions
# instead of Nominatim + OSRM
GOOGLE_MAPS_API_KEY: str | None = _get("GOOGLE_MAPS_API_KEY")

# Public API base URLs (no secrets)
OSRM_BASE_URL: str = _get("OSRM_BASE_URL") or "https://router.project-osrm.org"
NOMINATIM_BASE_URL: str = _get("NOMINATIM_BASE_URL") or \
    "https://nominatim.openstreetmap.org"

# Nominatim rate limit: 1 request per second (policy)
NOMINATIM_DELAY_SECONDS: float = 1.0

# User-Agent for Nominatim (required by usage policy)
NOMINATIM_USER_AGENT: str = _get("NOMINATIM_USER_AGENT") or \
    "RouteMapWebApp/1.0"
