"""
report.template — render report.md + report.html dari data + picked + narrative.

Input contract:
    data      : dict dari loader.load_all()
    picked    : dict dari picker.pick_all()
    narrative : dict dari generate.generate_narrative()
    meta      : dict tambahan (date, cost_est_rm) — optional

Output:
    write_report(...) → tulis report.md + report.html dalam report/out/
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent / "out"


# =============================================================================
# MARKDOWN RENDERER
# =============================================================================

def render_markdown(data: dict, picked: dict, narrative: dict,
                    meta: dict | None = None) -> str:
    meta = meta or {}
    summary = data.get("summary", {})
    lines: list[str] = []

    date_str = meta.get("date") or datetime.now(timezone.utc).strftime("%d %B %Y")

    # --- Title + headline ---
    lines.append(f"# Gen Z Malaysia Trend Report — {date_str}")
    lines.append("")
    lines.append(f"> *{narrative.get('headline', '')}*")
    lines.append("")

    # --- Snapshot ---
    lines.extend(_md_snapshot(summary))
    lines.append("")

    # --- Cerita Utama ---
    lines.append("## 📖 Cerita Utama")
    lines.append("")
    lines.append(narrative.get("cerita_utama", "").strip())
    lines.append("")

    # --- Suara Rakyat ---
    lines.extend(_md_quotes(picked.get("top_quotes", [])))
    lines.append("")

    # --- Topik Trending ---
    lines.extend(_md_topics(picked.get("topic_breakdown", [])))
    lines.append("")

    # --- Siapa Yang Disebut ---
    lines.extend(_md_entities(picked.get("entity_context", [])))
    lines.append("")

    # --- Bahasa Kami ---
    lines.extend(_md_slang(picked.get("slang_curated", [])))
    lines.append("")

    # --- Insight ---
    lines.append("## 🔍 Insight")
    lines.append("")
    lines.append(narrative.get("insight", "").strip())
    lines.append("")

    # --- Rekomendasi ---
    lines.append("## 💡 Rekomendasi")
    lines.append("")
    lines.append(narrative.get("rekomendasi", "").strip())
    lines.append("")

    # --- Footer ---
    lines.extend(_md_footer(data, narrative, meta))

    return "\n".join(lines)


def _md_snapshot(summary: dict) -> list[str]:
    total = summary.get("total_comments", 0)
    by_sent = summary.get("by_sentiment", {})
    pos = by_sent.get("positive", 0)
    neg = by_sent.get("negative", 0)
    neu = by_sent.get("neutral", 0)
    by_topic = summary.get("by_topic", {})
    top_topic = max(by_topic.items(), key=lambda kv: kv[1])[0] if by_topic else "-"

    def pct(n: int) -> str:
        return f"{round(100.0 * n / total, 1)}%" if total else "0%"

    return [
        "## 📊 Snapshot",
        "",
        f"- **Total komen dianalisis**: {total}",
        f"- **Topik dominan**: {top_topic}",
        f"- **Sentiment**: 🔴 {neg} negatif ({pct(neg)}) · "
        f"🟢 {pos} positif ({pct(pos)}) · ⚪ {neu} neutral ({pct(neu)})",
    ]


def _md_quotes(quotes: list[dict]) -> list[str]:
    if not quotes:
        return ["## 🗣️ Suara Rakyat", "", "_(tiada quote tersedia)_"]
    out = ["## 🗣️ Suara Rakyat", ""]
    for q in quotes:
        tag = f"[{q['topic']} · {q['sentiment']}]"
        out.append(f"> {q['text']}")
        out.append(f"> — *{tag}*")
        out.append("")
    return out


def _md_topics(breakdown: list[dict]) -> list[str]:
    if not breakdown:
        return ["## 🔥 Topik Trending", "", "_(tiada data)_"]
    out = ["## 🔥 Topik Trending", ""]
    for tb in breakdown:
        s = tb["sentiment"]
        entities = ", ".join(tb.get("top_entities", [])) or "-"
        out.append(
            f"### {tb['topic']} — {tb['count']} komen ({tb['pct']}%)"
        )
        out.append(
            f"🔴 {s['negative']} negatif · 🟢 {s['positive']} positif · "
            f"⚪ {s['neutral']} neutral"
        )
        out.append(f"Entities: `{entities}`")
        out.append("")
    return out


def _md_entities(entities: list[dict]) -> list[str]:
    if not entities:
        return ["## 👥 Siapa Yang Disebut", "", "_(tiada data)_"]
    out = ["## 👥 Siapa Yang Disebut", ""]
    for e in entities:
        out.append(f"### {e['name']} — {e['count']} sebutan")
        out.append("")
        for ex in e.get("examples", []):
            out.append(f"> {ex}")
            out.append("")
    return out


def _md_slang(slang: list[dict]) -> list[str]:
    if not slang:
        return ["## 🗨️ Bahasa Kami", "", "_(tiada slang signifikan)_"]
    out = ["## 🗨️ Bahasa Kami", "", "Signature bahasa Gen Z dalam dataset ni:", ""]
    for s in slang:
        out.append(f"- **{s['word']}** ({s['count']}x) — {s['note']}")
    return out


def _md_footer(data: dict, narrative: dict, meta: dict) -> list[str]:
    model = narrative.get("_meta", {}).get("model", "-")
    cost = meta.get("cost_est_rm")
    cost_str = f"~RM{cost:.6f}" if isinstance(cost, float) else "-"
    total = data.get("meta", {}).get("total_loaded", 0)
    return [
        "---",
        "",
        f"*ATRRIC Report Layer v1 · {total} komen · model: `{model}` · "
        f"kos anggaran: {cost_str}*",
    ]


# =============================================================================
# HTML RENDERER
# =============================================================================

_HTML_CSS = """
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", sans-serif;
  max-width: 780px;
  margin: 0 auto;
  padding: 24px 16px 60px;
  line-height: 1.65;
  color: #1a1a1a;
  background: #fafafa;
  font-size: 16px;
}
h1 { font-size: 1.7em; line-height: 1.25; margin: 0 0 8px; color: #111; }
h2 {
  font-size: 1.25em; margin: 32px 0 12px;
  padding-bottom: 6px; border-bottom: 2px solid #eee;
}
h3 { font-size: 1.05em; margin: 18px 0 6px; color: #333; }
blockquote {
  border-left: 4px solid #0a7;
  margin: 12px 0; padding: 8px 14px;
  background: #f0f8f5;
  border-radius: 0 6px 6px 0;
  font-style: italic;
  color: #244;
}
blockquote cite {
  display: block; margin-top: 6px;
  font-size: 0.85em; color: #567; font-style: normal;
}
.lede {
  font-size: 1.05em; color: #0a7;
  border-left: 3px solid #0a7;
  padding-left: 12px; margin: 0 0 28px;
  font-style: italic;
}
.snapshot {
  background: #fff; border: 1px solid #e5e5e5;
  border-radius: 10px; padding: 16px 20px; margin: 20px 0;
}
.snapshot ul { margin: 6px 0; padding-left: 20px; }
.snapshot li { margin: 4px 0; }
.sent-bar {
  display: flex; height: 10px; border-radius: 5px;
  overflow: hidden; margin: 10px 0;
}
.sent-bar .neg { background: #e34; }
.sent-bar .neu { background: #ccc; }
.sent-bar .pos { background: #0a7; }
.topic-card {
  background: #fff; border: 1px solid #e5e5e5;
  border-radius: 8px; padding: 12px 16px; margin: 10px 0;
}
.topic-card h3 { margin-top: 0; }
.topic-meta { font-size: 0.9em; color: #666; margin: 6px 0; }
.entity-card {
  background: #fff; border: 1px solid #e5e5e5;
  border-radius: 8px; padding: 12px 16px; margin: 10px 0;
}
.entity-card h3 { margin-top: 0; }
.slang-list { list-style: none; padding: 0; }
.slang-list li {
  background: #fff; border: 1px solid #eee;
  border-radius: 6px; padding: 8px 12px; margin: 6px 0;
}
.slang-word { font-weight: 600; color: #0a7; }
footer {
  margin-top: 40px; padding-top: 16px;
  border-top: 1px solid #ddd;
  font-size: 0.85em; color: #888; text-align: center;
}
@media (max-width: 480px) {
  body { padding: 16px 12px 40px; font-size: 15px; }
  h1 { font-size: 1.4em; }
}
"""


def render_html(data: dict, picked: dict, narrative: dict,
                meta: dict | None = None) -> str:
    meta = meta or {}
    summary = data.get("summary", {})
    date_str = meta.get("date") or datetime.now(timezone.utc).strftime("%d %B %Y")
    esc = html.escape

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="ms"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append(f"<title>Gen Z Malaysia Trend Report — {esc(date_str)}</title>")
    parts.append(f"<style>{_HTML_CSS}</style>")
    parts.append("</head><body>")

    # --- Title ---
    parts.append(f"<h1>Gen Z Malaysia Trend Report</h1>")
    parts.append(f'<div class="topic-meta">{esc(date_str)}</div>')
    parts.append(f'<p class="lede">{esc(narrative.get("headline", ""))}</p>')

    # --- Snapshot ---
    parts.append(_html_snapshot(summary))

    # --- Cerita Utama ---
    parts.append("<h2>📖 Cerita Utama</h2>")
    parts.append(_paras(narrative.get("cerita_utama", "")))

    # --- Suara Rakyat ---
    parts.append(_html_quotes(picked.get("top_quotes", [])))

    # --- Topik Trending ---
    parts.append(_html_topics(picked.get("topic_breakdown", [])))

    # --- Siapa Yang Disebut ---
    parts.append(_html_entities(picked.get("entity_context", [])))

    # --- Bahasa Kami ---
    parts.append(_html_slang(picked.get("slang_curated", [])))

    # --- Insight ---
    parts.append("<h2>🔍 Insight</h2>")
    parts.append(_paras(narrative.get("insight", "")))

    # --- Rekomendasi ---
    parts.append("<h2>💡 Rekomendasi</h2>")
    parts.append(_paras(narrative.get("rekomendasi", "")))

    # --- Footer ---
    model = narrative.get("_meta", {}).get("model", "-")
    cost = meta.get("cost_est_rm")
    cost_str = f"~RM{cost:.6f}" if isinstance(cost, float) else "-"
    total = data.get("meta", {}).get("total_loaded", 0)
    parts.append(
        f"<footer>ATRRIC Report Layer v1 · {total} komen · "
        f"model: <code>{esc(str(model))}</code> · kos: {esc(cost_str)}</footer>"
    )

    parts.append("</body></html>")
    return "\n".join(parts)


def _paras(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    return "".join(f"<p>{html.escape(b)}</p>" for b in blocks)


def _html_snapshot(summary: dict) -> str:
    total = summary.get("total_comments", 0)
    by_sent = summary.get("by_sentiment", {})
    pos = by_sent.get("positive", 0)
    neg = by_sent.get("negative", 0)
    neu = by_sent.get("neutral", 0)
    by_topic = summary.get("by_topic", {})
    top_topic = max(by_topic.items(), key=lambda kv: kv[1])[0] if by_topic else "-"

    def pct(n: int) -> float:
        return round(100.0 * n / total, 1) if total else 0.0

    p_neg, p_neu, p_pos = pct(neg), pct(neu), pct(pos)
    return f"""
<h2>📊 Snapshot</h2>
<div class="snapshot">
  <ul>
    <li><b>Total komen</b>: {total}</li>
    <li><b>Topik dominan</b>: {html.escape(top_topic)}</li>
    <li><b>Sentiment</b>: 🔴 {neg} negatif ({p_neg}%) ·
        🟢 {pos} positif ({p_pos}%) · ⚪ {neu} neutral ({p_neu}%)</li>
  </ul>
  <div class="sent-bar">
    <div class="neg" style="width:{p_neg}%"></div>
    <div class="neu" style="width:{p_neu}%"></div>
    <div class="pos" style="width:{p_pos}%"></div>
  </div>
</div>
""".strip()


def _html_quotes(quotes: list[dict]) -> str:
    if not quotes:
        return "<h2>🗣️ Suara Rakyat</h2><p><i>(tiada quote tersedia)</i></p>"
    out = ["<h2>🗣️ Suara Rakyat</h2>"]
    for q in quotes:
        tag = f"{q['topic']} · {q['sentiment']}"
        out.append(
            f"<blockquote>{html.escape(q['text'])}"
            f"<cite>— {html.escape(tag)}</cite></blockquote>"
        )
    return "\n".join(out)


def _html_topics(breakdown: list[dict]) -> str:
    if not breakdown:
        return "<h2>🔥 Topik Trending</h2><p><i>(tiada data)</i></p>"
    out = ["<h2>🔥 Topik Trending</h2>"]
    for tb in breakdown:
        s = tb["sentiment"]
        entities = ", ".join(tb.get("top_entities", [])) or "-"
        out.append(f'<div class="topic-card">')
        out.append(f"<h3>{html.escape(tb['topic'])} — {tb['count']} ({tb['pct']}%)</h3>")
        out.append(
            f'<div class="topic-meta">🔴 {s["negative"]} · '
            f'🟢 {s["positive"]} · ⚪ {s["neutral"]}</div>'
        )
        out.append(f'<div class="topic-meta">Entities: <code>{html.escape(entities)}</code></div>')
        out.append("</div>")
    return "\n".join(out)


def _html_entities(entities: list[dict]) -> str:
    if not entities:
        return "<h2>👥 Siapa Yang Disebut</h2><p><i>(tiada data)</i></p>"
    out = ["<h2>👥 Siapa Yang Disebut</h2>"]
    for e in entities:
        out.append('<div class="entity-card">')
        out.append(f"<h3>{html.escape(e['name'])} — {e['count']} sebutan</h3>")
        for ex in e.get("examples", []):
            out.append(f"<blockquote>{html.escape(ex)}</blockquote>")
        out.append("</div>")
    return "\n".join(out)


def _html_slang(slang: list[dict]) -> str:
    if not slang:
        return "<h2>🗨️ Bahasa Kami</h2><p><i>(tiada slang signifikan)</i></p>"
    out = ["<h2>🗨️ Bahasa Kami</h2>",
           "<p>Signature bahasa Gen Z dalam dataset ni:</p>",
           '<ul class="slang-list">']
    for s in slang:
        out.append(
            f'<li><span class="slang-word">{html.escape(s["word"])}</span> '
            f'({s["count"]}x) — {html.escape(s["note"])}</li>'
        )
    out.append("</ul>")
    return "\n".join(out)


# =============================================================================
# WRITER
# =============================================================================

def write_report(data: dict, picked: dict, narrative: dict,
                 meta: dict | None = None) -> dict:
    """Tulis report.md + report.html. Return path kedua-dua."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = render_markdown(data, picked, narrative, meta)
    html_str = render_html(data, picked, narrative, meta)

    md_path = OUT_DIR / "report.md"
    html_path = OUT_DIR / "report.html"
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(html_str, encoding="utf-8")

    return {"md": str(md_path), "html": str(html_path)}


# =============================================================================
# CLI self-test (python -m report.template)
# =============================================================================

if __name__ == "__main__":
    from report.loader import load_all
    from report.picker import pick_all

    print("=== TEMPLATE SELF-TEST ===")
    data = load_all()
    picked = pick_all(data)

    # Guna fallback naratif supaya test ni tak panggil LLM
    narrative = {
        "headline": "Test headline — placeholder sahaja.",
        "cerita_utama": "Paragraf pertama test.\n\nParagraf kedua test.",
        "insight": "Insight test.",
        "rekomendasi": "Rekomendasi test.",
        "_meta": {"model": "placeholder", "fallback": True},
    }

    paths = write_report(data, picked, narrative, meta={"date": "16 Oktober 2026"})
    print(f"✅ report.md   → {paths['md']}")
    print(f"✅ report.html → {paths['html']}")
    print()
    print("Preview markdown (10 baris pertama):")
    with open(paths["md"], encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            print(f"  {line.rstrip()}")