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

STRICT JSON only: {"entity":[...], "slang":[...]}"""

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
    B = _S["llm_batch"]
    for i in range(0, len(items), B):
        chunk = items[i:i+B]
        data = generate_json(json.dumps(chunk, ensure_ascii=False),
                             system=VERIFY, max_tokens=3000)
        if data is None:
            print(f"[discover] batch {i}: parse fail — skip")
            continue
        got = data.get(kind, [])
        ok.extend(got)
        print(f"[discover] batch {i}: +{len(got)} {kind}")
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

    save("entities", sorted(e_ok | set(new_e)))
    save("slang",    sorted(s_ok | set(new_s)))
    print(f"[discover] ✅ {len(e_ok|set(new_e))} entities, {len(s_ok|set(new_s))} slang")