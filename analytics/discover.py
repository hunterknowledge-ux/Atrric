import json
from collections import Counter
from pathlib import Path
from .store import load, save
from .normalize import tokens
from core.llm import generate_json

_S = json.loads((Path(__file__).parent / "settings.json").read_text())

VERIFY = """Classify Malaysian social media tokens.
For each token return ONE of:
- "entity": proper noun/brand/org/acronym
- "slang": colloquial/code word/Gen-Z term
- "normal": ordinary BM/English word
STRICT JSON only: {"entity":[...], "slang":[...]}"""

def _cand_entities(texts):
    c = Counter()
    for t in texts:
        for sent in t.split(". "):
            for m in __import__("re").finditer(r"\b([A-Z][A-Za-z]+|[A-Z]{2,})\b", sent):
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

def _verify(cands, kind):
    if not cands: return []
    ok = []
    B = _S["llm_batch"]
    for i in range(0, len(cands), B):
        chunk = cands[i:i+B]
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
    e_c = _cand_entities(texts); s_c = _cand_slang(texts)
    print(f"[discover] calon: {len(e_c)} entity, {len(s_c)} slang")

    e_ok = set(load("entities")); s_ok = set(load("slang"))
    e_new = [c for c in e_c if c not in e_ok]
    s_new = [c for c in s_c if c not in s_ok and c.lower() not in {x.lower() for x in e_ok}]

    print(f"[discover] sahkan via LLM: {len(e_new)} + {len(s_new)}")
    new_e = _verify(e_new, "entity")
    new_s = _verify(s_new, "slang")

    save("entities", sorted(e_ok | set(new_e)))
    save("slang",    sorted(s_ok | set(new_s)))
    print(f"[discover] ✅ {len(e_ok|set(new_e))} entities, {len(s_ok|set(new_s))} slang")
