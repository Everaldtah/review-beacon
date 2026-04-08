# Review Beacon

> Multi-platform review monitor + AI response generator — respond to every review in seconds, not hours.

## The Problem

Local businesses and SaaS products get reviews across 4–6 different platforms (Google, Yelp, G2, TripAdvisor, Capterra, etc.). Monitoring all of them manually is overwhelming. Crafting thoughtful, personalized responses takes 10–15 minutes per review. Most businesses respond to fewer than 30% of their reviews — especially negative ones — leaving reputation damage unaddressed.

## What It Does

Review Beacon aggregates reviews from all platforms into one inbox, analyzes sentiment automatically, and generates AI-powered response drafts that sound human and on-brand. The owner approves, edits if needed, and publishes — all in under 2 minutes.

## Features

- **Multi-platform ingestion** — Google, Yelp, G2, TripAdvisor, or any platform via API
- **Automatic sentiment analysis** — positive/negative/neutral classification with confidence score
- **AI response drafts** — powered by Claude or GPT, fallback to smart templates
- **Customizable tone** — professional, friendly, or formal per business
- **Response workflow** — draft → approve → publish lifecycle
- **Analytics dashboard** — rating trends, sentiment over time, response rate, platform breakdown
- **Unanswered queue** — surface reviews that haven't been responded to yet
- **Batch ingestion** — import historical reviews in bulk

## Tech Stack

- **Backend**: Python / FastAPI
- **Database**: SQLite (aiosqlite)
- **AI**: Anthropic Claude or OpenAI GPT (smart template fallback)
- **Sentiment**: Rule-based keyword model (no ML setup required)

## Installation

```bash
git clone https://github.com/Everaldtah/review-beacon
cd review-beacon
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# optionally add ANTHROPIC_API_KEY or OPENAI_API_KEY
python -m app.main
```

Server starts at http://localhost:8000

## Usage

### Register your business
```bash
curl -X POST http://localhost:8000/api/businesses \
  -H "Content-Type: application/json" \
  -d '{"name": "Bella Italia Restaurant", "category": "restaurant", "response_tone": "friendly"}'
```

### Ingest a review
```bash
curl -X POST http://localhost:8000/api/reviews/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "BIZ_ID",
    "platform": "google",
    "external_id": "ChIJabc123",
    "author_name": "Sarah Johnson",
    "rating": 2,
    "body": "The pasta was cold and service was slow. Disappointing for the price."
  }'
```

### Generate AI response
```bash
curl -X POST http://localhost:8000/api/responses/generate/REVIEW_ID
```

### Approve and mark published
```bash
curl -X POST http://localhost:8000/api/responses/REVIEW_ID/approve \
  -H "Content-Type: application/json" \
  -d '{"final_text": "Hi Sarah, I am so sorry about your experience..."}'

curl -X POST http://localhost:8000/api/responses/REVIEW_ID/publish
```

### View analytics
```bash
curl http://localhost:8000/api/analytics/BIZ_ID?days=30
```

## API Integration Pattern

Integrate with your existing review collection (Zapier, Make, or custom webhook):

```python
import httpx

async def forward_google_review(review_data):
    async with httpx.AsyncClient() as client:
        # Ingest
        ingest = await client.post("http://localhost:8000/api/reviews/ingest", json={
            "business_id": YOUR_BIZ_ID,
            "platform": "google",
            "external_id": review_data["review_id"],
            "author_name": review_data["author"],
            "rating": review_data["rating"],
            "body": review_data["text"],
        })
        review_id = ingest.json()["id"]
        
        # Auto-generate draft
        await client.post(f"http://localhost:8000/api/responses/generate/{review_id}")
```

## Monetization Model

| Plan | Price | Locations |
|------|-------|---------|
| Free | $0 | 1 location, 50 reviews/mo, template responses |
| Starter | $29/mo | 3 locations, unlimited reviews, AI responses |
| Agency | $99/mo | 20 locations, white-label, API access |
| Enterprise | Custom | Unlimited + dedicated support + custom integrations |

**Target customers**: Restaurant owners, hotel chains, SaaS companies with G2/Capterra presence, marketing agencies managing multiple clients.
**Market size**: 33M+ small businesses in the US. Online reputation is a top-3 marketing concern.
