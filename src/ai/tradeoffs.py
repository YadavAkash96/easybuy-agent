"""AI tradeoff variants: intent + constraints -> tradeoff specs."""

import json
import re

from google import genai

from src.core.types import ExtractedConstraints, TradeoffResponse, TradeoffVariant

DEFAULT_MODEL = "gemini-2.0-flash"


def parse_tradeoffs(
    intent: str,
    *,
    constraints: ExtractedConstraints,
    api_key: str,
    model: str | None = None,
) -> TradeoffResponse:
    prompt = (
        "You are a shopping assistant generating tradeoff variants.\n"
        "Return ONLY valid JSON with key \"variants\": array of objects with:\n"
        "- key: short id (value, fast, quality)\n"
        "- label: short label\n"
        "- summary: 1 sentence description\n"
        "- constraints: object with optional keys budget, deadline_days, size, preferences\n"
        "Use the provided constraints as baseline.\n"
        "For value: reduce budget ~15-25%.\n"
        "For fast: tighten deadline by 1-2 days if present.\n"
        "For quality: keep budget, add preferences like premium, durable if helpful.\n"
    )

    base = constraints.model_dump()
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model or DEFAULT_MODEL,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"{prompt}\nIntent: {intent}\n"
                                f"Baseline constraints: {json.dumps(base)}"
                            )
                        }
                    ],
                }
            ],
        )

        content = response.text or ""
        data = _extract_json(content)
        raw_variants = data.get("variants", [])
        normalized = [_normalize_variant(v) for v in raw_variants if isinstance(v, dict)]
        variants = [TradeoffVariant(**v) for v in normalized if "key" in v]
    except Exception:
        variants = []

    if not variants:
        variants = _fallback_variants(constraints)

    return TradeoffResponse(variants=variants)


def _normalize_variant(raw: dict) -> dict:
    if "key" not in raw:
        if "id" in raw:
            raw["key"] = raw["id"]
        elif "value" in raw:
            raw["key"] = raw["value"]
    if "label" in raw:
        label = str(raw["label"]).strip().lower()
        if "budget" in label or "value" in label or "cheap" in label:
            raw["label"] = "Budget-friendly"
        elif "fast" in label or "deliver" in label:
            raw["label"] = "Faster delivery"
        elif "quality" in label or "premium" in label:
            raw["label"] = "Higher quality"
    return raw


def _fallback_variants(constraints: ExtractedConstraints) -> list[TradeoffVariant]:
    base = constraints.model_dump()
    budget = constraints.budget or 400
    fast_deadline = max((constraints.deadline_days or 5) - 1, 1)
    return [
        TradeoffVariant(
            key="value",
            label="Budget-friendly",
            summary="Prioritizes lower price with acceptable quality.",
            constraints=ExtractedConstraints(
                **{**base, "budget": max(budget * 0.8, 50)}
            ),
        ),
        TradeoffVariant(
            key="fast",
            label="Faster delivery",
            summary="Prioritizes sooner delivery dates.",
            constraints=ExtractedConstraints(**{**base, "deadline_days": fast_deadline}),
        ),
        TradeoffVariant(
            key="quality",
            label="Higher quality",
            summary="Prioritizes durability and top-rated items.",
            constraints=ExtractedConstraints(
                **{
                    **base,
                    "preferences": list({"premium", "durable", *(constraints.preferences or [])}),
                }
            ),
        ),
    ]


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
