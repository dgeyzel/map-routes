"""Unit tests for LLM route parsing (mocked Gemini)."""

import json
import pytest
from unittest.mock import MagicMock, patch

from app.services import llm


def test_parse_route_query_returns_waypoint_list():
    """parse_route_query returns \
        a list of waypoint strings from Gemini response."""
    fake_response = MagicMock()
    fake_response.text = json.dumps(
        ["Skyline Blvd at CA-92", "Skyline Blvd at CA-17"]
    )
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = fake_response
    with (
        patch("app.services.llm.GEMINI_API_KEY", "test-key"),
        patch("app.services.llm.genai.Client", return_value=mock_client),
    ):
        result = llm.parse_route_query("Skyline Blvd from 92 to 17")
    assert result == ["Skyline Blvd at CA-92", "Skyline Blvd at CA-17"]


def test_parse_route_query_handles_markdown_code_block():
    """parse_route_query strips markdown code fence if present."""
    fake_response = MagicMock()
    fake_response.text = '```json\n["Calaveras Rd", "Felter Rd", "Sierra Rd"]\n```'  # noqa: E501
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = fake_response
    with (
        patch("app.services.llm.GEMINI_API_KEY", "test-key"),
        patch("app.services.llm.genai.Client", return_value=mock_client),
    ):
        result = llm.parse_route_query("Calavares to Felter to Sierra")
    assert result == ["Calaveras Rd", "Felter Rd", "Sierra Rd"]


def test_parse_route_query_raises_when_no_api_key():
    """parse_route_query raises ValueError when GEMINI_API_KEY is missing."""
    with patch("app.services.llm.GEMINI_API_KEY", None):
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            llm.parse_route_query("any query")
    with patch("app.services.llm.GEMINI_API_KEY", ""):
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            llm.parse_route_query("any query")


def test_parse_route_query_raises_when_empty_response():
    """parse_route_query raises ValueError when Gemini returns empty text."""
    fake_response = MagicMock()
    fake_response.text = None
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = fake_response
    with (
        patch("app.services.llm.GEMINI_API_KEY", "test-key"),
        patch("app.services.llm.genai.Client", return_value=mock_client),
    ):
        with pytest.raises(ValueError, match="empty response"):
            llm.parse_route_query("query")
    fake_response.text = ""
    with (
        patch("app.services.llm.GEMINI_API_KEY", "test-key"),
        patch("app.services.llm.genai.Client", return_value=mock_client),
    ):
        with pytest.raises(ValueError, match="empty response"):
            llm.parse_route_query("query")


def test_parse_route_query_raises_when_not_array():
    """parse_route_query raises ValueError \
        when response is not a JSON array."""
    fake_response = MagicMock()
    fake_response.text = '{"waypoints": ["A", "B"]}'
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = fake_response
    with (
        patch("app.services.llm.GEMINI_API_KEY", "test-key"),
        patch("app.services.llm.genai.Client", return_value=mock_client),
    ):
        with pytest.raises(ValueError, match="not a JSON array"):
            llm.parse_route_query("query")


def test_parse_route_query_raises_when_empty_array():
    """parse_route_query raises ValueError when response is empty array."""
    fake_response = MagicMock()
    fake_response.text = "[]"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = fake_response
    with (
        patch("app.services.llm.GEMINI_API_KEY", "test-key"),
        patch("app.services.llm.genai.Client", return_value=mock_client),
    ):
        with pytest.raises(ValueError, match="no waypoints"):
            llm.parse_route_query("query")
