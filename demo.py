"""
Demo script — creates a business, ingests sample reviews, and generates response drafts.
Run: python demo.py (with server running)
"""

import asyncio
import httpx

BASE = "http://localhost:8000"

SAMPLE_REVIEWS = [
    {"author": "Emily R.", "rating": 5, "platform": "google",
     "body": "Absolutely amazing experience! The food was incredible and the staff were so warm and welcoming. Will definitely be back!"},
    {"author": "Tom K.", "rating": 2, "platform": "yelp",
     "body": "Very disappointing. Waited 45 minutes for cold pasta. The server barely checked on us."},
    {"author": "Maria L.", "rating": 4, "platform": "google",
     "body": "Great atmosphere and good food overall. The tiramisu was to die for! Service was a bit slow but the quality made up for it."},
    {"author": "James B.", "rating": 1, "platform": "yelp",
     "body": "Worst experience ever. Found a hair in my food and the manager was rude about it. Never returning."},
    {"author": "Sophie W.", "rating": 5, "platform": "g2",
     "body": "This product has completely transformed our workflow. Highly recommend to any team!"},
]


async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:
        print("=== Review Beacon Demo ===\n")

        # 1. Create business
        r = await client.post("/api/businesses", json={
            "name": "Bella Italia Restaurant",
            "category": "restaurant",
            "response_tone": "friendly"
        })
        biz = r.json()
        biz_id = biz["id"]
        print(f"Business created: {biz['name']} (ID: {biz_id})\n")

        # 2. Ingest reviews
        review_ids = []
        for rev in SAMPLE_REVIEWS:
            r = await client.post("/api/reviews/ingest", json={
                "business_id": biz_id,
                "platform": rev["platform"],
                "author_name": rev["author"],
                "rating": rev["rating"],
                "body": rev["body"],
            })
            result = r.json()
            stars = "★" * rev["rating"] + "☆" * (5 - rev["rating"])
            print(f"  {stars} [{rev['platform']}] {rev['author']} → {result['sentiment']}")
            review_ids.append(result["id"])

        # 3. Generate AI responses
        print("\n--- Generated Response Drafts ---\n")
        for review_id in review_ids:
            r = await client.post(f"/api/responses/generate/{review_id}")
            resp = r.json()
            stars = "★" * resp["rating"]
            print(f"[{stars}] {resp['author'] or 'Anonymous'}")
            print(f"  → {resp['draft'][:120]}...")
            print()

        # 4. Analytics
        r = await client.get(f"/api/analytics/{biz_id}?days=30")
        analytics = r.json()
        ov = analytics["overview"]
        print(f"--- Analytics ---")
        print(f"  Total reviews: {ov['total_reviews']} | Avg rating: {ov['avg_rating']:.1f}/5")
        print(f"  Positive: {ov['positive']} | Neutral: {ov['neutral']} | Negative: {ov['negative']}")
        print(f"  Response rate: {ov['response_rate']}%")
        print(f"  Needs response: {len(analytics['needs_response'])} review(s)")
        print(f"\nDone! Visit http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main())
