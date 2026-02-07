"""Deterministic ranking logic for products."""

from src.core.types import Product, RankedProduct, ShoppingSpec


def _has_size(product: Product, size: str) -> bool:
    return any(variant.size == size for variant in product.variants)


def score_product(spec: ShoppingSpec, product: Product) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if product.price <= spec.budget:
        score += 50
        reasons.append("Price within budget")
    else:
        score -= 50
        reasons.append("Price over budget")

    if product.delivery_days <= spec.deadline_days:
        score += 40
        reasons.append("Delivery meets deadline")
    else:
        score -= 40
        reasons.append("Delivery misses deadline")

    must_have_hits = [tag for tag in spec.must_haves if tag in product.tags]
    if must_have_hits:
        score += 10 * len(must_have_hits)
        reasons.append("Matches must-have preferences")
    else:
        reasons.append("Missing must-have preferences")

    if _has_size(product, spec.size):
        score += 5
        reasons.append("Size available")
    else:
        score -= 20
        reasons.append("Size unavailable")

    return score, reasons


def rank_products(spec: ShoppingSpec, products: list[Product]) -> list[RankedProduct]:
    ranked: list[RankedProduct] = []
    for product in products:
        score, reasons = score_product(spec, product)
        ranked.append(RankedProduct(product=product, score=score, reasons=reasons))

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked
