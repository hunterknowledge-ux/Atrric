"""
core/rag.py — RAG wrapper untuk ATRRIC.

Satu-satunya tempat yang tahu tentang OmniFuse.
Bila nak swap engine lain (ship time), tukar file ni sahaja.
"""

from omnifuse import OmniFuse, EchoLLM, InMemoryGraph
from core.omnifuse_adapter import PocketVectorStore


class RAG:
    """High-level RAG interface untuk ATRRIC.

    Guna:
        rag = RAG()
        rag.retrieve("viral tak?")   # evidence je, tak panggil LLM
        rag.search("viral tak?")     # full: retrieve + LLM answer
    """

    def __init__(self, graph=None, llm=None):
        # vector: adapter sedia ada (dah works)
        self._vs = PocketVectorStore()
        # graph: InMemoryGraph default (boleh swap bila ada ontology)
        self._graph = graph if graph is not None else InMemoryGraph(
            nodes=[], triples=[]
        )
        # llm: default EchoLLM (no-op), plug Gemini/local bila ready
        self._llm = llm if llm is not None else EchoLLM()
        # engine: satu-satunya OmniFuse instance
        self._engine = OmniFuse(
            graph=self._graph,
            vector=self._vs,
            llm=self._llm,
        )

    # --- public API ---

    def retrieve(self, question: str, limit: int | None = None):
        """Vector + graph fusion. Return list of (chunk, score)."""
        return self._engine.retrieve(question, limit=limit)

    def search(self, question: str, synthesize: bool = True):
        """Full pipeline. Return SearchResult.

        synthesize=False → skips LLM (debug). Return evidence + prompt je.
        """
        return self._engine.search(question, synthesize=synthesize)

    def close(self):
        try:
            self._engine.close()
        except Exception:
            pass