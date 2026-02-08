# Architecture — Agentic Commerce (Option B: Skiing Outfit)

## System diagram

```
Browser (Next.js :3000)
  → POST http://localhost:8000/api/brief        { intent } 
  → POST http://localhost:8000/api/tradeoffs    { intent, constraints }
  → POST http://localhost:8000/api/discover     { spec }
  → POST http://localhost:8000/api/rank         { spec, products }
  → POST http://localhost:8000/api/cart         { ranked_products }
  → POST http://localhost:8000/api/checkout     { cart, address, payment }
  → FastAPI backend (:8000)
    → AI Orchestrator (intent → spec, Gemini)
    → Retailer adapters (≥3, mocked or real)
    → Ranking engine (deterministic scoring + return-aware weights)
    → Explain mode (post-hoc rationale)
    → Cart aggregator
    → Checkout orchestrator (simulated fan-out)
  ← Browser renders cart + ranking explanations
```

## Components

### Backend (Python / FastAPI)

| Component | File | Responsibility |
|-----------|------|----------------|
| API server | `src/main.py` | `/api/brief`, `/api/tradeoffs`, `/api/discover`, `/api/rank`, `/api/cart`, `/api/checkout`, `/health` |
| AI orchestrator | `src/ai/` | Intent parsing → structured shopping spec |
| Retailer adapters | `src/core/retailers/` | Mocked retailer catalogs + search |
| Ranking engine | `src/core/ranking.py` | Deterministic scoring + return-aware weights + soft brand/budget boosts |
| Explain mode | `src/core/ranking.py` | Post-hoc rationale from ranking signals |
| Cart aggregator | `src/core/cart.py` | Combined cart across retailers |
| Checkout orchestrator | `src/core/checkout.py` | Simulated per-retailer checkout steps |
| Types | `src/core/types.py` | Pydantic models for spec, products, cart, checkout |

### Frontend (Next.js / React)

| Component | File | Responsibility |
|-----------|------|----------------|
| Page | `frontend/app/page.tsx` | Renders the agentic commerce UI |
| Chat + Spec | `frontend/app/components/Chat.tsx` | Capture intent + show structured spec |
| Cart view | `frontend/app/components/Cart.tsx` | Combined cart, totals, per-item delivery |
| Ranking explanation | `frontend/app/components/RankingExplain.tsx` | Why #1 is ranked highest |
| Checkout preview | `frontend/app/components/Checkout.tsx` | Simulated fan-out checkout plan |
| Types | `frontend/lib/types.ts` | Spec/Product/Cart types |

## Data flow

1. User submits intent.
2. AI orchestrator parses intent → shopping spec.
3. Retailer adapters return products from ≥3 retailers.
4. Ranking engine scores and orders products with explanations.
5. Cart aggregator builds combined cart with totals.
6. User edits cart → repeat steps 2–5.
7. Checkout orchestrator builds per-retailer simulated steps.

## Trust boundaries

- **Browser**: untrusted
- **Backend**: trusted, holds AI model key and mock catalog data
- **Retailer APIs**: mocked or external

## Key decisions

- Deterministic ranking logic separate from AI.
- Mocked retailer catalogs for safe demo.
- Single combined cart with simulated checkout fan-out.

---

## Pitch: System Architecture with AI Integration

### One-sentence hook

> "We built an agentic shopping assistant that uses AI to decompose a
> vague outfit request into a structured, multi-retailer shopping cart
> — with transparent, explainable ranking."

### High-level system overview

```
+-------------------------------------------------------------+
|                      BROWSER  (:3000)                       |
|  Next.js 15 / React 19 / Tailwind CSS v4                   |
|                                                             |
|  [Intent] -> [Breakdown] -> [Search] -> [Cart] -> [Checkout]|
|   Step 1       Step 2       Step 3     Step 4      Step 5   |
+---------------------------+---------------------------------+
                            |
                       REST / JSON
                            |
+---------------------------v---------------------------------+
|                  FASTAPI BACKEND  (:8000)                   |
|                                                             |
|  /api/breakdown  /api/search  /api/cart  /api/checkout      |
|  /api/brief      /api/discover /api/rank /api/invoice/email |
+---------------------------+---------------------------------+
           |                |                |
     +-----v-----+   +-----v------+   +-----v------+
     |  Gemini    |   |  SerpAPI   |   |  Resend    |
     |  2.0 Flash |   |  Google    |   |  Email API |
     |  (Google)  |   |  Shopping  |   +------------+
     +-----+------+   +-----+------+
           |                |
     Google Search     Real product
     Grounding         listings
```

