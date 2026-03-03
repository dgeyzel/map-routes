"""Parse natural-language routes into ordered waypoint strings using Gemini."""

import json
import re
from typing import Any

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY

ROUTE_PARSE_PROMPT = """You are a route parser for a driving directions app in the United States (especially California).
Given a user's natural-language description of a driving route, output an ordered list of waypoints (places, road names, or intersections) that a geocoder can resolve.

Rules:
- Start waypoint = where the route begins; end waypoint = where the route ends. The END must be the full destination (e.g. where a road meets a highway), not a point halfway along.
- For "from A to B" or "between A and B" along one road, use exactly two waypoints: the start intersection and the end intersection (e.g. "Skyline Blvd from 92 to 17" -> start at Skyline at CA-92, end at Skyline at CA-17).
- Prefer intersection-style strings so geocoders return the actual junction: e.g. "Skyline Blvd and CA-17, California" or "CA-35 at CA-17, San Mateo County, CA" rather than a generic road name that might resolve to a midpoint.
- If the user is asking for a route between two points on the same road, use the start and end intersections.
- Do not include any waypoints that are not on the route.
- Make sure to include the roads specified by the user.  Do not include any roads that are not specified by the user.
- If the user specifies a road to exclude, do not include any waypoints on that road.

Examples:
- "Skyline Blvd from 92 to 17" -> ["Skyline Blvd at CA-92, California", "Skyline Blvd and CA-17, California"] (start at CA-92, end at the intersection with CA-17).
- "Calaveras to Felter to Sierra" -> three waypoints: Calaveras Rd, Felter Rd, Sierra Rd (or similar road names in California).

Output ONLY a single JSON array of strings, one string per waypoint in order. No other text.
User input: """  # noqa: E501


def parse_route_query(query: str) -> list[str]:
    """
    Use Gemini to parse a natural-language route \
        into an ordered list of waypoint strings.

    Args:
        query: Raw user input, e.g. "Skyline Blvd from 92 to 17".

    Returns:
        Ordered list of waypoint strings suitable for geocoding.

    Raises:
        ValueError: If GEMINI_API_KEY is missing or response is invalid.
    """
    if not GEMINI_API_KEY or not GEMINI_API_KEY.strip():
        raise ValueError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = ROUTE_PARSE_PROMPT + query.strip()
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=full_prompt,
        config=types.GenerateContentConfig(temperature=0.1),
    )

    if not response.text:
        raise ValueError("Gemini returned empty response")

    text = response.text.strip()
    # Handle markdown code block if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    data: Any = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("Gemini response is not a JSON array")
    waypoints = [str(w).strip() for w in data if w]
    if not waypoints:
        raise ValueError("Gemini returned no waypoints")
    return waypoints
