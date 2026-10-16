import json
import re
from collections import Counter
from pathlib import Path
from .store import load, save
from .normalize import tokens
from core.llm import generate_json

_S = json.loads((Path(__file__).parent / "settings.json").read_text())

VERIFY = """You are an expert in Malaysian social media language (Bahasa Melayu + Manglish + Gen-Z).

For each item {word, ctx}, decide ONE of:
- "entity": proper noun, brand, org, person, country, acronym
- "slang":  colloquial/code word/non-standard BM/internet slang
- "normal": ordinary Bahasa Malaysia or English word

IMPORTANT — ordinary BM words are NOT slang, even if frequent:
atas, bagi, baik, balik, banyak, baru, begitu, beli, ambil, pergi, buat, kata, sudah, boleh, mahu, minta, tengok, dengar

REAL slang examples (label these):
strawberi, acah kuat, skibidi, rizz, delulu, tercekik, padu, gempak, syok, membazir

REAL entity examples (label these):
SISPAA, TikTok, Shopee, KPM, Anwar, Malaysia, Gen Z, Millennials

Read the context sentence. If the word is ordinary BM in that context -> "normal".

STRICT JSON only: {"entity":["word1","word2"], "slang":["word1","word2"]}
Return each item as a PLAIN STRING, not an object."""

def _coerce(x):
    """Force item to string. LLM sometimes returns dicts."""
    if x is None:
        return None
    if isinstance(x, str):
        s = x.strip()
        return s or None
    if isinstance(x, dict):
        for k in ("word", "name", "text", "value", "entity", "slang"):
            if k in x:
                v = x[k]
                if isinstance(v, str):
                    return v.strip() or None
        v = next(iter(x.values()), None)
        return str(v).strip() if v is not None else None
    return str(x).strip() or None

def _normalize_entities(items):
    """Merge PTPTN/Ptptn/ptptn -> PTPTN. Prefer uppercase form when available.
    Multi-word names (e.g. 'Gen Z') keep title case."""
    seen = {}
    for x in items:
        if not isinstance(x, str):
            continue
        x = x.strip()
        if not x:
            continue

        has_space = " " in x
        if has_space:
            # Multi-word: title-case normalize, key = lowercase
            key = x.lower()
            canon = x  # keep first-seen casing for multi-word
        elif x.isupper() and len(x) <= 8:
            # Short all-caps acronym: keep as-is
            key = x
            canon = x
        else:
            # Single word mixed-case: uppercase if <= 8 chars, else lowercase
            if len(x) <= 8:
                key = x.upper()
                canon = x.upper()
            else:
                key = x.lower()
                canon = x

        if key not in seen:
            seen[key] = canon

    return sorted(seen.values())

def _cand_entities(texts):
    c = Counter()
    for t in texts:
        for sent in t.split(". "):
            for m in re.finditer(r"\b([A-Z][A-Za-z]+|[A-Z]{2,})\b", sent):
                if m.start() == 0:
                    continue
                c[m.group(1)] += 1
    return [w for w, n in c.items() if n >= _S["min_count_entity"]]

def _cand_slang(texts):
    c = Counter()
    for t in texts:
        for w in tokens(t.lower()):
            if len(w) >= _S["min_word_length"]:
                c[w] += 1
    return [w for w, n in c.items() if n >= _S["min_count_slang"]]

def _verify(cands, kind, texts):
    if not cands:
        return []
    def ctx_for(w):
        pat = re.compile(rf"\b{re.escape(w)}\b", re.I)
        for t in texts:
            for sent in t.split(". "):
                if pat.search(sent):
                    return sent[:200]
        return ""
    items = [{"word": w, "ctx": ctx_for(w)} for w in cands]

    ok = []
    B = min(_S["llm_batch"], 20)

    def _do_batch(chunk, tag=""):
        try:
            data = generate_json(json.dumps(chunk, ensure_ascii=False),
                                 system=VERIFY, max_tokens=4000)
        except Exception as e:
            print(f"[discover] {kind} {tag} error: {e}")
            return []
        if data is None:
            return None
        got = data.get(kind, [])
        out = []
        for x in got:
            s = _coerce(x)
            if s:
                out.append(s)
        return out

    for i in range(0, len(items), B):
        chunk = items[i:i+B]
        res = _do_batch(chunk, f"batch {i}")
        if res is None:
            print(f"[discover] {kind} batch {i}: parse fail — retry split")
            half = max(1, len(chunk) // 2)
            res = []
            for j in range(0, len(chunk), half):
                sub = chunk[j:j+half]
                r2 = _do_batch(sub, f"batch {i}+{j}")
                if r2:
                    res.extend(r2)
        ok.extend(res)
        print(f"[discover] {kind} batch {i}: +{len(res)}")

    return ok

def run(items):
    texts = [i["text"] for i in items]
    print(f"[discover] {len(texts)} teks")
    e_c = _cand_entities(texts)
    s_c = _cand_slang(texts)
    print(f"[discover] calon: {len(e_c)} entity, {len(s_c)} slang")

    e_ok = set(load("entities"))
    s_ok = set(load("slang"))
    e_new = [c for c in e_c if c not in e_ok]
    s_new = [c for c in s_c
             if c not in s_ok and c.lower() not in {x.lower() for x in e_ok}]

    print(f"[discover] sahkan via LLM: {len(e_new)} + {len(s_new)}")
    new_e = _verify(e_new, "entity", texts)
    new_s = _verify(s_new, "slang", texts)

    # Coerce to strings
    raw_e = {x for x in new_e if isinstance(x, str) and x}
    raw_s = {x for x in new_s if isinstance(x, str) and x}

    # Merge existing + new, then normalize entities
    all_e = _normalize_entities(list(e_ok | raw_e))
    all_s = sorted({x.lower() if not (" " in x) else x for x in (s_ok | raw_s)})

    save("entities", all_e)
    save("slang", all_s)
    print(f"[discover] ✅ {len(all_e)} entities, {len(all_s)} slang")