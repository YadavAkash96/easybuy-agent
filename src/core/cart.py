"""Cart aggregation logic."""

from src.core.types import Cart, CartItem, Product, ProductVariant


def _select_variant(product: Product, size: str) -> ProductVariant | None:
    for variant in product.variants:
        if variant.size == size:
            return variant
    return None


def build_cart(products: list[Product], size: str) -> Cart:
    items: list[CartItem] = []
    total = 0.0

    for product in products:
        variant = _select_variant(product, size)
        items.append(
            CartItem(
                product=product,
                quantity=1,
                selected_variant=variant,
                missing_variant=variant is None,
            )
        )
        total += product.price

    return Cart(items=items, total_cost=total)
