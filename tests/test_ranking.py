"""Unit tests for ranking logic."""

from src.core.ranking import rank_products
from src.core.types import Product, ProductVariant, ShoppingSpec


def test_rank_prefers_within_budget_and_deadline():
    spec = ShoppingSpec(
        intent="Downhill skiing outfit",
        budget=400,
        deadline_days=5,
        size="M",
        must_haves=["waterproof"],
        nice_to_haves=[],
    )

    products = [
        Product(
            id="fast",
            name="Fast Jacket",
            category="jacket",
            price=180.0,
            delivery_days=3,
            retailer="AlpineCo",
            variants=[ProductVariant(size="M", color="black")],
            tags=["waterproof"],
        ),
        Product(
            id="slow",
            name="Slow Jacket",
            category="jacket",
            price=160.0,
            delivery_days=9,
            retailer="SnowMart",
            variants=[ProductVariant(size="M", color="blue")],
            tags=["waterproof"],
        ),
    ]

    ranked = rank_products(spec, products)

    assert ranked[0].product.id == "fast"
    assert ranked[0].score >= ranked[1].score
    assert "delivery" in " ".join(ranked[0].reasons).lower()