### End-to-end data flow

```
User: "I need a skiing outfit, budget $400, size M, 5-day delivery"
  |
  v
+---------------------------------------------------------------+
| STEP 1: INTENT BREAKDOWN              Gemini 2.0 Flash        |
|---------------------------------------------------------------|
| Input:  raw text intent                                       |
| Output: articles[] + constraints{}                            |
|                                                               |
| "skiing outfit" --> [ Ski Jacket      ]    budget: $400       |
|                     [ Ski Pants       ]    size: M            |
|                     [ Gloves         ]    deadline: 5 days   |
|                     [ Goggles        ]    preferences: []    |
|                     [ Thermal Layer  ]                        |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
| STEP 2: USER REVIEW & SELECTION            Frontend           |
|---------------------------------------------------------------|
| Toggle cards ON/OFF per article                               |
| Edit constraints (budget, size, deadline)                     |
| User confirms --> triggers parallel search                    |
+-------------------------------+-------------------------------+
                                |
           +--------------------+--------------------+
           |                    |                    |
           v                    v                    v
+------------------+  +------------------+  +------------------+
| /api/search      |  | /api/search      |  | /api/search      |
| "Ski Jacket"     |  | "Ski Pants"      |  | "Gloves"         |
+--------+---------+  +--------+---------+  +--------+---------+
         |                     |                     |
         v                     v                     v
+---------------------------------------------------------------+
| STEP 3: DISCOVER + RANK (per article)                         |
|---------------------------------------------------------------|
|                                                               |
|  SerpAPI Google Shopping                                      |
|  ~~~~~~~~~~~~~~~~~~~~~~~~                                     |
|  Query: "{article} skiing size M"                             |
|  Returns: raw product listings from multiple retailers        |
|                                                               |
|         +----------------------------------------------+      |
|         |  DETERMINISTIC RANKING ENGINE                |      |
|         |----------------------------------------------|      |
|         |                                              |      |
|         |  score = 0.30 x price_score                  |      |
|         |        + 0.20 x delivery_score               |      |
|         |        + 0.20 x rating_score                 |      |
|         |        + 0.15 x match_score                  |      |
|         |        + 0.15 x return_score                 |      |
|         |                                              |      |
|         |  Each factor: [0..1], fully transparent       |      |
|         |  Hard penalty: x0.5 if price > 1.5x budget   |      |
|         +----------------------------------------------+      |
|                                                               |
|  Output: top 3 ranked products per article + reasoning        |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
| STEP 4: CART ASSEMBLY                     Core Logic          |
|---------------------------------------------------------------|
| User picks 1 product per article                              |
| Variant matching: find correct size across retailers          |
| Flags missing sizes (missing_variant = true)                  |
| Aggregates total cost across all retailers                    |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
| STEP 5: CHECKOUT + INVOICE                                    |
|---------------------------------------------------------------|
|                                                               |
|  Checkout Plan (simulated fan-out by retailer):               |
|  +-------------------+  +-------------------+                 |
|  | Amazon            |  | REI               |                 |
|  | - Open checkout   |  | - Open checkout   |                 |
|  | - Autofill addr   |  | - Autofill addr   |                 |
|  | - Submit: Jacket  |  | - Submit: Pants   |                 |
|  +-------------------+  +-------------------+                 |
|                                                               |
|  Invoice Email:                                               |
|  OpenAI (gpt-4o-mini) --> personalized confirmation message   |
|  fpdf                 --> PDF invoice with item table          |
|  Resend API           --> email with PDF attachment            |
+---------------------------------------------------------------+
```

### Where AI is structural (not cosmetic)

