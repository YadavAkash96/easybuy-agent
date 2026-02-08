"""Unit tests for intent chat — conversational intent gathering."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.ai.intent_chat import chat_intent
from src.core.types import IntentChatResponse

GREETING_RESPONSE = json.dumps(
    {
        "reply": "Great! What's your budget for this skiing outfit?",
        "ready": False,
        "intent_summary": None,
    }
)

READY_RESPONSE = json.dumps(
    {
        "reply": "Perfect, I have everything I need! Let me summarize your request.",
        "ready": True,
        "intent_summary": "Skiing outfit, budget $400, size M, delivery within 5 days",
    }
)

NOT_READY_RESPONSE = json.dumps(
    {
        "reply": "What size do you need?",
        "ready": False,
        "intent_summary": None,
    }
)


# --- chat_intent unit tests ---


def test_chat_intent_returns_reply():
    mock_response = MagicMock()
    mock_response.text = GREETING_RESPONSE

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.intent_chat.genai.Client", return_value=mock_client):
        result = chat_intent(
            [{"role": "user", "content": "I want a skiing outfit"}],
            api_key="fake-key",
        )

    assert result.reply == "Great! What's your budget for this skiing outfit?"
    assert result.ready is False
    assert result.intent_summary is None


def test_chat_intent_returns_ready_with_summary():
    mock_response = MagicMock()
    mock_response.text = READY_RESPONSE

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.intent_chat.genai.Client", return_value=mock_client):
        result = chat_intent(
            [
                {"role": "user", "content": "I want a skiing outfit"},
                {"role": "assistant", "content": "What's your budget?"},
                {"role": "user", "content": "$400, size M, 5 days"},
            ],
            api_key="fake-key",
        )

    assert result.ready is True
    assert result.intent_summary is not None
    assert "400" in result.intent_summary


def test_chat_intent_handles_markdown_wrapped_json():
    wrapped = f"```json\n{NOT_READY_RESPONSE}\n```"
    mock_response = MagicMock()
    mock_response.text = wrapped

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.intent_chat.genai.Client", return_value=mock_client):
        result = chat_intent(
            [{"role": "user", "content": "I need ski gear"}],
            api_key="fake-key",
        )

    assert result.reply == "What size do you need?"
    assert result.ready is False


def test_chat_intent_raises_on_empty_response():
    mock_response = MagicMock()
    mock_response.text = ""

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.intent_chat.genai.Client", return_value=mock_client):
        with pytest.raises(ValueError, match="empty response"):
            chat_intent(
                [{"role": "user", "content": "hi"}],
                api_key="fake-key",
            )


def test_chat_intent_raises_on_invalid_json():
    mock_response = MagicMock()
    mock_response.text = "not json at all"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.intent_chat.genai.Client", return_value=mock_client):
        with pytest.raises(ValueError, match="valid JSON"):
            chat_intent(
                [{"role": "user", "content": "hi"}],
                api_key="fake-key",
            )


# --- /api/intent-chat endpoint tests ---


@pytest.fixture()
def client():
    from src.main import app

    return TestClient(app)


def test_intent_chat_endpoint_returns_correct_shape(client):
    mock_response = MagicMock()
    mock_response.text = GREETING_RESPONSE

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with (
        patch("src.ai.intent_chat.genai.Client", return_value=mock_client),
        patch("src.main.GEMINI_API_KEY", "fake-key"),
    ):
        resp = client.post(
            "/api/intent-chat",
            json={"messages": [{"role": "user", "content": "I want ski gear"}]},
        )

    assert resp.status_code == 200
    body = resp.json()
    parsed = IntentChatResponse(**body)
    assert parsed.reply
    assert parsed.ready is False


def test_intent_chat_endpoint_returns_503_without_api_key(client):
    with patch("src.main.GEMINI_API_KEY", ""):
        resp = client.post(
            "/api/intent-chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 503


def test_intent_chat_endpoint_returns_502_on_ai_error(client):
    mock_response = MagicMock()
    mock_response.text = "not json"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with (
        patch("src.ai.intent_chat.genai.Client", return_value=mock_client),
        patch("src.main.GEMINI_API_KEY", "fake-key"),
    ):
        resp = client.post(
            "/api/intent-chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 502
