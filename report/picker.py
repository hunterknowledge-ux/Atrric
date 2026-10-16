"""
report.picker — rule-based selection. TAK panggil LLM.

Tanggungjawab:
    - pilih top quotes (sentiment ekstrem + diversity)
    - kumpul entity context (contoh komen per entity)
    - kurasi slang (buang filler, kekalkan yang bermakna)
    - breakdown per topic (sentiment + entity dalam topic)

Output contract (pick_all):
    {
        "top_quotes":     [ {text, topic, sentiment, sentiment_score,
                             entities, source, id}, ... ],  # 5 items
        "entity_context": [ {name, count, examples: [str, str]}, ... ],
        "slang_curated":  [ {word, count, note}, ... ],
        "topic_breakdown":[ {topic, count, pct,
                             sentiment: {pos, neg, neu},
                             top_entities: [str, ...]}, ... ],
    }
"""

from __future__ import annotations

from collections import defaultdict


# --- Config: slang yang tak bermakna untuk report (shorthand/filler) ---
# Auto-discover tak sesuai sebab ni linguistik, bukan data-driven.
# Senang edit kalau developer nak tambah buang.
FILLER_SLANG: set[str] = {
    "ri", "sy", "utk", "sbb", "mng", "dh", "x",
    "nak", "lah", "la", "je", "kot", "kan", "pun",
    "tu", "ni", "yg", "dgn", "tp", "tapi", "kalo",
    "kalau", "dah", "tak", "xde", "xd", "nk",
    "bkn", "bukan", "sgt", "sangat", "mmg", "memang",
    "hah", "ha", "eh", "oh", "ah", "hmm", "hmmm",
}

# --- Config: berapa banyak setiap section ---
TOP_QUOTES_N     = 5
ENTITY_CTX_N     = 5      # top N entities untuk context
ENTITY_EX_N      = 2      # contoh komen per entity
SLANG_CURATED_N  = 8      # top N slang selepas filter
TOPIC_BREAK_N    = 5      # top N topic
QUOTE_MAX_CHARS  = 220    # truncate panjang quote


# --- Public API ---

def pick_all(data: dict) -> dict:
    """Entry point. Terima output load_all(). Return picked dict."""
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
        "slang_curated":   curate_slang(
                              summary.get("top_slang", []),
                              n=SLANG_CURATED_N,
                           ),
        "topic_breakdown": pick_topic_breakdown(
                              summary,
                              comments,
                              n=TOPIC_BREAK_N,
                           ),
    }


# --- Top quotes ---

def pick_top_quotes(comments: list[dict], n: int = 5) -> list[dict]:
    """Pilih quote impactful + diversity (elak 2 quote dari topic sama kalau boleh)."""
    if not comments:
        return []

    # Filter: mesti ada text, mesti ada sentiment_score
    candidates = [
        c for c in comments
        if c.get("text") and isinstance(c.get("sentiment_score"), (int, float))
    ]
    # Sort: paling ekstrem dulu (|score| besar)
    candidates.sort(
        key=lambda c: abs(c.get("sentiment_score", 0.0)),
        reverse=True,
    )

    picked: list[dict] = []
    used_topics: set[str] = set()

    # Pass 1: diversity — 1 per topic
    for c in candidates:
        if len(picked) >= n:
            break
        topic = c.get("topic", "unknown")
        if topic in used_topics:
            continue
        picked.append(_quote_shape(c))
        used_topics.add(topic)

    # Pass 2: top up kalau tak cukup (kadang topic terhad)
    if len(picked) < n:
        picked_ids = {q["id"] for q in picked}
        for c in candidates:
            if len(picked) >= n:
                break
            if c.get("id") in picked_ids:
                continue
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


# --- Entity context ---

def pick_entity_context(
    top_entities: list[dict],
    comments: list[dict],
    n: int = 5,
    ex: int = 2,
) -> list[dict]:
    """Untuk setiap top entity, cari contoh komen yang sebut entity tu."""
    if not top_entities:
        return []

    # Index: entity → list komen
    idx: dict[str, list[dict]] = defaultdict(list)
    for c in comments:
        for e in c.get("entities", []):
            idx[e].append(c)

    out: list[dict] = []
    for entry in top_entities[:n]:
        name = entry.get("name", "")
        count = entry.get("count", 0)
        if not name:
            continue

        # Ambil contoh: sort by |sentiment|, ambil `ex` teratas
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

        out.append({
            "name":     name,
            "count":    count,
            "examples": examples,
        })

    return out


# --- Slang curation ---

