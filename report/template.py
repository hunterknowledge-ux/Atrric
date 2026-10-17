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
    
    # Fallback: pecah ikut ayat
    sents = re.split(r'(?<=[.!?])\s+', paras[0])
    if len(sents) >= 3:
        return " ".join(sents[:2]), [" ".join(sents[2:])]
    return None, paras

def _methodology_text(data: dict) -> str:
    total = data.get("meta", {}).get("total_loaded", 0)
    sources = data.get("meta", {}).get("sources", [])
    src_str = ", ".join(sources) if sources else "platform terpilih"
    return f"Laporan ini berdasarkan analisis {total} komen awam yang dikumpul dari {src_str}. Setiap komen diproses melalui pipeline ATRRIC: Extract → Process → Generate. Sentiment diklasifikasi menggunakan LLM, manakala entity dan slang di-discover secara automatik dari dataset melalui analytics layer. Insight kualitatif dijana dengan model bahasa berasaskan data yang sama untuk memastikan konsistensi."

def _disclaimer_text() -> str:
    return "Laporan ini dijana secara automatik oleh ATRRIC Report Layer v1. Data adalah berdasarkan sampel komen awam pada tempoh yang dinyatakan dan tidak mengklaim mewakili keseluruhan populasi Gen Z Malaysia. ATRRIC tidak menjamin ketepatan 100% untuk keputusan kritikal — sila gunakan sebagai rujukan strategik bersama analisis tambahan. Untuk analisis khusus atau custom scope, hubungi team ATRRIC."

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
    
    # Ambil slang terus dari Python (dah ditapis)
    slang_data = picked.get("slang_raw", [])

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

    lines.extend(_md_quotes(picked.get("top_quotes", [])))
    lines.append("")

    lines.extend(_md_topics(picked.get("topic_breakdown", [])))
    lines.append("")

    lines.extend(_md_entities(picked.get("entity_context", [])))
    lines.append("")

    lines.extend(_md_slang(slang_data))
    lines.append("")

    insight_text = narrative.get('insight', '').strip()
    insight_paras = _split_long_text(insight_text)
    lines.append("## 08 · Insight\n")
    for p in insight_paras: lines.append(f"{p}\n")

    reco_text = narrative.get('rekomendasi', '').strip()
    reco_paras = _split_long_text(reco_text)
    lines.append("## 09 · Rekomendasi\n")
    for p in reco_paras: lines.append(f"{p}\n")

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

