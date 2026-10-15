"""
core/ontology_induction_poc.py

POC — Iterative Schema Induction untuk ATRRIC.
Berdasarkan kertas: Avram et al. (Okt 2026)
"Learning to Structure Data from User-Generated Thematic Corpora"

3 iterasi. 10 chunk sample. Ilmu-mini-v3.3.
Zero hardcoded domain — biar LLM discover sendiri.
"""

import json
import re
from collections import Counter
from core.env_loader import load_env
load_env()

from core.ilmu_llm import IlmuLLM
from core.store import _get_db


# ══════════════════════════════════════════════════════════
# STEP 1 — EXTRACT ATTRIBUTES (unconstrained)
# ══════════════════════════════════════════════════════════

EXTRACT_PROMPT = """Extract implicit attributes from these Malaysian social media comments.

DO NOT use a fixed schema. Discover whatever attributes are actually present.

For each chunk, output a JSON list of objects:
[{{"attribute": "...", "value": "..."}}, ...]

Rules:
- Attribute names: free-form, in English, lowercase (e.g. "age", "topic", "emotion")
- Only extract attributes CLEARLY stated or strongly implied
- Skip short/empty chunks (haha, thanks, emoji only)
- No explanation. Output JSON only.

Chunks:
{chunks}

Output:"""


def extract_attributes(llm, chunks):
    chunks_text = "\n\n".join(
        f"[CHUNK {i}]\n{c[:500]}"
        for i, c in enumerate(chunks)
    )
    prompt = EXTRACT_PROMPT.format(chunks=chunks_text)
    
    raw = llm.generate(prompt, max_tokens=2000, temperature=0.3)
    
    # Parse JSON
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            data = data.get("attributes", data.get("data", []))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError as e:
        print(f"  [!] JSON parse fail: {e}")
        print(f"  Raw (first 300): {raw[:300]}")
        return []


# ══════════════════════════════════════════════════════════
# STEP 2 — AGGREGATE FREQUENCY
# ══════════════════════════════════════════════════════════

def aggregate(attributes):
    """Return Counter of attribute names."""
    counter = Counter()
    for item in attributes:
        if isinstance(item, dict):
            name = str(item.get("attribute", "")).strip().lower()
            if name and len(name) < 50:
                counter[name] += 1
    return counter


# ══════════════════════════════════════════════════════════
# STEP 3 — CONSOLIDATE SEMANTIC
# ══════════════════════════════════════════════════════════

CONSOLIDATE_PROMPT = """These are attribute names extracted from social media comments.
Some refer to the same concept (e.g. "age" and "umur" and "berapa_tahun").

Group them into canonical clusters. Use SHORT English names.

Input attribute names:
{attrs}

Output JSON only:
[{{"canonical": "...", "aliases": ["...", "..."]}}, ...]

Output:"""


def consolidate(llm, counter, top_k=20):
    top = counter.most_common(top_k)
    names = [n for n, _ in top]
    if len(names) < 2:
        return [{"canonical": n, "aliases": [n]} for n in names]
    
    prompt = CONSOLIDATE_PROMPT.format(attrs="\n".join(names))
    raw = llm.generate(prompt, max_tokens=1500, temperature=0.2)
    
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    
    try:
        clusters = json.loads(raw)
        if isinstance(clusters, list):
            return clusters
    except json.JSONDecodeError:
        pass
    
    return [{"canonical": n, "aliases": [n]} for n in names]


# ══════════════════════════════════════════════════════════
# MAIN — ITERATION LOOP
# ══════════════════════════════════════════════════════════

def load_sample_chunks(n=10):
    db = _get_db()
    meta_path = db.metadata_file
    with open(meta_path) as f:
        meta = json.load(f)
    docs = meta.get("documents", {})
    chunks = []
    for doc_id, doc in docs.items():
        text = doc.get("text", "").strip()
        if len(text) > 50:  # skip junk
            chunks.append(text)
        if len(chunks) >= n:
            break
    return chunks


def main():
    print("=== ONTOLOGY INDUCTION POC ===\n")
    
    llm = IlmuLLM()
    print(f"Model: {llm.model}\n")
    
    chunks = load_sample_chunks(10)
    print(f"Sample: {len(chunks)} chunks\n")
    
    prev_schema = None
    
    for iteration in range(1, 4):
        print(f"--- Iteration {iteration} ---")
        
        # Extract
        attrs = extract_attributes(llm, chunks)
        print(f"  Extracted: {len(attrs)} attribute-value pairs")
        
        # Aggregate
        counter = aggregate(attrs)
        print(f"  Unique attributes: {len(counter)}")
        print(f"  Top 5: {counter.most_common(5)}")
        
        # Consolidate
        clusters = consolidate(llm, counter, top_k=15)
        schema = {c["canonical"] for c in clusters if c.get("canonical")}
        print(f"  After consolidation: {len(schema)} attributes")
        print(f"  Schema: {sorted(schema)}")
        
        # Convergence check
        if prev_schema == schema:
            print(f"  ✅ Converged at iteration {iteration}\n")
            break
        
        prev_schema = schema
        print()
    
    # Cost
    u = llm.last_usage
    cost = u.get("prompt_tokens", 0) * 0.20/1e6 + u.get("completion_tokens", 0) * 1.20/1e6
    print(f"\n=== DONE ===")
    print(f"Last call cost: RM{cost:.6f}")
    print(f"Schema: {sorted(schema)}")


if __name__ == "__main__":
    main()