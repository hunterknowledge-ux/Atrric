"""
report.template — render report.md + report.html (B2B consulting format).
"""

from __future__ import annotations
import html
import re
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "out"

DEFAULT_PREPARED_FOR = "B2B Client"
DEFAULT_BRAND_TAG = "Market Intelligence"

SECTIONS = [
    ("s01", "Ringkasan Eksekutif"), ("s02", "Snapshot Data"),
    ("s03", "Cerita Utama"), ("s04", "Suara Responden"),
    ("s05", "Topik Trending"), ("s06", "Entiti Utama"),
    ("s07", "Bahasa & Slang"), ("s08", "Insight"),
    ("s09", "Rekomendasi"),
]

def _default_report_id() -> str:
    return "ATRRIC-" + datetime.now(timezone.utc).strftime("%Y-%m-%d")

def _default_period() -> str:
    return datetime.now(timezone.utc).strftime("%B %Y")

def _split_exec_summary(cerita_utama: str) -> tuple[str | None, list[str]]:
    text = (cerita_utama or "").strip()
    if not text: return None, []
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paras) >= 2: return paras[0], paras[1:]
    sents = re.split(r'(?<=[.!?])\s+', paras[0])
    if len(sents) >= 3: return " ".join(sents[:2]), [" ".join(sents[2:])]
    return None, paras

def _split_long_text(text: str) -> list[str]:
    text = (text or "").strip()
    if not text: return []
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    out = []
    for p in paras:
        if len(p) > 250:
            sents = re.split(r'(?<=[.!?])\s+', p)
            chunk = []
            for s in sents:
                chunk.append(s)
                if len(" ".join(chunk)) > 200:
                    out.append(" ".join(chunk))
                    chunk = []
            if chunk: out.append(" ".join(chunk))
        else: out.append(p)
    return out

def _methodology_text(data: dict) -> str:
    total = data.get("meta", {}).get("total_loaded", 0)
    sources = data.get("meta", {}).get("sources", [])
    src_str = ", ".join(sources) if sources else "platform terpilih"
    return f"Laporan ini berdasarkan analisis {total} komen awam yang dikumpul dari {src_str}. Setiap komen diproses melalui pipeline ATRRIC: Extract → Process → Generate. Sentiment diklasifikasi menggunakan LLM, manakala entity dan slang di-discover secara automatik dari dataset melalui analytics layer. Insight kualitatif dijana dengan model bahasa berasaskan data yang sama untuk memastikan konsistensi."

def _disclaimer_text() -> str:
    return "Laporan ini dijana secara automatik oleh ATRRIC Report Layer v1. Data adalah berdasarkan sampel komen awam pada tempoh yang dinyatakan dan tidak mengklaim mewakili keseluruhan populasi Gen Z Malaysia. ATRRIC tidak menjamin ketepatan 100% untuk keputusan kritikal — sila gunakan sebagai rujukan strategik bersama analisis tambahan. Untuk analisis khusus atau custom scope, hubungi team ATRRIC."

def _get_curated_quotes(picked: dict, narrative: dict) -> list[dict]:
    """Gabungkan semula ID quote yang ditapis LLM dengan teks penuh."""
    allowed_ids = {q["id"] for q in narrative.get("quotes_curated", []) if "id" in q}
    if not allowed_ids: return picked.get("top_quotes", [])[:5]
    return [q for q in picked.get("top_quotes", []) if q["id"] in allowed_ids][:5]

