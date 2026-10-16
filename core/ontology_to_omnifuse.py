"""
core/ontology_to_omnifuse.py

Convert ontology_graph.json → OmniFuse InMemoryGraph.

Handle:
- Strip "chunk_" prefix dari chunk nodes (untuk match dengan store)
- Convert JSON format → OmniFuse Node + Triple models
- Public API: get_ontology_graph()
"""

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from omnifuse.models import Node, Triple
from omnifuse import InMemoryGraph


ONTOLOGY_FILE = _ROOT / "ontology_graph.json"


def load_ontology():
    """Load JSON file."""
    if not ONTOLOGY_FILE.exists():
        raise FileNotFoundError(
            f"Ontology file tak jumpa: {ONTOLOGY_FILE}\n"
            f"Run: python core/ontology_extract.py"
        )
    return json.loads(ONTOLOGY_FILE.read_text())


def _normalize_id(raw_id, kind):
    """Strip 'chunk_' prefix untuk chunk nodes — match dengan store ID."""
    if kind == "chunk" and raw_id.startswith("chunk_"):
        return raw_id[6:]
    return raw_id


def convert(ontology):
    """Convert ontology JSON → InMemoryGraph."""
    # Nodes
    nodes = []
    for n in ontology["nodes"]:
        node_id = _normalize_id(n["id"], n["kind"])
        nodes.append(Node(
            id=node_id,
            label=n["label"],
            kind=n["kind"],
        ))

    # Triples
    triples = []
    for e in ontology["edges"]:
        subj = e["subject"]
        # Strip prefix kalau subject is chunk node
        if subj.startswith("chunk_"):
            subj = subj[6:]

        triples.append(Triple(
            s=subj,
            p=e["predicate"],
            o=e["object"],
        ))

    return InMemoryGraph(nodes=nodes, triples=triples)


def get_ontology_graph():
    """Public API — call from core/rag.py."""
    ont = load_ontology()
    return convert(ont)


if __name__ == "__main__":
    print("=== ONTOLOGY → OMNIFUSE CONVERTER ===\n")

    ont = load_ontology()
    print(f"Source: {ONTOLOGY_FILE.name}")
    print(f"Nodes:  {len(ont['nodes'])}")
    print(f"Edges:  {len(ont['edges'])}")
    print(f"Chunks: {ont['chunks_processed']}")
    print()

    print("Converting...")
    graph = get_ontology_graph()
    print("✅ Done\n")

    # Test 1: Search labels
    print("=== TEST 1: search_labels ===")
    for query in ["gen z", "millennial", "cikgu", "pendidikan"]:
        hits = graph.search_labels(query, limit=3)
        print(f"\n'{query}': {len(hits)} hits")
        for node, score in hits[:3]:
            print(f"  {score:.3f} | {node.id[:40]} ({node.kind})")

    # Test 2: Neighbors
    print("\n=== TEST 2: neighbors ===")
    hits = graph.search_labels("gen z", limit=1)
    if hits:
        test_node = hits[0][0]
        print(f"Test node: {test_node.id} ({test_node.kind})")
        nbrs = graph.neighbors(test_node.id, hops=1, limit=10)
        print(f"Neighbors: {len(nbrs)}")
        for t in nbrs[:10]:
            print(f"  {t}")

    # Test 3: Neighbor IDs
    print("\n=== TEST 3: neighbor_ids ===")
    if hits:
        nids = graph.neighbor_ids(test_node.id, limit=10, direction="both")
        print(f"Neighbor IDs: {len(nids)}")
        for nid in nids[:5]:
            print(f"  {nid}")