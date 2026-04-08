"""
Review Beacon — Multi-platform review monitor + AI response generator.
Aggregates Google, Yelp, and G2 reviews. Generates personalized response drafts with AI.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from datetime import datetime

from app.routes import businesses, reviews, responses, analytics
from app.database import init_db

app = FastAPI(
    title="Review Beacon",
    description="Multi-platform review monitor + AI response generator for local businesses and SaaS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(businesses.router, prefix="/api/businesses", tags=["businesses"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(responses.router, prefix="/api/responses", tags=["responses"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Review Beacon</title>
        <style>
            body { font-family: -apple-system, sans-serif; max-width: 860px; margin: 60px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .star { color: #f39c12; }
            .ep { font-family: monospace; background: #f8f9fa; padding: 8px 12px; border-radius: 4px; margin: 6px 0; display: block; }
            .badge { background: #3498db; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>Review Beacon <span class="badge">v1.0.0</span></h1>
        <p>
            <span class="star">★★★★★</span> Monitor reviews across Google, Yelp, and G2 in one place.
            Get AI-generated response drafts for every new review — in seconds.
        </p>
        <h2>API Endpoints</h2>
        <span class="ep">POST /api/businesses — Register a business</span>
        <span class="ep">POST /api/reviews/ingest — Submit reviews from any platform</span>
        <span class="ep">GET  /api/reviews?businessId= — List all reviews (sorted, filtered)</span>
        <span class="ep">POST /api/responses/generate/{review_id} — Generate AI response draft</span>
        <span class="ep">GET  /api/responses/{review_id} — Get response draft</span>
        <span class="ep">POST /api/responses/{review_id}/publish — Mark as published</span>
        <span class="ep">GET  /api/analytics/{business_id} — Sentiment trends and rating breakdown</span>
        <span class="ep">GET  /docs — Interactive API docs</span>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
