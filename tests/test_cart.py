"""Unit tests for cart aggregation."""

from src.core.cart import build_cart
from src.core.types import Product, ProductVariant


def test_build_cart_totals_and_variant_selection():
    products = [
        Product(
            id="p1",
            name="Jacket",
            category="jacket",
            price=200.0,
            delivery_days=3,
            retailer="AlpineCo",
            variants=[ProductVariant(size="M", color="black")],
            tags=["waterproof"],
        ),
        Product(
            id="p2",
            name="Pants",
            category="pants",
            price=120.0,
            delivery_days=4,
            retailer="SnowMart",
            variants=[ProductVariant(size="L", color="blue")],
            tags=[],
        ),
    ]

    cart = build_cart(products, size="M")

    assert cart.total_cost == 320.0
    assert cart.items[0].missing_variant is False
    assert cart.items[1].missing_variant is True
