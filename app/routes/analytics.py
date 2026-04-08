"""Analytics and sentiment reporting."""

from fastapi import APIRouter, Depends
from app.database import get_db

router = APIRouter()


@router.get("/{business_id}")
async def get_analytics(business_id: str, days: int = 30, db=Depends(get_db)):
    """Sentiment trends, rating distribution, and platform breakdown."""

    # Overall stats
    cursor = await db.execute(
        """SELECT
             COUNT(*) as total_reviews,
             AVG(rating) as avg_rating,
             SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
             SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
             SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
             SUM(CASE WHEN response_id IS NOT NULL THEN 1 ELSE 0 END) as responded,
             SUM(CASE WHEN response_id IS NULL THEN 1 ELSE 0 END) as unanswered
           FROM reviews WHERE business_id = ? AND reviewed_at >= datetime('now', ?)""",
        (business_id, f"-{days} days")
    )
    stats = dict(await cursor.fetchone())
    stats["avg_rating"] = round(stats["avg_rating"] or 0, 2)
    stats["response_rate"] = round(
        (stats["responded"] / max(stats["total_reviews"], 1)) * 100, 1
    )

    # Rating distribution
    cursor = await db.execute(
        "SELECT rating, COUNT(*) as count FROM reviews WHERE business_id = ? GROUP BY rating ORDER BY rating DESC",
        (business_id,)
    )
    rating_dist = {str(r["rating"]): r["count"] for r in await cursor.fetchall()}

    # Platform breakdown
    cursor = await db.execute(
        """SELECT platform, COUNT(*) as count, AVG(rating) as avg_rating
           FROM reviews WHERE business_id = ?
           GROUP BY platform ORDER BY count DESC""",
        (business_id,)
    )
    platforms = [{"platform": r["platform"], "count": r["count"], "avg_rating": round(r["avg_rating"] or 0, 2)}
                 for r in await cursor.fetchall()]

    # Daily trend
    cursor = await db.execute(
        """SELECT date, avg_rating, review_count, positive_count, negative_count
           FROM sentiment_daily
           WHERE business_id = ? AND date >= date('now', ?)
           ORDER BY date ASC""",
        (business_id, f"-{days} days")
    )
    trend = [dict(r) for r in await cursor.fetchall()]

    # Recent negative reviews needing response
    cursor = await db.execute(
        """SELECT r.id, r.author_name, r.rating, r.body, r.platform, r.reviewed_at
           FROM reviews r
           LEFT JOIN review_responses rr ON r.id = rr.review_id
           WHERE r.business_id = ? AND r.rating <= 3 AND rr.id IS NULL
           ORDER BY r.reviewed_at DESC LIMIT 5""",
        (business_id,)
    )
    needs_response = [dict(r) for r in await cursor.fetchall()]

    return {
        "overview": stats,
        "rating_distribution": rating_dist,
        "by_platform": platforms,
        "trend": trend,
        "needs_response": needs_response,
    }
