"""
core/rag.py — RAG wrapper untuk ATRRIC.

Satu-satunya tempat yang tahu tentang OmniFuse.
Bila nak swap engine lain (ship time), tukar file ni sahaja.

v2: Auto-load ontology graph kalau ada.
v3: Bypass OmniFuse synthesis, guna custom prompt untuk elak terpotong.
"""

from omnifuse import EchoLLM, InMemoryGraph, OmniFuse

from core.omnifuse_adapter import PocketVectorStore


class RAG:
    """High-level RAG interface untuk ATRRIC."""

    def __init__(self, graph=None, llm=None):
        # vector: adapter sedia ada (dah works)
        self._vs = PocketVectorStore()

        # graph: load ontology kalau ada, fallback ke empty
        if graph is not None:
            self._graph = graph
        else:
            self._graph = self._load_ontology_graph()

        # llm: default EchoLLM (no-op), plug ILMU bila ready
        self._llm = llm if llm is not None else EchoLLM()

        # engine: satu-satunya OmniFuse instance
        self._engine = OmniFuse(
            graph=self._graph,
            vector=self._vs,
            llm=self._llm,
        )

    def _load_ontology_graph(self):
        """Load ontology_graph.json → InMemoryGraph. Fallback ke empty."""
        try:
            from core.ontology_to_omnifuse import get_ontology_graph
            graph = get_ontology_graph()
            print("[RAG] Ontology loaded")
            return graph
        except FileNotFoundError:
            print("[RAG] No ontology graph — empty graph")
            return InMemoryGraph(nodes=[], triples=[])
        except Exception as e:
            print(f"[RAG] Ontology load fail: {e} — empty graph")
            return InMemoryGraph(nodes=[], triples=[])

    # --- public API ---

    def retrieve(self, question: str, limit: int | None = None):
        """Vector + graph fusion. Return list of (chunk, score)."""
        return self._engine.retrieve(question, limit=limit)

    def search(self, question: str, synthesize: bool = True):
        """Full pipeline. Return SearchResult."""
        return self._engine.search(question, synthesize=synthesize)

    def close(self):
        try:
            self._engine.close()
        except Exception:
            pass


# ─────────────────────────────────────────────────
# Contract untuk frontend
# ─────────────────────────────────────────────────

_RAG_INSTANCE = None

def _get_rag():
    """Lazy singleton."""
    global _RAG_INSTANCE
    if _RAG_INSTANCE is None:
        from core.ilmu_llm import IlmuLLM
        _RAG_INSTANCE = RAG(llm=IlmuLLM())
    return _RAG_INSTANCE


def answer_question(q: str, top_k: int = 2) -> dict:
    """
    Entry point yang diubah suai untuk elak terpotong.
    Bypass OmniFuse synthesis, guna retrieve + IlmuLLM terus.
    """
    if not q or not q.strip():
        raise ValueError("Query kosong")

    rag = _get_rag()
    
    try:
        # 1. Ambil data RAG (Hadkan 2 je supaya context tak melimpah)
        chunks = rag.retrieve(q, limit=top_k)
        
        # 2. Satukan data jadi teks
        context_text = ""
        sources = []
        for c in chunks:
            text = getattr(c, "text", str(c))
            context_text += f"- {text}\n"
            src = getattr(c, "title", "") or ""
            if src and src not in sources:
                sources.append(src)

        # 3. Prompt khas yang kita kawal 100%
        final_prompt = f"""
        DATA RAG (Gunakan ini sebagai bukti):
        {context_text}
        
        TUGASAN:
        {q}
        
        ARAHAN KETAT:
        1. Tulis analisa dalam bentuk 2 perenggan biasa (bukan senarai nombor).
        2. JANGAN guna angka 1, 2, 3 atau bullet point.
        3. Tulis padat dan ringkas. Pastikan ayat terakhir tamat dengan noktah.
        """

        # 4. Panggil LLM terus (guna limit 2048 token)
        answer = rag._llm.generate(final_prompt, max_tokens=2048)
        
        return {
            "answer": answer,
            "sources": sources,
        }
        
    except Exception as e:
        raise RuntimeError(f"RAG pipeline failed: {e}") from e