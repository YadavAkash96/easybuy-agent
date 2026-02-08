"""AI breakdown parser: intent -> suggested articles + extracted constraints."""

import json
import re

from google import genai

from src.core.types import BreakdownResponse, ExtractedConstraints, SuggestedArticle

DEFAULT_MODEL = "gemini-3-pro-preview"


def parse_breakdown(
    intent: str, *, api_key: str, model: str | None = None
) -> BreakdownResponse:
    prompt = (
        "You are a shopping assistant that breaks down a purchase intent into "
        "individual article categories and extracts constraints.\n"
        "Return ONLY valid JSON with two keys:\n"
        '- "articles": array of objects with "name" (display name) and "category" (slug)\n'
        '- "constraints": object with optional keys "budget" (number), '
        '"deadline_days" (number), "size" (string), "preferences" (list of strings)\n'
        "Example: a skiing outfit might include jacket, pants, goggles, gloves, "
        "helmet, base layer, socks.\n"
        "Extract any budget, deadline, size, and style preferences from the intent."
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=[{"role": "user", "parts": [{"text": f"{prompt}\nIntent: {intent}"}]}],
    )

    content = response.text or ""
    data = _extract_json(content)

    articles = [SuggestedArticle(**a) for a in data.get("articles", [])]
    constraints = ExtractedConstraints(**data.get("constraints", {}))

    return BreakdownResponse(articles=articles, constraints=constraints)


def _extract_json(content: str) -> dict:
    if not content.strip():
        raise ValueError("AI returned empty response")

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", content)
        if not match:
            raise ValueError("AI response was not valid JSON")
        return json.loads(match.group(0))
