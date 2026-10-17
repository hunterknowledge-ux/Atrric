"""
report.picker — rule-based selection. TAK panggil LLM.
"""

from __future__ import annotations
from collections import defaultdict

TOP_QUOTES_N     = 5
ENTITY_CTX_N     = 5
ENTITY_EX_N      = 2
SLANG_RAW_N      = 15
TOPIC_BREAK_N    = 5
QUOTE_MAX_CHARS  = 220

# Senarai stopword Melayu standard (NLP practice)
MALAY_STOPWORDS = {
    "lah", "bang", "jer", "korang", "mmg", "pon", "sbb", "skrg", "mcm", 
    "ckp", "sgt", "dlm", "yg", "tak", "dgn", "tp", "ni", "tu", "je", 
    "kot", "kan", "nak", "dah", "x", "bagi", "pada", "ada", "aku", "kau", 
    "dia", "mereka", "kita", "kami", "kamu", "hahaha", "gila", "dorang"
}

SPAM_KEYWORDS = {
    "pinjaman", "whatsapp", "kripto", "crypto", "buy house", 
    "investment", "melabur", "scam", "click link", "klik link", "wa.me"
}

def _is_spam(text: str) -> bool:
    t_lower = text.lower()
    if len(text) > 300: return True
    if len(text) < 10: return True
    if any(kw in t_lower for kw in SPAM_KEYWORDS): return True
    if len(text) > 30:
        caps = sum(1 for c in text if c.isupper())
        if caps / len(text) > 0.5: return True
    return False

def _is_meaningful_slang(word: str) -> bool:
    w = word.lower().strip()
    if len(w) < 2: return False
    if w in MALAY_STOPWORDS: return False # Buang guna standard NLP stopwords
    if not any(v in w for v in "aeiou"): return False # Buang yang takde vokal (cth: sbb)
    return True

def pick_all(data: dict) -> dict:
    summary  = data.get("summary", {})
    comments = data.get("comments", [])
    
    src_counts = defaultdict(int)
    for c in comments:
        src_counts[c.get("source", "unknown")] += 1
    total_c = len(comments) or 1
    src_dist = ", ".join(
        f"{src} ({round(100.0*cnt/total_c, 1)}%)" 
        for src, cnt in sorted(src_counts.items(), key=lambda x: x[1], reverse=True)
    )

    # Tapis slang guna NLP standard filter
    raw_slang = summary.get("top_slang", [])
    clean_slang = [s for s in raw_slang if _is_meaningful_slang(s["word"])][:SLANG_RAW_N]

    return {
        "top_quotes":      pick_top_quotes(comments, n=TOP_QUOTES_N),
        "entity_context":  pick_entity_context(summary.get("top_entities", []), comments, n=ENTITY_CTX_N, ex=ENTITY_EX_N),
        "slang_raw":       clean_slang, 
        "topic_breakdown": pick_topic_breakdown(summary, comments, n=TOPIC_BREAK_N),
        "source_dist":     src_dist,
    }

def pick_top_quotes(comments: list[dict], n: int = 5) -> list[dict]:
    if not comments: return []
    candidates = [c for c in comments if c.get("text") and isinstance(c.get("sentiment_score"), (int, float)) and not _is_spam(c["text"])]
    candidates.sort(key=lambda c: abs(c.get("sentiment_score", 0.0)), reverse=True)

    picked, used_topics = [], set()
    for c in candidates:
        if len(picked) >= n: break
        topic = c.get("topic", "unknown")
        if topic in used_topics: continue
        picked.append(_quote_shape(c))
        used_topics.add(topic)

    if len(picked) < n:
        picked_ids = {q["id"] for q in picked}
        for c in candidates:
            if len(picked) >= n: break
            if c.get("id") in picked_ids: continue
            picked.append(_quote_shape(c))
    return picked

def _quote_shape(c: dict) -> dict:
    text = c.get("text", "").strip()
    if len(text) > QUOTE_MAX_CHARS: text = text[: QUOTE_MAX_CHARS - 1].rstrip() + "…"
    return {"id": c.get("id", ""), "text": text, "topic": c.get("topic", "unknown"), "sentiment": c.get("sentiment", "neutral"), "sentiment_score": float(c.get("sentiment_score", 0.0)), "entities": c.get("entities", [])[:5], "source": c.get("source", "")}

def pick_entity_context(top_entities: list[dict], comments: list[dict], n: int = 5, ex: int = 2) -> list[dict]:
    if not top_entities: return []
    idx = defaultdict(list)
    for c in comments:
        for e in c.get("entities", []): idx[e].append(c)

    out = []
    for entry in top_entities[:n]:
        name, count = entry.get("name", ""), entry.get("count", 0)
        if not name: continue
        
        # 1. Ambil semua quote yang sebut entiti ni & bukan spam
        pool = [c for c in idx.get(name, []) if not _is_spam(c.get("text", ""))]
        if not pool: continue

        # 2. Cari topik dominan untuk entiti ni (Contextual Matching)
        topic_counts = defaultdict(int)
        for c in pool:
            if c.get("topic"): topic_counts[c.get("topic")] += 1
        
        dominant_topic = None
        if topic_counts:
            dominant_topic = max(topic_counts.items(), key=lambda x: x[1])[0]
            # Tapis pool supaya ambil quote dari topik dominan sahaja
            filtered_pool = [c for c in pool if c.get("topic") == dominant_topic]
            if filtered_pool:
                pool = filtered_pool # Kalau ada, guna yang dah ditapis

        # 3. Sort ikut emosi paling kuat
        pool_sorted = sorted([c for c in pool if c.get("text")], key=lambda c: abs(c.get("sentiment_score", 0.0)), reverse=True)
        
        examples = []
        for c in pool_sorted[:ex]:
            t = c.get("text", "").strip()
            if len(t) > QUOTE_MAX_CHARS: t = t[: QUOTE_MAX_CHARS - 1].rstrip() + "…"
            examples.append(t)
            
        out.append({"name": name, "count": count, "examples": examples})
    return out

def pick_topic_breakdown(summary: dict, comments: list[dict], n: int = 5) -> list[dict]:
    by_topic = summary.get("by_topic", {})
    if not by_topic: return []
    total = sum(by_topic.values()) or 1
    top_topics = sorted(by_topic.items(), key=lambda kv: kv[1], reverse=True)[:n]
    stats = {t: {"pos": 0, "neg": 0, "neu": 0, "entities": defaultdict(int)} for t, _ in top_topics}
    for c in comments:
        t = c.get("topic")
        if t not in stats: continue
        s = c.get("sentiment", "neutral")
        if s == "positive": stats[t]["pos"] += 1
        elif s == "negative": stats[t]["neg"] += 1
        else: stats[t]["neu"] += 1
        for e in c.get("entities", []): stats[t]["entities"][e] += 1
    out = []
    for topic, count in top_topics:
        st = stats[topic]
        top_e = sorted(st["entities"].items(), key=lambda kv: kv[1], reverse=True)[:3]
        out.append({"topic": topic, "count": count, "pct": round(100.0 * count / total, 1), "sentiment": {"positive": st["pos"], "negative": st["neg"], "neutral": st["neu"]}, "top_entities": [name for name, _ in top_e]})
    return out