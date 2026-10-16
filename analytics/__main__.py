import sys, json
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
            if not line.strip(): continue
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

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    items = load_all()
    print(f"[analytics] {len(items)} items loaded")

    if cmd == "discover":
        discover(items); return

    if cmd == "run":
        done = _load_ckpt()
        if done:
            print(f"[analytics] resume: {len(done)} done, {len(items)-len(done)} remaining")
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

    print("usage: python -m analytics [discover|run]")

if __name__ == "__main__":
    main()