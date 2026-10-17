import json
import re
import time
from collections import Counter
from pathlib import Path
from .store import load, save
from .normalize import tokens
from core.llm import generate_json

_S = json.loads((Path(__file__).parent / "settings.json").read_text())

VERIFY = """You are an expert in Malaysian social media language.
For each item {word, ctx}, decide ONE of:
- "entity": proper noun, brand, org, person, country, acronym (e.g. SISPAA, TikTok)
- "slang":  colloquial/code word/internet slang (e.g. strawberi, skibidi, rizz, padu)
- "normal": ordinary Bahasa Malaysia OR English word (e.g. bayar, cuba, school, value)

IMPORTANT:
1. Standard BM words are NOT slang.
2. Standard English words are NOT slang.
3. Read context. If normal, return "normal".

STRICT JSON only: {"entity":["word1"], "slang":["word2"]}"""

TOPIC_DISCOVER = """Analyze Malaysian social media comments.
The existing topics we already have are: {existing}

Propose 3-5 NEW broad topic categories that are NOT in the existing list but are highly relevant to these comments.
Must be lowercase, 1-2 words, snake_case if needed.
Do NOT use specific entities or names.

STRICT JSON only: {"topics":["new_topic1","new_topic2"]}"""

def _coerce(x):
    if x is None: return None
    if isinstance(x, str):
        s = x.strip(); return s or None
    if isinstance(x, dict):
        for k in ("word","name","text","value","entity","slang"):
            if k in x:
                v = x[k]
                if isinstance(v, str): return v.strip() or None
        v = next(iter(x.values()), None)
        return str(v).strip() if v is not None else None
    return str(x).strip() or None

def _discover_topics(texts, existing_topics):
    if not texts: return []
    sample = [t[:300] for t in texts[:60]]
    existing_str = ", ".join(existing_topics) if existing_topics else "none"
    
    sys_prompt = TOPIC_DISCOVER.replace("{existing}", existing_str)
    
    try:
        time.sleep(1.5)
        data = generate_json("Comments:\n" + "\n".join(f"- {t}" for t in sample),
                             system=sys_prompt, max_tokens=600, task="discover")
    except Exception as e:
        print(f"[discover] topic error: {e}"); return []
    if not data: return []
    
    # Hanya ambil topik yang belum ada dalam senarai lama
    new_topics = {str(t).strip().lower() for t in data.get("topics", []) if t}
    return sorted(new_topics - set(existing_topics))

def _cand_entities(texts):
    c = Counter()
    for t in texts:
        for sent in t.split(". "):
            for m in re.finditer(r"\b([A-Z][A-Za-z]+|[A-Z]{2,})\b", sent):
                if m.start() == 0: continue
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
    if not cands: return []
    def ctx_for(w):
        pat = re.compile(rf"\b{re.escape(w)}\b", re.I)
        for t in texts:
            for sent in t.split(". "):
                if pat.search(sent): return sent[:150]
        return ""
    items = [{"word": w, "ctx": ctx_for(w)} for w in cands]
    ok = []
    B = _S.get("llm_batch", 10)
    
    def _do_batch(chunk, tag=""):
        try:
            time.sleep(1.5) # Elak rate limit
            data = generate_json(json.dumps(chunk, ensure_ascii=False),
                                 system=VERIFY, max_tokens=4000, task="discover")
        except Exception as e:
            print(f"[discover] {kind} {tag} error: {e}"); return []
        if data is None: return None
        out = []
        for x in data.get(kind, []):
            s = _coerce(x)
            if s: out.append(s)
        return out
        
    for i in range(0, len(items), B):
        chunk = items[i:i+B]
        res = _do_batch(chunk, f"batch {i}")
        if res is None:
            print(f"[discover] {kind} batch {i}: parse fail")
            res = []
        ok.extend(res)
        print(f"[discover] {kind} batch {i}: +{len(res)}")
    return ok

def _normalize_entities(items):
    seen = {}
    for x in items:
        if not isinstance(x, str): continue
        x = x.strip()
        if not x: continue
        if " " in x:
            key, canon = x.lower(), x
        elif x.isupper() and len(x) <= 8:
            key = canon = x
        else:
            if len(x) <= 6: key = canon = x.upper()
            else: key, canon = x.lower(), x
        if key not in seen: seen[key] = canon
    return sorted(seen.values())

def run(items):
    texts = [i["text"] for i in items]
    print(f"[discover] {len(texts)} teks")

    # --- TOPIC DISCOVERY (Automatic Merge) ---
    existing_topics = load("topics")
    print(f"[discover] Semak topik baru (sedia ada: {len(existing_topics)})...")
    
    new_topics = _discover_topics(texts, existing_topics)
    if new_topics:
        merged_topics = sorted(list(set(existing_topics) | set(new_topics)))
        save("topics", merged_topics)
        print(f"[discover] ✅ +{len(new_topics)} topik baru ditambah. Total: {len(merged_topics)}")
    else:
        print("[discover] Tiada topik baru ditemui.")

    # --- ENTITY & SLANG DISCOVERY ---
    e_c = _cand_entities(texts)
    s_c = _cand_slang(texts)
    print(f"[discover] calon: {len(e_c)} entity, {len(s_c)} slang")

    e_ok = set(load("entities")); s_ok = set(load("slang"))
    e_new = [c for c in e_c if c not in e_ok]
    e_lower = {x.lower() for x in e_ok}
    s_new = [c for c in s_c if c not in s_ok and c.lower() not in e_lower]

    print(f"[discover] sahkan via LLM: {len(e_new)} + {len(s_new)}")
    new_e = _verify(e_new, "entity", texts)
    new_s = _verify(s_new, "slang", texts)

    raw_e = {x for x in new_e if isinstance(x, str) and x}
    raw_s = {x for x in new_s if isinstance(x, str) and x}

    all_e = _normalize_entities(list(e_ok | raw_e))
    all_s = sorted({x.lower() if " " not in x else x for x in (s_ok | raw_s)})

    save("entities", all_e)
    save("slang", all_s)
    print(f"[discover] ✅ {len(all_e)} entities, {len(all_s)} slang")