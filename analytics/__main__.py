import sys
import json
from pathlib import Path
from .loader import load_all
from .discover import run as discover
from .extract import one as extract_one
from .aggregate import write

CKPT = Path("analytics_out/_checkpoint.jsonl")
CKPT_INTERVAL = 20

def _load_ckpt():
    done = {}
    if CKPT.exists():
        for line in CKPT.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                done[r["id"]] = r
            except json.JSONDecodeError:
                continue
    return done

def _append_ckpt(rec):
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    with CKPT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def _reprocess(items):
    """Rebuild analytics_out/*.json from cached comments.jsonl + fresh loader."""
    ck = Path("analytics_out/comments.jsonl")
    existing = {}
    if ck.exists():
        for line in ck.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                existing[r["id"]] = r
            except json.JSONDecodeError:
                continue
    print(f"[analytics] reprocess: {len(existing)} existing records")
    merged = []
    for it in items:
        old = existing.get(it["id"])
        if old:
            it["topic"]           = old.get("topic")
            it["sentiment"]       = old.get("sentiment")
            it["sentiment_score"] = old.get("sentiment_score")
            it["entities"]        = old.get("entities") or []
            it["slang"]           = old.get("slang") or []
        merged.append(it)
    s = write(merged)
    print(json.dumps(s, ensure_ascii=False, indent=2))
    return s

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    items = load_all()
    print(f"[analytics] {len(items)} items loaded")

    if cmd == "discover":
        discover(items)
        return

    if cmd == "reprocess":
        _reprocess(items)
        return

    if cmd == "run":
        done = _load_ckpt()
        if done:
            print(f"[analytics] resume: {len(done)} done, "
                  f"{len(items) - len(done)} remaining")
        n = 0
        try:
            for n, it in enumerate(items, 1):
                if it["id"] in done:
                    it.update(done[it["id"]])
                    continue
                res = extract_one(it["text"])
                it.update(res)
                _append_ckpt({**it, **res})
                if n % CKPT_INTERVAL == 0:
                    print(f"  {n}/{len(items)}...")
        except KeyboardInterrupt:
            print(f"\n[analytics] interrupted at {n}/{len(items)} — progress saved")
            return
        s = write(items)
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return

    print("usage: python -m analytics [discover|run|reprocess]")

if __name__ == "__main__":
    main()