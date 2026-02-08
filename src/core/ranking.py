"""Deterministic ranking logic for products.

Normalized scoring (0–1 per dimension) with transparent breakdown.
Formula: (w_price*price + w_delivery*delivery + w_rating*rating
          + w_match*match + w_return*return) * penalty
"""

from src.core.types import BudgetRange, Product, RankedProduct, ScoreBreakdown


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


def _match_score(
    product: Product,
    preferences: list[str] | None,
    brand_preferences: list[str] | None,
) -> tuple[float, float]:
    """Keyword match against product name + description + retailer.

    Returns (preference_score, brand_score).
    """
    text = (product.name + " " + product.description + " " + product.retailer).lower()

    pref_score = 0.5
    if preferences:
        hits = sum(1 for kw in preferences if kw.lower() in text)
        pref_score = min(hits / len(preferences), 1.0)

    brand_score = 0.5
    if brand_preferences:
        brand_hits = sum(1 for b in brand_preferences if b.lower() in text)
        brand_score = min(brand_hits / len(brand_preferences), 1.0)

    return pref_score, brand_score


def _return_score(retailer: str) -> float:
    """Heuristic return-friendliness by retailer (0–1)."""
    normalized = (retailer or "").lower()
    scores = {
        "rei": 0.95,
        "patagonia": 0.9,
        "north face": 0.85,
        "amazon": 0.75,
        "walmart": 0.7,
        "target": 0.7,
        "backcountry": 0.8,
        "evo": 0.8,
    }
    for key, value in scores.items():
        if key in normalized:
            return value
    return 0.6


def score_product(
    product: Product,
    *,
    budget: float = 0,
    delivery_days: int = 0,
    preferences: list[str] | None = None,
    brand_preferences: list[str] | None = None,
    budget_range: BudgetRange | None = None,
    weights: dict[str, float] | None = None,
) -> tuple[float, ScoreBreakdown, list[str]]:
    """Score a single product. Returns (score, breakdown, reasons)."""
    ps = _price_score(product.price, budget)
    ds = _delivery_score(product.delivery_days, delivery_days)
    rs = _rating_score(product.rating)
    pref_score, brand_score = _match_score(product, preferences, brand_preferences)
    ms = (0.7 * pref_score + 0.3 * brand_score) if brand_preferences else pref_score
    rts = _return_score(product.retailer)

    penalty = 1.0
    penalty_reason = ""

    # Budget range soft boost/penalty
    range_reason = ""
    if budget_range and budget_range.enabled:
        min_price = budget_range.current_min or budget_range.min
        max_price = budget_range.current_max or budget_range.max
        if min_price <= product.price <= max_price:
            ps = min(ps + 0.1, 1.0)
            range_reason = "Within item budget range"
        else:
            ps = max(ps - 0.1, 0.0)
            range_reason = "Outside item budget range"

    # Penalize products way over budget
    if budget > 0 and product.price > budget * 1.5:
        penalty = 0.5
        penalty_reason = "Price >150% of budget"

    w = weights or {
        "price": 0.30,
        "delivery": 0.20,
        "rating": 0.20,
        "match": 0.15,
        "return": 0.15,
    }
    raw = (
        w["price"] * ps
        + w["delivery"] * ds
        + w["rating"] * rs
        + w["match"] * ms
        + w["return"] * rts
    )
    final = raw * penalty

    breakdown = ScoreBreakdown(
        price_score=round(ps, 3),
        delivery_score=round(ds, 3),
        rating_score=round(rs, 3),
        match_score=round(ms, 3),
        return_score=round(rts, 3),
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
    if brand_score >= 0.6:
        reasons.append("Preferred brand match")
    if range_reason:
        reasons.append(range_reason)
    if rts >= 0.8:
        reasons.append("Flexible returns")

    return round(final, 4), breakdown, reasons


def rank_products(
    products: list[Product],
    *,
    budget: float = 0,
    delivery_days: int = 0,
    preferences: list[str] | None = None,
    brand_preferences: list[str] | None = None,
    budget_range: BudgetRange | None = None,
    weights: dict[str, float] | None = None,
) -> list[RankedProduct]:
    """Rank products by normalized scoring. Returns sorted list."""
    ranked: list[RankedProduct] = []
    for product in products:
        score, breakdown, reasons = score_product(
            product,
            budget=budget,
            delivery_days=delivery_days,
            preferences=preferences,
            brand_preferences=brand_preferences,
            budget_range=budget_range,
            weights=weights,
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
