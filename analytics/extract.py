from core.llm import generate_json

SYS = """Analyze one Malaysian social media comment.
Return STRICT JSON with keys:
- topic: short label (e.g. "education","economy","social","gov_service")
- sentiment: "positive"|"negative"|"neutral"
- sentiment_score: float -1.0 to 1.0
- entities: list of proper nouns/brands/orgs/acronyms mentioned
- slang: list of colloquial/code words used
Return ONLY JSON, no markdown."""

def one(text):
    d = generate_json(text[:800], system=SYS, max_tokens=500)
    if d is None:
        return {"topic": None, "sentiment": "neutral", "sentiment_score": 0.0,
                "entities": [], "slang": []}
    return {
        "topic": d.get("topic"),
        "sentiment": d.get("sentiment", "neutral"),
        "sentiment_score": float(d.get("sentiment_score", 0.0)),
        "entities": d.get("entities") or [],
        "slang": d.get("slang") or [],
    }
