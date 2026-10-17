import json
import re
from collections import Counter
from pathlib import Path

_ALNUM = re.compile(r"[A-Za-z]")
_DIR = Path(__file__).parent

_MASTER_SLANG = set()
_sp = _DIR / "discovered" / "slang.json"
if _sp.exists():
    _MASTER_SLANG = {w.lower() for w in json.loads(_sp.read_text(encoding="utf-8"))}

def _type(d):
    return "OP" if d == 0 else ("R" if d == 1 else "R:R")

def _norm_entity(x):
    if not isinstance(x, str): return None
    x = x.strip()
    if not x or len(x) < 2: return None
    if " " in x: return x
    if x.isupper() and len(x) <= 8: return x
    if len(x) <= 6: return x.upper()
    return x.lower()

def _clean_slang(x):
    if not isinstance(x, str): return None
    x = x.strip()
    if not x or not _ALNUM.search(x): return None
    x = x.lower()
    if _MASTER_SLANG and x not in _MASTER_SLANG: return None
    return x

def write(items, out_dir="analytics_out"):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    for i in items:
        seen = set(); clean_e = []
        for e in (i.get("entities") or []):
            n = _norm_entity(e)
            if n and n not in seen: seen.add(n); clean_e.append(n)
        i["entities"] = clean_e

        seen = set(); clean_s = []
        for s in (i.get("slang") or []):
            n = _clean_slang(s)
            if n and n not in seen: seen.add(n); clean_s.append(n)
        i["slang"] = clean_s

    with (out / "comments.jsonl").open("w", encoding="utf-8") as f:
        for i in items:
            f.write(json.dumps({
                "id": i["id"], "source": i["source"], "type": _type(i["depth"]),
                "text": i["text"], "topic": i.get("topic"),
                "sentiment": i.get("sentiment"),
                "sentiment_score": i.get("sentiment_score"),
                "entities": i.get("entities", []), "slang": i.get("slang", []),
            }, ensure_ascii=False) + "\n")

    tc = Counter(i["topic"] for i in items if i.get("topic"))
    sc = Counter(i["sentiment"] for i in items)
    ec = Counter(e for i in items for e in i.get("entities", []))
    sl = Counter(w for i in items for w in i.get("slang", []))
    ty = Counter(_type(i["depth"]) for i in items)

    s = {
        "total_comments": len(items),
        "by_type": dict(ty),
        "by_topic": dict(tc.most_common()),
        "by_sentiment": {"negative": sc.get("negative",0), "neutral": sc.get("neutral",0), "positive": sc.get("positive",0)},
        "top_entities": [{"name":k,"count":v} for k,v in ec.most_common(20)],
        "top_slang":    [{"word":k,"count":v} for k,v in sl.most_common(20)],
    }
    (out / "summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    return s