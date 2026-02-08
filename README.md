# Hack Nation — Gemini Chat

Streaming chat app powered by Gemini. Python (FastAPI) backend + Next.js frontend.

## Quick start

```bash
# 1. Copy env and add your Gemini API key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your-actual-key

# 2. Start both services
make up

# 3. Open http://localhost:3000
```

docker compose up

## Commands

```bash
make up       # Build and start backend (:8000) + frontend (:3000)
make down     # Stop all services
make test     # Run all backend tests
make lint     # Run ruff linter
make format   # Auto-format Python code
```

## SerpAPI Dev / Prod Mode

SerpAPI credits are limited. Dev mode serves precomputed responses from a local cache so you can iterate on UI and ranking without burning API calls.

```bash
# 1. Capture live SerpAPI responses (run once, requires SERPAPI_API_KEY in .env)
make capture-cache

# 2. Start in dev mode (default) — reads from cache, zero API calls
make dev

# 3. Start in prod mode — live SerpAPI calls for the real demo
make prod
```

`make up` defaults to dev mode. Set `SERPAPI_MODE=prod` to switch.

## Architecture

See [docs/architecture.md](docs/architecture.md).

```
Browser (:3000) → POST /api/chat → FastAPI (:8000) → Gemini API → SSE stream back
```

## Docs

- [Architecture](docs/architecture.md)
- [Requirements](docs/requirements.md)
- [Failure modes](docs/failure-modes.md)
- [AI role](docs/ai-role.md)
- [Testing](docs/testing.md)
- [Plan](docs/plan.md)
