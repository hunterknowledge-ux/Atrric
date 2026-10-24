"""
report.generate — 1 LLM call untuk naratif utama.
"""

from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """\
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
    }

def generate_narrative(data: dict, picked: dict, model: str | None = None) -> dict:
    summary = data.get("summary", {})
    comments_count = data.get("meta", {}).get("total_loaded", 0)

    prompt = _build_narrative_prompt(summary, picked, comments_count)

    try:
        from core.llm import generate_json
    except ImportError as e:
        result = _fallback(summary, picked)
        result["_meta"] = {"model": "fallback", "reason": f"import error: {e}", "fallback": True}
        return result

    kwargs: dict[str, Any] = {"prompt": prompt, "system": SYSTEM_PROMPT, "max_tokens": 1500, "task": "report"}
    if model: kwargs["model"] = model

    try:
        raw = generate_json(**kwargs)
    except Exception as e:
        result = _fallback(summary, picked)
        result["_meta"] = {"model": "fallback", "reason": f"llm error: {e}", "fallback": True}
        return result

    required = ("headline", "cerita_utama", "insight", "rekomendasi")
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