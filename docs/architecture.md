# Architecture — Gemini Chat Skeleton

## System diagram

```
Browser (Next.js :3000)
  → POST http://localhost:8000/api/chat  { messages: [{role, content}] }
  → FastAPI backend (:8000)
    → Gemini API (google-genai SDK, streaming)
    ← SSE chunks: data: {"token": "..."}\n\n
  ← Browser renders tokens incrementally
```

## Components

### Backend (Python / FastAPI)

| Component | File | Responsibility |
|-----------|------|----------------|
| API server | `src/main.py` | CORS, `/api/chat` (SSE streaming), `/health` |
| Gemini client | `src/ai/gemini.py` | Wraps `google-genai` SDK, yields SSE-formatted chunks |
| Types | `src/core/types.py` | Pydantic models: `Message`, `ChatRequest` |

### Frontend (Next.js / React)

| Component | File | Responsibility |
|-----------|------|----------------|
| Page | `frontend/app/page.tsx` | Renders `<Chat />` |
| Chat | `frontend/app/components/Chat.tsx` | State, fetch+ReadableStream SSE parsing, AbortController |
| MessageList | `frontend/app/components/MessageList.tsx` | Renders messages, auto-scrolls |
| MessageComposer | `frontend/app/components/MessageComposer.tsx` | Text input + send/stop button |
| Types | `frontend/lib/types.ts` | `Message` type |

## Data flow

1. User types message → `MessageComposer` calls `onSend`
2. `Chat` appends user message, POSTs to `/api/chat`
3. FastAPI validates request via Pydantic
4. `stream_chat()` calls Gemini SDK, streams chunks
5. `StreamingResponse` sends SSE lines back to browser
6. `Chat` reads `ReadableStream`, parses SSE, updates assistant message token-by-token
7. User can click "Stop" → `AbortController.abort()` cancels the fetch

## Trust boundaries

- **Browser**: untrusted, never sees API key
- **Backend**: trusted, holds `GEMINI_API_KEY`, proxies to Gemini
- **Gemini API**: external dependency

## Key decisions

- Two-stack (Python + Next.js) to keep AI logic in Python
- SSE over `fetch` + `ReadableStream` (not `EventSource` — POST required)
- `assistant` → `model` role mapping for Gemini API
- `NEXT_PUBLIC_API_URL` for browser-side fetch target
