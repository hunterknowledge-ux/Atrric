"""
report.generate — 1 LLM call untuk naratif utama.

Input:  data (dari loader) + picked (dari picker)
Output: {
    "headline":      str,
    "cerita_utama":  str,   # 2-3 paragraf
    "insight":       str,   # kenapa trend ni jadi
    "rekomendasi":   str,   # cadangan untuk pembaca
    "_meta":         {model, tokens_in_est, tokens_out_est, fallback: bool}
}

Kalau LLM fail (None dari generate_json), return fallback naratif supaya
report tetap boleh render (numbers section kekal berguna).
"""

from __future__ import annotations

import json
from typing import Any


# --- Prompt builder ---

SYSTEM_PROMPT = """\
Kau analyst market intelligence untuk Gen Z Malaysia.
Tulis dalam Bahasa Melayu santai + English istilah teknikal bila perlu.
Nada: profesional tapi mesra, macam report B2B untuk agency.
JANGAN guna bullet point. JANGAN guna header. Tulis paragraf je.
JANGAN reka data — guna angka dan quote yang diberi sahaja.
Output MESTI JSON sahaja, tiada teks lain di luar JSON.
"""


def _build_prompt(summary: dict, picked: dict, comments_count: int) -> str:
    # Ringkaskan supaya prompt tak membengkak
    top_ent = ", ".join(
        f"{e['name']}({e['count']})" for e in summary.get("top_entities", [])[:8]
    )
    by_sent = summary.get("by_sentiment", {})
    by_topic = summary.get("by_topic", {})
    top_topics = sorted(by_topic.items(), key=lambda kv: kv[1], reverse=True)[:5]
    topic_str = ", ".join(f"{t}({n})" for t, n in top_topics)

    # Quotes ringkas (buang id/source, kekal text+topic+sentiment)
    quotes_block = "\n".join(
        f"- [{q['topic']}|{q['sentiment']}] {q['text'][:200]}"
        for q in picked.get("top_quotes", [])
    ) or "(tiada quote)"

    # Slang
    slang_block = ", ".join(
        f"{s['word']}({s['count']})" for s in picked.get("slang_curated", [])
    ) or "(tiada)"

    # Topic breakdown ringkas
    tb_block = "\n".join(
        f"- {tb['topic']}: {tb['count']} komen ({tb['pct']}%), "
        f"+{tb['sentiment']['positive']}/-{tb['sentiment']['negative']}/"
        f"~{tb['sentiment']['neutral']}, top: {', '.join(tb['top_entities'])}"
        for tb in picked.get("topic_breakdown", [])
    ) or "(tiada)"

    return f"""Data snapshot (Gen Z Malaysia, {comments_count} komen dianalisis):

SENTIMENT: pos={by_sent.get('positive',0)} neg={by_sent.get('negative',0)} neu={by_sent.get('neutral',0)}
TOP TOPICS: {topic_str}
TOP ENTITIES: {top_ent}
SLANG VIRAL: {slang_block}

TOPIC BREAKDOWN:
{tb_block}

CONTOH SUARA RAKYAT:
{quotes_block}

Tulis report dalam JSON dengan 4 field ini (semua string, guna \\n\\n untuk pisah paragraf kalau perlu):

{{
  "headline": "satu ayat hook, 10-15 patah, grab attention tapi jujur",
  "cerita_utama": "2-3 paragraf naratif — apa yang Gen Z Malaysia risau/bual bulan ni. Guna angka sentimen + topik. Sebut entity utama (PTPTN, HAZIQ, dll). Rujuk slang sebagai signature budaya.",
  "insight": "1-2 paragraf — KENAPA trend ni jadi. Sambung sentiment + topic + entity jadi tafsiran. Contoh: 'Resah PTPTN ni bukan pasal duit sahaja — ia simbol tekanan sistemik terhadap generasi yang baru masuk alam dewasa.'",
  "rekomendasi": "1-2 paragraf — cadangan actionable untuk pembaca B2B. Contoh: agency, brand, researcher. Nada: konstruktif, bukan menggurui."
}}

Output JSON sahaja. Tiada teks sebelum atau selepas JSON."""


# --- Fallback ---

