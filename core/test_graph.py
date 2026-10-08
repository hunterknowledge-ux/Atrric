"""Smoke test graph fusion — InMemoryGraph primitives + RAG integration."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnifuse.models import Node, Triple
from omnifuse import InMemoryGraph
from core.rag import RAG


def build_dummy_graph():
    nodes = [
        Node(id="tiktok", label="TikTok", kind="platform"),
        Node(id="gen-z", label="Gen Z", kind="demographic"),
        Node(id="viral", label="Viral", kind="concept"),
    ]
    triples = [
        Triple(s="gen-z", p="uses", o="tiktok"),
        Triple(s="tiktok", p="causes", o="viral"),
    ]
    return InMemoryGraph(nodes=nodes, triples=triples)


def test_primitives():
    print("\n=== Test 1: InMemoryGraph primitives ===")
    g = build_dummy_graph()

    hits = g.search_labels("TikTok")
    print(f"  search_labels('TikTok'): {len(hits)} hits")
    for node, score in hits[:3]:
        print(f"    {score:.3f} | {node.id} ({node.label})")

    try:
        nbrs = g.neighbors("gen-z", hops=1, limit=10)
        print(f"  neighbors('gen-z'): {len(nbrs)} facts")
        for f in nbrs[:3]:
            print(f"    {f}")
    except Exception as e:
        print(f"  neighbors error: {type(e).__name__}: {e}")

    try:
        nids = g.neighbor_ids("gen-z", limit=10, direction="both")
        print(f"  neighbor_ids('gen-z'): {nids}")
    except Exception as e:
        print(f"  neighbor_ids error: {type(e).__name__}: {e}")


def test_rag():
    print("\n=== Test 2: RAG with graph ===")
    g = build_dummy_graph()
    rag = RAG(graph=g)

    for q in ["TikTok Gen Z", "viral"]:
        hits = rag.retrieve(q, limit=3)
        print(f"\n  query: {q!r} -> {len(hits)} hits")
        for h in hits[:3]:
            chunk, score = h[0], h[1]
            text = getattr(chunk, "text", str(chunk))[:50]
            print(f"    {score:.4f} | {text}")

    rag.close()


if __name__ == "__main__":
    test_primitives()
    test_rag()
    print("\ndone.")