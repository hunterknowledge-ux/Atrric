"""
report.picker — rule-based selection. TAK panggil LLM.

Tanggungjawab:
    - pilih top quotes (sentiment ekstrem + diversity)
    - kumpul entity context (contoh komen per entity)
    - hantar slang mentah (LLM akan tapis secara organik)
    - breakdown per topic (sentiment + entity dalam topic)
"""

from __future__ import annotations

from collections import defaultdict


TOP_QUOTES_N     = 5
ENTITY_CTX_N     = 5
ENTITY_EX_N      = 2
SLANG_RAW_N      = 15     # Hantar top 15 ke LLM untuk ditapis
TOPIC_BREAK_N    = 5
QUOTE_MAX_CHARS  = 220

def pick_all(data: dict) -> dict:
    summary  = data.get("summary", {})
    comments = data.get("comments", [])
    return {
        "top_quotes":      pick_top_quotes(comments, n=TOP_QUOTES_N),
        "entity_context":  pick_entity_context(
                              summary.get("top_entities", []),
                              comments,
                              n=ENTITY_CTX_N,
                              ex=ENTITY_EX_N,
                           ),
        # Hantar 15 slang mentah. LLM akan tapis dalam generate.py
        "slang_raw":       summary.get("top_slang", [])[:SLANG_RAW_N],
        "topic_breakdown": pick_topic_breakdown(
                              summary,
                              comments,
                              n=TOPIC_BREAK_N,
                           ),
    }

def pick_top_quotes(comments: list[dict], n: int = 5) -> list[dict]:
    if not comments: return []
    candidates = [
        c for c in comments
        if c.get("text") and isinstance(c.get("sentiment_score"), (int, float))
    ]
    candidates.sort(key=lambda c: abs(c.get("sentiment_score", 0.0)), reverse=True)

    picked: list[dict] = []
    used_topics: set[str] = set()

    for c in candidates:
        if len(picked) >= n: break
        topic = c.get("topic", "unknown")
        if topic in used_topics: continue
        picked.append(_quote_shape(c))
        used_topics.add(topic)

    if len(picked) < n:
        picked_ids = {q["id"] for q in picked}
        for c in candidates:
            if len(c) >= n: break
            if c.get("id") in picked_ids: continue
            picked.append(_quote_shape(c))
    return picked

def _quote_shape(c: dict) -> dict:
    text = c.get("text", "").strip()
    if len(text) > QUOTE_MAX_CHARS:
        text = text[: QUOTE_MAX_CHARS - 1].rstrip() + "…"
    return {
        "id":              c.get("id", ""),
        "text":            text,
        "topic":           c.get("topic", "unknown"),
        "sentiment":       c.get("sentiment", "neutral"),
        "sentiment_score": float(c.get("sentiment_score", 0.0)),
        "entities":        c.get("entities", [])[:5],
        "source":          c.get("source", ""),
    }

def pick_entity_context(top_entities: list[dict], comments: list[dict], n: int = 5, ex: int = 2) -> list[dict]:
    if not top_entities: return []
    idx: dict[str, list[dict]] = defaultdict(list)
    for c in comments:
        for e in c.get("entities", []):
            idx[e].append(c)

    out: list[dict] = []
    for entry in top_entities[:n]:
        name = entry.get("name", "")
        count = entry.get("count", 0)
        if not name: continue

        pool = idx.get(name, [])
        pool_sorted = sorted(
            [c for c in pool if c.get("text")],
            key=lambda c: abs(c.get("sentiment_score", 0.0)),
            reverse=True,
        )

        examples: list[str] = []
        for c in pool_sorted[:ex]:
            t = c.get("text", "").strip()
            if len(t) > QUOTE_MAX_CHARS:
                t = t[: QUOTE_MAX_CHARS - 1].rstrip() + "…"
            examples.append(t)

        out.append({"name": name, "count": count, "examples": examples})
    return out

def pick_topic_breakdown(summary: dict, comments: list[dict], n: int = 5) -> list[dict]:
    by_topic = summary.get("by_topic", {})
    if not by_topic: return []

    total = sum(by_topic.values()) or 1
    top_topics = sorted(by_topic.items(), key=lambda kv: kv[1], reverse=True)[:n]

    stats: dict[str, dict] = {
        t: {"pos": 0, "neg": 0, "neu": 0, "entities": defaultdict(int)}
        for t, _ in top_topics
    }

    for c in comments:
        t = c.get("topic")
        if t not in stats: continue
        s = c.get("sentiment", "neutral")
        if s == "positive": stats[t]["pos"] += 1
        elif s == "negative": stats[t]["neg"] += 1
        else: stats[t]["neu"] += 1
        for e in c.get("entities", []):
            stats[t]["entities"][e] += 1

    out: list[dict] = []
    for topic, count in top_topics:
        st = stats[topic]
        top_e = sorted(st["entities"].items(), key=lambda kv: kv[1], reverse=True)[:3]
        out.append({
            "topic": topic,
            "count": count,
            "pct": round(100.0 * count / total, 1),
            "sentiment": {"positive": st["pos"], "negative": st["neg"], "neutral": st["neu"]},
            "top_entities": [name for name, _ in top_e],
        })
    return out