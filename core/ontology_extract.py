"""
core/ontology_extract.py

Extract values dari chunks guna schema yang discovered.
v2: Better prompt — skip if unsure, explicit rules untuk age/role.
"""

import json
import re
import sys
import time
from pathlib import Path

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


def load_schema():
    return json.loads(SCHEMA_FILE.read_text())


EXTRACT_PROMPT = """Extract values for these attributes from the comment.

ATTRIBUTES: {attributes}

Output a JSON list:
[{{"attribute": "...", "value": "..."}}, ...]

RULES:
- Only use attributes from the list above
- ONLY extract if value is CLEARLY stated in text
- If not clearly stated, SKIP that attribute — DON'T guess
- age = number range (e.g. "20s", "18-25"), NOT generation name
- role = author role (e.g. "op", "replier"), NOT username
- generation = generation name (Gen Z, Millennials, Alpha)
- topic = subject being discussed (1-3 words)
- emotion = emotional tone (frustrated, angry, sad, etc)
- stance = position taken (agree, disagree, critical, etc)
- target_group = who is being discussed (parents, teachers, etc)
- tone = communication style (sarcastic, formal, casual, etc)
- value: short, 1-5 words, lowercase
- No explanation. JSON only.

Comment:
{chunk}

Output:"""


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
        if isinstance(data, list):
            # Validate — buang value nonsense
            clean = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                attr = str(item.get("attribute", "")).strip().lower()
                val = str(item.get("value", "")).strip().lower()
                if not attr or not val or len(val) > 50:
                    continue
                # Filter: age tak boleh jadi "gen z"
                if attr == "age" and any(
                    g in val for g in ["gen", "millennial", "alpha", "boomer"]
                ):
                    continue
                # Filter: role tak boleh jadi username
                if attr == "role" and val.startswith("@"):
                    continue
                clean.append({"attribute": attr, "value": val})
            return clean
    except json.JSONDecodeError:
        pass
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
    print("=== ONTOLOGY EXTRACTION v2 ===\n")

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
    print(f"Chunks processed: {len(chunks)}")
    print(f"Total attributes: {total_attrs}")
    print(f"Avg attrs/chunk:  {total_attrs / len(chunks):.1f}")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")

    # Attribute distribution
    from collections import Counter
    attr_dist = Counter()
    for item in results:
        for a in item["attributes"]:
            attr_dist[a["attribute"]] += 1
    print(f"\n=== ATTRIBUTE DISTRIBUTION ===")
    for attr, count in attr_dist.most_common():
        print(f"  {attr}: {count}")

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
    for n in nodes[:8]:
        print(f"  {n['id']} ({n['kind']})")


if __name__ == "__main__":
    main()