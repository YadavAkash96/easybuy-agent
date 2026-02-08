# Architecture — Agentic Commerce

## One-sentence hook

> "We built an AI shopping agent that turns a single sentence into a fully
> assembled, multi-retailer cart — using Gemini to understand what you
> actually need, SerpAPI to find real products, and Resend to close the
> loop with an invoice."

---

## High-level system diagram

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

---

## Where AI is structural (not cosmetic)

### What breaks if AI is removed?

| Capability | With Gemini | Without AI |
|---|---|---|
| Intent understanding | User says "skiing outfit" and the agent gathers budget, size, deadline through natural conversation | User must fill a rigid form field-by-field |
| Article decomposition | "skiing outfit" becomes 5 specific articles (jacket, pants, gloves, goggles, thermal layer) with constraints | User must manually list every item they need |
| Cross-retailer search | SerpAPI finds real products; ranking engine scores them transparently | User manually searches each retailer site |
| Invoice delivery | Personalized confirmation email with PDF via Resend | No post-purchase communication |

**Without AI, the system is a dumb product search box.**
With AI, one sentence drives an end-to-end purchasing pipeline.

---

## End-to-end data flow

### Step 1: Intent Chat (Gemini 3 Pro Preview)

```
User: "I need a skiing outfit"
                |
                v
    +---------------------------+
    | /api/intent-chat          |
    |                           |
    | Gemini acts as a shopping |
    | clerk — asks follow-up    |
    | questions one at a time:  |
    |                           |
    | "What's your budget?"     |
    | "What size do you wear?"  |
    | "When do you need it by?" |
    |                           |
    | Output:                   |
    | ready: true               |
    | intent_summary:           |
    | "Skiing outfit, $400,     |
    |  size M, 5-day delivery"  |
    +---------------------------+
```

**AI role:** Inference under ambiguity. The user doesn't need to know what
fields matter — the LLM discovers them through conversation.

### Step 2: Breakdown (Gemini 3 Pro Preview)

```
    intent_summary
          |
          v
    +---------------------------+
    | /api/breakdown            |
    |                           |
    | Input:  "Skiing outfit,   |
    |   $400, size M, 5 days"   |
    |                           |
    | Output:                   |
    |   articles:               |
    |     - Ski Jacket          |
    |     - Ski Pants           |
    |     - Gloves              |
    |     - Goggles             |
    |     - Thermal Layer       |
    |   constraints:            |
    |     budget: $400          |
    |     size: M               |
    |     deadline_days: 5      |
    +---------------------------+
```

**AI role:** Decomposition. A single intent becomes a structured shopping
list. The user reviews and toggles articles on/off before proceeding.

### Step 3: Search + Rank (SerpAPI + Deterministic Engine)

```
    Enabled articles (parallel)
          |
    +-----+-----+-----+
    |     |     |     |
    v     v     v     v
  +------+ +------+ +------+
  |Jacket| |Pants | |Gloves|  ... per article
  +--+---+ +--+---+ +--+---+
     |        |        |
     v        v        v
  SerpAPI Google Shopping
  Real product listings from live retailers
     |
     v
  +------------------------------------------+
  | DETERMINISTIC RANKING ENGINE             |
  |                                          |
  |  score = 0.30 x price_score              |
  |        + 0.20 x delivery_score           |
  |        + 0.20 x rating_score             |
  |        + 0.15 x match_score              |
  |        + 0.15 x return_score             |
  |                                          |
  |  Tradeoff modes shift weights:           |
  |    "value"   -> price 0.45               |
  |    "fast"    -> delivery 0.40            |
  |    "quality" -> rating 0.50              |
  |                                          |
  |  Output: top 3 ranked per article        |
  |  + per-factor score breakdown            |
  +------------------------------------------+
```

**SerpAPI role:** Real product crawling from Google Shopping — prices,
delivery estimates, ratings, retailer sources. Not mocked data.

**Ranking is deliberately NOT AI.** It's deterministic and transparent:
users see exactly why product #1 outranks #2 via the (i) info icon.

### Step 4: Cart Assembly

```
  User picks 1 product per article
          |
          v
  +---------------------------+
  | Multi-retailer cart       |
  |                           |
  | - Jacket: Amazon  $89    |
  | - Pants:  REI     $120   |
  | - Gloves: Walmart $35    |
  |                           |
  | Total: $244 / $400 budget |
  | Delivery: all by Feb 13   |
  +---------------------------+
```

### Step 5: Checkout + Invoice (OpenAI + fpdf + Resend)

```
  +---------------------------+     +---------------------------+
  | Checkout fan-out          |     | Invoice pipeline          |
  | (simulated per-retailer)  |     |                           |
  |                           |     | OpenAI gpt-4o-mini        |
  | Amazon:                   |     |   -> confirmation message |
  |   Connecting...           |     |                           |
  |   Adding to cart...       |     | fpdf                      |
  |   Verifying address...    |     |   -> PDF invoice          |
  |   Order placed!           |     |                           |
  | REI:                      |     | Resend API                |
  |   Connecting...           |     |   -> email with PDF       |
  |   ...                     |     |   attachment to customer   |
  +---------------------------+     +---------------------------+
```

---

## External API integration map

