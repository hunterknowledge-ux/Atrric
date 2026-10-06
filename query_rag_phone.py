"""
query_rag_phone.py - Query the RAG index (phone mode).

Takes a user question, embeds it, searches the vector store,
builds a prompt with retrieved context, and calls the LLM.
"""

import argparse
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from core.embed import embed, EmbedError
from core.llm import generate, LLMError
from core import store as vector_store


def query(question: str, top_k: int = None) -> None:
    """Run a full RAG query."""
    k = top_k if top_k is not None else config.TOP_K

    print("=== ATRRIC QUERY (PHONE MODE) ===")
    print(f"Question: {question}")
    print(f"Top-K: {k}")
    print()

    # Load store
    chunks = vector_store.load()
    if not chunks:
        print("Store is empty. Run build_rag_phone.py first.")
        sys.exit(1)
    print(f"Store has {len(chunks)} chunks")

    # Embed question
    print("Embedding question...")
    try:
        q_vec = embed(question)
    except EmbedError as e:
        print(f"Embed failed: {e}")
        sys.exit(1)

    # Search
    print(f"Searching top-{k}...")
    results = vector_store.search(q_vec, top_k=k, chunks=chunks)
    if not results:
        print("No results found.")
        sys.exit(1)

    print("Retrieved:")
    for i, r in enumerate(results, 1):
        preview = r["chunk"]["text"][:60].replace("\n", " ")
        print(f"  [{i}] score={r['score']:.4f} | {preview}...")
    print()

    # Build context from top results
    context = "\n\n".join(r["chunk"]["text"] for r in results)

    # Build prompt
    prompt = (
        f"Data:\n{context}\n\n"
        f"Soalan: {question}\n"
        f"Jawapan:"
    )

    # Generate
    print("Generating answer...")
    try:
        answer = generate(prompt)
    except LLMError as e:
        print(f"LLM failed: {e}")
        sys.exit(1)

    print()
    print("=== ANSWER ===")
    print(answer)
    print()

    # Sources
    print("=== SOURCES ===")
    for i, r in enumerate(results, 1):
        src = r["chunk"].get("source", "unknown")
        print(f"  [{i}] {src} (score: {r['score']:.4f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atrric phone-mode query")
    parser.add_argument("question", type=str, help="Your question")
    parser.add_argument("--top_k", type=int, default=None, help="Number of chunks")
    args = parser.parse_args()

    query(args.question, top_k=args.top_k)