"""
build_rag_phone.py - Build RAG index for phone mode.

Reads .txt files from data/, chunks them, embeds each chunk,
and saves the vectors to vector_store.json.
"""

import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from core.chunk import chunk_text
from core.embed import embed, EmbedError
from core import store as vector_store


def build() -> None:
    """Build the RAG index from files in data/."""
    print("=== ATRRIC BUILD (PHONE MODE) ===")
    print(f"Data dir: {config.DATA_DIR}")
    print(f"Store file: {config.VECTOR_STORE_FILE}")
    print()

    # Find .txt files
    txt_files = sorted(config.DATA_DIR.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {config.DATA_DIR}")
        sys.exit(1)

    print(f"Found {len(txt_files)} file(s):")
    for f in txt_files:
        print(f"  - {f.name}")
    print()

    # Fresh chunks list
    chunks = []

    for file_path in txt_files:
        print(f"Processing: {file_path.name}")
        text = file_path.read_text(encoding="utf-8")
        print(f"  {len(text)} chars")

        file_chunks = chunk_text(text)
        print(f"  {len(file_chunks)} chunks")

        for i, chunk in enumerate(file_chunks):
            try:
                vec = embed(chunk)
            except EmbedError as e:
                print(f"  [{i+1}/{len(file_chunks)}] Embed failed: {e}")
                continue

            vector_store.add_chunk(
                chunks,
                text=chunk,
                vector=vec,
                source=file_path.name,
            )
            print(f"  [{i+1}/{len(file_chunks)}] Embedded ({len(chunk)} chars)")

    # Save
    if not chunks:
        print("\nNo chunks embedded. Aborting.")
        sys.exit(1)

    vector_store.save(chunks)
    print()
    print(f"=== DONE ===")
    print(f"Chunks stored: {len(chunks)}")
    print(f"Store: {config.VECTOR_STORE_FILE}")


if __name__ == "__main__":
    build()