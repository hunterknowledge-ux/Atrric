"""
core/test_graphrag_vs_naive.py

Compare GraphRAG (dengan graph) vs Naive RAG (empty graph).
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.env_loader import load_env
load_env()

from omnifuse import InMemoryGraph
from core.rag import RAG
from core.ilmu_llm import IlmuLLM


QUERIES = [
    "Apa isu pendidikan sekarang?",
    "Kenapa Gen Z dikatakan lemah?",
    "Apa peranan cikgu dalam isu pendidikan?",
    "Bagaimana Millennials dilihat oleh Gen Z?",
    "Apa SISPAA dan kenapa ia disebut?",
]


def run_query(rag, q):
    r = rag.search(q, synthesize=True)
    return {
        "answer": r.answer or "",
        "chunks": len(r.chunks or []),
        "evidence": len(r.evidence or []),
        "relations": len(r.relations or []),
    }


def main():
    print("=== GRAPHRAG vs NAIVE RAG ===\n")

    llm = IlmuLLM()

    # GraphRAG — dengan graph
    print("Loading GraphRAG (with ontology)...")
    rag_graph = RAG(llm=llm)

    # Naive — empty graph
    print("Loading Naive RAG (empty graph)...")
    rag_naive = RAG(graph=InMemoryGraph(nodes=[], triples=[]), llm=llm)

    print()
    print("=" * 70)

    for i, q in enumerate(QUERIES, 1):
        print(f"\n### QUERY {i}: {q}\n")

        # Naive
        print("[NAIVE RAG]")
        n = run_query(rag_naive, q)
        print(f"  chunks: {n['chunks']} | evidence: {n['evidence']} | relations: {n['relations']}")
        print(f"  answer: {n['answer'][:200]}...")

        print()

        # GraphRAG
        print("[GRAPHRAG]")
        g = run_query(rag_graph, q)
        print(f"  chunks: {g['chunks']} | evidence: {g['evidence']} | relations: {g['relations']}")
        print(f"  answer: {g['answer'][:200]}...")

        print("-" * 70)

    rag_graph.close()
    rag_naive.close()


if __name__ == "__main__":
    main()