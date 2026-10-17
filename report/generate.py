"""
report.generate — 1 LLM call untuk naratif utama + tapis slang.
"""

from __future__ import annotations
import json
from typing import Any

SYSTEM_PROMPT = """\
Kau analyst market intelligence untuk Gen Z Malaysia.
Tulis dalam Bahasa Melayu santai + English istilah teknikal bila perlu.
Nada: profesional tapi mesra, macam report B2B untuk agency.

TUGAS KAU:
1. Tulis naratif mengikut format JSON yang diminta.
2. TAPIS senarai SLANG VIRAL yang diberi. Buang singkatan Melayu biasa (contoh: utk, mre, sbb, lah). Kekalkan HANYA slang budaya Gen Z sebenar (contoh: ceplos, sambung belajar). Masukkan hasil tapis ke dalam JSON field "slang_curated".

JANGAN guna bullet point. JANGAN guna header. Tulis paragraf je.
JANGAN reka data — guna angka dan quote yang diberi sahaja.
PENTING: Setiap paragraf dalam "cerita_utama" MESTI dipisah dengan \\n\\n.
Output MESTI JSON sahaja, tiada teks lain di luar JSON.
"""

def _build_prompt(summary: dict, picked: dict, comments_count: int) -> str:
    top_ent = ", ".join(f"{e['name']}({e['count']})" for e in summary.get("top_entities", [])[:8])
    by_sent = summary.get("by_sentiment", {})
    by_topic = summary.get("by_topic", {})
    top_topics = sorted(by_topic.items(), key=lambda kv: kv[1], reverse=True)[:5]
    topic_str = ", ".join(f"{t}({n})" for t, n in top_topics)

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

SENTIMENT: pos={by_sent.get('positive',0)} neg={by_sent.get('negative',0)} neu={by_sent.get('neutral',0)}
TOP TOPICS: {topic_str}
TOP ENTITIES: {top_ent}
SLANG VIRAL (MENTAH): {slang_block}

TOPIC BREAKDOWN:
{tb_block}

CONTOH SUARA RAKYAT:
{quotes_block}

Tulis report dalam JSON dengan 5 field ini (semua string, guna \\n\\n untuk pisah paragraf):

{{
  "headline": "satu ayat hook, 10-15 patah, grab attention tapi jujur",
  "cerita_utama": "2-3 paragraf naratif — apa yang Gen Z Malaysia risau/bual bulan ni. Guna angka sentimen + topik. Sebut entity utama.",
  "insight": "1-2 paragraf — KENAPA trend ni jadi. Sambung sentiment + topic + entity jadi tafsiran.",
  "rekomendasi": "1-2 paragraf — cadangan actionable untuk pembaca B2B. Nada: konstruktif.",
  "slang_curated": [
    {{"word": "ceplos", "count": 8, "note": "gagal / tak lepas"}},
    {{"word": "sambung belajar", "count": 7, "note": "teruskan pengajian"}}
  ]
}}

Output JSON sahaja."""

def _fallback(summary: dict, picked: dict) -> dict:
    by_sent = summary.get("by_sentiment", {})
    total = summary.get("total_comments", 0)
    neg = by_sent.get("negative", 0)
    pct = round(100.0 * neg / total, 1) if total else 0
    
    # Fallback slang (guna mentah kalau LLM fail)
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
        "max_tokens": 1800, # Naikkan sikit sebab ada slang_curated
        "task": "report"    # Guna Router
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