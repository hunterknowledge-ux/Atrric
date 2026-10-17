from .store import load as load_discovered
from core.llm import generate_json

_SYS_CACHE = None

def _build_sys():
    global _SYS_CACHE
    if _SYS_CACHE is not None: return _SYS_CACHE
    topics = load_discovered("topics")
    if topics:
        topic_line = f"- topic: ONE from this list -> {', '.join(topics)}"
    else:
        topic_line = '- topic: short label (e.g. "education","economy")'
    _SYS_CACHE = f"""Analyze one Malaysian social media comment.
Return STRICT JSON with keys:
{topic_line}
- sentiment: "positive"|"negative"|"neutral"
- sentiment_score: float -1.0 to 1.0
- entities: list of proper nouns/brands/orgs/acronyms
- slang: list of colloquial/code words
Return ONLY JSON, no markdown."""
    return _SYS_CACHE

def one(text):
    try:
        d = generate_json(text[:800], system=_build_sys(), max_tokens=500, task="extract")
    except Exception as e:
        print(f"[extract] error: {e}")
        d = None
    if d is None:
        return {"topic": None, "sentiment": "neutral", "sentiment_score": 0.0,
                "entities": [], "slang": []}
    try: score = float(d.get("sentiment_score", 0.0))
    except: score = 0.0
    return {
        "topic": d.get("topic"),
        "sentiment": d.get("sentiment", "neutral"),
        "sentiment_score": score,
        "entities": d.get("entities") or [],
        "slang": d.get("slang") or [],
    }