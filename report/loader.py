"""
report.loader — baca analytics_out/* → dict untuk Report layer.

Output contract (load_all):
    {
        "summary":  dict,           # raw summary.json
        "comments": list[dict],     # semua baris comments.jsonl
        "meta": {
            "loaded_at":    ISO str,
            "total_loaded": int,
            "sources":      list[str],   # sumber unik (dedup)
        }
    }
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

# --- Path resolution: guna config kalau ada, fallback relatif repo ---
try:
    from config import ANALYTICS_OUT  # type: ignore
    ANALYTICS_DIR = Path(ANALYTICS_OUT)
except Exception:
    ANALYTICS_DIR = Path(__file__).resolve().parent.parent / "analytics_out"

COMMENTS_FILE = ANALYTICS_DIR / "comments.jsonl"
SUMMARY_FILE = ANALYTICS_DIR / "summary.json"


# --- Public API ---

def load_all(limit: int | None = None) -> dict:
    """Baca summary + comments. Kalau `limit` diberi, ambil N komen pertama sahaja."""
    summary = load_summary()
    comments = load_comments(limit=limit)
    return {
        "summary": summary,
        "comments": comments,
        "meta": {
            "loaded_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "total_loaded": len(comments),
            "sources": _unique_sources(comments),
        },
    }


def load_summary() -> dict:
    if not SUMMARY_FILE.exists():
        raise FileNotFoundError(f"summary.json tak jumpa: {SUMMARY_FILE}")
    with SUMMARY_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_comments(limit: int | None = None) -> list[dict]:
    if not COMMENTS_FILE.exists():
        raise FileNotFoundError(f"comments.jsonl tak jumpa: {COMMENTS_FILE}")
    out: list[dict] = []
    with COMMENTS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # skip baris rosak, jangan crash seluruh pipeline
                continue
            if limit is not None and len(out) >= limit:
                break
    return out


# --- Internal ---

def _unique_sources(comments: list[dict]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for c in comments:
        s = c.get("source")
        if s and s not in seen:
            seen.add(s)
            result.append(s)
    return result


# --- CLI self-test (python -m report.loader) ---

if __name__ == "__main__":
    data = load_all()
    s = data["summary"]
    print("=== LOADER SELF-TEST ===")
    print(f"summary keys     : {list(s.keys())[:6]}")
    print(f"total_comments   : {s.get('total_comments')}")
    print(f"loaded comments  : {data['meta']['total_loaded']}")
    print(f"unique sources   : {data['meta']['sources']}")
    print(f"top entity [0]   : {s.get('top_entities', [{}])[0]}")
    print(f"top slang  [0]   : {s.get('top_slang', [{}])[0]}")
    first_id = data["comments"][0].get("id") if data["comments"] else "-"
    print(f"first comment id : {first_id}")