def render_markdown(data: dict, picked: dict, narrative: dict, meta: dict | None = None) -> str:
    meta = meta or {}
    summary = data.get("summary", {})
    lines: list[str] = []

    date_str = meta.get("date") or datetime.now(timezone.utc).strftime("%d %B %Y")
    report_id = meta.get("report_id") or _default_report_id()
    prepared_for = meta.get("prepared_for") or DEFAULT_PREPARED_FOR
    period = meta.get("period") or _default_period()
    total = summary.get("total_comments", 0)

    exec_text, body_paras = _split_exec_summary(narrative.get("cerita_utama", ""))
    slang_data = narrative.get("slang_curated", [])
    final_quotes = _get_curated_quotes(picked, narrative)

    lines.append("# ATRRIC · Market Intelligence\n\n**CONFIDENTIAL**\n")
    lines.append("| | |\n|---|---|")
    lines.append(f"| Prepared for | {prepared_for} |")
    lines.append(f"| Report ID | {report_id} |")
    lines.append(f"| Period | {period} |")
    lines.append(f"| Sample size | {total} komen |\n---\n")

    lines.append(f"## Gen Z Malaysia Trend Report — {date_str}\n")
    lines.append(f"> *{narrative.get('headline', '')}*\n")

    lines.append("### Kandungan\n")
    for i, (_, title) in enumerate(SECTIONS, start=1): lines.append(f"{i}. {title}")
    lines.append("")

    lines.append("## 01 · Ringkasan Eksekutif\n")
    lines.append(f"> {exec_text}\n" if exec_text else "_(tiada ringkasan)_\n")

    lines.extend(_md_snapshot(summary))
    lines.append("")

    lines.append("## 03 · Cerita Utama\n")
    for p in body_paras: lines.append(f"{p}\n")

    lines.extend(_md_quotes(final_quotes))
    lines.append("")

    lines.extend(_md_topics(picked.get("topic_breakdown", [])))
    lines.append("")
    lines.extend(_md_entities(picked.get("entity_context", [])))
    lines.append("")
    lines.extend(_md_slang(slang_data))
    lines.append("")

    lines.append("## 08 · Insight\n")
    for p in _split_long_text(narrative.get('insight', '')): lines.append(f"{p}\n")

    lines.append("## 09 · Rekomendasi\n")
    for p in _split_long_text(narrative.get('rekomendasi', '')): lines.append(f"{p}\n")

    lines.append("---\n## Metodologi\n")
    lines.append(f"{_methodology_text(data)}\n")
    lines.append("## Disclaimer\n")
    lines.append(f"{_disclaimer_text()}\n")

    lines.append("---\n")
    model = narrative.get("_meta", {}).get("model", "-")
    cost = meta.get("cost_est_rm")
    cost_str = f"~RM{cost:.6f}" if isinstance(cost, float) else "-"
    lines.append(f"*ATRRIC · Market Intelligence for Gen Z Malaysia*  ")
    lines.append(f"*Report ID {report_id} · {total} komen · model `{model}` · kos {cost_str}*")

    return "\n".join(lines)

def _md_snapshot(summary: dict) -> list[str]:
    total = summary.get("total_comments", 0)
    by_sent = summary.get("by_sentiment", {})
    pos, neg, neu = by_sent.get("positive", 0), by_sent.get("negative", 0), by_sent.get("neutral", 0)
    by_topic = summary.get("by_topic", {})
    top_topic = max(by_topic.items(), key=lambda kv: kv[1])[0] if by_topic else "-"
    def pct(n: int) -> str: return f"{round(100.0 * n / total, 1)}%" if total else "0%"
    return ["## 02 · Snapshot Data\n", f"- **Total komen dianalisis**: {total}", f"- **Topik dominan**: {top_topic}", f"- **Sentiment**: {neg} negatif ({pct(neg)}) · {pos} positif ({pct(pos)}) · {neu} neutral ({pct(neu)})"]

def _md_quotes(quotes: list[dict]) -> list[str]:
    if not quotes: return ["## 04 · Suara Responden\n", "_(tiada quote tersedia)_"]
    out = ["## 04 · Suara Responden\n"]
    for q in quotes: out.append(f"> {q['text']}\n> — *[{q['topic']} · {q['sentiment']}]*\n")
    return out

def _md_topics(breakdown: list[dict]) -> list[str]:
    if not breakdown: return ["## 05 · Topik Trending\n", "_(tiada data)_"]
    out = ["## 05 · Topik Trending\n"]
    for tb in breakdown:
        s = tb["sentiment"]
        entities = ", ".join(tb.get("top_entities", [])) or "-"
        out.append(f"### {tb['topic']} — {tb['count']} komen ({tb['pct']}%)")
        out.append(f"{s['negative']} negatif · {s['positive']} positif · {s['neutral']} neutral")
        out.append(f"Entities: `{entities}`\n")
    return out

def _md_entities(entities: list[dict]) -> list[str]:
    if not entities: return ["## 06 · Entiti Utama\n", "_(tiada data)_"]
    out = ["## 06 · Entiti Utama\n"]
    for e in entities:
        out.append(f"### {e['name']} — {e['count']} sebutan\n")
        for ex in e.get("examples", []): out.append(f"> {ex}\n")
    return out

def _md_slang(slang: list[dict]) -> list[str]:
    if not slang: return ["## 07 · Bahasa & Slang\n", "_(tiada slang signifikan)_"]
    out = ["## 07 · Bahasa & Slang\n", "Signature bahasa Gen Z dalam dataset ni:\n"]
    for s in slang: out.append(f"- **{s['word']}** ({s['count']}x) — {s.get('note', 'slanga Gen Z')}")
    return out

# (Paste _HTML_CSS penuh dari mesej lepas sini. Aku tak paste sebab nak jimat ruang, 
#  pastikan kau copy dari fail template.py kau yang sekarang (yang ada CSS Claude tu).)

def render_html(data: dict, picked: dict, narrative: dict, meta: dict | None = None) -> str:
    # ... (Sama macam render_markdown, pastikan guna `final_quotes = _get_curated_quotes(picked, narrative)`)
    # ... (Cari bahagian `_html_quotes(picked.get("top_quotes", []))` dan tukar jadi `_html_quotes(final_quotes)`)
    pass