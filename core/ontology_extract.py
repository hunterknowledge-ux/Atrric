"""
core/ontology_extract.py

Extract values dari chunks guna schema discovered.
v4: Scale mode — process ALL chunks dengan resume + progress save.

Guna:
    python core/ontology_extract.py              # process semua, resume kalau ada
    python core/ontology_extract.py --reset      # start fresh
    python core/ontology_extract.py --limit 50   # process 50 je (test)
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from collections import Counter

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.env_loader import load_env
load_env()

from core.ilmu_llm import IlmuLLM
from core.store import _get_db


SCHEMA_FILE = _ROOT / "core" / "ontology_schema.json"
OUTPUT_FILE = _ROOT / "ontology_graph.json"
PROGRESS_FILE = _ROOT / "ontology_extract_progress.jsonl"  # append-only

MAX_RETRIES = 3
DELAY = 0.5

BLACKLIST_VALUES = {"not stated", "unknown", "n/a", "none", "null", "", "-"}
BLACKLIST_ATTRS = {"attribute", "value", "type", "key"}


def load_schema():
    return json.loads(SCHEMA_FILE.read_text())


EXTRACT_PROMPT = """Analyze this Malaysian social media comment and extract ONLY the attributes that are CLEARLY present.

AVAILABLE ATTRIBUTES: {attributes}

Output format (JSON list):
[{{"attribute": "...", "value": "..."}}, ...]

CRITICAL RULES:
1. If a comment discusses only 2-3 things, output ONLY 2-3 attributes
2. DO NOT force all 8 attributes — better fewer & accurate than many & wrong
3. If comment is short/joke like "haha", "thanks", output []
4. If attribute is not clearly stated, SKIP it — DON'T guess

ATTRIBUTE DEFINITIONS:
- age: number range (e.g. "20s", "18-25", "13yo") — NOT generation name
- emotion: emotional tone (frustrated, angry, sad, happy, sarcastic)
- generation: generation name only (Gen Z, Millennials, Gen Alpha, Boomer)
- role: author role (op, replier, commenter) — NOT username
- stance: position (agree, disagree, critical, support, neutral)
- target_group: who is discussed (parents, teachers, government, students)
- tone: communication style (sarcastic, formal, casual, emotional)
- topic: subject (education, economy, politics, social_media)

Example: "OP: Gen Z lemah, macam strawberi"
Output: [{{"attribute": "topic", "value": "education"}}, {{"attribute": "target_group", "value": "gen z"}}, {{"attribute": "stance", "value": "critical"}}]

Comment:
{chunk}

