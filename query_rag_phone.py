"""
query_rag_phone.py - Query the RAG index (phone mode).

Hardcore mode: forces LLM to skip preamble and go straight to content.
Uses 3-layer enforcement:
  1. Aggressive system prompt
  2. Assistant prefill (###)
  3. Post-process regex strip
"""

import argparse
import re
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from core.embed import embed, EmbedError
from core.llm import generate, LLMError
from core import store as vector_store


# ─────────────────────────────────────────────────────────────
# Layer 1: Aggressive system prompt
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
Kau adalah pembantu analisis data.

PERATURAN KERAS (WAJIB PATUH):
1. TERUS jawab soalan. JANGAN bagi mukadimah.
2. DILARANG MULA dengan frasa berikut:
   - "Berdasarkan data..."
   - "Berdasarkan bukti..."
   - "Berikut adalah..."
   - "Ini adalah..."
   - "Berdasarkan perbincangan..."
   - "Based on the data..."
   - "The data shows..."
3. MULA output terus dengan markdown heading: ### 
   Contoh: "### Pandangan Gen Z tentang PTPTN"
4. Guna struktur: heading + bullet points.
5. Kalau data tak cukup, tulis terus "Data tidak mencukupi."
6. JANGAN tulis "Data:" atau "Soalan:" dalam jawapan.

Pelanggaran peraturan = output tidak berguna.
"""


# ─────────────────────────────────────────────────────────────
# Layer 2: Assistant prefill (force start with ###)
# ─────────────────────────────────────────────────────────────

PREFILL = "### "


# ─────────────────────────────────────────────────────────────
# Layer 3: Post-process regex strip (safety net)
# ─────────────────────────────────────────────────────────────

FRAMING_PATTERNS = [
    r"^Berdasarkan\s+(?:data|bukti|maklumat|informasi)\s+(?:yang\s+)?(?:diberikan|ada|tersedia)[^.]*[.:]?\s*",
    r"^Berdasarkan\s+perbincangan\s+dalam\s+(?:data|bukti)[^.]*[.:]?\s*",
    r"^Berdasarkan\s+kepada\s+(?:data|bukti)[^.]*[.:]?\s*",
    r"^Based\s+on\s+the\s+(?:data|evidence|information|context)[^.]*[.:]?\s*",
    r"^Daripada\s+(?:data|bukti)[^.]*[.:]?\s*",
    r"^Mengikut\s+(?:data|bukti)[^.]*[.:]?\s*",
    r"^Berikut\s+adalah\s+[^:]*:\s*",
    r"^Ini\s+adalah\s+[^:]*:\s*",
    r"^The\s+(?:data|evidence)\s+(?:shows|indicates|suggests)[^.]*[.:]?\s*",
]


def _strip_framing(text: str) -> str:
    """Strip any preamble/framing that escaped layers 1 and 2."""
    if not text:
        return text
    s = text.lstrip()

    # Loop: strip multiple framing layers if stacked
    for _ in range(3):
        before = s
        for pat in FRAMING_PATTERNS:
            new_s = re.sub(pat, "", s, count=1, flags=re.IGNORECASE)
            if new_s != s:
                s = new_s
                break
        if s == before:
            break

    # Normalize headings with dash prefix: "### - **X**" -> "### **X**"
    s = re.sub(r"^(#{1,6})\s*[-•]\s*", r"\1 ", s, flags=re.MULTILINE)

    return s.strip()


# ─────────────────────────────────────────────────────────────
# Main query
# ─────────────────────────────────────────────────────────────

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

    # Build context
    context = "\n\n".join(r["chunk"]["text"] for r in results)

    # Build prompt — minimal, direct
    user_msg = f"{question}\n\nDATA:\n{context}"

    # Generate with all 3 layers
    print("Generating answer...")
    try:
        answer = generate(
            user_msg,
            system=SYSTEM_PROMPT,
            prefill=PREFILL,
            temperature=0.2,
            max_tokens=600,
        )
    except LLMError as e:
        print(f"LLM failed: {e}")
        sys.exit(1)

    # Layer 3: post-process safety net
    answer = _strip_framing(answer)

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