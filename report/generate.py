"""
report.generate — 2 LLM calls: 1 untuk naratif, 1 untuk tapis kualiti.
"""

from __future__ import annotations
import json
from typing import Any

NARRATIVE_SYSTEM_PROMPT = """\
Kau adalah Senior Market Intelligence Analyst untuk Gen Z Malaysia.
Tugas kau adalah membedah data dan menghasilkan insight tajam untuk agensi B2B.

PERATURAN KETAT:
1. JANGAN guna ayat klise/generik (contoh: "tekanan ekonomi", "perlu pendekatan empati").
2. Setiap Insight dan Rekomendasi MESTI merujuk kepada sekurang-kurangnya SATU entiti spesifik dan SATU angka dari data.
3. Bagi konteks kepada entiti. Cakap KENAPA ia disebut.
4. Tulis perenggan padu. JANGAN guna bullet point.
5. PENTING: Setiap perenggan MESTI dipisah dengan \\n\\n.
6. Output MESTI JSON sahaja.
"""

FILTER_SYSTEM_PROMPT = """\
Kau adalah Editor Kualiti Kanan.
Tugas kau:
1. TAPIS SLANG: Buang singkatan Melayu (utk, sbb), partikel (lah, pon), dan bahasa pasar (gila, hahaha). KEKALKAN HANYA slang budaya Gen Z sebenar (ceplos, red flag, dll). JANGAN masukkan perkataan yang kau nak buang ke dalam JSON.
2. TAPIS QUOTE: Buang quote yang nampak macam iklan/spam (contoh: tawaran pinjaman, kripto, beli rumah). Pilih 5 quote terbaik yang paling ikhlas mewakili suara manusia.

Output MESTI JSON sahaja dengan format:
{
  "slang_curated": [{"word": "ceplos", "count": 8, "note": "gagal"}],
  "quotes_curated": [{"id": "id_quote_1"}, {"id": "id_quote_2"}]
}
"""

def _build_narrative_prompt(summary: dict, picked: dict, comments_count: int) -> str:
    top_ent = ", ".join(f"{e['name']}({e['count']})" for e in summary.get("top_entities", [])[:8])
    by_sent = summary.get("by_sentiment", {})
    by_topic = summary.get("by_topic", {})
    top_topics = sorted(by_topic.items(), key=lambda kv: kv[1], reverse=True)[:5]
    topic_str = ", ".join(f"{t}({n})" for t, n in top_topics)
    src_dist = picked.get("source_dist", "unknown")

    quotes_block = "\n".join(f"- [{q['topic']}|{q['sentiment']}] {q['text'][:200]}" for q in picked.get("top_quotes", [])) or "(tiada quote)"
    tb_block = "\n".join(f"- {tb['topic']}: {tb['count']} komen ({tb['pct']}%), +{tb['sentiment']['positive']}/-{tb['sentiment']['negative']}/~{tb['sentiment']['neutral']}, top: {', '.join(tb['top_entities'])}" for tb in picked.get("topic_breakdown", [])) or "(tiada)"

    return f"""Data snapshot (Gen Z Malaysia, {comments_count} komen):
SUMBER DATA: {src_dist}
SENTIMENT: pos={by_sent.get('positive',0)} neg={by_sent.get('negative',0)} neu={by_sent.get('neutral',0)}
TOP TOPICS: {topic_str}
TOP ENTITIES: {top_ent}

TOPIC BREAKDOWN:
{tb_block}

CONTOH SUARA RAKYAT:
{quotes_block}

Tulis report dalam JSON dengan 4 field ini (semua string, guna \\n\\n untuk pisah perenggan):
{{
  "headline": "satu ayat hook, 10-15 patah, grab attention. Sebut angka/entiti.",
  "cerita_utama": "2-3 perenggan naratif. Beri konteks KENAPA entiti ini disebut.",
  "insight": "1-2 perenggan. Analisis KENAPA trend ni jadi. Sambung sentiment + topik + entity.",
  "rekomendasi": "1-2 perenggan. Cadangan STRATEGIK spesifik. Elak ayat klise."
}}
Output JSON sahaja."""

