"""
core/ontology_induction_poc.py

Iterative Schema Induction untuk ATRRIC.
Berdasarkan kertas: Avram et al. (Okt 2026)

Update v2:
- 10 iterasi (bukan 3)
- 50 chunk sample (bukan 10)
- Better consolidation prompt (explicit rules)
- Convergence check (80% overlap)
- Track core attributes
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.env_loader import load_env
load_env()

from core.ilmu_llm import IlmuLLM
from core.store import _get_db


# ══════════════════════════════════════════════════════════
# STEP 1 — EXTRACT ATTRIBUTES (per chunk)
# ══════════════════════════════════════════════════════════

EXTRACT_PROMPT = """Extract implicit attributes from this Malaysian social media comment.

DO NOT use a fixed schema. Discover whatever attributes are actually present.

Output a JSON list of objects:
[{{"attribute": "...", "value": "..."}}, ...]

Rules:
- Attribute names: free-form, in English, lowercase
- Only extract attributes CLEARLY stated or strongly implied
- Focus on: emotion, topic, target_group, stance, tone, generation
- Skip meta: observation, reference, response (bukan attribute)
- Skip short/empty chunks
- No explanation. Output JSON only.

Comment:
{chunk}

Output:"""


def extract_attributes(llm, chunks):
    all_attrs = []
    fails = 0
    for i, chunk in enumerate(chunks):
        prompt = EXTRACT_PROMPT.format(chunk=chunk[:500])
        raw = llm.generate(prompt, max_tokens=800, temperature=0.3)

        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = data.get("attributes", data.get("data", []))
            if isinstance(data, list):
                all_attrs.extend(data)
        except json.JSONDecodeError:
            fails += 1

    return all_attrs, fails


# ══════════════════════════════════════════════════════════
# STEP 2 — AGGREGATE
# ══════════════════════════════════════════════════════════

def aggregate(attributes):
    counter = Counter()
    for item in attributes:
        if isinstance(item, dict):
            name = str(item.get("attribute", "")).strip().lower()
            if name and len(name) < 50:
                counter[name] += 1
    return counter


# ══════════════════════════════════════════════════════════
# STEP 3 — CONSOLIDATE (Better prompt)
# ══════════════════════════════════════════════════════════

CONSOLIDATE_PROMPT = """These are attribute names extracted from social media comments.
Some refer to the same concept. Group them into canonical clusters.

RULES:
- Merge semantically same: attitude/stance/perspective → "stance"
- Skip meta attributes: observation, reference, response, point
- Skip duplicate: generation + generation_label → "generation"
- Prefer SHORT English names (1-2 words)
- Max 10 canonical attributes
- Only keep attributes that appear 2+ times in input

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
# STEP 4 — CONVERGENCE CHECK (80% overlap)
# ══════════════════════════════════════════════════════════

def is_converged(prev_schema, schema, threshold=0.8):
    if not prev_schema or not schema:
        return False
    intersection = len(prev_schema & schema)
    union = len(prev_schema | schema)
    if union == 0:
        return False
    overlap = intersection / union
    return overlap >= threshold


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def load_sample_chunks(n=50):
    db = _get_db()
    meta_path = db.metadata_file
    with open(meta_path) as f:
        meta = json.load(f)
    docs = meta.get("documents", {})
    chunks = []
    for doc_id, doc in docs.items():
        text = doc.get("text", "").strip()
        if len(text) > 50:
            chunks.append(text)
        if len(chunks) >= n:
            break
    return chunks


def main():
    print("=== ONTOLOGY INDUCTION (v2) ===\n")

    llm = IlmuLLM()
    print(f"Model: {llm.model}")

    chunks = load_sample_chunks(50)
    print(f"Sample: {len(chunks)} chunks")
    print(f"Max iterations: 10\n")

    prev_schema = None
    schema = set()
    all_schemas = []
    total_fails = 0

    for iteration in range(1, 11):
        print(f"--- Iteration {iteration} ---")

        attrs, fails = extract_attributes(llm, chunks)
        total_fails += fails
        print(f"  Extracted: {len(attrs)} pairs (fails: {fails})")

        counter = aggregate(attrs)
        print(f"  Unique: {len(counter)}")
        print(f"  Top 5: {counter.most_common(5)}")

        clusters = consolidate(llm, counter, top_k=20)
        schema = {c["canonical"] for c in clusters if c.get("canonical")}
        all_schemas.append(schema)
        print(f"  Schema ({len(schema)}): {sorted(schema)}")

        if is_converged(prev_schema, schema):
            print(f"  ✅ CONVERGED at iteration {iteration}\n")
            break

        prev_schema = schema
        print()

    # Core attributes — muncul 3+ iterasi
    print("\n=== CORE ATTRIBUTES (muncul 3+ iterasi) ===")
    attr_count = Counter()
    for s in all_schemas:
        for a in s:
            attr_count[a] += 1
    core = [a for a, c in attr_count.items() if c >= 3]
    for a in sorted(core):
        print(f"  {a}: {attr_count[a]}x")

    # Final
    print("\n=== FINAL SCHEMA ===")
    print(f"Attributes: {sorted(schema)}")
    print(f"Core (stable): {sorted(core)}")

    u = llm.last_usage
    cost = u.get("prompt_tokens", 0) * 0.20/1e6 + u.get("completion_tokens", 0) * 1.20/1e6
    print(f"\nLast call cost: RM{cost:.6f}")
    print(f"Total JSON fails: {total_fails}")


if __name__ == "__main__":
    main()