| Service | Module | Purpose |
|---|---|---|
| **Google Gemini 3 Pro Preview** | `src/ai/intent_chat.py` | Conversational intent gathering — personalized shopping clerk |
| **Google Gemini 3 Pro Preview** | `src/ai/breakdown.py` | Intent decomposition into articles + constraints |
| **Google Gemini 3 Pro Preview** | `src/ai/brief.py` | Intent parsing into structured `ShoppingSpec` |
| **Google Gemini 3 Pro Preview** | `src/ai/gemini.py` | Chat streaming + Google Search grounding |
| **SerpAPI** | `src/core/retailers/` | Google Shopping crawling — real product listings, prices, ratings |
| **OpenAI gpt-4o-mini** | `src/ai/message.py` | Personalized order confirmation message |
| **Resend** | `src/core/email.py` | Invoice email delivery with PDF attachment |
| **fpdf** | `src/core/invoice.py` | PDF invoice generation (local, no API) |
| *(none)* | `src/core/ranking.py` | Deterministic scoring — NO AI, fully transparent |
| *(none)* | `src/core/cart.py` | Cart aggregation — pure logic |

---

## Feedback loop

```
     User speaks naturally
          |
          v
    +-----------+
    | Intent    |<-- Gemini gathers budget/size/deadline
    | Chat      |    through conversation (not a form)
    +-----------+
          |
          v
    +-----------+
    | Breakdown |<-- Gemini decomposes intent into articles
    +-----------+
          |
          v
    +-----------+
    | Toggle    |<-- User enables/disables articles
    |           |    User edits constraints
    +-----------+
          |
          v
    +-----------+
    | Search    |<-- SerpAPI finds real products
    | + Rank    |<-- Deterministic scoring with reasons
    +-----------+
          |
          v
    +-----------+
    | Review    |<-- User sees WHY each product ranked
    | + Pick    |    (i) icon shows score breakdown
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
    | Checkout  |<-- Per-retailer simulated fan-out
    |  + Email  |<-- Resend delivers PDF invoice
    +-----------+
```

---

## Component table

### Backend (Python / FastAPI)

| Component | File | Responsibility |
|---|---|---|
| API server | `src/main.py` | All endpoints: `/api/intent-chat`, `/api/breakdown`, `/api/search`, `/api/cart`, `/api/checkout`, `/api/invoice/email`, `/health` |
| Intent chat | `src/ai/intent_chat.py` | Gemini-powered conversational intent gathering |
| Breakdown | `src/ai/breakdown.py` | Gemini intent decomposition into articles + constraints |
| Brief parser | `src/ai/brief.py` | Gemini intent -> `ShoppingSpec` |
| Chat + Search | `src/ai/gemini.py` | Gemini chat streaming + Google Search grounding |
| Retailer discovery | `src/core/retailers/` | SerpAPI Google Shopping -> `Product[]` |
| Ranking engine | `src/core/ranking.py` | Deterministic scoring (5 factors, configurable weights) |
| Cart aggregator | `src/core/cart.py` | Multi-retailer cart assembly |
| Checkout orchestrator | `src/core/checkout.py` | Simulated per-retailer checkout steps |
| Invoice generator | `src/core/invoice.py` | PDF invoice via fpdf |
| Email sender | `src/core/email.py` | Resend API for invoice email delivery |
| Message generator | `src/ai/message.py` | OpenAI personalized confirmation message |
| Types | `src/core/types.py` | Pydantic models for all request/response types |

### Frontend (Next.js / React)

| Component | File | Responsibility |
|---|---|---|
| Wizard orchestrator | `frontend/app/components/ShoppingWizard.tsx` | State machine: intent -> breakdown -> search -> cart |
| Intent step | `frontend/app/components/steps/IntentStep.tsx` | WhatsApp-like chat UI with Gemini shopping clerk |
| Breakdown step | `frontend/app/components/steps/BreakdownStep.tsx` | Toggle cards for articles + constraint badges |
| Search step | `frontend/app/components/steps/SearchStep.tsx` | Per-article search results with product ranking |
| Step indicator | `frontend/app/components/StepIndicator.tsx` | 5-step horizontal progress bar |
| Checkout page | `frontend/app/checkout/page.tsx` | Unified cart, checkout modal, invoice |
| Types | `frontend/lib/types.ts` | TypeScript types for all API interfaces |
| API helpers | `frontend/lib/api.ts` | Shared `postJSON` helper |

---

## Trust boundaries

- **Browser**: untrusted
- **Backend**: trusted — holds API keys for Gemini, SerpAPI, OpenAI, Resend
- **SerpAPI**: external — real Google Shopping data, cached in dev mode
- **Gemini**: external — LLM inference, structured JSON output
- **Resend**: external — email delivery

---

## Demo moment

> The user types **"I need a skiing outfit"** — the Gemini-powered clerk
> asks about budget, size, and deadline through natural conversation.
> One sentence later, the system breaks the intent into 5 articles,
> searches real products via SerpAPI across retailers, ranks them with
> transparent scores, and assembles a multi-retailer cart. The user
> clicks "One-Click Order All" and receives a PDF invoice via email
> through Resend. The **(i)** icon on each product reveals exactly why
> it was chosen — no black box.
