"""Retailer discovery via SerpAPI Google Shopping."""

import json
import os
import re
from pathlib import Path
from typing import Any

import httpx

from src.core.types import Product, ProductVariant, ShoppingSpec

_CACHE_PATH = Path(__file__).parent / "fixtures" / "serpapi_cache.json"
_cache: dict[str, Any] | None = None


def _is_dev_mode() -> bool:
    return os.environ.get("SERPAPI_MODE", "dev").lower() == "dev"


def _load_cache() -> dict[str, Any]:
    global _cache  # noqa: PLW0603
    if _cache is not None:
        return _cache
    if _CACHE_PATH.exists():
        _cache = json.loads(_CACHE_PATH.read_text())
    else:
        _cache = {}
    return _cache


def _normalize_key(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def _discover_from_cache(article_name: str) -> dict[str, Any]:
    cache = _load_cache()
    key = _normalize_key(article_name)
    return cache.get(key, {"shopping_results": []})


def _discover_from_api(
    query: str, api_key: str
) -> dict[str, Any]:
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
    }
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        resp = client.get("https://serpapi.com/search.json", params=params)
    if resp.status_code >= 400:
        raise ValueError("SerpAPI request failed")
    return resp.json()


def discover_products(
    spec: ShoppingSpec,
    *,
    api_key: str,
) -> list[Product]:
    parts = [spec.intent]
    if spec.must_haves:
        parts.extend(spec.must_haves)
    parts.append(f"size {spec.size}")
    query = " ".join(parts)

    if _is_dev_mode():
        data = _discover_from_cache(spec.intent)
    else:
        data = _discover_from_api(query, api_key)

    results = data.get("shopping_results", [])

    products: list[Product] = []
    for item in results:
        try:
            products.append(_to_product(item, spec.size))
        except Exception:
            continue

    return [p for p in products if p.price > 0 and p.delivery_days > 0]


def _to_product(item: dict[str, Any], size: str) -> Product:
    variants_raw = item.get("variants") or [{"size": size}]
    variants = [
        ProductVariant(size=v.get("size", size), color=v.get("color"))
        for v in variants_raw
    ]

    return Product(
        id=str(item.get("product_id") or item.get("title")),
        name=str(item.get("title")),
        category=_infer_category(str(item.get("title", ""))),
        price=_parse_price(item.get("extracted_price") or item.get("price")),
        delivery_days=_parse_delivery_days(item.get("delivery")),
        rating=_parse_rating(item.get("rating")),
        rating_count=_parse_rating_count(item.get("reviews")),
        retailer=str(item.get("source", "unknown")),
        url=item.get("link") or item.get("product_link"),
        image_url=item.get("thumbnail"),
        variants=variants,
        tags=[str(tag) for tag in item.get("tags", [])],
    )


def _parse_delivery_days(value: Any) -> int:
    """Estimate delivery days from SerpAPI delivery text.

    Examples: "Free delivery by Tue", "2-day delivery", "Free delivery", None.
    """
    if not value:
        return 5
    text = str(value).lower()
    # "2-day", "3 day", "next day", "1-day"
    day_match = re.search(r"(\d+)\s*-?\s*day", text)
    if day_match:
        return max(int(day_match.group(1)), 1)
    if "next day" in text or "overnight" in text:
        return 1
    # "by Mon", "by Tue" — means arriving soon
    if re.search(r"by\s+(mon|tue|wed|thu|fri|sat|sun)", text):
        return 3
    # Has some delivery text but no timing info
    return 4


def _parse_price(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        raise ValueError("Missing price")
    match = re.search(r"[\d,.]+", str(value))
    if not match:
        raise ValueError("Invalid price")
    return float(match.group(0).replace(",", ""))


def _parse_rating(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"[\d.]+", str(value))
    if not match:
        return 0.0
    return float(match.group(0))


def _parse_rating_count(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return max(value, 0)
    match = re.search(r"[\d,]+", str(value))
    if not match:
        return 0
    return int(match.group(0).replace(",", ""))


def _infer_category(title: str) -> str:
    lower = title.lower()
    for keyword in ["jacket", "pants", "gloves", "goggles", "helmet", "boots"]:
        if keyword in lower:
            return keyword
    return "other"