Output (JSON only):"""


def _safe_generate(llm, prompt, chunk_id):
    for attempt in range(MAX_RETRIES):
        try:
            return llm.generate(prompt, max_tokens=600, temperature=0.2)
        except Exception as e:
            wait = 2 ** attempt
            if attempt < MAX_RETRIES - 1:
                print(f"[retry {attempt+1}] {type(e).__name__}, wait {wait}s")
                time.sleep(wait)
    return None


def _strip_fence(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return raw


def _clean_attributes(data, valid_attrs):
    if not isinstance(data, list):
        return []

    clean = []
    seen = set()

    for item in data:
        if not isinstance(item, dict):
            continue
        attr = str(item.get("attribute", "")).strip().lower()
        val = str(item.get("value", "")).strip().lower()

        if not attr or not val or len(val) > 50 or len(attr) > 30:
            continue
        if attr in BLACKLIST_ATTRS or val in BLACKLIST_VALUES:
            continue
        if attr not in valid_attrs:
            continue

        if attr == "age" and any(g in val for g in ["gen", "millennial", "alpha", "boomer"]):
            continue
        if attr == "role" and val.startswith("@"):
            continue
        if attr == "generation":
            if not any(g in val for g in ["gen z", "gen alpha", "millennial", "boomer", "gen x"]):
                continue

        key = (attr, val)
        if key in seen:
            continue
        seen.add(key)
        clean.append({"attribute": attr, "value": val})

    return clean


def extract_chunk(llm, chunk, attributes, chunk_id):
    prompt = EXTRACT_PROMPT.format(
        attributes=", ".join(attributes),
        chunk=chunk[:600],
    )
    raw = _safe_generate(llm, prompt, chunk_id)
    if raw is None:
        return None  # null = fail (retry later)

    raw = _strip_fence(raw)
    try:
        data = json.loads(raw)
        return _clean_attributes(data, set(attributes))
    except json.JSONDecodeError:
        return None  # null = fail


def load_all_chunks():
    db = _get_db()
    with open(db.metadata_file) as f:
        meta = json.load(f)
    docs = meta.get("documents", {})
    chunks = []
    for chunk_id, doc in docs.items():
        text = doc.get("text", "").strip()
        if len(text) > 50:
            chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "source": doc.get("metadata", {}).get("source", "unknown"),
            })
    return chunks


def load_progress():
    """Baca progress — return dict {chunk_id: result}."""
    if not PROGRESS_FILE.exists():
        return {}
    done = {}
    with PROGRESS_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if r.get("status") == "ok":
                    done[r["chunk_id"]] = r
            except json.JSONDecodeError:
                continue
    return done


def save_progress(record):
    """Append 1 record ke progress file."""
    with PROGRESS_FILE.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_graph(results):
    nodes = {}
    edges = []

    for item in results:
        chunk_id = item["chunk_id"]
        chunk_node_id = f"chunk_{chunk_id}"
        nodes[chunk_node_id] = {
            "id": chunk_node_id,
            "label": f"Chunk {chunk_id[:8]}",
            "kind": "chunk",
        }

        for attr_pair in item["attributes"]:
            attr = attr_pair["attribute"]
            val = attr_pair["value"]
            val_node_id = f"{attr}:{val}"
            nodes[val_node_id] = {
                "id": val_node_id,
                "label": val,
                "kind": attr,
            }
            edges.append({
                "subject": chunk_node_id,
                "predicate": f"has_{attr}",
                "object": val_node_id,
            })

    return list(nodes.values()), edges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Start fresh, buang progress")
    parser.add_argument("--limit", type=int, default=None, help="Process N chunks je")
    args = parser.parse_args()

    if args.reset:
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink()
        print("Reset: progress + output dibuang\n")

    print("=== ONTOLOGY EXTRACTION v4 (scale) ===\n")

    schema = load_schema()
    attributes = schema["attributes"]
    print(f"Schema: {attributes}\n")

    all_chunks = load_all_chunks()
    if args.limit:
        all_chunks = all_chunks[:args.limit]
    print(f"Total chunks: {len(all_chunks)}")

    # Resume
    done = load_progress()
    if done:
        print(f"Resume: {len(done)} chunks dah siap, skip")

    pending = [c for c in all_chunks if c["chunk_id"] not in done]
    print(f"Pending: {len(pending)}\n")

    if not pending:
        print("Semua chunks dah process. Selesai.")
    else:
        # Estimate cost
        est_cost = len(pending) * 0.001
        est_min = len(pending) * 6 / 60
        print(f"Est. cost: ~RM{est_cost:.2f}")
        print(f"Est. masa: ~{est_min:.0f} minit\n")
        print("Tekan Ctrl+C bila-bila untuk stop (progress saved)\n")

        llm = IlmuLLM()
        fails = 0
        start = time.time()

        try:
            for i, c in enumerate(pending, 1):
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(pending) - i) / rate if rate > 0 else 0

                print(f"[{i}/{len(pending)}] eta={eta:.0f}s | {c['source'][:20]}...", end=" ", flush=True)

                attrs = extract_chunk(llm, c["text"], attributes, c["chunk_id"])

                if attrs is None:
                    fails += 1
                    print("FAIL")
                    save_progress({
                        "chunk_id": c["chunk_id"],
                        "source": c["source"],
                        "status": "fail",
                    })
                else:
                    print(f"{len(attrs)} attrs")
                    save_progress({
                        "chunk_id": c["chunk_id"],
                        "source": c["source"],
                        "status": "ok",
                        "attributes": attrs,
                    })

                time.sleep(DELAY)

        except KeyboardInterrupt:
            print("\n\n[!] Stopped. Progress saved.")
            print(f"    Run semula untuk resume.")

    # Build final graph dari semua progress
    print("\n=== BUILDING GRAPH ===")
    done = load_progress()
    results = list(done.values())

    nodes, edges = build_graph(results)

    print(f"Chunks processed: {len(results)}/{len(all_chunks)}")
    total_attrs = sum(len(r.get("attributes", [])) for r in results)
    print(f"Total attrs: {total_attrs}")
    if results:
        print(f"Avg attrs/chunk: {total_attrs / len(results):.2f}")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")

    attr_dist = Counter()
    for r in results:
        for a in r.get("attributes", []):
            attr_dist[a["attribute"]] += 1
    print(f"\n=== DISTRIBUTION ===")
    for attr, count in attr_dist.most_common():
        pct = count / len(results) * 100 if results else 0
        print(f"  {attr}: {count} ({pct:.0f}%)")

    output = {
        "schema": attributes,
        "chunks_processed": len(results),
        "chunks_total": len(all_chunks),
        "nodes": nodes,
        "edges": edges,
        "raw_results": results,
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved: {OUTPUT_FILE.name}")


if __name__ == "__main__":
    main()