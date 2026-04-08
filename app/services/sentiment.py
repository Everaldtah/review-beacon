"""
Simple rule-based sentiment analysis.
Used when no AI key is configured.
"""

POSITIVE_KEYWORDS = [
    "excellent", "amazing", "fantastic", "wonderful", "great", "love", "loved",
    "best", "outstanding", "perfect", "awesome", "recommend", "highly", "brilliant",
    "superb", "exceptional", "impressive", "delightful", "pleasant", "satisfied",
    "helpful", "friendly", "fast", "easy", "intuitive", "smooth", "clean",
]

NEGATIVE_KEYWORDS = [
    "terrible", "awful", "horrible", "worst", "bad", "hate", "disgusting",
    "poor", "disappointing", "waste", "useless", "broken", "buggy", "slow",
    "frustrating", "annoying", "rude", "unprofessional", "overpriced", "scam",
    "never", "avoid", "incompetent", "unreliable", "crashed", "unusable",
]


def analyze_sentiment(text: str, rating: int) -> tuple[str, float]:
    """
    Returns (sentiment_label, score) where score is -1.0 to 1.0.
    """
    if not text:
        # Use rating alone
        if rating >= 4:
            return "positive", (rating - 3) / 2.0
        elif rating <= 2:
            return "negative", (rating - 3) / 2.0
        return "neutral", 0.0

    lower = text.lower()
    positive_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in lower)
    negative_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in lower)

    # Combine text sentiment with rating
    text_score = (positive_hits - negative_hits) / max(positive_hits + negative_hits, 1)
    rating_score = (rating - 3) / 2.0  # Maps 1–5 to -1.0–1.0

    combined = (text_score * 0.4) + (rating_score * 0.6)

    if combined > 0.2:
        label = "positive"
    elif combined < -0.2:
        label = "negative"
    else:
        label = "neutral"

    return label, round(combined, 3)
