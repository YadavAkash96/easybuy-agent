"""Unit tests for Gemini brief parser."""

from unittest.mock import MagicMock, patch

from src.ai.brief import parse_brief


def test_parse_brief_returns_spec():
    mock_response = MagicMock()
    mock_response.text = (
        '{"intent":"Ski","budget":400,"deadline_days":5,"size":"M",'
        '"must_haves":["waterproof"],"nice_to_haves":["insulated"]}'
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.brief.genai.Client", return_value=mock_client):
        spec = parse_brief("Need a skiing outfit", api_key="fake-key")

    assert spec.budget == 400
    assert spec.size == "M"


def test_parse_brief_raises_on_invalid_json():
    mock_response = MagicMock()
    mock_response.text = "not json"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.brief.genai.Client", return_value=mock_client):
        import pytest

        with pytest.raises(ValueError, match="valid JSON"):
            parse_brief("Need a skiing outfit", api_key="fake-key")
