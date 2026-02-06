"""Integration tests for the /api/chat endpoint (mocked Gemini)."""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.anyio
@patch("src.main.stream_chat")
@patch("src.main.GEMINI_API_KEY", "fake-key")
async def test_chat_returns_sse_stream(mock_stream):
    mock_stream.return_value = iter(
        ['data: {"token": "Hi"}\n\n', "data: [DONE]\n\n"]
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert 'data: {"token": "Hi"}' in resp.text
    assert "data: [DONE]" in resp.text


@pytest.mark.anyio
async def test_chat_rejects_empty_messages():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/chat", json={"messages": []})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_chat_rejects_invalid_role():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/chat",
            json={"messages": [{"role": "system", "content": "bad"}]},
        )
    assert resp.status_code == 422


@pytest.mark.anyio
@patch("src.main.GEMINI_API_KEY", "")
async def test_chat_returns_503_when_no_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
    assert resp.status_code == 503
    assert "API key" in resp.json()["detail"]


@pytest.mark.anyio
@patch("src.main.stream_chat")
@patch("src.main.GEMINI_API_KEY", "fake-key")
async def test_chat_returns_500_on_gemini_error(mock_stream):
    mock_stream.side_effect = Exception("Gemini exploded")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
    assert resp.status_code == 500
    assert "Gemini" in resp.json()["detail"]


@pytest.mark.anyio
@patch("src.main.stream_chat")
@patch("src.main.LLM_MODEL", "gemini-3-pro-preview")
@patch("src.main.GEMINI_API_KEY", "fake-key")
async def test_chat_passes_model_from_env(mock_stream):
    mock_stream.return_value = iter(["data: [DONE]\n\n"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
    _, kwargs = mock_stream.call_args
    assert kwargs["model"] == "gemini-3-pro-preview"


@pytest.mark.anyio
@patch("src.main.stream_chat")
@patch("src.main.LLM_MODEL", "")
@patch("src.main.GEMINI_API_KEY", "fake-key")
async def test_chat_uses_default_model_when_env_empty(mock_stream):
    mock_stream.return_value = iter(["data: [DONE]\n\n"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
    _, kwargs = mock_stream.call_args
    assert "model" not in kwargs