def _fallback(summary: dict) -> dict:
    by_sent = summary.get("by_sentiment", {})
    total = summary.get("total_comments", 0)
    neg = by_sent.get("negative", 0)
    pct = round(100.0 * neg / total, 1) if total else 0
    return {
        "headline": f"{total} suara Gen Z Malaysia dianalisis — {pct}% membawa nada negatif.",
        "cerita_utama": (
            f"Analisis {total} komen dari pelbagai platform menunjukkan dominasi "
            f"sentiment negatif ({pct}%). Topik utama adalah sosial dan pendidikan, "
            "dengan PTPTN, HAZIQ, dan SPM sebagai entiti paling kerap disebut.\n\n"
            "(Naratif penuh tidak dapat dijana oleh LLM pada masa ini. "
            "Bahagian angka di bawah masih boleh dirujuk.)"
        ),
        "insight": "Analisis kualitatif tidak tersedia. Sila rujuk snapshot angka untuk gambaran kuantitatif.",
        "rekomendasi": "Jalankan semula report layer apabila LLM API kembali tersedia.",
    }


# --- Public API ---

def generate_narrative(data: dict, picked: dict, model: str | None = None) -> dict:
    """
    Panggil LLM 1 kali untuk naratif utama.
    Return dict dengan 4 field naratif + _meta.
    """
    summary = data.get("summary", {})
    comments_count = data.get("meta", {}).get("total_loaded", 0)

    prompt = _build_prompt(summary, picked, comments_count)

    try:
        from core.llm import generate_json
    except ImportError as e:
        result = _fallback(summary)
        result["_meta"] = {
            "model": "fallback",
            "reason": f"import error: {e}",
            "fallback": True,
        }
        return result

    kwargs: dict[str, Any] = {
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "max_tokens": 1500,
    }
    if model:
        kwargs["model"] = model

    try:
        raw = generate_json(**kwargs)
    except Exception as e:
        result = _fallback(summary)
        result["_meta"] = {
            "model": "fallback",
            "reason": f"llm error: {e}",
            "fallback": True,
        }
        return result

    # Validate shape
    required = ("headline", "cerita_utama", "insight", "rekomendasi")
    if not isinstance(raw, dict) or not all(k in raw for k in required):
        result = _fallback(summary)
        result["_meta"] = {
            "model": "fallback",
            "reason": "invalid LLM response shape",
            "raw_preview": str(raw)[:200],
            "fallback": True,
        }
        return result

    # Est token (rough — 1 token ≈ 4 chars)
    tokens_in_est = len(prompt) // 4
    tokens_out_est = sum(len(str(raw[k])) for k in required) // 4

    raw["_meta"] = {
        "model": model or "default (ilmu-mini-v3.3)",
        "tokens_in_est": tokens_in_est,
        "tokens_out_est": tokens_out_est,
        "fallback": False,
    }
    return raw


# --- CLI self-test (python -m report.generate) ---

if __name__ == "__main__":
    import sys
    from report.loader import load_all
    from report.picker import pick_all

    print("=== GENERATE SELF-TEST ===")
    print("Loading data + picking...")
    data = load_all()
    picked = pick_all(data)

    print(f"Prompt char count (est): building...")
    # Build prompt untuk estimate kos tanpa call LLM
    prompt = _build_prompt(data["summary"], picked, data["meta"]["total_loaded"])
    est_in = len(prompt) // 4
    print(f"  input tokens  : ~{est_in}")
    print(f"  output tokens : ~1500 (max)")
    # ilmu-mini-v3.3 rate assumption: ~RM0.38 / 1M token
    cost_est = (est_in + 1500) * 0.38 / 1_000_000
    print(f"  cost estimate : ~RM{cost_est:.6f} (ilmu-mini-v3.3)")
    print()

    # Confirm dulu
    if "--yes" not in sys.argv:
        ans = input("Run LLM call? [y/N] ").strip().lower()
        if ans != "y":
            print("Cancelled.")
            sys.exit(0)

    print("Calling LLM...")
    result = generate_narrative(data, picked)
    print()
    print("=== RESULT ===")
    print(f"model     : {result['_meta'].get('model')}")
    print(f"fallback  : {result['_meta'].get('fallback')}")
    print(f"tokens    : in~{result['_meta'].get('tokens_in_est')} out~{result['_meta'].get('tokens_out_est')}")
    print()
    print(f"HEADLINE:\n  {result['headline']}\n")
    print(f"CERITA UTAMA:\n  {result['cerita_utama'][:400]}...\n")
    print(f"INSIGHT:\n  {result['insight'][:300]}...\n")
    print(f"REKOMENDASI:\n  {result['rekomendasi'][:300]}...")