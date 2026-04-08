"""Business registration and management."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid
from app.database import get_db

router = APIRouter()


class BusinessCreate(BaseModel):
    name: str
    category: str = "general"
    location: Optional[str] = None
    website: Optional[str] = None
    google_place_id: Optional[str] = None
    yelp_business_id: Optional[str] = None
    g2_product_slug: Optional[str] = None
    owner_email: Optional[str] = None
    response_tone: str = "professional"


@router.post("")
async def create_business(payload: BusinessCreate, db=Depends(get_db)):
    bid = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO businesses (id, name, category, location, website,
           google_place_id, yelp_business_id, g2_product_slug, owner_email, response_tone)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (bid, payload.name, payload.category, payload.location, payload.website,
         payload.google_place_id, payload.yelp_business_id, payload.g2_product_slug,
         payload.owner_email, payload.response_tone),
    )
    await db.commit()
    return {"id": bid, "name": payload.name}


@router.get("")
async def list_businesses(db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM businesses ORDER BY created_at DESC")
    return [dict(r) for r in await cursor.fetchall()]


@router.get("/{bid}")
async def get_business(bid: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM businesses WHERE id = ?", (bid,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Business not found")
    return dict(row)


@router.put("/{bid}/tone")
async def update_tone(bid: str, tone: str, db=Depends(get_db)):
    if tone not in ("professional", "friendly", "formal"):
        raise HTTPException(status_code=400, detail="tone must be professional, friendly, or formal")
    await db.execute("UPDATE businesses SET response_tone = ? WHERE id = ?", (tone, bid))
    await db.commit()
    return {"updated": True, "tone": tone}
