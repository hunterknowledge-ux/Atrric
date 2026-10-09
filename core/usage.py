"""Cost tracking untuk ILMU API calls.

Log file: logs/ilmu_usage.jsonl (gitignored).
Setiap line = 1 JSON record untuk 1 call.

PRICING hardcoded untuk ILMU Mini v3.3.
Kalau tukar model, update PRICE_INPUT / PRICE_OUTPUT di bawah.
"""

import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "ilmu_usage.jsonl"

# ILMU Mini v3.3 — RM per 1M tokens
# (update kalau tukar model)
PRICE_INPUT = 0.20 / 1_000_000
PRICE_OUTPUT = 1.20 / 1_000_000


def log_call(model: str, usage: dict, label: str = ""):
    """Append satu call ke log file."""
    LOG_DIR.mkdir(exist_ok=True)

    inp = usage.get("prompt_tokens", 0)
    out = usage.get("completion_tokens", 0)

    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "input": inp,
        "output": out,
        "cost_rm": round(inp * PRICE_INPUT + out * PRICE_OUTPUT, 8),
        "label": label,
    }

    with LOG_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")


def read_log():
    """Yield setiap record dari log."""
    if not LOG_FILE.exists():
        return
    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def report(days: int = None):
    """Print summary. days=None → semua."""
    from datetime import timedelta

    cutoff = None
    if days:
        cutoff = datetime.now() - timedelta(days=days)

    total_calls = 0
    total_in = 0
    total_out = 0
    total_cost = 0.0
    by_label = {}

    for r in read_log():
        if cutoff:
            try:
                ts = datetime.fromisoformat(r["ts"])
                if ts < cutoff:
                    continue
            except (KeyError, ValueError):
                pass

        total_calls += 1
        total_in += r.get("input", 0)
        total_out += r.get("output", 0)
        total_cost += r.get("cost_rm", 0.0)

        lbl = r.get("label", "") or "(unlabeled)"
        by_label.setdefault(lbl, {"calls": 0, "cost": 0.0})
        by_label[lbl]["calls"] += 1
        by_label[lbl]["cost"] += r.get("cost_rm", 0.0)

    print(f"=== ILMU Usage Report ===")
    print(f"Period: {'last ' + str(days) + ' days' if days else 'all time'}")
    print()
    print(f"Total calls:    {total_calls}")
    print(f"Total input:    {total_in:,} tokens")
    print(f"Total output:   {total_out:,} tokens")
    print(f"Total cost:     RM{total_cost:.6f}")
    print()

    if by_label:
        print("By label:")
        for lbl, v in sorted(by_label.items(), key=lambda x: -x[1]["cost"]):
            print(f"  {lbl:20s} {v['calls']:5d} calls  RM{v['cost']:.6f}")


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else None
    report(days)