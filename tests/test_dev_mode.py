"""Tests for SerpAPI dev/prod mode with precomputed cache."""

from unittest.mock import MagicMock, patch

import pytest

import src.core.retailers as retailers_mod
from src.core.retailers import (
    _discover_from_cache,
    _normalize_key,
    discover_products,
)
from src.core.types import ShoppingSpec


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset the module-level cache singleton between tests."""
    retailers_mod._cache = None
    yield
    retailers_mod._cache = None


# --- _normalize_key ---


def test_normalize_key_lowercases():
    assert _normalize_key("Ski Jacket waterproof") == "ski jacket waterproof"


def test_normalize_key_collapses_whitespace():
    assert _normalize_key("ski   jacket   waterproof") == "ski jacket waterproof"


def test_normalize_key_strips_and_collapses():
    assert _normalize_key("  Ski   Jacket  ") == "ski jacket"


# --- _discover_from_cache ---


def test_cache_hit_returns_data():
    cache = {
        "ski jacket": {
            "shopping_results": [
                {
                    "product_id": "cached-1",
                    "title": "Cached Ski Jacket",
                    "extracted_price": 150.0,
                    "source": "CacheStore",
                    "delivery": "2-day delivery",
                    "product_link": "https://example.com/jacket",
                }
            ]
        }
    }
    with patch("src.core.retailers._load_cache", return_value=cache):
        result = _discover_from_cache("Ski Jacket")
    assert result["shopping_results"][0]["product_id"] == "cached-1"


def test_cache_miss_returns_empty():
    cache = {"some other query": {"shopping_results": [{"title": "X"}]}}
    with patch("src.core.retailers._load_cache", return_value=cache):
        result = _discover_from_cache("nonexistent query")
    assert result == {"shopping_results": []}


# --- discover_products with mode switching ---


def _make_spec(intent: str = "Ski Jacket") -> ShoppingSpec:
    return ShoppingSpec(
        intent=intent,
        budget=400,
        deadline_days=5,
        size="M",
        must_haves=["waterproof"],
        nice_to_haves=[],
    )


def test_dev_mode_uses_cache():
    """In dev mode, discover_products reads from cache instead of calling API."""
    cache_response = {
        "shopping_results": [
            {
                "product_id": "cached-1",
                "title": "Cached Ski Jacket",
                "extracted_price": 150.0,
                "source": "CacheStore",
                "delivery": "2-day delivery",
                "product_link": "https://example.com/jacket",
            }
        ]
    }

    with (
        patch("src.core.retailers._is_dev_mode", return_value=True),
        patch("src.core.retailers._discover_from_cache", return_value=cache_response),
        patch("src.core.retailers.httpx.Client") as mock_httpx,
    ):
        products = discover_products(_make_spec(), api_key="fake-key")

    # Should not have called httpx at all
    mock_httpx.assert_not_called()
    assert len(products) == 1
    assert products[0].name == "Cached Ski Jacket"


def test_prod_mode_calls_api():
    """In prod mode, discover_products calls the real SerpAPI via httpx."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "shopping_results": [
            {
                "product_id": "live-1",
                "title": "Live Ski Jacket",
                "extracted_price": 200.0,
                "source": "LiveStore",
                "delivery": "3-day delivery",
                "product_link": "https://example.com/live-jacket",
            }
        ]
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_response

    with (
        patch("src.core.retailers._is_dev_mode", return_value=False),
        patch("src.core.retailers.httpx.Client", return_value=mock_client),
    ):
        products = discover_products(_make_spec(), api_key="fake-key")

    mock_client.__enter__.return_value.get.assert_called_once()
    assert len(products) == 1
    assert products[0].name == "Live Ski Jacket"
