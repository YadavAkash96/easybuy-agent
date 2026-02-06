"""FastAPI app — chat proxy to Gemini with SSE streaming."""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.ai.gemini import stream_chat
from src.core.types import ChatRequest

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "")

app = FastAPI(title="hack-nation-backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not set. API key is required.")

    try:
        kwargs: dict = {"api_key": GEMINI_API_KEY}
        if LLM_MODEL:
            kwargs["model"] = LLM_MODEL
        return StreamingResponse(
            stream_chat(req.messages, **kwargs),
            media_type="text/event-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}") from e
