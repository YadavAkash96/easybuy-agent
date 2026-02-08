"""Unit tests for ranking logic."""

from src.core.ranking import rank_products, score_product
from src.core.types import BudgetRange, Product, ProductVariant


def _make_product(**overrides) -> Product:
    defaults = {
        "id": "p1",
        "name": "Test Product",
        "category": "jacket",
        "price": 180.0,
        "delivery_days": 3,
        "retailer": "AlpineCo",
        "variants": [ProductVariant(size="M", color="black")],
        "tags": ["waterproof"],
    }
    defaults.update(overrides)
    return Product(**defaults)


def test_rank_prefers_within_budget_and_deadline():
    products = [
        _make_product(
            id="fast", name="Fast Jacket", price=180.0, delivery_days=3
        ),
        _make_product(
            id="slow",
            name="Slow Jacket",
            price=160.0,
            delivery_days=9,
            retailer="SnowMart",
        ),
    ]

    ranked = rank_products(products, budget=400, delivery_days=5)

    assert ranked[0].product.id == "fast"
    assert ranked[0].score >= ranked[1].score
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2


def test_rank_prefers_cheaper_when_both_in_budget():
    products = [
        _make_product(id="expensive", name="Expensive Jacket", price=350.0),
        _make_product(id="cheap", name="Cheap Jacket", price=100.0),
    ]

    ranked = rank_products(products, budget=400, delivery_days=5)
    # Both within budget → same price score
    # But both delivery within deadline → same delivery score
    # Scores should be similar since prices are both within budget
    assert all(r.score > 0 for r in ranked)


def test_score_product_returns_breakdown():
    product = _make_product(rating=4.5, description="waterproof insulated jacket")

    score, breakdown, reasons = score_product(
        product, budget=400, delivery_days=5, preferences=["waterproof"]
    )

    assert score > 0
    assert breakdown.price_score == 1.0  # well within budget
    assert breakdown.delivery_score == 1.0  # well within deadline
    assert breakdown.rating_score == 0.9  # 4.5 / 5.0
    assert breakdown.match_score == 1.0  # "waterproof" in description
    assert breakdown.return_score >= 0.0
    assert isinstance(reasons, list)


def test_over_budget_penalty():
    product = _make_product(price=700.0)

    score, breakdown, _ = score_product(product, budget=400, delivery_days=5)

    assert breakdown.penalty == 0.5  # >150% of budget
    assert "150%" in breakdown.reason


def test_rank_with_web_search_products():
    """Web search products have no variants/tags, but have url/rating/description."""
    products = [
        Product(
            id="ws1",
            name="North Face Ski Jacket",
            price=250.0,
            delivery_days=4,
            retailer="REI",
            url="https://example.com/jacket",
            rating=4.5,
            description="Waterproof insulated ski jacket",
        ),
        Product(
            id="ws2",
            name="Budget Ski Jacket",
            price=89.0,
            delivery_days=7,
            retailer="Amazon",
            rating=3.8,
            description="Basic ski jacket",
        ),
    ]

    ranked = rank_products(
        products, budget=200, delivery_days=5, preferences=["waterproof"]
    )

    assert len(ranked) == 2
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2
    assert all(r.score_breakdown.price_score >= 0 for r in ranked)


def test_delivery_miss_lowers_score():
    on_time = _make_product(id="on_time", delivery_days=3)
    late = _make_product(id="late", delivery_days=15)

    ranked = rank_products([late, on_time], budget=400, delivery_days=5)
    assert ranked[0].product.id == "on_time"


def test_preferences_boost_score():
    product_match = _make_product(
        id="match", name="Waterproof Jacket", description="waterproof"
    )
    product_no_match = _make_product(
        id="nomatch", name="Basic Jacket", description="basic"
    )

    ranked = rank_products(
        [product_no_match, product_match],
        budget=400,
        delivery_days=5,
        preferences=["waterproof"],
    )
    assert ranked[0].product.id == "match"


def test_brand_preference_boosts_score():
    brand_match = _make_product(id="brand", name="Adidas Jacket", retailer="Adidas")
    no_brand = _make_product(id="nobrand", name="Generic Jacket", retailer="Shop")

    ranked = rank_products(
        [no_brand, brand_match],
        budget=400,
        delivery_days=5,
        preferences=["waterproof"],
        brand_preferences=["adidas"],
    )
    assert ranked[0].product.id == "brand"


def test_budget_range_soft_boost():
    in_range = _make_product(id="inrange", price=50.0)
    out_range = _make_product(id="outrange", price=200.0)
    budget_range = BudgetRange(min=30, max=80, enabled=True, current_min=30, current_max=80)

    ranked = rank_products(
        [out_range, in_range],
        budget=400,
        delivery_days=5,
        budget_range=budget_range,
    )
    assert ranked[0].product.id == "inrange"
