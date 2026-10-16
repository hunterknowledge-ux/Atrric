"""
core/ontology_extract.py

Extract values dari chunks guna schema yang discovered.
Output: nodes + edges untuk OmniFuse InMemoryGraph.
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


def load_schema():
    return json.loads(SCHEMA_FILE.read_text())


EXTRACT_PROMPT = """Extract values for these attributes from the comment.

ATTRIBUTES: {attributes}

Output a JSON list:
[{{"attribute": "...", "value": "..."}}, ...]

Rules:
- Only use attributes from the list above
- Value: short, 1-5 words
- Skip attribute if not clearly present
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
            return data
    except json.JSONDecodeError:
        pass
    return []


def build_graph(results):
    """Convert extraction results → nodes + edges."""
    nodes = {}   # id -> {label, kind}
    edges = []   # {subject, predicate, object}
    
    for item in results:
        chunk_id = item["chunk_id"]
        source = item["source"]
        
        # Chunk node
        chunk_node_id = f"chunk_{chunk_id}"
        nodes[chunk_node_id] = {
            "id": chunk_node_id,
            "label": f"Chunk {chunk_id}",
            "kind": "chunk",
        }
        
        for attr_pair in item["attributes"]:
            attr = attr_pair.get("attribute", "").strip().lower()
            val = str(attr_pair.get("value", "")).strip().lower()
            if not attr or not val or len(val) > 50:
                continue
            
            # Value node
            val_node_id = f"{attr}:{val}"
            nodes[val_node_id] = {
                "id": val_node_id,
                "label": val,
                "kind": attr,
            }
            
            # Chunk → Value edge
            edges.append({
                "subject": chunk_node_id,
                "predicate": f"has_{attr}",
                "object": val_node_id,
            })
    
    return list(nodes.values()), edges


def main():
    print("=== ONTOLOGY EXTRACTION ===\n")
    
    schema = load_schema()
    attributes = schema["attributes"]
    print(f"Schema: {attributes}\n")
    
    # Test 20 chunk dulu
    TEST_SIZE = 20
    
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
    
    for i, c in enumerate(chunks, 1):
        print(f"  [{i}/{len(chunks)}] {c['source']}...", end=" ", flush=True)
        attrs = extract_chunk(llm, c["text"], attributes, c["chunk_id"])
        results.append({
            "chunk_id": c["chunk_id"],
            "source": c["source"],
            "attributes": attrs,
        })
        print(f"{len(attrs)} attrs")
        time.sleep(DELAY)
    
    # Build graph
    nodes, edges = build_graph(results)
    
    print(f"\n=== RESULT ===")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    # Save
    output = {
        "schema": attributes,
        "chunks_processed": len(chunks),
        "nodes": nodes,
        "edges": edges,
        "raw_results": results,
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved: {OUTPUT_FILE.name}")
    
    # Sample
    print(f"\n=== SAMPLE NODES ===")
    for n in nodes[:5]:
        print(f"  {n['id']} ({n['kind']})")
    print(f"\n=== SAMPLE EDGES ===")
    for e in edges[:5]:
        print(f"  {e['subject']} → {e['predicate']} → {e['object']}")


if __name__ == "__main__":
    main()