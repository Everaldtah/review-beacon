"""
AI-powered review response generator.
Generates personalized, on-brand responses to customer reviews.
Falls back to template responses when no AI key is available.
"""

import os
from typing import Dict, Any

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


async def generate_response(review: Dict, business: Dict) -> Dict[str, str]:
    """Generate a response draft for a review."""

    if ANTHROPIC_API_KEY:
        return await _generate_with_anthropic(review, business)
    elif OPENAI_API_KEY:
        return await _generate_with_openai(review, business)
    else:
        return _generate_template(review, business)


async def _generate_with_anthropic(review: Dict, business: Dict) -> Dict[str, str]:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        tone = business.get("response_tone", "professional")
        rating = review.get("rating", 3)
        sentiment = "positive" if rating >= 4 else "negative" if rating <= 2 else "mixed"

        prompt = f"""You are responding to a customer review on behalf of {business['name']}.

Review details:
- Platform: {review.get('platform', 'online')}
- Rating: {rating}/5 stars
- Author: {review.get('author_name', 'A customer')}
- Review: {review.get('body', review.get('title', 'No text provided'))}

Business context:
- Business name: {business['name']}
- Category: {business.get('category', 'business')}
- Response tone: {tone}

Write a {tone} response that:
1. Thanks the reviewer by name if provided
2. {"Acknowledges their positive experience and reinforces it" if sentiment == "positive" else "Acknowledges their concerns sincerely and offers to make it right" if sentiment == "negative" else "Acknowledges both positive and negative aspects"}
3. Keeps it concise (2–4 sentences)
4. Ends with an invitation to return or contact directly
5. Does NOT use generic corporate language or excessive exclamation points
6. Reflects a real human writing, not a bot

Only output the response text, nothing else."""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"text": message.content[0].text, "model": "claude-3-haiku"}
    except Exception as e:
        return _generate_template(review, business)


async def _generate_with_openai(review: Dict, business: Dict) -> Dict[str, str]:
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        rating = review.get("rating", 3)
        sentiment = "positive" if rating >= 4 else "negative" if rating <= 2 else "mixed"
        tone = business.get("response_tone", "professional")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You write {tone} review responses for {business['name']}."},
                {"role": "user", "content": f"Respond to this {sentiment} {rating}/5 review by {review.get('author_name', 'a customer')}: {review.get('body', review.get('title', ''))}"}
            ],
            max_tokens=200,
        )
        return {"text": response.choices[0].message.content, "model": "gpt-3.5-turbo"}
    except Exception:
        return _generate_template(review, business)


def _generate_template(review: Dict, business: Dict) -> Dict[str, str]:
    """Template-based response when no AI key is configured."""
    rating = review.get("rating", 3)
    author = review.get("author_name") or "there"
    name = business.get("name", "our business")
    tone = business.get("response_tone", "professional")

    first_name = author.split()[0] if author and author != "there" else author

    if rating >= 4:
        templates = [
            f"Thank you so much for your kind words, {first_name}! We're thrilled to hear you had such a great experience at {name}. Your feedback means the world to our team, and we look forward to welcoming you back soon.",
            f"Hi {first_name}, thank you for taking the time to share your experience! It's wonderful to know we hit the mark for you. We hope to see you again at {name} very soon!",
        ]
    elif rating <= 2:
        templates = [
            f"Hi {first_name}, thank you for sharing your feedback — I'm genuinely sorry your experience didn't meet our standards. This is not the level of service we strive to provide. Please reach out to us directly so we can make this right.",
            f"Thank you for your honest feedback, {first_name}. I'm sorry to hear about your experience and take this seriously. We'd love the chance to address your concerns directly — please contact us so we can resolve this.",
        ]
    else:
        templates = [
            f"Hi {first_name}, thank you for your review! We're glad to hear some aspects of your visit worked well. We always strive to do better, and your feedback helps us improve. We hope to see you again at {name}!",
        ]

    import random
    return {"text": random.choice(templates), "model": "template"}