def _split_long_text(text: str) -> list[str]:
    text = (text or "").strip()
    if not text: return []
    if "\n\n" in text: return [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(text) > 400:
        sents = re.split(r'(?<=[.!?])\s+', text)
        mid = len(sents) // 2
        return [" ".join(sents[:mid]), " ".join(sents[mid:])]
    return [text]

# (MASUKKAN _HTML_CSS DARI MESEJ SEBELUM NI SINI, JANGAN UBAH)
_HTML_CSS = r""" ... (salin balik CSS dari mesej lepas) ... """

def render_html(data: dict, picked: dict, narrative: dict, meta: dict | None = None) -> str:
    meta = meta or {}
    summary = data.get("summary", {})
    esc = html.escape

    date_str = meta.get("date") or datetime.now(timezone.utc).strftime("%d %B %Y")
    report_id = meta.get("report_id") or _default_report_id()
    prepared_for = meta.get("prepared_for") or DEFAULT_PREPARED_FOR
    period = meta.get("period") or _default_period()
    total = summary.get("total_comments", 0)

    exec_text, body_paras = _split_exec_summary(narrative.get("cerita_utama", ""))
    
    # Ambil slang terus dari Python
    slang_data = picked.get("slang_raw", [])

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="ms"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append(f"<title>Gen Z Malaysia Trend Report — {esc(date_str)}</title>")
    parts.append(f"<style>{_HTML_CSS}</style>")
    parts.append("</head><body>")

    parts.append('<header class="report-header"><div class="brand"><span class="brand-mark">ATRRIC</span>')
    parts.append(f'<span class="brand-tag">{esc(DEFAULT_BRAND_TAG)}</span></div><span class="confidential-badge">Confidential</span></header>')

    parts.append('<section class="report-meta">')
    for label, value in [("Prepared for", prepared_for), ("Report ID", report_id), ("Period", period), ("Sample size", f"{total} komen")]:
        parts.append(f'<div class="meta-item"><span class="meta-label">{esc(label)}</span><span class="meta-value">{esc(value)}</span></div>')
    parts.append("</section>")

    parts.append(f"<h1>Gen Z Malaysia Trend Report</h1>")
    parts.append(f'<p class="lede">{esc(narrative.get("headline", ""))}</p>')

    parts.append('<nav class="toc"><div class="toc-title">Kandungan</div><ol>')
    for sid, title in SECTIONS: parts.append(f'<li><a href="#{sid}">{esc(title)}</a></li>')
    parts.append("</ol></nav>")

    parts.append('<section class="exec-summary" id="s01"><h2><span class="sec-num">01</span>Ringkasan Eksekutif</h2><div class="callout">')
    parts.append(f"<p>{esc(exec_text)}</p>" if exec_text else "<p><i>(tiada ringkasan)</i></p>")
    parts.append("</div></section>")

    parts.append('<section id="s02"><h2><span class="sec-num">02</span>Snapshot Data</h2>')
    parts.append(_html_snapshot(summary))
    parts.append("</section>")

    parts.append('<section id="s03"><h2><span class="sec-num">03</span>Cerita Utama</h2>')
    if body_paras:
        for p in body_paras: parts.append(f"<p>{esc(p)}</p>")
    else: parts.append("<p><i>(tiada naratif)</i></p>")
    parts.append("</section>")

    parts.append('<section id="s04"><h2><span class="sec-num">04</span>Suara Responden</h2>')
    parts.append(_html_quotes(picked.get("top_quotes", [])))
    parts.append("</section>")

    parts.append('<section id="s05"><h2><span class="sec-num">05</span>Topik Trending</h2>')
    parts.append(_html_topics(picked.get("topic_breakdown", [])))
    parts.append("</section>")

    parts.append('<section id="s06"><h2><span class="sec-num">06</span>Entiti Utama</h2>')
    parts.append(_html_entities(picked.get("entity_context", [])))
    parts.append("</section>")

    parts.append('<section id="s07"><h2><span class="sec-num">07</span>Bahasa &amp; Slang</h2>')
    parts.append(_html_slang(slang_data))
    parts.append("</section>")

    parts.append('<section id="s08"><h2><span class="sec-num">08</span>Insight</h2>')
    for p in _split_long_text(narrative.get("insight", "")): parts.append(f"<p>{esc(p)}</p>")
    parts.append("</section>")

    parts.append('<section id="s09"><h2><span class="sec-num">09</span>Rekomendasi</h2>')
    for p in _split_long_text(narrative.get("rekomendasi", "")): parts.append(f"<p>{esc(p)}</p>")
    parts.append("</section>")

    parts.append(f'<section class="methodology"><h2>Metodologi</h2><p>{esc(_methodology_text(data))}</p></section>')
    parts.append(f'<section class="disclaimer"><p>{esc(_disclaimer_text())}</p></section>')

    model = narrative.get("_meta", {}).get("model", "-")
    cost = meta.get("cost_est_rm")
    cost_str = f"~RM{cost:.6f}" if isinstance(cost, float) else "-"
    parts.append("<footer>")
    parts.append('<div class="footer-brand">ATRRIC · Market Intelligence for Gen Z Malaysia</div>')
    parts.append(f'<div class="footer-meta">Report ID {esc(report_id)} · {total} komen · model <code>{esc(str(model))}</code> · kos {esc(cost_str)}</div>')
    parts.append("</footer></body></html>")
    return "\n".join(parts)

# (salin balik _paras, _html_snapshot, _html_quotes, _html_topics, _html_entities, _html_slang, write_report dari mesej lepas)