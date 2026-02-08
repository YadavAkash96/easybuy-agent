"""One-time script to capture SerpAPI responses for dev mode cache.

Usage:
    docker compose run --rm backend python scripts/capture_serpapi.py
"""

import json
import os
import re
from pathlib import Path

import httpx

SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")
CACHE_PATH = Path("src/core/retailers/fixtures/serpapi_cache.json")

ARTICLES = [
    {"name": "Ski Jacket", "must_haves": ["waterproof", "warm"]},
    {"name": "Ski Pants", "must_haves": ["waterproof", "warm"]},
    {"name": "Ski Gloves", "must_haves": ["waterproof", "warm"]},
    {"name": "Ski Goggles", "must_haves": []},
    {"name": "Base Layer", "must_haves": ["warm"]},
    {"name": "Ski Helmet", "must_haves": []},
]

SIZE = "M"


def _normalize_key(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def _build_query(article: dict) -> str:
    parts = [article["name"]]
    parts.extend(article["must_haves"])
    parts.append(f"size {SIZE}")
    return " ".join(parts)


def main() -> None:
    if not SERPAPI_API_KEY:
        print("ERROR: SERPAPI_API_KEY not set in environment.")
        raise SystemExit(1)

    cache: dict[str, dict] = {}

    for article in ARTICLES:
        query = _build_query(article)
        key = _normalize_key(article["name"])
        print(f"Fetching: {query} (cache key: {key})")

        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": SERPAPI_API_KEY,
        }

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            resp = client.get("https://serpapi.com/search.json", params=params)

        if resp.status_code >= 400:
            print(f"  FAILED ({resp.status_code}), skipping.")
            continue

        data = resp.json()
        n_results = len(data.get("shopping_results", []))
        print(f"  OK — {n_results} shopping results")
        cache[key] = data

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))
    print(f"\nCache written to {CACHE_PATH} ({len(cache)} entries)")


if __name__ == "__main__":
    main()
