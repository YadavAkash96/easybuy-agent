# EasyBuy — Super Smart Shopping Assistant

EasyBuy is an agentic shopping assistant for end-to-end ecommerce. Simply describe what you need — EasyBuy gathers your intent through natural conversation powered by Google Gemini, searches real products across retailers via SerpAPI, ranks them with transparent scores, and assembles a one-click checkout. After purchase, a personalized PDF invoice is delivered straight to your email inbox via Resend.

Built for the 4th Hack-Nation Global AI Hackathon (Feb 2026), VC Track — Agentic Commerce challenge.

## System Architecture

```
+----------------------------------------------------------------+
|                      BROWSER  (:3000)                          |
|  Next.js 15 / React 19 / Tailwind CSS v4                      |
|                                                                |
|  [Chat]  -->  [Breakdown]  -->  [Search]  -->  [Cart]  -->  [Checkout]
|  Step 1       Step 2           Step 3        Step 4       Step 5
+-------------------------------+--------------------------------+
                                |
                           REST / JSON
                                |
+-------------------------------v--------------------------------+
|                    FASTAPI BACKEND  (:8000)                    |
|                                                                |
|  /api/intent-chat   Conversational intent gathering            |
|  /api/breakdown     Intent --> articles[] + constraints{}      |
|  /api/search        Per-article product discovery + ranking    |
|  /api/cart          Multi-retailer cart assembly               |
|  /api/checkout      Simulated per-retailer fan-out             |
|  /api/invoice/email PDF invoice generation + email delivery    |
+--------+-----------------------+-------------------+-----------+
         |                       |                   |
   +-----v---------+     +------v--------+    +-----v--------+
   | Google Gemini  |     |   SerpAPI     |    |   Resend     |
   | 3 Pro Preview  |     |   Google      |    |   Email API  |
   |                |     |   Shopping    |    +--------------+
   +-----+--+------+     +------+--------+
         |  |                    |
   Intent   Article        Real product
   chat     breakdown      listings
```

## Quick start

```bash
# 1. Copy env and add your Gemini API key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your-actual-key

# 2. Start both services
make up

# 3. Open http://localhost:3000
```

docker compose build --no-cache frontend                                      
docker compose up                                                             

docker compose build --no-cache && docker compose up 
docker compose down                                             

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

## Docs

- [Architecture](docs/architecture.md)
- [Requirements](docs/requirements.md)
- [Failure modes](docs/failure-modes.md)
- [AI role](docs/ai-role.md)
- [Testing](docs/testing.md)
- [Plan](docs/plan.md)
