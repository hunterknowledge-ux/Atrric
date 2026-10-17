"""
report.generate — 1 LLM call untuk naratif utama + tapis slang.
"""

from __future__ import annotations
import json
from typing import Any

# --- PROMPT BARU: STRICT ANALYST ---
SYSTEM_PROMPT = """\
Kau adalah Senior Market Intelligence Analyst untuk Gen Z Malaysia.
Tugas kau adalah membedah data dan menghasilkan insight tajam untuk agensi B2B.

PERATURAN KETAT (WAJIB PATUH):
1. JANGAN guna ayat klise/generik (contoh terlarang: "tekanan ekonomi", "perlu pendekatan empati", "kempen komunikasi yang responsif").
2. Setiap Insight dan Rekomendasi MESTI merujuk kepada sekurang-kurangnya SATU entiti spesifik (cth: PTPTN, HAZIQ) dan SATU angka dari data.
3. Bagi konteks kepada entiti. Jangan sekadar cakap "HAZIQ disebut 36 kali". Cakap KENAPA (cth: "HAZIQ dipuji kerana...").
4. TAPIS senarai SLANG VIRAL. Buang singkatan Melayu biasa (cth: utk, mre, sbb). Kekalkan HANYA slang budaya Gen Z sebenar. Masukkan hasil tapis ke dalam JSON field "slang_curated".
5. JANGAN guna bullet point dalam naratif. Tulis perenggan padu.
6. PENTING: Setiap perenggan dalam "cerita_utama" MESTI dipisah dengan \\n\\n.
7. Output MESTI JSON sahaja, tiada teks lain di luar JSON.
"""

def _build_prompt(summary: dict, picked: dict, comments_count: int) -> str:
    top_ent = ", ".join(f"{e['name']}({e['count']})" for e in summary.get("top_entities", [])[:8])
    by_sent = summary.get("by_sentiment", {})
    by_topic = summary.get("by_topic", {})
    top_topics = sorted(by_topic.items(), key=lambda kv: kv[1], reverse=True)[:5]
    topic_str = ", ".join(f"{t}({n})" for t, n in top_topics)
    src_dist = picked.get("source_dist", "unknown")

    quotes_block = "\n".join(
        f"- [{q['topic']}|{q['sentiment']}] {q['text'][:200]}"
        for q in picked.get("top_quotes", [])
    ) or "(tiada quote)"

    slang_block = ", ".join(
        f"{s['word']}({s['count']})" for s in picked.get("slang_raw", [])
    ) or "(tiada)"

    tb_block = "\n".join(
        f"- {tb['topic']}: {tb['count']} komen ({tb['pct']}%), "
        f"+{tb['sentiment']['positive']}/-{tb['sentiment']['negative']}/"
        f"~{tb['sentiment']['neutral']}, top: {', '.join(tb['top_entities'])}"
        for tb in picked.get("topic_breakdown", [])
    ) or "(tiada)"

    return f"""Data snapshot (Gen Z Malaysia, {comments_count} komen dianalisis):

SUMBER DATA (Source Distribution): {src_dist}
SENTIMENT: pos={by_sent.get('positive',0)} neg={by_sent.get('negative',0)} neu={by_sent.get('neutral',0)}
TOP TOPICS: {topic_str}
TOP ENTITIES: {top_ent}
SLANG VIRAL (MENTAH): {slang_block}

TOPIC BREAKDOWN:
{tb_block}

CONTOH SUARA RAKYAT:
{quotes_block}

Tulis report dalam JSON dengan 5 field ini (semua string, guna \\n\\n untuk pisah perenggan):

{{
  "headline": "satu ayat hook, 10-15 patah, grab attention. Sebut angka/entiti.",
  "cerita_utama": "2-3 perenggan naratif. Guna angka sentimen + topik. Beri konteks KENAPA entiti ini disebut. Rujuk source distribution.",
  "insight": "1-2 perenggan. Analisis KENAPA trend ni jadi (bukan sekadar apa). Sambung sentiment + topik + entity jadi tafsiran tajam.",
  "rekomendasi": "1-2 perenggan. Cadangan STRATEGIK spesifik untuk agensi B2B. Elak ayat klise.",
  "slang_curated": [
    {{"word": "ceplos", "count": 8, "note": "gagal / tak lepas"}}
  ]
}}

Output JSON sahaja."""

def _fallback(summary: dict, picked: dict) -> dict:
    by_sent = summary.get("by_sentiment", {})
    total = summary.get("total_comments", 0)
    neg = by_sent.get("negative", 0)
    pct = round(100.0 * neg / total, 1) if total else 0
    
    raw_slang = picked.get("slang_raw", [])[:5]
    slang_fallback = [{"word": s["word"], "count": s["count"], "note": "slanga Gen Z"} for s in raw_slang]

    return {
        "headline": f"{total} suara Gen Z Malaysia dianalisis — {pct}% membawa nada negatif.",
        "cerita_utama": f"Analisis {total} komen dari pelbagai platform menunjukkan dominasi sentiment negatif ({pct}%).\n\n(Naratif penuh tidak dapat dijana oleh LLM pada masa ini. Bahagian angka di bawah masih boleh dirujuk.)",
        "insight": "Analisis kualitatif tidak tersedia. Sila rujuk snapshot angka untuk gambaran kuantitatif.",
        "rekomendasi": "Jalankan semula report layer apabila LLM API kembali tersedia.",
        "slang_curated": slang_fallback,
    }

def generate_narrative(data: dict, picked: dict, model: str | None = None) -> dict:
    summary = data.get("summary", {})
    comments_count = data.get("meta", {}).get("total_loaded", 0)

    prompt = _build_prompt(summary, picked, comments_count)

    try:
        from core.llm import generate_json
    except ImportError as e:
        result = _fallback(summary, picked)
        result["_meta"] = {"model": "fallback", "reason": f"import error: {e}", "fallback": True}
        return result

    kwargs: dict[str, Any] = {
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "max_tokens": 1800,
        "task": "report"
    }
    if model:
        kwargs["model"] = model

    try:
        raw = generate_json(**kwargs)
    except Exception as e:
        result = _fallback(summary, picked)
        result["_meta"] = {"model": "fallback", "reason": f"llm error: {e}", "fallback": True}
        return result

    required = ("headline", "cerita_utama", "insight", "rekomendasi", "slang_curated")
    if not isinstance(raw, dict) or not all(k in raw for k in required):
        result = _fallback(summary, picked)
        result["_meta"] = {"model": "fallback", "reason": "invalid LLM response shape", "fallback": True}
        return result

    tokens_in_est = len(prompt) // 4
    tokens_out_est = sum(len(str(raw[k])) for k in required) // 4

    raw["_meta"] = {
        "model": model or "default (router)",
        "tokens_in_est": tokens_in_est,
        "tokens_out_est": tokens_out_est,
        "fallback": False,
    }
    return raw