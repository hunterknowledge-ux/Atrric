import sys, json
from .loader import load_all
from .discover import run as discover
from .extract import one as extract_one
from .aggregate import write
def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    items = load_all()
    print(f"[analytics] {len(items)} items loaded")
    if cmd == "discover":
        discover(items); return
    if cmd == "run":
        for n, it in enumerate(items, 1):
            if n % 10 == 0: print(f"  {n}/{len(items)}...")
            it.update(extract_one(it["text"]))
        s = write(items)
        print(json.dumps(s, ensure_ascii=False, indent=2)); return
    print("usage: python -m analytics [discover|run]")
if __name__ == "__main__": main()
