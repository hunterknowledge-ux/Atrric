"""
core/test_graphrag_vs_naive.py

Compare Naive RAG vs GraphRAG — full answer, metrics, side-by-side.
"""

import sys
import time
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.env_loader import load_env

load_env()

from omnifuse import InMemoryGraph

from core.ilmu_llm import IlmuLLM
from core.rag import RAG

QUERIES = [
    "Kenapa Gen Z dikatakan lemah?",
    "Apa isu pendidikan sekarang?",
    "Bagaimana Millennials dilihat oleh Gen Z?",
]


def run(rag, q):
    t0 = time.time()
    try:
        r = rag.search(q, synthesize=True)
        return {
            "ok": True,
            "answer": r.answer or "",
            "chunks": len(r.chunks or []),
            "evidence": len(r.evidence or []),
            "relations": len(r.relations or []),
            "elapsed": round(time.time() - t0, 1),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "elapsed": round(time.time() - t0, 1)}


def main():
    print("=" * 75)
    print("NAIVE RAG (vector-only)  vs  GRAPHRAG (vector + ontology)")
    print("=" * 75)

    llm = IlmuLLM()

    print("\nLoading RAG engines...")
    rag_graph = RAG(llm=llm)
    rag_naive = RAG(graph=InMemoryGraph(nodes=[], triples=[]), llm=llm)

    for i, q in enumerate(QUERIES, 1):
        print(f"\n{'#' * 75}")
        print(f"QUERY {i}: {q}")
        print(f"{'#' * 75}")

        # NAIVE
        print("\n--- NAIVE RAG ---")
        n = run(rag_naive, q)
        if n["ok"]:
            print(f"chunks: {n['chunks']}  |  relations: {n['relations']}  |  time: {n['elapsed']}s")
            print(f"\n{n['answer']}")
        else:
            print(f"ERROR: {n['error']}")

        print()

        # GRAPHRAG
        print("--- GRAPHRAG ---")
        g = run(rag_graph, q)
        if g["ok"]:
            print(f"chunks: {g['chunks']}  |  relations: {g['relations']}  |  time: {g['elapsed']}s")
            print(f"\n{g['answer']}")
        else:
            print(f"ERROR: {g['error']}")

    rag_graph.close()
    rag_naive.close()
    print(f"\n{'=' * 75}\nDONE")


if __name__ == "__main__":
    main()