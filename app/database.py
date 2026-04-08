"""Database setup."""

import aiosqlite
import os

DB_PATH = os.getenv("DATABASE_URL", "review_beacon.db")


async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS businesses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                location TEXT,
                website TEXT,
                google_place_id TEXT,
                yelp_business_id TEXT,
                g2_product_slug TEXT,
                owner_email TEXT,
                response_tone TEXT DEFAULT 'professional',  -- professional | friendly | formal
                auto_draft INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                platform TEXT NOT NULL,  -- google | yelp | g2 | tripadvisor | manual
                external_id TEXT,
                author_name TEXT,
                author_photo TEXT,
                rating INTEGER NOT NULL,  -- 1-5
                title TEXT,
                body TEXT,
                reviewed_at TEXT,
                sentiment TEXT DEFAULT 'neutral',  -- positive | neutral | negative
                sentiment_score REAL DEFAULT 0,
                response_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(platform, external_id)
            );

            CREATE TABLE IF NOT EXISTS review_responses (
                id TEXT PRIMARY KEY,
                review_id TEXT NOT NULL UNIQUE,
                draft_text TEXT NOT NULL,
                final_text TEXT,
                status TEXT DEFAULT 'draft',  -- draft | approved | published | skipped
                ai_model TEXT,
                published_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (review_id) REFERENCES reviews(id)
            );

            CREATE TABLE IF NOT EXISTS sentiment_daily (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                date TEXT NOT NULL,
                avg_rating REAL,
                review_count INTEGER DEFAULT 0,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                neutral_count INTEGER DEFAULT 0,
                UNIQUE(business_id, date)
            );
        """)
        await db.commit()
