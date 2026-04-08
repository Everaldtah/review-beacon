"""Review ingestion and retrieval."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import uuid
import json
from datetime import datetime, date

from app.database import get_db
from app.services.sentiment import analyze_sentiment

router = APIRouter()


class ReviewIngest(BaseModel):
    business_id: str
    platform: str  # google | yelp | g2 | tripadvisor | manual
    external_id: Optional[str] = None
    author_name: Optional[str] = None
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    reviewed_at: Optional[str] = None


class BatchIngest(BaseModel):
    reviews: List[ReviewIngest]


@router.post("/ingest")
async def ingest_review(payload: ReviewIngest, db=Depends(get_db)):
    cursor = await db.execute("SELECT id FROM businesses WHERE id = ?", (payload.business_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Business not found")

    if not 1 <= payload.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1–5")

    sentiment_label, sentiment_score = analyze_sentiment(
        (payload.body or "") + " " + (payload.title or ""), payload.rating
    )

    review_id = str(uuid.uuid4())
    external_id = payload.external_id or review_id
    reviewed_at = payload.reviewed_at or datetime.utcnow().isoformat()

    try:
        await db.execute(
            """INSERT INTO reviews (id, business_id, platform, external_id, author_name,
               rating, title, body, reviewed_at, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (review_id, payload.business_id, payload.platform, external_id,
             payload.author_name, payload.rating, payload.title, payload.body,
             reviewed_at, sentiment_label, sentiment_score),
        )
        await db.commit()
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=409, detail="Review already ingested (duplicate external_id + platform)")
        raise

    # Update daily sentiment aggregate
    review_date = reviewed_at[:10]
    await db.execute(
        """INSERT INTO sentiment_daily (id, business_id, date, avg_rating, review_count,
           positive_count, negative_count, neutral_count)
           VALUES (?, ?, ?, ?, 1,
             CASE WHEN ? = 'positive' THEN 1 ELSE 0 END,
             CASE WHEN ? = 'negative' THEN 1 ELSE 0 END,
             CASE WHEN ? = 'neutral' THEN 1 ELSE 0 END)
           ON CONFLICT(business_id, date) DO UPDATE SET
             avg_rating = (avg_rating * review_count + ?) / (review_count + 1),
             review_count = review_count + 1,
             positive_count = positive_count + CASE WHEN ? = 'positive' THEN 1 ELSE 0 END,
             negative_count = negative_count + CASE WHEN ? = 'negative' THEN 1 ELSE 0 END,
             neutral_count = neutral_count + CASE WHEN ? = 'neutral' THEN 1 ELSE 0 END""",
        (str(uuid.uuid4()), payload.business_id, review_date, payload.rating,
         sentiment_label, sentiment_label, sentiment_label,
         payload.rating, sentiment_label, sentiment_label, sentiment_label),
    )
    await db.commit()

    return {
        "id": review_id,
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "needs_response": payload.rating <= 3,
    }


@router.post("/ingest/batch")
async def ingest_batch(payload: BatchIngest, db=Depends(get_db)):
    results = []
    for review in payload.reviews:
        try:
            sentiment_label, sentiment_score = analyze_sentiment(
                (review.body or "") + " " + (review.title or ""), review.rating
            )
            review_id = str(uuid.uuid4())
            external_id = review.external_id or review_id
            reviewed_at = review.reviewed_at or datetime.utcnow().isoformat()
            await db.execute(
                """INSERT OR IGNORE INTO reviews (id, business_id, platform, external_id,
                   author_name, rating, title, body, reviewed_at, sentiment, sentiment_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (review_id, review.business_id, review.platform, external_id,
                 review.author_name, review.rating, review.title, review.body,
                 reviewed_at, sentiment_label, sentiment_score),
            )
            results.append({"id": review_id, "sentiment": sentiment_label})
        except Exception as e:
            results.append({"error": str(e), "author": review.author_name})

    await db.commit()
    return {"ingested": len([r for r in results if "id" in r]), "results": results}


@router.get("")
async def list_reviews(
    business_id: str,
    platform: str = None,
    sentiment: str = None,
    min_rating: int = None,
    max_rating: int = None,
    unanswered: bool = False,
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_db)
):
    query = "SELECT r.*, rr.status as response_status FROM reviews r LEFT JOIN review_responses rr ON r.id = rr.review_id WHERE r.business_id = ?"
    params = [business_id]
    if platform:
        query += " AND r.platform = ?"; params.append(platform)
    if sentiment:
        query += " AND r.sentiment = ?"; params.append(sentiment)
    if min_rating:
        query += " AND r.rating >= ?"; params.append(min_rating)
    if max_rating:
        query += " AND r.rating <= ?"; params.append(max_rating)
    if unanswered:
        query += " AND rr.id IS NULL"
    query += " ORDER BY r.reviewed_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor = await db.execute(query, params)
    return [dict(r) for r in await cursor.fetchall()]