def _build_filter_prompt(picked: dict) -> str:
    slang_in = json.dumps(picked.get("slang_raw", []), ensure_ascii=False)
    quotes_in = json.dumps([{"id": q["id"], "text": q["text"]} for q in picked.get("top_quotes", [])], ensure_ascii=False)
    return f"SLANG MENTAH:\n{slang_in}\n\nQUOTE MENTAH:\n{quotes_in}"

def _fallback(summary: dict, picked: dict) -> dict:
    by_sent = summary.get("by_sentiment", {})
    total = summary.get("total_comments", 0)
    neg = by_sent.get("negative", 0)
    pct = round(100.0 * neg / total, 1) if total else 0
    return {
        "headline": f"{total} suara Gen Z Malaysia dianalisis — {pct}% membawa nada negatif.",
        "cerita_utama": f"Analisis {total} komen dari pelbagai platform menunjukkan dominasi sentiment negatif ({pct}%).\n\n(Naratif penuh tidak dapat dijana oleh LLM pada masa ini. Bahagian angka di bawah masih boleh dirujuk.)",
        "insight": "Analisis kualitatif tidak tersedia. Sila rujuk snapshot angka untuk gambaran kuantitatif.",
        "rekomendasi": "Jalankan semula report layer apabila LLM API kembali tersedia.",
        "slang_curated": [],
        "quotes_curated": [q["id"] for q in picked.get("top_quotes", [])[:5]]
    }

def generate_narrative(data: dict, picked: dict, model: str | None = None) -> dict:
    summary = data.get("summary", {})
    comments_count = data.get("meta", {}).get("total_loaded", 0)

    try:
        from core.llm import generate_json
    except ImportError as e:
        result = _fallback(summary, picked)
        result["_meta"] = {"model": "fallback", "reason": f"import error: {e}", "fallback": True}
        return result

    # --- CALL 1: Narrative ---
    prompt = _build_narrative_prompt(summary, picked, comments_count)
    kwargs: dict[str, Any] = {"prompt": prompt, "system": NARRATIVE_SYSTEM_PROMPT, "max_tokens": 1500, "task": "report"}
    if model: kwargs["model"] = model

    try:
        raw_narrative = generate_json(**kwargs)
    except Exception as e:
        result = _fallback(summary, picked)
        result["_meta"] = {"model": "fallback", "reason": f"llm error: {e}", "fallback": True}
        return result

    required = ("headline", "cerita_utama", "insight", "rekomendasi")
    if not isinstance(raw_narrative, dict) or not all(k in raw_narrative for k in required):
        result = _fallback(summary, picked)
        result["_meta"] = {"model": "fallback", "reason": "invalid LLM response shape", "fallback": True}
        return result

    # --- CALL 2: Quality Filter (Slang + Quotes) ---
    filter_prompt = _build_filter_prompt(picked)
    slang_kwargs = {"prompt": filter_prompt, "system": FILTER_SYSTEM_PROMPT, "max_tokens": 800, "task": "report"}
    if model: slang_kwargs["model"] = model

    try:
        raw_filter = generate_json(**slang_kwargs)
        
        # --- THE PYTHON HACK (Untuk pastikan takde slang sampah terlepas) ---
        raw_slang = raw_filter.get("slang_curated", []) if isinstance(raw_filter, dict) else []
        slang_curated = []
        for s in raw_slang:
            note = s.get("note", "").lower()
            if "buang" in note or "pasar" in note or "singkatan" in note:
                continue # Skip kalau LLM sendiri cakap benda tu sampah
            slang_curated.append(s)

        quotes_curated = raw_filter.get("quotes_curated", []) if isinstance(raw_filter, dict) else []
        if not isinstance(quotes_curated, list) or len(quotes_curated) < 3:
            quotes_curated = [{"id": q["id"]} for q in picked.get("top_quotes", [])[:5]]
    except Exception:
        slang_curated = []
        quotes_curated = [{"id": q["id"]} for q in picked.get("top_quotes", [])[:5]]

    raw_narrative["slang_curated"] = slang_curated
    raw_narrative["quotes_curated"] = quotes_curated
    raw_narrative["_meta"] = {
        "model": model or "default (router)",
        "tokens_in_est": (len(prompt) + len(filter_prompt)) // 4,
        "tokens_out_est": (sum(len(str(raw_narrative[k])) for k in required) + len(str(raw_filter))) // 4,
        "fallback": False,
    }
    return raw_narrative