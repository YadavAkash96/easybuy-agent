"""Unit tests for Gemini breakdown parser."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.ai.breakdown import parse_breakdown
from src.core.types import BreakdownResponse

VALID_AI_RESPONSE = json.dumps(
    {
        "articles": [
            {"name": "Down Jacket", "category": "jacket"},
            {"name": "Ski Pants", "category": "pants"},
            {"name": "Ski Goggles", "category": "goggles"},
            {"name": "Ski Gloves", "category": "gloves"},
            {"name": "Ski Helmet", "category": "helmet"},
        ],
        "constraints": {
            "budget": 400,
            "deadline_days": 5,
            "size": "M",
            "preferences": ["waterproof", "warm"],
        },
    }
)


# --- parse_breakdown unit tests ---


def test_parse_breakdown_returns_articles_and_constraints():
    mock_response = MagicMock()
    mock_response.text = VALID_AI_RESPONSE

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.breakdown.genai.Client", return_value=mock_client):
        result = parse_breakdown("Skiing outfit, $400, size M, 5 days", api_key="fake-key")

    assert len(result.articles) == 5
    assert result.articles[0].name == "Down Jacket"
    assert result.articles[0].category == "jacket"
    assert result.articles[0].selected is True
    assert result.constraints.budget == 400
    assert result.constraints.deadline_days == 5
    assert result.constraints.size == "M"
    assert "waterproof" in result.constraints.preferences


def test_parse_breakdown_handles_markdown_wrapped_json():
    wrapped = f"```json\n{VALID_AI_RESPONSE}\n```"
    mock_response = MagicMock()
    mock_response.text = wrapped

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.breakdown.genai.Client", return_value=mock_client):
        result = parse_breakdown("Skiing outfit", api_key="fake-key")

    assert len(result.articles) == 5
    assert result.constraints.budget == 400


def test_parse_breakdown_raises_on_empty_response():
    mock_response = MagicMock()
    mock_response.text = ""

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.breakdown.genai.Client", return_value=mock_client):
        with pytest.raises(ValueError, match="empty response"):
            parse_breakdown("Skiing outfit", api_key="fake-key")


def test_parse_breakdown_raises_on_invalid_json():
    mock_response = MagicMock()
    mock_response.text = "not json at all"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.breakdown.genai.Client", return_value=mock_client):
        with pytest.raises(ValueError, match="valid JSON"):
            parse_breakdown("Skiing outfit", api_key="fake-key")


def test_parse_breakdown_defaults_missing_constraints():
    partial = json.dumps(
        {
            "articles": [{"name": "Jacket", "category": "jacket"}],
            "constraints": {},
        }
    )
    mock_response = MagicMock()
    mock_response.text = partial

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.breakdown.genai.Client", return_value=mock_client):
        result = parse_breakdown("Skiing outfit", api_key="fake-key")

    assert len(result.articles) == 1
    assert result.constraints.budget is None
    assert result.constraints.size is None
    assert result.constraints.preferences == []


# --- /api/breakdown endpoint tests ---


@pytest.fixture()
def client():
    from src.main import app

    return TestClient(app)


def test_breakdown_endpoint_returns_correct_shape(client):
    mock_response = MagicMock()
    mock_response.text = VALID_AI_RESPONSE

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with (
        patch("src.ai.breakdown.genai.Client", return_value=mock_client),
        patch("src.main.GEMINI_API_KEY", "fake-key"),
    ):
        resp = client.post("/api/breakdown", json={"intent": "Skiing outfit"})

    assert resp.status_code == 200
    body = resp.json()
    parsed = BreakdownResponse(**body)
    assert len(parsed.articles) == 5
    assert parsed.constraints.budget == 400


def test_breakdown_endpoint_returns_503_without_api_key(client):
    with patch("src.main.GEMINI_API_KEY", ""):
        resp = client.post("/api/breakdown", json={"intent": "Skiing outfit"})

    assert resp.status_code == 503


def test_breakdown_endpoint_returns_502_on_ai_error(client):
    mock_response = MagicMock()
    mock_response.text = "not json"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with (
        patch("src.ai.breakdown.genai.Client", return_value=mock_client),
        patch("src.main.GEMINI_API_KEY", "fake-key"),
    ):
        resp = client.post("/api/breakdown", json={"intent": "Skiing outfit"})

    assert resp.status_code == 502
