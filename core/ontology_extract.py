"""
core/ontology_extract.py

Extract values dari chunks guna schema yang discovered.
v3: Prompt explicit "don't force fill" + post-process filter.
"""

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
MAX_RETRIES = 3
DELAY = 0.5
TEST_SIZE = 20

# Post-process filters
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

Example input: "OP: Gen Z lemah, macam strawberi"
Example output: [{{"attribute": "topic", "value": "education"}}, {{"attribute": "target_group", "value": "gen z"}}, {{"attribute": "stance", "value": "critical"}}]
(Only 3 attrs — not 8)

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
                print(f"    [retry {attempt+1}] {type(e).__name__}, wait {wait}s")
                time.sleep(wait)
    return None


def _strip_fence(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return raw


def _clean_attributes(data, valid_attrs):
    """Post-process: buang nonsense, dedup, validate."""
    if not isinstance(data, list):
        return []

    clean = []
    seen = set()

    for item in data:
        if not isinstance(item, dict):
            continue

        attr = str(item.get("attribute", "")).strip().lower()
        val = str(item.get("value", "")).strip().lower()

        # Validate basic
        if not attr or not val:
            continue
        if len(val) > 50 or len(attr) > 30:
            continue

        # Filter blacklist
        if attr in BLACKLIST_ATTRS:
            continue
        if val in BLACKLIST_VALUES:
            continue

        # Validate attribute ada dalam schema
        if attr not in valid_attrs:
            continue

        # Filter: age tak boleh jadi "gen z"
        if attr == "age":
            if any(g in val for g in ["gen", "millennial", "alpha", "boomer"]):
                continue

        # Filter: role tak boleh jadi username
        if attr == "role" and val.startswith("@"):
            continue

        # Filter: generation mesti explicit
        if attr == "generation":
            valid_gens = ["gen z", "gen alpha", "millennial", "boomer", "gen x"]
            if not any(g in val for g in valid_gens):
                continue

        # Dedup
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
        return []

    raw = _strip_fence(raw)
    try:
        data = json.loads(raw)
        return _clean_attributes(data, set(attributes))
    except json.JSONDecodeError:
        return []


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
    print("=== ONTOLOGY EXTRACTION v3 ===\n")

    schema = load_schema()
    attributes = schema["attributes"]
    print(f"Schema: {attributes}\n")

    db = _get_db()
    with open(db.metadata_file) as f:
        meta = json.load(f)
    docs = meta.get("documents", {})

    chunks = []
    for chunk_id, doc in list(docs.items())[:TEST_SIZE]:
        text = doc.get("text", "").strip()
        if len(text) > 50:
            chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "source": doc.get("metadata", {}).get("source", "unknown"),
            })

    print(f"Extracting from {len(chunks)} chunks (test)...\n")

    llm = IlmuLLM()
    results = []
    total_attrs = 0

    for i, c in enumerate(chunks, 1):
        print(f"  [{i}/{len(chunks)}] {c['source']}...", end=" ", flush=True)
        attrs = extract_chunk(llm, c["text"], attributes, c["chunk_id"])
        total_attrs += len(attrs)
        results.append({
            "chunk_id": c["chunk_id"],
            "source": c["source"],
            "attributes": attrs,
        })
        print(f"{len(attrs)} attrs")
        time.sleep(DELAY)

    nodes, edges = build_graph(results)

    print(f"\n=== RESULT ===")
    print(f"Chunks: {len(chunks)}")
    print(f"Total attrs: {total_attrs}")
    print(f"Avg attrs/chunk: {total_attrs / len(chunks):.2f}")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")

    attr_dist = Counter()
    for item in results:
        for a in item["attributes"]:
            attr_dist[a["attribute"]] += 1
    print(f"\n=== DISTRIBUTION ===")
    for attr, count in attr_dist.most_common():
        print(f"  {attr}: {count} ({count/len(chunks)*100:.0f}%)")

    output = {
        "schema": attributes,
        "chunks_processed": len(chunks),
        "nodes": nodes,
        "edges": edges,
        "raw_results": results,
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved: {OUTPUT_FILE.name}")

    print(f"\n=== SAMPLE NODES ===")
    for n in nodes[:10]:
        print(f"  {n['id']} ({n['kind']})")


if __name__ == "__main__":
    main()