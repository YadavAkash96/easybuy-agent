"""Unit tests for mocked retailer discovery."""

from src.core.retailers import discover_products
from src.core.types import ShoppingSpec


def test_discover_products_from_three_retailers():
    spec = ShoppingSpec(
        intent="Downhill skiing outfit",
        budget=400,
        deadline_days=5,
        size="M",
        must_haves=["waterproof"],
        nice_to_haves=[],
    )

    products = discover_products(spec)
    retailers = {product.retailer for product in products}

    assert len(retailers) >= 3
    assert all(product.price > 0 for product in products)
    assert all(product.delivery_days > 0 for product in products)
