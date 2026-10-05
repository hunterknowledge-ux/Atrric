"""
core/store.py - Simple JSON vector store.

Stores chunks with their embedding vectors in a JSON file.
Search uses cosine similarity (pure Python, no numpy needed).

Format of vector_store.json:
{
  "chunks": [
    {"id": "chunk_0", "text": "...", "vector": [...], "source": "..."},
    ...
  ]
}
"""

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class StoreError(Exception):
    """Raised when store operations fail."""
    pass


def load(path: Optional[Path] = None) -> List[Dict]:
    """Load chunks from JSON file. Returns empty list if file missing."""
    path = path or config.VECTOR_STORE_FILE
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("chunks", [])
    except (json.JSONDecodeError, OSError) as e:
        raise StoreError(f"Failed to load store: {e}") from e


def save(chunks: List[Dict], path: Optional[Path] = None) -> None:
    """Save chunks to JSON file."""
    path = path or config.VECTOR_STORE_FILE
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"chunks": chunks}, f, ensure_ascii=False)
    except OSError as e:
        raise StoreError(f"Failed to save store: {e}") from e


def add_chunk(
    chunks: List[Dict],
    text: str,
    vector: List[float],
    source: str,
) -> Dict:
    """Append one chunk to the list. Returns the new chunk."""
    chunk = {
        "id": f"chunk_{len(chunks)}",
        "text": text,
        "vector": vector,
        "source": source,
    }
    chunks.append(chunk)
    return chunk


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Pure-python cosine similarity between two vectors."""
    if len(a) != len(b):
        raise ValueError(f"Vector length mismatch: {len(a)} vs {len(b)}")
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


def search(
    query_vector: List[float],
    top_k: int = 3,
    chunks: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Find top_k most similar chunks to query_vector.

    Returns list of dicts: {chunk, score} sorted by score descending.
    """
    if chunks is None:
        chunks = load()

    if not chunks:
        return []

    scored = []
    for chunk in chunks:
        vec = chunk.get("vector")
        if not vec:
            continue
        try:
            score = cosine_similarity(query_vector, vec)
        except ValueError:
            continue
        scored.append({"chunk": chunk, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    # Self-test: create store with dummy vectors
    test_path = Path("/tmp/test_store.json")
    if test_path.exists():
        test_path.unlink()

    chunks = []
    add_chunk(chunks, "Gen Z suka TikTok", [1.0, 0.0, 0.0], "test.txt")
    add_chunk(chunks, "Harga barang naik", [0.0, 1.0, 0.0], "test.txt")
    add_chunk(chunks, "AI penting", [0.0, 0.0, 1.0], "test.txt")
    save(chunks, test_path)

    loaded = load(test_path)
    print(f"Loaded {len(loaded)} chunks")

    results = search([0.9, 0.1, 0.0], top_k=2, chunks=loaded)
    for r in results:
        print(f"  score={r['score']:.4f} | {r['chunk']['text']}")