"""Deterministic ranking logic for products.

Normalized scoring (0–1 per dimension) with transparent breakdown.
Formula: (0.35*price + 0.25*delivery + 0.20*rating + 0.20*match) * penalty
"""

from src.core.types import Product, RankedProduct, ScoreBreakdown


def _price_score(price: float, budget: float) -> float:
    """1.0 if price <= budget, linear decay to 0 at 2x budget."""
    if budget <= 0:
        return 0.5
    ratio = price / budget
    if ratio <= 1.0:
        return 1.0
    return max(0.0, 1.0 - (ratio - 1.0))


def _delivery_score(delivery_days: int, deadline: int) -> float:
    """1.0 if on time, linear decay to 0 at 2x deadline."""
    if deadline <= 0:
        return 0.5
    if delivery_days <= deadline:
        return 1.0
    return max(0.0, 1.0 - (delivery_days - deadline) / deadline)


def _rating_score(rating: float) -> float:
    """Normalize 0-5 rating to 0-1."""
    return min(max(rating / 5.0, 0.0), 1.0)


def _match_score(product: Product, preferences: list[str] | None) -> float:
    """Keyword match against product name + description."""
    if not preferences:
        return 0.5
    text = (product.name + " " + product.description).lower()
    hits = sum(1 for kw in preferences if kw.lower() in text)
    return min(hits / len(preferences), 1.0)


def score_product(
    product: Product,
    *,
    budget: float = 0,
    delivery_days: int = 0,
    preferences: list[str] | None = None,
) -> tuple[float, ScoreBreakdown, list[str]]:
    """Score a single product. Returns (score, breakdown, reasons)."""
    ps = _price_score(product.price, budget)
    ds = _delivery_score(product.delivery_days, delivery_days)
    rs = _rating_score(product.rating)
    ms = _match_score(product, preferences)

    penalty = 1.0
    penalty_reason = ""

    # Penalize products way over budget
    if budget > 0 and product.price > budget * 1.5:
        penalty = 0.5
        penalty_reason = "Price >150% of budget"

    raw = 0.35 * ps + 0.25 * ds + 0.20 * rs + 0.20 * ms
    final = raw * penalty

    breakdown = ScoreBreakdown(
        price_score=round(ps, 3),
        delivery_score=round(ds, 3),
        rating_score=round(rs, 3),
        match_score=round(ms, 3),
        penalty=penalty,
        reason=penalty_reason,
    )

    reasons: list[str] = []
    if ps >= 0.8:
        reasons.append("Price within budget")
    elif ps < 0.5:
        reasons.append("Price over budget")
    if ds >= 0.8:
        reasons.append("Delivery meets deadline")
    elif ds < 0.5:
        reasons.append("Delivery misses deadline")
    if rs >= 0.6:
        reasons.append("Well rated")
    if ms >= 0.6:
        reasons.append("Good keyword match")

    return round(final, 4), breakdown, reasons


def rank_products(
    products: list[Product],
    *,
    budget: float = 0,
    delivery_days: int = 0,
    preferences: list[str] | None = None,
) -> list[RankedProduct]:
    """Rank products by normalized scoring. Returns sorted list."""
    ranked: list[RankedProduct] = []
    for product in products:
        score, breakdown, reasons = score_product(
            product,
            budget=budget,
            delivery_days=delivery_days,
            preferences=preferences,
        )
        ranked.append(
            RankedProduct(
                product=product,
                score=score,
                score_breakdown=breakdown,
                reasons=reasons,
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    for i, item in enumerate(ranked):
        item.rank = i + 1
    return ranked
