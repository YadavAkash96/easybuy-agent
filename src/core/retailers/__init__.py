"""Mocked retailer discovery for agentic commerce."""

from src.core.types import Product, ProductVariant, ShoppingSpec


def _catalog() -> list[Product]:
    return [
        Product(
            id="alpine-jacket-1",
            name="Alpine Waterproof Jacket",
            category="jacket",
            price=210.0,
            delivery_days=3,
            retailer="AlpineCo",
            variants=[
                ProductVariant(size="M", color="black"),
                ProductVariant(size="L", color="black"),
            ],
            tags=["waterproof", "insulated"],
        ),
        Product(
            id="snow-pants-1",
            name="SnowPro Pants",
            category="pants",
            price=130.0,
            delivery_days=4,
            retailer="SnowMart",
            variants=[
                ProductVariant(size="M", color="blue"),
                ProductVariant(size="S", color="blue"),
            ],
            tags=["waterproof"],
        ),
        Product(
            id="peak-gloves-1",
            name="Peak Thermal Gloves",
            category="gloves",
            price=35.0,
            delivery_days=2,
            retailer="PeakGear",
            variants=[
                ProductVariant(size="M", color="gray"),
                ProductVariant(size="L", color="gray"),
            ],
            tags=["insulated"],
        ),
        Product(
            id="alpine-goggles-1",
            name="Alpine Goggles",
            category="goggles",
            price=65.0,
            delivery_days=5,
            retailer="AlpineCo",
            variants=[ProductVariant(size="M", color="black")],
            tags=[],
        ),
    ]


def discover_products(spec: ShoppingSpec) -> list[Product]:
    products = _catalog()
    filtered: list[Product] = []

    for product in products:
        if product.price <= 0 or product.delivery_days <= 0:
            continue
        filtered.append(product)

    return filtered