```
+-------------------------------------------------------------------+
|                  WHAT BREAKS IF AI IS REMOVED?                    |
+-------------------------------------------------------------------+
|                                                                   |
|  WITHOUT AI:                                                      |
|  - User must manually list every article they need                |
|  - User must manually search each retailer                       |
|  - No budget/size/deadline extraction from natural language       |
|  - No cross-retailer comparison                                  |
|  - System becomes a dumb product search box                      |
|                                                                   |
|  WITH AI:                                                         |
|  +---------------------+     +------------------------------+    |
|  | Gemini 2.0 Flash    |     | Deterministic Ranker         |    |
|  |---------------------|     |------------------------------|    |
|  | "skiing outfit" --> |     | Products from SerpAPI -->    |    |
|  |  5 specific items   |     |  scored on 5 transparent     |    |
|  |  + constraints      |     |  factors with reasons        |    |
|  |                     |     |                              |    |
|  | ROLE: inference     |     | ROLE: decision-making with   |    |
|  |  under ambiguity    |     |  explainable signals         |    |
|  +---------------------+     +------------------------------+    |
|                                                                   |
|  AI enables the INTENT -> PURCHASE pipeline to be fully           |
|  automated from a single sentence of natural language.            |
+-------------------------------------------------------------------+
```

### External API integration map

```
+--------------------+       +--------------------+
|   Gemini 2.0 Flash |       |   SerpAPI          |
|   (Google AI)      |       |   Google Shopping   |
+---------+----------+       +---------+----------+
          |                            |
          | Intent parsing             | Product discovery
          | Article decomposition      | Real-time listings
          | Google Search grounding    | Price + delivery data
          |                            |
+---------v----------------------------v----------+
|              FASTAPI BACKEND                    |
|                                                 |
|  src/ai/breakdown.py   Gemini -> articles[]     |
|  src/ai/brief.py       Gemini -> ShoppingSpec   |
|  src/ai/gemini.py       Gemini + Google Search  |
|  src/core/retailers/   SerpAPI -> Product[]     |
|  src/core/ranking.py   NO API (deterministic)   |
|  src/core/cart.py      NO API (aggregation)     |
|  src/core/checkout.py  NO API (simulated)       |
|  src/core/invoice.py   NO API (fpdf local)      |
|  src/core/email.py     Resend -> email delivery |
|  src/ai/message.py     OpenAI -> confirmation   |
+---------+----------------------------+----------+
          |                            |
+---------v----------+       +---------v----------+
|   OpenAI           |       |   Resend           |
|   gpt-4o-mini      |       |   Email API        |
+---------+----------+       +---------+----------+
          |                            |
   Customer message             Invoice email
   generation                   with PDF attachment
```

### Feedback loop

```
     User intent
          |
          v
    +-----------+
    | Breakdown |<-- Gemini decomposes intent
    +-----------+
          |
          v
    +-----------+
    |  Toggle   |<-- User enables/disables articles
    +-----------+    User edits constraints
          |
          v
    +-----------+
    |  Search   |<-- SerpAPI finds real products
    |  + Rank   |<-- Deterministic scoring with reasons
    +-----------+
          |
          v
    +-----------+
    |  Review   |<-- User sees WHY each product ranked
    |  + Pick   |    (i) icon shows score breakdown
    +-----------+    User can go back, adjust, re-search
          |               |
          |          +----+  <-- FEEDBACK LOOP
          |          |         User adjusts budget/prefs
          v          v         System re-ranks instantly
    +-----------+
    |   Cart    |<-- Multi-retailer aggregation
    +-----------+
          |
          v
    +-----------+
    | Checkout  |<-- Per-retailer instructions
    |  + Email  |<-- AI-written confirmation + PDF invoice
    +-----------+
```

### Demo moment

> The user types **one sentence** — "I need a skiing outfit, $400, size M,
> delivered in 5 days" — and the system autonomously breaks it into 5
> articles, searches real products across retailers, ranks them with
> transparent scores, and assembles a multi-retailer cart. The (i) icon
> on each product reveals *exactly why* it was chosen.
