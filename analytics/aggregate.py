import json
from collections import Counter
from pathlib import Path
def _type(d): return "OP" if d == 0 else ("R" if d == 1 else "R:R")
def write(items, out_dir="analytics_out"):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    with (out/"comments.jsonl").open("w", encoding="utf-8") as f:
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
    s = {"total_comments": len(items), "by_type": dict(ty),
         "by_topic": dict(tc.most_common()),
         "by_sentiment": {"negative": sc.get("negative",0),
                          "neutral":  sc.get("neutral",0),
                          "positive": sc.get("positive",0)},
         "top_entities": [{"name":k,"count":v} for k,v in ec.most_common(20)],
         "top_slang":    [{"word":k,"count":v} for k,v in sl.most_common(20)]}
    (out/"summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    return s
