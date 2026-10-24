"""
core/ontology_induction_poc.py

Iterative Schema Induction untuk ATRRIC — v3.
Berdasarkan kertas: Avram et al. (Okt 2026)

v3 changes:
- Retry dengan exponential backoff (SSL/network fail)
- Delay 0.5s antara call (elak rate limit)
- Sample 20 chunk (bukan 50)
- 5 iterasi max (bukan 10)
- Save progress (resume kalau crash)
"""

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.env_loader import load_env

load_env()

from core.ilmu_llm import IlmuLLM
from core.store import _get_db

PROGRESS_FILE = _ROOT / "ontology_progress.json"
SAMPLE_SIZE = 20
MAX_ITERATIONS = 5
DELAY_BETWEEN_CALLS = 0.5
MAX_RETRIES = 3


# ══════════════════════════════════════════════════════════
# STEP 1 — EXTRACT (per chunk, dengan retry)
# ══════════════════════════════════════════════════════════

EXTRACT_PROMPT = """Extract implicit attributes from this Malaysian social media comment.

DO NOT use a fixed schema. Discover whatever attributes are actually present.

Output a JSON list of objects:
[{{"attribute": "...", "value": "..."}}, ...]

Rules:
- Attribute names: free-form, in English, lowercase
- Only extract attributes CLEARLY stated or strongly implied
- Focus on: emotion, topic, target_group, stance, tone, generation
- Skip meta: observation, reference, response
- Skip short/empty chunks
- No explanation. Output JSON only.

Comment:
{chunk}

Output:"""


def _safe_generate(llm, prompt, max_tokens, temperature, chunk_id):
    """Generate dengan retry + backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            return llm.generate(prompt, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            wait = 2 ** attempt
            err_type = type(e).__name__
            if attempt < MAX_RETRIES - 1:
                print(f"    [retry {attempt+1}] chunk {chunk_id}: {err_type}, wait {wait}s")
                time.sleep(wait)
            else:
                print(f"    [FAIL] chunk {chunk_id}: {err_type}")
    return None


def _strip_fence(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return raw


def extract_attributes(llm, chunks):
    all_attrs = []
    fails = 0
    for i, chunk in enumerate(chunks):
        print(f"  chunk {i+1}/{len(chunks)}...", end=" ", flush=True)
        prompt = EXTRACT_PROMPT.format(chunk=chunk[:500])
        raw = _safe_generate(llm, prompt, 800, 0.3, i)

        if raw is None:
            fails += 1
            print("FAIL")
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        raw = _strip_fence(raw)
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = data.get("attributes", data.get("data", []))
            if isinstance(data, list):
                all_attrs.extend(data)
                print(f"ok ({len(data)} attrs)")
            else:
                print("not list")
                fails += 1
        except json.JSONDecodeError:
            print("json fail")
            fails += 1

        time.sleep(DELAY_BETWEEN_CALLS)

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
# STEP 3 — CONSOLIDATE
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
    raw = _safe_generate(llm, prompt, 1500, 0.2, "consolidate")

    if raw is None:
        return [{"canonical": n, "aliases": [n]} for n in names]

    raw = _strip_fence(raw)
    try:
        clusters = json.loads(raw)
        if isinstance(clusters, list):
            return clusters
    except json.JSONDecodeError:
        pass

    return [{"canonical": n, "aliases": [n]} for n in names]


# ══════════════════════════════════════════════════════════
# STEP 4 — CONVERGENCE
# ══════════════════════════════════════════════════════════

def is_converged(prev_schema, schema, threshold=0.8):
    if not prev_schema or not schema:
        return False
    intersection = len(prev_schema & schema)
    union = len(prev_schema | schema)
    if union == 0:
        return False
    return (intersection / union) >= threshold


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def load_sample_chunks(n=SAMPLE_SIZE):
    db = _get_db()
    with open(db.metadata_file) as f:
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


def save_progress(iteration, schemas):
    PROGRESS_FILE.write_text(json.dumps({
        "last_iter": iteration,
        "schemas": [sorted(s) for s in schemas],
    }, indent=2))


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            data = json.loads(PROGRESS_FILE.read_text())
            return data.get("last_iter", 0), [set(s) for s in data.get("schemas", [])]
        except Exception:
            pass
    return 0, []


def main():
    print("=== ONTOLOGY INDUCTION v3 ===\n")

    llm = IlmuLLM()
    print(f"Model: {llm.model}")

    chunks = load_sample_chunks(SAMPLE_SIZE)
    print(f"Sample: {len(chunks)} chunks")
    print(f"Max iterations: {MAX_ITERATIONS}")
    print("Est. cost: ~RM0.05\n")

    start_iter, all_schemas = load_progress()
    if start_iter > 0:
        print(f"Resuming from iteration {start_iter + 1}")
        prev_schema = all_schemas[-1] if all_schemas else None
    else:
        start_iter = 1
        prev_schema = None
        all_schemas = []

    schema = set()

    try:
        for iteration in range(start_iter, MAX_ITERATIONS + 1):
            print(f"\n--- Iteration {iteration} ---")

            attrs, fails = extract_attributes(llm, chunks)
            print(f"  Extracted: {len(attrs)} pairs (fails: {fails})")

            counter = aggregate(attrs)
            print(f"  Unique: {len(counter)}")
            print(f"  Top 5: {counter.most_common(5)}")

            clusters = consolidate(llm, counter, top_k=20)
            schema = {c["canonical"] for c in clusters if c.get("canonical")}
            all_schemas.append(schema)
            print(f"  Schema ({len(schema)}): {sorted(schema)}")

            save_progress(iteration, all_schemas)

            if is_converged(prev_schema, schema):
                print(f"  ✅ CONVERGED at iteration {iteration}")
                break

            prev_schema = schema

    except KeyboardInterrupt:
        print("\n\n[!] Interrupted. Progress saved.")
        print("    Run again untuk resume.")

    # Core attributes
    print("\n=== CORE ATTRIBUTES (muncul 3+ iterasi) ===")
    attr_count = Counter()
    for s in all_schemas:
        for a in s:
            attr_count[a] += 1
    core = [a for a, c in attr_count.items() if c >= 3]
    for a in sorted(core):
        print(f"  {a}: {attr_count[a]}x")

    print("\n=== FINAL SCHEMA ===")
    print(f"Attributes: {sorted(schema)}")
    print(f"Core (stable): {sorted(core)}")

    if PROGRESS_FILE.exists():
        print(f"\n💡 Delete progress to restart: rm {PROGRESS_FILE.name}")


if __name__ == "__main__":
    main()