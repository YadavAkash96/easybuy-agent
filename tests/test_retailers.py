"""Unit tests for SerpAPI Google Shopping discovery."""

from unittest.mock import MagicMock, patch

from src.core.retailers import (
    _parse_delivery_days,
    _parse_price,
    _parse_rating,
    _parse_rating_count,
    discover_products,
)
from src.core.types import ShoppingSpec


def test_discover_products_from_three_retailers():
    spec = ShoppingSpec(
        intent="Ski Jacket",
        budget=400,
        deadline_days=5,
        size="M",
        must_haves=["waterproof"],
        nice_to_haves=[],
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "shopping_results": [
            {
                "product_id": "p1",
                "title": "Waterproof Ski Jacket",
                "extracted_price": 199.0,
                "price": "$199",
                "rating": 4.6,
                "reviews": 120,
                "source": "StoreA",
                "product_link": "https://storea.example/jacket",
                "thumbnail": "https://storea.example/jacket.jpg",
                "delivery": "Free delivery by Tue",
            },
            {
                "product_id": "p2",
                "title": "Insulated Ski Pants",
                "extracted_price": 120.0,
                "price": "$120",
                "rating": 4.2,
                "reviews": 32,
                "source": "StoreB",
                "product_link": "https://storeb.example/pants",
                "thumbnail": "https://storeb.example/pants.jpg",
                "delivery": "2-day delivery",
            },
            {
                "product_id": "p3",
                "title": "Thermal Ski Gloves",
                "extracted_price": 35.0,
                "price": "$35",
                "rating": 4.8,
                "reviews": 88,
                "source": "StoreC",
                "product_link": "https://storec.example/gloves",
                "thumbnail": "https://storec.example/gloves.jpg",
                "delivery": None,
            },
        ]
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_response

    with patch("src.core.retailers.httpx.Client", return_value=mock_client):
        products = discover_products(spec, api_key="fake-key")

    retailers = {product.retailer for product in products}

    assert len(retailers) >= 3
    assert all(product.price > 0 for product in products)
    assert all(product.delivery_days > 0 for product in products)

    # Verify delivery parsing
    by_name = {p.name: p for p in products}
    assert by_name["Waterproof Ski Jacket"].delivery_days == 3  # "by Tue"
    assert by_name["Insulated Ski Pants"].delivery_days == 2  # "2-day"
    assert by_name["Thermal Ski Gloves"].delivery_days == 5  # None -> default

    # Verify image_url and url parsed
    assert by_name["Waterproof Ski Jacket"].image_url == "https://storea.example/jacket.jpg"
    assert by_name["Waterproof Ski Jacket"].url == "https://storea.example/jacket"


def test_parse_delivery_days_variants():
    assert _parse_delivery_days(None) == 5
    assert _parse_delivery_days("") == 5
    assert _parse_delivery_days("Free delivery by Tue") == 3
    assert _parse_delivery_days("Free delivery by Mon") == 3
    assert _parse_delivery_days("2-day delivery") == 2
    assert _parse_delivery_days("3 day shipping") == 3
    assert _parse_delivery_days("next day delivery") == 1
    assert _parse_delivery_days("overnight shipping") == 1
    assert _parse_delivery_days("Free delivery") == 4
    assert _parse_delivery_days("Free delivery on $75+") == 4


def test_parse_price_formats():
    assert _parse_price(59.99) == 59.99
    assert _parse_price("$199") == 199.0
    assert _parse_price("$1,299.99") == 1299.99


def test_parse_rating_formats():
    assert _parse_rating(None) == 0.0
    assert _parse_rating(4.5) == 4.5
    assert _parse_rating("4.7 out of 5") == 4.7


def test_parse_rating_count_formats():
    assert _parse_rating_count(None) == 0
    assert _parse_rating_count(120) == 120
    assert _parse_rating_count("1,234") == 1234


def test_discover_query_includes_size_and_preferences():
    """Verify the SerpAPI query is clean: article + prefs + size, no budget."""
    spec = ShoppingSpec(
        intent="Ski Jacket",
        budget=400,
        deadline_days=5,
        size="M",
        must_haves=["waterproof", "insulated"],
        nice_to_haves=[],
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"shopping_results": []}

    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_response

    with patch("src.core.retailers.httpx.Client", return_value=mock_client):
        discover_products(spec, api_key="fake-key")

    call_args = mock_client.__enter__.return_value.get.call_args
    query = call_args.kwargs.get("params", call_args[1].get("params", {}))["q"]
    assert "Ski Jacket" in query
    assert "waterproof" in query
    assert "insulated" in query
    assert "size M" in query
    assert "400" not in query
    assert "budget" not in query