def curate_slang(top_slang: list[dict], n: int = 8) -> list[dict]:
    """Buang filler/shorthand. Kekalkan yang ada nilai budaya."""
    if not top_slang:
        return []

    out: list[dict] = []
    for entry in top_slang:
        word = (entry.get("word") or "").strip().lower()
        if not word or word in FILLER_SLANG:
            continue
        out.append({
            "word":  entry.get("word", ""),
            "count": entry.get("count", 0),
            "note":  _slang_note(word),
        })
        if len(out) >= n:
            break
    return out


# Nota pendek untuk slang tertentu. Fallback: "slanga Gen Z".
_SLANG_NOTES: dict[str, str] = {
    "ceplos":           "ceplos — gagal / tak lepas (slanga viral)",
    "sambung belajar":  "sambung belajar — teruskan pengajian ke peringkat lebih tinggi",
    "alhamdulillah":    "alhamdulillah — rasa syukur, biasa dalam komen positif",
    "confirm":          "confirm — pasti (bahasa rojak)",
    "toxic":            "toxic — suasana/tingkah negatif",
    "red flag":         "red flag — tanda bahaya dalam hubungan/situasi",
    "green flag":       "green flag — tanda positif",
    "healing":          "healing — proses pulih emosi",
    "self-care":        "self-care — jaga diri sendiri",
    "burnout":          "burnout — letih mental melampau",
}

def _slang_note(word: str) -> str:
    return _SLANG_NOTES.get(word, "slanga / istilah Gen Z")


# --- Topic breakdown ---

def pick_topic_breakdown(
    summary: dict,
    comments: list[dict],
    n: int = 5,
) -> list[dict]:
    """Untuk top N topic: kira sentiment + top entities dalam topic tu."""
    by_topic = summary.get("by_topic", {})
    if not by_topic:
        return []

    total = sum(by_topic.values()) or 1
    top_topics = sorted(by_topic.items(), key=lambda kv: kv[1], reverse=True)[:n]

    # Pre-index: topic → {pos, neg, neu, entity_counter}
    stats: dict[str, dict] = {
        t: {"pos": 0, "neg": 0, "neu": 0, "entities": defaultdict(int)}
        for t, _ in top_topics
    }

    for c in comments:
        t = c.get("topic")
        if t not in stats:
            continue
        s = c.get("sentiment", "neutral")
        if s == "positive":
            stats[t]["pos"] += 1
        elif s == "negative":
            stats[t]["neg"] += 1
        else:
            stats[t]["neu"] += 1
        for e in c.get("entities", []):
            stats[t]["entities"][e] += 1

    out: list[dict] = []
    for topic, count in top_topics:
        st = stats[topic]
        # Top 3 entities dalam topic ni
        top_e = sorted(
            st["entities"].items(), key=lambda kv: kv[1], reverse=True
        )[:3]
        out.append({
            "topic":        topic,
            "count":        count,
            "pct":          round(100.0 * count / total, 1),
            "sentiment": {
                "positive": st["pos"],
                "negative": st["neg"],
                "neutral":  st["neu"],
            },
            "top_entities": [name for name, _ in top_e],
        })
    return out


# --- CLI self-test (python -m report.picker) ---

if __name__ == "__main__":
    from report.loader import load_all
    import json

    data = load_all()
    picked = pick_all(data)
    print("=== PICKER SELF-TEST ===")
    print(f"top_quotes      : {len(picked['top_quotes'])}")
    print(f"entity_context  : {len(picked['entity_context'])}")
    print(f"slang_curated   : {len(picked['slang_curated'])}")
    print(f"topic_breakdown : {len(picked['topic_breakdown'])}")
    print()
    print("--- sample quote [0] ---")
    if picked["top_quotes"]:
        q = picked["top_quotes"][0]
        print(f"  topic     : {q['topic']}")
        print(f"  sentiment : {q['sentiment']} ({q['sentiment_score']:+.2f})")
        print(f"  text      : {q['text'][:120]}")
    print()
    print("--- slang curated ---")
    for s in picked["slang_curated"]:
        print(f"  {s['word']:<20} x{s['count']:<4} — {s['note']}")
    print()
    print("--- entity [0] ---")
    if picked["entity_context"]:
        e = picked["entity_context"][0]
        print(f"  {e['name']} ({e['count']}) — {len(e['examples'])} contoh")
    print()
    print("--- topic [0] ---")
    if picked["topic_breakdown"]:
        print(json.dumps(picked["topic_breakdown"][0], indent=2, ensure_ascii=False))