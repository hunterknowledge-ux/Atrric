"""
ingest.py — Incremental data ingestion untuk ATRRIC.

Guna:
    python ingest.py            # auto-detect + process
    python ingest.py --status   # tunjuk manifest
    python ingest.py --force    # re-process semua
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from core.chunk import chunk_text
from core.embed import embed, EmbedError
from core import store as vector_store

RAW_DIR = ROOT / "raw_data"
MANIFEST_PATH = RAW_DIR / ".manifest.json"


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"version": 1, "files": {}}


def save_manifest(m: dict):
    MANIFEST_PATH.write_text(json.dumps(m, indent=2, ensure_ascii=False))


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def scan_files() -> dict:
    out = {}
    for p in sorted(RAW_DIR.glob("*.txt")):
        out[p.name] = {"path": p, "hash": file_hash(p)}
    return out


def diff_files(manifest: dict, current: dict) -> dict:
    old = manifest.get("files", {})
    new = set(current) - set(old)
    changed = {k for k in current if k in old and current[k]["hash"] != old[k]["hash"]}
    removed = set(old) - set(current)
    skipped = set(current) - new - changed
    return {
        "new": sorted(new),
        "changed": sorted(changed),
        "removed": sorted(removed),
        "skipped": sorted(skipped),
    }


def process_file(name: str, path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embedded = 0
    for i, chunk in enumerate(chunks):
        try:
            vec = embed(chunk)
        except EmbedError as e:
            print(f"   [!] Embed fail chunk {i}: {e}")
            continue
        vector_store.add_chunk([], chunk, vec, source=name)
        embedded += 1
    return embedded


def main():
    force = "--force" in sys.argv
    status_only = "--status" in sys.argv

    manifest = load_manifest()
    current = scan_files()

    if status_only:
        print(f"Manifest: {MANIFEST_PATH}")
        print(f"Files tracked: {len(manifest.get('files', {}))}\n")
        for name, info in manifest.get("files", {}).items():
            print(f"  • {name} — {info.get('chunks', 0)} chunks @ {info.get('processed_at', '?')}")
        return

    if force:
        d = {"new": list(current), "changed": [], "removed": [], "skipped": []}
    else:
        d = diff_files(manifest, current)

    print(f"\n=== ATRRIC Ingest ===")
    print(f"Scan:  {RAW_DIR}")
    print(f"Found: {len(current)} file(s)\n")
    print(f"  New:     {len(d['new'])}")
    print(f"  Changed: {len(d['changed'])}")
    print(f"  Removed: {len(d['removed'])}")
    print(f"  Skipped: {len(d['skipped'])}\n")

    if not (d["new"] or d["changed"]):
        print("Tiada file baru/berubah. Done.")
        return

    to_process = d["new"] + d["changed"]
    total = 0
    for idx, name in enumerate(to_process, 1):
        path = current[name]["path"]
        size = path.stat().st_size
        print(f"[{idx}/{len(to_process)}] {name} ({size} bytes)")
        n = process_file(name, path)
        total += n
        manifest.setdefault("files", {})[name] = {
            "hash": current[name]["hash"],
            "chunks": n,
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }
        print(f"   → {n} chunks embedded\n")

    if d["removed"]:
        print(f"  {len(d['removed'])} file dah tiada dalam raw_data/:")
        for name in d["removed"]:
            print(f"    • {name}")
        print("   (Chunks lama masih dalam store — delete belum diimplementasi)\n")

    # Save store ke disk — KRITIKAL
    vector_store.save([])
    print(" Store saved to disk.\n")

    manifest["last_run"] = datetime.now().isoformat(timespec="seconds")
    save_manifest(manifest)
    print(f"✓ Done. {total} chunks diproses.")


if __name__ == "__main__":
    main()