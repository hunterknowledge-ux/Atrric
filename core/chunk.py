"""
core/chunk.py - Text chunking for RAG.

Splits long text into smaller chunks suitable for embedding.
Strategy: split by paragraphs first, fall back to sentence splitting,
then hard-split if needed. Respects chunk_size and overlap.
"""

import re
import sys
from pathlib import Path
from typing import List

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


def chunk_text(
    text: str,
    chunk_size: int = None,
    overlap: int = None,
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Input text to chunk.
        chunk_size: Target size per chunk (chars). Defaults to config.CHUNK_SIZE.
        overlap: Overlap between chunks (chars). Defaults to config.CHUNK_OVERLAP.

    Returns:
        List of non-empty chunk strings.
    """
    if not text or not text.strip():
        return []

    size = chunk_size if chunk_size is not None else config.CHUNK_SIZE
    ovl = overlap if overlap is not None else config.CHUNK_OVERLAP

    # Normalize whitespace
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        # If paragraph alone > size, hard-split it
        if len(para) > size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_split(para, size, ovl))
            continue

        # Try to add paragraph to current chunk
        if not current:
            current = para
        elif len(current) + 2 + len(para) <= size:
            current = f"{current}\n\n{para}"
        else:
            chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


def _hard_split(text: str, size: int, overlap: int) -> List[str]:
    """Hard-split long text by character, with overlap."""
    if size <= 0:
        return [text]

    step = max(1, size - overlap)
    parts = []
    for i in range(0, len(text), step):
        chunk = text[i:i + size].strip()
        if chunk:
            parts.append(chunk)
    return parts


if __name__ == "__main__":
    test_text = (
        "Gen Z Malaysia suka TikTok. Mereka juga aktif di Instagram.\n\n"
        "Harga barang naik adalah isu utama. Ramai beralih ke alternatif murah.\n\n"
        "AI makin penting dalam pendidikan dan pekerjaan."
    )

    chunks = chunk_text(test_text, chunk_size=80, overlap=20)
    print(f"Total chunks: {len(chunks)}")
    for i, c in enumerate(chunks, 1):
        print(f"--- Chunk {i} ({len(c)} chars) ---")
        print(c)
        print()