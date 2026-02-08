"""Gemini client — streaming chat + web search with grounding."""

import json
import logging
import re
import uuid
from collections.abc import Generator

from google import genai
from google.genai import types

from src.core.types import Message, Product

DEFAULT_MODEL = "gemini-3-pro-preview"

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Chat streaming (legacy, kept for backward compat)
# ---------------------------------------------------------------------------


def _to_gemini_contents(messages: list[Message]) -> list[dict]:
    """Convert our Message list to Gemini SDK content format."""
    contents = []
    for msg in messages:
        role = "model" if msg.role == "assistant" else msg.role
        contents.append({"role": role, "parts": [{"text": msg.content}]})
    return contents


def stream_chat(
    messages: list[Message], *, api_key: str, model: str = DEFAULT_MODEL
) -> Generator[str, None, None]:
    """Stream a chat response from Gemini, yielding SSE-formatted lines."""
    client = genai.Client(api_key=api_key)
    contents = _to_gemini_contents(messages)

    for chunk in client.models.generate_content_stream(
        model=model, contents=contents
    ):
        if chunk.text:
            yield f"data: {json.dumps({'token': chunk.text})}\n\n"

    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Article search — Phase 1: Google Search grounding, Phase 2: structuring
# ---------------------------------------------------------------------------

ARTICLE_SEARCH_PROMPT = """\
You are a product search assistant. Find real products available for purchase online.

Search for: {query}

Requirements:
- Find 4-6 specific products from different retailers
- Include exact prices in USD
- Include estimated delivery times in days
- Include product ratings if available
- Focus on products that are currently available to buy
- Prefer well-known retailers

For each product found, provide:
- Product name
- Price (USD)
- Retailer name
- Estimated delivery days
- Rating (out of 5)
- Brief description
- Product URL if available
"""

STRUCTURING_PROMPT = """\
You are a data structuring assistant. Convert product information into structured data.

Given the following product search results, call the display_products function with
the extracted product data. Extract ALL products mentioned.

Search results:
{search_text}
"""

ARTICLE_TOOL_DECLARATIONS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="display_products",
                description="Display a list of products found from web search",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "products": types.Schema(
                            type="ARRAY",
                            items=types.Schema(
                                type="OBJECT",
                                properties={
                                    "title": types.Schema(
                                        type="STRING",
                                        description="Product name/title",
                                    ),
                                    "price": types.Schema(
                                        type="NUMBER",
                                        description="Price in USD",
                                    ),
                                    "retailer": types.Schema(
                                        type="STRING",
                                        description="Retailer or store name",
                                    ),
                                    "delivery_days": types.Schema(
                                        type="NUMBER",
                                        description="Estimated delivery time in days",
                                    ),
                                    "rating": types.Schema(
                                        type="NUMBER",
                                        description="Rating out of 5",
                                    ),
                                    "description": types.Schema(
                                        type="STRING",
                                        description="Brief product description",
                                    ),
                                    "url": types.Schema(
                                        type="STRING",
                                        description="Product URL",
                                    ),
                                },
                                required=["title", "price", "retailer"],
                            ),
                        )
                    },
                    required=["products"],
                ),
            )
        ]
    )
]


def _products_from_function_args(
    args: dict, fallback_urls: list[str] | None = None
) -> list[Product]:
    """Convert display_products function call args to Product models."""
    products: list[Product] = []
    raw_items = args.get("products", [])
    urls = fallback_urls or []

    for i, item in enumerate(raw_items):
        price = float(item.get("price", 0))
        if price <= 0:
            continue
        delivery = int(item.get("delivery_days", 5))
        if delivery <= 0:
            delivery = 5

        url = item.get("url", "")
        if not url and i < len(urls):
            url = urls[i]

        products.append(
            Product(
                id=str(uuid.uuid4())[:8],
                name=item.get("title", "Unknown Product"),
                category="",
                price=price,
                delivery_days=delivery,
                retailer=item.get("retailer", "Unknown"),
                url=url,
                rating=float(item.get("rating", 0)),
                description=item.get("description", ""),
            )
        )

    return products


def _build_search_query(
    article_name: str,
    intent: str,
    constraints: dict,
) -> str:
    """Build a search query string from article + constraints."""
    parts = [f"{article_name} for {intent}"]
    budget = constraints.get("budget")
    if budget:
        parts.append(f"under ${int(budget)}")
    size = constraints.get("size")
    if size:
        parts.append(f"size {size}")
    prefs = constraints.get("preferences", [])
    if prefs:
        parts.append(" ".join(prefs))
    return ", ".join(parts)


def _extract_grounding_urls(candidate) -> list[str]:
    """Extract URLs from grounding metadata if available."""
    urls: list[str] = []
    try:
        metadata = candidate.grounding_metadata
        if metadata and metadata.grounding_chunks:
            for chunk in metadata.grounding_chunks:
                if hasattr(chunk, "web") and chunk.web and chunk.web.uri:
                    urls.append(chunk.web.uri)
    except Exception:
        pass
    return urls


def search_article(
    article_name: str,
    constraints: dict,
    intent: str,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> list[Product]:
    """Search for products matching an article using Gemini with Google Search grounding.

    Phase 1: Google Search grounding to find real products.
    Phase 2: Function calling to structure the results.
    """
    client = genai.Client(api_key=api_key)
    query = _build_search_query(article_name, intent, constraints)

    # Phase 1: Search with Google Search grounding
    search_prompt = ARTICLE_SEARCH_PROMPT.format(query=query)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    logger.info("Phase 1: Searching for '%s'", query)
    search_response = client.models.generate_content(
        model=model,
        contents=search_prompt,
        config=types.GenerateContentConfig(
            tools=[search_tool],
            temperature=0.3,
        ),
    )

    search_text = search_response.text or ""
    if not search_text.strip():
        logger.warning("Empty search response for '%s'", article_name)
        return []

    # Extract grounding URLs
    grounding_urls: list[str] = []
    if search_response.candidates:
        grounding_urls = _extract_grounding_urls(search_response.candidates[0])

    # Phase 2: Structure results via function calling
    structuring_prompt = STRUCTURING_PROMPT.format(search_text=search_text)

    logger.info("Phase 2: Structuring results for '%s'", article_name)
    structure_response = client.models.generate_content(
        model=model,
        contents=structuring_prompt,
        config=types.GenerateContentConfig(
            tools=ARTICLE_TOOL_DECLARATIONS,
            temperature=0.1,
        ),
    )

    # Extract function call
    if structure_response.candidates:
        candidate = structure_response.candidates[0]
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.function_call and part.function_call.name == "display_products":
                    args = dict(part.function_call.args) if part.function_call.args else {}
                    return _products_from_function_args(args, grounding_urls)

    # Fallback: try to parse JSON from text response
    logger.warning("No function call in structuring response, trying JSON fallback")
    text = structure_response.text or ""
    return _try_parse_products_from_text(text, grounding_urls)


def _try_parse_products_from_text(
    text: str, fallback_urls: list[str] | None = None
) -> list[Product]:
    """Last-resort: try to find JSON in text response."""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return []
    try:
        data = json.loads(match.group())
        if "products" in data:
            return _products_from_function_args(data, fallback_urls)
    except (json.JSONDecodeError, KeyError):
        pass
    return []
