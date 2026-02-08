"""Conversational intent gathering — shopping clerk chat."""

import json
import re

from google import genai

from src.core.types import IntentChatResponse

DEFAULT_MODEL = "gemini-3-pro-preview"

SYSTEM_PROMPT = """\
You are a friendly shopping assistant (like a clerk in a store). Your job is to \
gather 4 pieces of information from the customer through natural conversation:

1. **What to buy** — the type of outfit or items they need
2. **Budget** — how much they want to spend (in USD)
3. **Size** — their clothing size
4. **Delivery deadline** — when they need it by (in days)

Rules:
- Be warm, concise, and conversational (1-2 sentences per reply)
- Ask for ONE missing piece of info at a time
- If the user provides multiple pieces at once, acknowledge them all
- When ALL 4 pieces are gathered, set ready=true and provide an intent_summary
- The intent_summary should be a single sentence combining all 4 pieces

You MUST respond in valid JSON with exactly these keys:
{
  "reply": "your conversational message to the user",
  "ready": false,
  "intent_summary": null
}

When all info is gathered:
{
  "reply": "confirmation message",
  "ready": true,
  "intent_summary": "single sentence summary of what they want"
}
"""


def chat_intent(
    messages: list[dict],
    *,
    api_key: str,
    model: str | None = None,
) -> IntentChatResponse:
    """Send conversation history to LLM, get next reply or ready signal."""
    client = genai.Client(api_key=api_key)

    contents = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}]
    contents.append(
        {"role": "model", "parts": [{"text": "Understood. I'll respond in JSON."}]}
    )

    for msg in messages:
        role = "model" if msg.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=contents,
    )

    content = response.text or ""
    data = _extract_json(content)

    return IntentChatResponse(
        reply=data.get("reply", ""),
        ready=data.get("ready", False),
        intent_summary=data.get("intent_summary"),
    )


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
