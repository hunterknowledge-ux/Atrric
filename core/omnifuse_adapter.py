"""
core/omnifuse_adapter.py
PocketVectorStore — adapter core.store -> OmniFuse VectorStore protocol.
Tidak sentuh store.py. Hanya wrap.
"""

import numpy as np
from omnifuse.models import Chunk, ChunkMutationResult

from core import embed as core_embed
from core import store as core_store

_DIM = 128


class PocketVectorStore:
    """OmniFuse VectorStore protocol over PocketVectorDB."""

    def __init__(self):
        self._db = core_store._get_db()

    # --- VectorStore protocol ---

    def search(self, query: str, *, limit: int = 20) -> list[tuple[Chunk, float]]:
        vec = core_embed.get_embedding(query)
        results = core_store.search(vec, top_k=limit)
        return [(self._to_chunk(r["chunk"]), float(r["score"])) for r in results]

    def fetch(self, ids: list[str]) -> list[Chunk]:
        want = set(ids)
        return [c for c in self._iter_all() if c.id in want]

    def upsert_chunks(self, chunks: list[Chunk]) -> ChunkMutationResult:
        for c in chunks:
            vec = c.embedding if c.embedding else core_embed.get_embedding(c.text)
            core_store.add_chunk([], c.text, vec, c.title or "unknown")
        core_store.save([])
        return ChunkMutationResult(inserted=len(chunks), result=True)

    def delete_chunks(self, ids: list[str]) -> ChunkMutationResult:
        # PocketVectorDB tak support delete native
        return ChunkMutationResult(missing=len(ids), result=False)

    # --- internal ---

    def _to_chunk(self, raw: dict) -> Chunk:
        return Chunk(id=raw["id"], text=raw["text"], title=raw.get("source", ""))

    def _iter_all(self) -> list[Chunk]:
        n = self._db.count()
        if n == 0:
            return []
        zero = np.zeros(_DIM, dtype=np.float32)
        res = self._db.query(zero, n_results=n)
        ids = res.get("ids", [])
        docs = res.get("documents", [])
        metas = res.get("metadatas", [])
        out = []
        for i in range(len(ids)):
            meta = metas[i] if i < len(metas) and isinstance(metas[i], dict) else {}
            out.append(Chunk(
                id=ids[i],
                text=docs[i] if i < len(docs) else "",
                title=meta.get("source", ""),
            ))
        return out