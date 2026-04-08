"""AI response generation and management."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.services.response_generator import generate_response

router = APIRouter()


class ApproveResponse(BaseModel):
    final_text: Optional[str] = None  # Override the draft, or use draft as-is


@router.post("/generate/{review_id}")
async def generate_review_response(review_id: str, db=Depends(get_db)):
    """Generate an AI response draft for a review."""
    cursor = await db.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    review = await cursor.fetchone()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    cursor = await db.execute("SELECT * FROM businesses WHERE id = ?", (review["business_id"],))
    business = await cursor.fetchone()

    review_dict = dict(review)
    business_dict = dict(business) if business else {"name": "Our Business", "response_tone": "professional"}

    result = await generate_response(review_dict, business_dict)

    # Upsert response
    cursor = await db.execute("SELECT id FROM review_responses WHERE review_id = ?", (review_id,))
    existing = await cursor.fetchone()

    if existing:
        await db.execute(
            "UPDATE review_responses SET draft_text = ?, ai_model = ?, status = 'draft' WHERE review_id = ?",
            (result["text"], result.get("model"), review_id)
        )
    else:
        response_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO review_responses (id, review_id, draft_text, ai_model) VALUES (?, ?, ?, ?)",
            (response_id, review_id, result["text"], result.get("model"))
        )
    await db.commit()

    return {
        "review_id": review_id,
        "draft": result["text"],
        "model": result.get("model"),
        "rating": review_dict["rating"],
        "author": review_dict.get("author_name"),
    }


@router.get("/{review_id}")
async def get_response(review_id: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM review_responses WHERE review_id = ?", (review_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No response draft found. Generate one first.")
    return dict(row)


@router.post("/{review_id}/approve")
async def approve_response(review_id: str, payload: ApproveResponse, db=Depends(get_db)):
    """Approve and optionally edit the response before marking as ready to publish."""
    cursor = await db.execute("SELECT * FROM review_responses WHERE review_id = ?", (review_id,))
    resp = await cursor.fetchone()
    if not resp:
        raise HTTPException(status_code=404, detail="No draft found")

    final = payload.final_text or resp["draft_text"]
    await db.execute(
        "UPDATE review_responses SET final_text = ?, status = 'approved' WHERE review_id = ?",
        (final, review_id)
    )
    await db.commit()
    return {"approved": True, "final_text": final}


@router.post("/{review_id}/publish")
async def mark_published(review_id: str, db=Depends(get_db)):
    """Mark the response as published (after posting manually or via platform API)."""
    await db.execute(
        "UPDATE review_responses SET status = 'published', published_at = ? WHERE review_id = ?",
        (datetime.utcnow().isoformat(), review_id)
    )
    await db.execute(
        "UPDATE reviews SET response_id = (SELECT id FROM review_responses WHERE review_id = ?) WHERE id = ?",
        (review_id, review_id)
    )
    await db.commit()
    return {"published": True, "published_at": datetime.utcnow().isoformat()}


@router.get("")
async def list_responses(business_id: str, status: str = None, db=Depends(get_db)):
    query = """SELECT rr.*, r.author_name, r.rating, r.platform, r.body
               FROM review_responses rr
               JOIN reviews r ON rr.review_id = r.id
               WHERE r.business_id = ?"""
    params = [business_id]
    if status:
        query += " AND rr.status = ?"; params.append(status)
    query += " ORDER BY rr.created_at DESC"
    cursor = await db.execute(query, params)
    return [dict(r) for r in await cursor.fetchall()]
