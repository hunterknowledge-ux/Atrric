"""
core/store.py - Vector store wrapper using PocketVectorDB.

Persistent, cosine-similarity search on ARMv7/Termux.
Replaces the previous JSON+numpy implementation.

PocketVectorDB API (verified 2026-10):
    add(embedding, metadata=None, text=None) -> str
    query(embedding, n_results=10) -> {ids, documents, metadatas, distances}
    count() -> int
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from pocketvectordb import VectorDB


class StoreError(Exception):
    """Raised when store operations fail."""
    pass


_db: Optional[VectorDB] = None


def _get_db() -> VectorDB:
    """Get or create the PocketVectorDB instance (singleton)."""
    global _db
    if _db is None:
        try:
            _db = VectorDB(
                storage_path=str(config.POCKET_VECTOR_DIR),
                dimension=config.EMBED_DIM,
            )
        except Exception as e:
            raise StoreError(f"Failed to open PocketVectorDB: {e}") from e
    return _db


def load(path: Optional[Path] = None) -> List[Dict]:
    """
    Return a list with length = number of chunks in store.

    Used by callers to check "is store empty?".
    Actual data is retrieved via search().
    """
    db = _get_db()
    try:
        n = db.count()
    except Exception as e:
        raise StoreError(f"Failed to read count: {e}") from e
    return [{"id": i} for i in range(n)]


def save(chunks: List[Dict], path: Optional[Path] = None) -> None:
    """No-op. PocketVectorDB persists on every add()."""
    return


def add_chunk(
    chunks: List[Dict],
    text: str,
    vector: List[float],
    source: str,
) -> Dict:
    """Add one chunk. Returns {id, text, source}."""
    db = _get_db()
    try:
        vec = np.array(vector, dtype=np.float32)
        doc_id = db.add(
            vec,
            metadata={"source": source},
            text=text,
        )
    except Exception as e:
        raise StoreError(f"Failed to add chunk: {e}") from e

    chunk = {"id": doc_id, "text": text, "source": source}
    chunks.append(chunk)
    return chunk


def search(
    query_vector: List[float],
    top_k: int = 3,
    chunks: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Find top_k most similar chunks.

    Returns list of {chunk: {id, text, source}, score}.
    Score = 1 - cosine_distance (range -1 to 1, higher = more similar).
    """
    db = _get_db()
    try:
        q = np.array(query_vector, dtype=np.float32)
        results = db.query(q, n_results=top_k)
    except Exception as e:
        raise StoreError(f"Search failed: {e}") from e

    ids = results.get("ids", [])
    docs = results.get("documents", [])
    metas = results.get("metadatas", [])
    dists = results.get("distances", [])

    out = []
    for i in range(len(ids)):
        dist = float(dists[i]) if i < len(dists) else 0.0
        score = 1.0 - dist
        meta = metas[i] if i < len(metas) and isinstance(metas[i], dict) else {}
        out.append({
            "chunk": {
                "id": ids[i],
                "text": docs[i] if i < len(docs) else "",
                "source": meta.get("source", "unknown"),
            },
            "score": score,
        })
    return out


if __name__ == "__main__":
    # Self-test with 128D vectors (matching config.EMBED_DIM)
    print("PocketVectorDB wrapper self-test...")

    dim = config.EMBED_DIM

    def make_vec(seed: int) -> List[float]:
        """Deterministic 128D pseudo-random vector."""
        np.random.seed(seed)
        v = np.random.randn(dim).astype(np.float32)
        return (v / np.linalg.norm(v)).tolist()

    chunks = []
    add_chunk(chunks, "Gen Z suka TikTok", make_vec(1), "test.txt")
    add_chunk(chunks, "Harga barang naik", make_vec(2), "test.txt")
    add_chunk(chunks, "AI penting", make_vec(3), "test.txt")

    loaded = load()
    print(f"Store has {len(loaded)} chunks")

    # Query with vector similar to first chunk
    q = make_vec(1)
    q[0] += 0.05
    results = search(q, top_k=2)
    print("Top results:")
    for r in results:
        print(f"  score={r['score']:.4f} | {r['chunk']['text']}")