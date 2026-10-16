"""
report.template — render report.md + report.html (B2B consulting format).

Input contract:
    data      : dict dari loader.load_all()
    picked    : dict dari picker.pick_all()
    narrative : dict dari generate.generate_narrative()
    meta      : dict tambahan (date, cost_est_rm, prepared_for, report_id, period)

Output:
    write_report(...) → tulis report.md + report.html dalam report/out/
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent / "out"

DEFAULT_PREPARED_FOR = "B2B Client"
DEFAULT_BRAND_TAG = "Market Intelligence"

# Section titles (numbered 01-09) — tukar sini kalau nak rename
SECTIONS = [
    ("s01", "Ringkasan Eksekutif"),
    ("s02", "Snapshot Data"),
    ("s03", "Cerita Utama"),
    ("s04", "Suara Responden"),
    ("s05", "Topik Trending"),
    ("s06", "Entiti Utama"),
    ("s07", "Bahasa & Slang"),
    ("s08", "Insight"),
    ("s09", "Rekomendasi"),
]


# =============================================================================
# HELPERS — meta + narrative splitting
# =============================================================================

def _default_report_id() -> str:
    return "ATRRIC-" + datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _default_period() -> str:
    return datetime.now(timezone.utc).strftime("%B %Y")


def _split_exec_summary(cerita_utama: str) -> tuple[str | None, list[str]]:
    """Split cerita_utama: paragraph pertama → exec summary, rest → body."""
    paras = [p.strip() for p in (cerita_utama or "").split("\n\n") if p.strip()]
    if not paras:
        return None, []
    if len(paras) == 1:
        return paras[0], paras
    return paras[0], paras[1:]


def _methodology_text(data: dict) -> str:
    total = data.get("meta", {}).get("total_loaded", 0)
    sources = data.get("meta", {}).get("sources", [])
    src_str = ", ".join(sources) if sources else "platform terpilih"
    return (
        f"Laporan ini berdasarkan analisis {total} komen awam yang dikumpul "
        f"dari {src_str}. Setiap komen diproses melalui pipeline ATRRIC: "
        f"Extract → Process → Generate. Sentiment diklasifikasi menggunakan "
        f"LLM, manakala entity dan slang di-discover secara automatik dari "
        f"dataset melalui analytics layer. Insight kualitatif dijana dengan "
        f"model bahasa berasaskan data yang sama untuk memastikan konsistensi."
    )


def _disclaimer_text() -> str:
    return (
        "Laporan ini dijana secara automatik oleh ATRRIC Report Layer v1. "
        "Data adalah berdasarkan sampel komen awam pada tempoh yang dinyatakan "
        "dan tidak mengklaim mewakili keseluruhan populasi Gen Z Malaysia. "
        "ATRRIC tidak menjamin ketepatan 100% untuk keputusan kritikal — "
        "sila gunakan sebagai rujukan strategik bersama analisis tambahan. "
        "Untuk analisis khusus atau custom scope, hubungi team ATRRIC."
    )


# =============================================================================
# MARKDOWN RENDERER
# =============================================================================

def render_markdown(data: dict, picked: dict, narrative: dict,
                    meta: dict | None = None) -> str:
    meta = meta or {}
    summary = data.get("summary", {})
    lines: list[str] = []

    date_str = meta.get("date") or datetime.now(timezone.utc).strftime("%d %B %Y")
    report_id = meta.get("report_id") or _default_report_id()
    prepared_for = meta.get("prepared_for") or DEFAULT_PREPARED_FOR
    period = meta.get("period") or _default_period()
    total = summary.get("total_comments", 0)

    exec_text, body_paras = _split_exec_summary(narrative.get("cerita_utama", ""))

    # --- Cover block ---
    lines.append("# ATRRIC · Market Intelligence")
    lines.append("")
    lines.append("**CONFIDENTIAL**")
    lines.append("")
    lines.append(f"| | |")
    lines.append(f"|---|---|")
    lines.append(f"| Prepared for | {prepared_for} |")
    lines.append(f"| Report ID | {report_id} |")
    lines.append(f"| Period | {period} |")
    lines.append(f"| Sample size | {total} komen |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Title + lede ---
    lines.append(f"## Gen Z Malaysia Trend Report — {date_str}")
    lines.append("")
    lines.append(f"> *{narrative.get('headline', '')}*")
    lines.append("")

    # --- TOC ---
    lines.append("### Kandungan")
    lines.append("")
    for i, (_, title) in enumerate(SECTIONS, start=1):
        lines.append(f"{i}. {title}")
    lines.append("")

    # --- 01 Exec summary ---
    lines.append("## 01 · Ringkasan Eksekutif")
    lines.append("")
    if exec_text:
        lines.append(f"> {exec_text}")
    else:
        lines.append("_(tiada ringkasan)_")
    lines.append("")

    # --- 02 Snapshot ---
    lines.extend(_md_snapshot(summary))
    lines.append("")

    # --- 03 Cerita Utama ---
    lines.append("## 03 · Cerita Utama")
    lines.append("")
    for p in body_paras:
        lines.append(p)
        lines.append("")

    # --- 04 Suara Responden ---
    lines.extend(_md_quotes(picked.get("top_quotes", [])))
    lines.append("")

    # --- 05 Topik Trending ---
    lines.extend(_md_topics(picked.get("topic_breakdown", [])))
    lines.append("")

    # --- 06 Entiti ---
    lines.extend(_md_entities(picked.get("entity_context", [])))
    lines.append("")

    # --- 07 Bahasa ---
    lines.extend(_md_slang(picked.get("slang_curated", [])))
    lines.append("")

    # --- 08 Insight ---
    lines.append("## 08 · Insight")
    lines.append("")
    lines.append(narrative.get("insight", "").strip())
    lines.append("")

    # --- 09 Rekomendasi ---
    lines.append("## 09 · Rekomendasi")
    lines.append("")
    lines.append(narrative.get("rekomendasi", "").strip())
    lines.append("")

    # --- Methodology + Disclaimer ---
    lines.append("---")
    lines.append("")
    lines.append("## Metodologi")
    lines.append("")
    lines.append(_methodology_text(data))
    lines.append("")
    lines.append("## Disclaimer")
    lines.append("")
    lines.append(_disclaimer_text())
    lines.append("")

    # --- Footer ---
    lines.append("---")
    lines.append("")
    model = narrative.get("_meta", {}).get("model", "-")
    cost = meta.get("cost_est_rm")
    cost_str = f"~RM{cost:.6f}" if isinstance(cost, float) else "-"
    lines.append(f"*ATRRIC · Market Intelligence for Gen Z Malaysia*  ")
    lines.append(f"*Report ID {report_id} · {total} komen · model `{model}` · kos {cost_str}*")

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
        "## 02 · Snapshot Data",
        "",
        f"- **Total komen dianalisis**: {total}",
        f"- **Topik dominan**: {top_topic}",
        f"- **Sentiment**: {neg} negatif ({pct(neg)}) · "
        f"{pos} positif ({pct(pos)}) · {neu} neutral ({pct(neu)})",
    ]


def _md_quotes(quotes: list[dict]) -> list[str]:
    if not quotes:
        return ["## 04 · Suara Responden", "", "_(tiada quote tersedia)_"]
    out = ["## 04 · Suara Responden", ""]
    for q in quotes:
        tag = f"[{q['topic']} · {q['sentiment']}]"
        out.append(f"> {q['text']}")
        out.append(f"> — *{tag}*")
        out.append("")
    return out


def _md_topics(breakdown: list[dict]) -> list[str]:
    if not breakdown:
        return ["## 05 · Topik Trending", "", "_(tiada data)_"]
    out = ["## 05 · Topik Trending", ""]
    for tb in breakdown:
        s = tb["sentiment"]
        entities = ", ".join(tb.get("top_entities", [])) or "-"
        out.append(f"### {tb['topic']} — {tb['count']} komen ({tb['pct']}%)")
        out.append(
            f"{s['negative']} negatif · {s['positive']} positif · "
            f"{s['neutral']} neutral"
        )
        out.append(f"Entities: `{entities}`")
        out.append("")
    return out


def _md_entities(entities: list[dict]) -> list[str]:
    if not entities:
        return ["## 06 · Entiti Utama", "", "_(tiada data)_"]
    out = ["## 06 · Entiti Utama", ""]
    for e in entities:
        out.append(f"### {e['name']} — {e['count']} sebutan")
        out.append("")
        for ex in e.get("examples", []):
            out.append(f"> {ex}")
            out.append("")
    return out


def _md_slang(slang: list[dict]) -> list[str]:
    if not slang:
        return ["## 07 · Bahasa & Slang", "", "_(tiada slang signifikan)_"]
    out = ["## 07 · Bahasa & Slang", "",
           "Signature bahasa Gen Z dalam dataset ni:", ""]
    for s in slang:
        out.append(f"- **{s['word']}** ({s['count']}x) — {s['note']}")
    return out


# =============================================================================
# CSS — dari Claude, consulting-grade B2B
# =============================================================================

_HTML_CSS = r"""
/* ATRRIC Report Layer | consulting-grade B2B stylesheet.
   CSS only. System fonts only. No external resources. Accent: deep navy. */

/* ---------- 1. TOKENS ---------- */
:root{
  --surface:#faf9f7;
  --surface-2:#fffefc;
  --ink:#131313;
  --ink-2:#5a5a55;
  --accent:#1a2b47;
  --neg:#b04a3f;
  --pos:#2f6b46;
  --neutral:#8a8a85;
  --border:#e6e3dc;

  --accent-wash:#eceef2;
  --accent-ring:rgba(26,43,71,.2);
  --callout-bg:#f1f2f4;
  --code-bg:#f0eee9;
  --rule:#7a7974;
  --stamp:rgba(176,74,63,.4);

  --radius:5px;
  --gap:1rem;
  --card-pad:clamp(1.05rem,.8rem + 1vw,1.4rem);
  --measure:68ch;
  --col:780px;
  --pad:clamp(1.15rem,.6rem + 2.2vw,2rem);

  --font-body:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
  --font-display:'Iowan Old Style','Palatino Linotype',Palatino,Charter,'Sitka Text',Cambria,Georgia,'Noto Serif',serif;
  --font-mono:ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace;

  --fs-body:clamp(1rem,.94rem + .28vw,1.0625rem);
  --fs-h1:clamp(2.1rem,1.6rem + 2vw,2.6rem);
  --fs-h2:clamp(1.3rem,1.18rem + .5vw,1.5rem);
  --fs-label:.8125rem;
}

@media (prefers-color-scheme:dark){
  :root{
    --surface:#151514;
    --surface-2:#1c1c1a;
    --ink:#ebe9e3;
    --ink-2:#a8a59c;
    --accent:#8fa6cf;
    --neg:#d9867b;
    --pos:#6fae88;
    --neutral:#8b8a84;
    --border:#2f2e2b;
    --accent-wash:#1f242d;
    --accent-ring:rgba(143,166,207,.22);
    --callout-bg:#20242b;
    --code-bg:#252523;
    --rule:#77756f;
    --stamp:rgba(217,134,123,.4);
  }
}

@supports (color:color-mix(in oklch,red,blue)){
  :root{
    --accent-wash:color-mix(in oklch,var(--accent) 7%,var(--surface));
    --accent-ring:color-mix(in oklch,var(--accent) 20%,transparent);
    --callout-bg:color-mix(in oklch,var(--accent) 6%,var(--surface-2));
    --code-bg:color-mix(in oklch,var(--ink) 6%,var(--surface));
    --rule:color-mix(in oklch,var(--ink) 55%,var(--surface));
    --stamp:color-mix(in oklch,var(--neg) 40%,transparent);
  }
}

/* ---------- 2. BASE ---------- */
*,*::before,*::after{box-sizing:border-box}

html{
  background:var(--surface);
  color-scheme:light dark;
  -webkit-text-size-adjust:100%;
  text-size-adjust:100%;
  scroll-behavior:smooth;
}

body{
  max-width:calc(var(--col) + 2 * var(--pad));
  margin:0 auto;
  padding:clamp(1.25rem,.5rem + 3.5vw,3rem) var(--pad) 3.5rem;
  color:var(--ink);
  font-family:var(--font-body);
  font-size:var(--fs-body);
  line-height:1.68;
  font-variant-numeric:lining-nums tabular-nums;
  font-kerning:normal;
  overflow-wrap:break-word;
  -webkit-font-smoothing:antialiased;
}

::selection{background:var(--accent-ring)}

section{margin-top:3em;scroll-margin-top:1.25rem}
section:has(> .callout){margin-top:3.5em}
.exec-summary{margin-top:3.5em}
.exec-summary > h2{border-top:2px solid var(--accent)}

h1,h2,h3{margin:0;color:var(--ink)}

h1{
  margin:clamp(1.75rem,1rem + 3vw,2.75rem) 0 .55rem;
  font-family:var(--font-display);
  font-size:var(--fs-h1);
  font-weight:600;
  line-height:1.15;
  letter-spacing:-.02em;
}

.lede{
  max-width:var(--measure);
  margin:0;
  font-family:var(--font-display);
  font-size:clamp(1.1rem,1.02rem + .4vw,1.25rem);
  font-style:italic;
  line-height:1.6;
  color:var(--ink-2);
}

h2{
  display:flex;
  align-items:baseline;
  margin:0 0 1.5em;
  padding-top:1rem;
  border-top:1px solid var(--rule);
  font-family:var(--font-display);
  font-size:var(--fs-h2);
  font-weight:600;
  line-height:1.2;
  letter-spacing:-.01em;
}

h3{
  margin:0 0 .6rem;
  font-size:1.0625rem;
  font-weight:600;
  line-height:1.3;
}

p{max-width:var(--measure);margin:0 0 1.1em}
p:last-child{margin-bottom:0}
section:not(.methodology) > h2 + p{font-size:1.0625em}
strong,b{font-weight:600}

a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:.18em}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

code{
  padding:3px 6px;
  border-radius:2px;
  background:var(--code-bg);
  font-family:var(--font-mono);
  font-size:.9em;
  overflow-wrap:anywhere;
  -webkit-box-decoration-break:clone;
  box-decoration-break:clone;
}

section ul,section ol{max-width:var(--measure);margin:0 0 1.1em;padding-left:1.35rem}
section li{margin:.3em 0}
section li::marker{color:var(--accent)}

.sec-num{
  display:inline-flex;
  align-items:center;
  flex:none;
  gap:.6rem;
  margin-right:.9rem;
  font-family:var(--font-mono);
  font-size:.84rem;
  font-weight:600;
  letter-spacing:.06em;
  color:var(--accent);
}
.sec-num::after{content:'';width:1.25rem;height:1px;background:currentColor;opacity:.5}

/* ---------- 3. COVER ---------- */
.report-header{
  display:flex;
  flex-wrap:wrap;
  align-items:flex-start;
  justify-content:space-between;
  gap:.9rem 1.25rem;
  padding:1.1rem 0 1rem;
  border-top:3px solid var(--accent);
  border-bottom:1px solid var(--border);
}
.brand{display:flex;flex-direction:column;gap:.45rem}
.brand-mark{
  font-size:1.2rem;
  font-weight:700;
  line-height:1;
  letter-spacing:.24em;
  color:var(--accent);
}
.brand-tag{
  font-size:var(--fs-label);
  line-height:1.2;
  letter-spacing:.04em;
  color:var(--ink-2);
}
.confidential-badge{
  padding:.3rem .65rem;
  border:1px solid var(--neg);
  border-radius:2px;
  outline:1px solid var(--stamp);
  outline-offset:2px;
  font-size:var(--fs-label);
  font-weight:600;
  line-height:1.2;
  letter-spacing:.1em;
  text-transform:uppercase;
  white-space:nowrap;
  color:var(--neg);
}

.report-meta{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:1.1rem 1.25rem;
  margin:0;
  padding:1.15rem 0 1.3rem;
  border-bottom:1px solid var(--border);
}
.meta-item{display:flex;flex-direction:column;gap:.3rem;min-width:0}
.meta-label{
  font-size:var(--fs-label);
  font-weight:600;
  line-height:1.3;
  letter-spacing:.1em;
  text-transform:uppercase;
  color:var(--ink-2);
}
.meta-value{
  font-size:1rem;
  font-weight:600;
  line-height:1.35;
  color:var(--ink);
  overflow-wrap:anywhere;
}

/* ---------- 4. TOC ---------- */
.toc{
  margin:clamp(1.75rem,1rem + 2.5vw,2.5rem) 0 0;
  padding:1.25rem 1.4rem 1rem;
  border:1px solid var(--border);
  border-radius:var(--radius);
  background:var(--surface-2);
}
.toc-title{
  margin-bottom:.6rem;
  font-size:var(--fs-label);
  font-weight:600;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:var(--ink-2);
}
.toc ol{margin:0;padding:0;list-style:none;counter-reset:toc}
.toc li{margin:0;break-inside:avoid;counter-increment:toc}
.toc a{
  display:flex;
  align-items:baseline;
  gap:.75rem;
  margin-inline:-.45rem;
  padding:.4rem .45rem;
  border-radius:2px;
  color:var(--ink);
  line-height:1.4;
  text-decoration:none;
  transition:background-color .15s ease,color .15s ease;
}
.toc a::before{
  content:counter(toc,decimal-leading-zero);
  flex:none;
  font-family:var(--font-mono);
  font-size:.84rem;
  font-weight:600;
  color:var(--accent);
}
.toc a:hover{background:var(--accent-wash);color:var(--accent)}
.toc a:focus-visible{outline:2px solid var(--accent);outline-offset:1px;background:var(--accent-ring)}

/* ---------- 5. EXECUTIVE SUMMARY ---------- */
.callout{
  margin:0;
  padding:calc(var(--card-pad) + .2rem) calc(var(--card-pad) + .3rem);
  border-left:5px solid var(--accent);
  border-radius:0 var(--radius) var(--radius) 0;
  background:var(--callout-bg);
}
.callout p{
  max-width:none;
  margin:0;
  font-family:var(--font-display);
  font-size:clamp(1.08rem,1rem + .35vw,1.2rem);
  line-height:1.65;
  color:var(--ink);
}
.callout p + p{margin-top:1em}

/* ---------- 6. SNAPSHOT ---------- */
.snapshot{
  padding:var(--card-pad) calc(var(--card-pad) + .1rem) calc(var(--card-pad) + .1rem);
  border:1px solid var(--border);
  border-radius:var(--radius);
  background:var(--surface-2);
}
.snapshot ul{list-style:none;max-width:none;margin:0 0 1.25rem;padding:0}
.snapshot li{position:relative;margin:0 0 .55rem;padding-left:1.15rem;line-height:1.55}
.snapshot li:last-child{margin-bottom:0}
.snapshot li::before{
  content:'';
  position:absolute;
  left:0;
  top:.58em;
  width:.4rem;
  height:.4rem;
  background:var(--accent);
}
.snapshot b{font-weight:600}

.sent-bar{
  position:relative;
  display:flex;
  height:8px;
  overflow:hidden;
  border-radius:999px;
  background:var(--border);
}
.sent-bar > *{flex:none;height:100%}
.sent-bar .neg{background:var(--neg)}
.sent-bar .neu{background:var(--neutral)}
.sent-bar .pos{background:var(--pos)}
.sent-bar .neu,.sent-bar .pos{border-left:2px solid var(--surface-2)}
.sent-bar::after{
  content:'';
  position:absolute;
  inset:0;
  border-radius:inherit;
  box-shadow:inset 0 1px 2px rgba(0,0,0,.22);
  pointer-events:none;
}

/* ---------- 7. QUOTES ---------- */
blockquote{
  --bq-pt:0px;
  --bq-indent:clamp(2rem,1.6rem + 1.6vw,2.75rem);
  position:relative;
  margin:0;
  padding:var(--bq-pt) 0 0 var(--bq-indent);
  font-family:var(--font-display);
  font-size:clamp(1.05rem,1rem + .3vw,1.18rem);
  font-style:italic;
  line-height:1.6;
  color:var(--ink);
}
blockquote::before{
  content:'\201C';
  content:'\201C' / '';
  position:absolute;
  top:var(--bq-pt);
  left:0;
  font-family:var(--font-display);
  font-size:3em;
  font-style:normal;
  line-height:1;
  color:var(--accent);
  opacity:.2;
}
blockquote + blockquote{
  --bq-pt:1.6rem;
  margin-top:1.6rem;
  border-top:1px solid var(--border);
}
blockquote cite{
  display:block;
  margin-top:.9rem;
  font-family:var(--font-body);
  font-size:1.0625rem;
  font-style:normal;
  font-weight:600;
  font-variant-caps:all-small-caps;
  line-height:1.3;
  letter-spacing:.09em;
  color:var(--ink-2);
}

/* ---------- 8. CARDS ---------- */
.topic-card,.entity-card{
  padding:var(--card-pad) calc(var(--card-pad) + .1rem);
  border:1px solid var(--border);
  border-radius:var(--radius);
  background:var(--surface-2);
}
.topic-meta{
  margin:.15rem 0 0;
  font-family:var(--font-mono);
  font-size:.85rem;
  line-height:1.6;
  color:var(--ink-2);
}
.topic-meta + .topic-meta{margin-top:.3rem}
.topic-meta code,.footer-meta code{font-size:1em}

.entity-card blockquote{--bq-indent:2rem;margin-top:.8rem;font-size:1rem}
.entity-card blockquote::before{font-size:2.4em}

section:has(> .topic-card),
section:has(> .entity-card){
  display:grid;
  grid-template-columns:minmax(0,1fr);
  gap:var(--gap);
  align-content:start;
}
section:has(> .topic-card) > h2,
section:has(> .entity-card) > h2{margin-bottom:calc(1.5em - var(--gap))}

/* ---------- 9. SLANG ---------- */
.slang-list{
  list-style:none;
  max-width:none;
  margin:0;
  padding:0;
  border-top:1px solid var(--border);
}
.slang-list li{
  display:flex;
  align-items:baseline;
  gap:.75rem;
  margin:0;
  padding:.7rem 0;
  border-bottom:1px solid var(--border);
  line-height:1.5;
}
.slang-list li::before{
  content:'';
  flex:none;
  width:.4rem;
  height:.4rem;
  background:var(--accent);
  transform:translateY(-.12em);
}
.slang-word{
  flex:none;
  min-width:6.25rem;
  font-family:var(--font-mono);
  font-size:.9375rem;
  font-weight:600;
  color:var(--accent);
}

/* ---------- 10. CLOSING MATTER ---------- */
.methodology,.disclaimer{color:var(--ink-2);border-top:1px solid var(--border)}
.methodology{margin-top:4rem;padding-top:1.35rem;font-size:.9375rem;line-height:1.65}
.methodology h2{
  display:block;
  margin:0 0 .6rem;
  padding:0;
  border:0;
  font-size:1.0625rem;
  color:var(--ink);
}
.disclaimer{margin-top:1.75rem;padding-top:1.1rem;font-size:var(--fs-label);line-height:1.6}

footer{
  margin-top:3.5rem;
  padding-top:1.25rem;
  border-top:1px solid var(--border);
  text-align:center;
  font-size:.8rem;
  line-height:1.6;
  color:var(--ink-2);
}
.footer-brand{font-weight:600;letter-spacing:.08em;color:var(--ink)}
.footer-meta{margin-top:.2rem}

/* ---------- 11. RESPONSIVE ---------- */
@media (min-width:40rem){
  .report-meta{grid-template-columns:repeat(4,minmax(0,1fr))}
  .meta-item + .meta-item{padding-left:1.25rem;border-left:1px solid var(--border)}
  .toc ol{columns:2;column-gap:2.5rem}
}
@media (min-width:46rem){
  section:has(> .topic-card){grid-template-columns:repeat(2,minmax(0,1fr))}
  section:has(> .topic-card) > h2{grid-column:1 / -1}
}

/* ---------- 12. ENHANCEMENTS ---------- */
@supports (text-wrap:balance){h1,h2{text-wrap:balance}}
@supports (text-wrap:pretty){p,li,blockquote,.lede{text-wrap:pretty}}

@keyframes rise{
  from{opacity:0;transform:translateY(8px)}
  to{opacity:1;transform:none}
}
body > *{animation:rise .26s ease-out both}

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation:none !important;transition:none !important}
}

/* ---------- 13. PRINT: A4 PORTRAIT ---------- */
@page{size:A4 portrait;margin:20mm 18mm 22mm}

@media print{
  :root{
    --surface:#fff;
    --surface-2:#fff;
    --ink:#000;
    --ink-2:#3a3a37;
    --accent:#1a2b47;
    --neg:#9d3a30;
    --pos:#245a39;
    --neutral:#8a8a85;
    --border:#cfccc4;
    --accent-wash:transparent;
    --accent-ring:rgba(26,43,71,.2);
    --callout-bg:transparent;
    --code-bg:transparent;
    --rule:#000;
    --stamp:rgba(157,58,48,.45);
  }
  html{background:#fff;font-size:10.5pt;scroll-behavior:auto}
  body{max-width:none;padding:0;font-size:10.5pt;line-height:1.55}
  *{animation:none !important;transition:none !important}

  p,.lede,section ul,section ol{max-width:none}
  h1{margin-top:14pt;font-size:24pt}
  h2{padding-top:8pt;font-size:14pt}
  h3{font-size:11pt}
  .lede{font-size:12pt}
  .callout p{font-size:11pt}
  blockquote{font-size:10.5pt}
  blockquote cite{font-size:13pt}
  code{font-size:.95em}
  .brand-tag,.meta-label,.toc-title,.confidential-badge,.sec-num,.toc a::before,.topic-meta,.disclaimer{font-size:9.75pt}
  .methodology{font-size:10pt}
  footer{font-size:9pt}

  h1,h2,h3{break-after:avoid;page-break-after:avoid}
  p{orphans:3;widows:3}
  .report-header,.report-meta,.toc,.snapshot,.callout,.topic-card,.entity-card,blockquote,.slang-list li{
    break-inside:avoid;
    page-break-inside:avoid;
  }

  a{color:inherit;text-decoration:none}
  .toc ol{columns:1}
  .toc,.snapshot,.topic-card,.entity-card{background:none}
  .toc a:hover{background:none;color:inherit}
  .callout{background:none;border-left-width:4px}

  .sent-bar,.sent-bar > *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .sent-bar::after{display:none}
  .sent-bar .pos{background-image:repeating-linear-gradient(135deg,transparent 0 3px,rgba(255,255,255,.55) 3px 5px)}
}
"""


# =============================================================================
# HTML RENDERER
# =============================================================================

def render_html(data: dict, picked: dict, narrative: dict,
                meta: dict | None = None) -> str:
    meta = meta or {}
    summary = data.get("summary", {})
    esc = html.escape

    date_str = meta.get("date") or datetime.now(timezone.utc).strftime("%d %B %Y")
    report_id = meta.get("report_id") or _default_report_id()
    prepared_for = meta.get("prepared_for") or DEFAULT_PREPARED_FOR
    period = meta.get("period") or _default_period()
    total = summary.get("total_comments", 0)

    exec_text, body_paras = _split_exec_summary(narrative.get("cerita_utama", ""))

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="ms"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append(f"<title>Gen Z Malaysia Trend Report — {esc(date_str)}</title>")
    parts.append(f"<style>{_HTML_CSS}</style>")
    parts.append("</head><body>")

    # --- Cover header ---
    parts.append('<header class="report-header">')
    parts.append('<div class="brand">')
    parts.append('<span class="brand-mark">ATRRIC</span>')
    parts.append(f'<span class="brand-tag">{esc(DEFAULT_BRAND_TAG)}</span>')
    parts.append("</div>")
    parts.append('<span class="confidential-badge">Confidential</span>')
    parts.append("</header>")

    # --- Meta block ---
    parts.append('<section class="report-meta">')
    for label, value in [
        ("Prepared for", prepared_for),
        ("Report ID", report_id),
        ("Period", period),
        ("Sample size", f"{total} komen"),
    ]:
        parts.append(
            f'<div class="meta-item">'
            f'<span class="meta-label">{esc(label)}</span>'
            f'<span class="meta-value">{esc(value)}</span>'
            f'</div>'
        )
    parts.append("</section>")

    # --- Title + lede ---
    parts.append(f"<h1>Gen Z Malaysia Trend Report</h1>")
    parts.append(f'<p class="lede">{esc(narrative.get("headline", ""))}</p>')

    # --- TOC ---
    parts.append('<nav class="toc">')
    parts.append('<div class="toc-title">Kandungan</div>')
    parts.append("<ol>")
    for sid, title in SECTIONS:
        parts.append(f'<li><a href="#{sid}">{esc(title)}</a></li>')
    parts.append("</ol>")
    parts.append("</nav>")

    # --- 01 Exec summary ---
    parts.append('<section class="exec-summary" id="s01">')
    parts.append('<h2><span class="sec-num">01</span>Ringkasan Eksekutif</h2>')
    parts.append('<div class="callout">')
    if exec_text:
        parts.append(f"<p>{esc(exec_text)}</p>")
    else:
        parts.append("<p><i>(tiada ringkasan)</i></p>")
    parts.append("</div>")
    parts.append("</section>")

    # --- 02 Snapshot ---
    parts.append('<section id="s02">')
    parts.append('<h2><span class="sec-num">02</span>Snapshot Data</h2>')
    parts.append(_html_snapshot(summary))
    parts.append("</section>")

    # --- 03 Cerita Utama ---
    parts.append('<section id="s03">')
    parts.append('<h2><span class="sec-num">03</span>Cerita Utama</h2>')
    if body_paras:
        for p in body_paras:
            parts.append(f"<p>{esc(p)}</p>")
    else:
        parts.append("<p><i>(tiada naratif)</i></p>")
    parts.append("</section>")

    # --- 04 Suara Responden ---
    parts.append('<section id="s04">')
    parts.append('<h2><span class="sec-num">04</span>Suara Responden</h2>')
    parts.append(_html_quotes(picked.get("top_quotes", [])))
    parts.append("</section>")

    # --- 05 Topik Trending ---
    parts.append('<section id="s05">')
    parts.append('<h2><span class="sec-num">05</span>Topik Trending</h2>')
    parts.append(_html_topics(picked.get("topic_breakdown", [])))
    parts.append("</section>")

    # --- 06 Entiti Utama ---
    parts.append('<section id="s06">')
    parts.append('<h2><span class="sec-num">06</span>Entiti Utama</h2>')
    parts.append(_html_entities(picked.get("entity_context", [])))
    parts.append("</section>")

    # --- 07 Bahasa & Slang ---
    parts.append('<section id="s07">')
    parts.append('<h2><span class="sec-num">07</span>Bahasa &amp; Slang</h2>')
    parts.append(_html_slang(picked.get("slang_curated", [])))
    parts.append("</section>")

    # --- 08 Insight ---
    parts.append('<section id="s08">')
    parts.append('<h2><span class="sec-num">08</span>Insight</h2>')
    parts.append(_paras(narrative.get("insight", "")))
    parts.append("</section>")

    # --- 09 Rekomendasi ---
    parts.append('<section id="s09">')
    parts.append('<h2><span class="sec-num">09</span>Rekomendasi</h2>')
    parts.append(_paras(narrative.get("rekomendasi", "")))
    parts.append("</section>")

    # --- Methodology ---
    parts.append('<section class="methodology">')
    parts.append("<h2>Metodologi</h2>")
    parts.append(f"<p>{esc(_methodology_text(data))}</p>")
    parts.append("</section>")

    # --- Disclaimer ---
    parts.append('<section class="disclaimer">')
    parts.append(f"<p>{esc(_disclaimer_text())}</p>")
    parts.append("</section>")

    # --- Footer ---
    model = narrative.get("_meta", {}).get("model", "-")
    cost = meta.get("cost_est_rm")
    cost_str = f"~RM{cost:.6f}" if isinstance(cost, float) else "-"
    parts.append("<footer>")
    parts.append('<div class="footer-brand">ATRRIC · Market Intelligence for Gen Z Malaysia</div>')
    parts.append(
        f'<div class="footer-meta">Report ID {esc(report_id)} · {total} komen · '
        f'model <code>{esc(str(model))}</code> · kos {esc(cost_str)}</div>'
    )
    parts.append("</footer>")

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
    return (
        '<div class="snapshot">'
        "<ul>"
        f"<li><b>Total komen</b>: {total}</li>"
        f"<li><b>Topik dominan</b>: {html.escape(top_topic)}</li>"
        f'<li><b>Sentiment</b>: {neg} negatif ({p_neg}%) · '
        f"{pos} positif ({p_pos}%) · {neu} neutral ({p_neu}%)</li>"
        "</ul>"
        '<div class="sent-bar">'
        f'<div class="neg" style="width:{p_neg}%"></div>'
        f'<div class="neu" style="width:{p_neu}%"></div>'
        f'<div class="pos" style="width:{p_pos}%"></div>'
        "</div>"
        "</div>"
    )


def _html_quotes(quotes: list[dict]) -> str:
    if not quotes:
        return "<p><i>(tiada quote tersedia)</i></p>"
    out: list[str] = []
    for q in quotes:
        tag = f"{q['topic']} · {q['sentiment']}"
        out.append(
            f"<blockquote>{html.escape(q['text'])}"
            f"<cite>— {html.escape(tag)}</cite></blockquote>"
        )
    return "\n".join(out)


def _html_topics(breakdown: list[dict]) -> str:
    if not breakdown:
        return "<p><i>(tiada data)</i></p>"
    out: list[str] = []
    for tb in breakdown:
        s = tb["sentiment"]
        entities = ", ".join(tb.get("top_entities", [])) or "-"
        out.append('<div class="topic-card">')
        out.append(
            f"<h3>{html.escape(tb['topic'])} — {tb['count']} ({tb['pct']}%)</h3>"
        )
        out.append(
            f'<div class="topic-meta">{s["negative"]} · '
            f'{s["positive"]} · {s["neutral"]}</div>'
        )
        out.append(
            f'<div class="topic-meta">Entities: '
            f'<code>{html.escape(entities)}</code></div>'
        )
        out.append("</div>")
    return "\n".join(out)


def _html_entities(entities: list[dict]) -> str:
    if not entities:
        return "<p><i>(tiada data)</i></p>"
    out: list[str] = []
    for e in entities:
        out.append('<div class="entity-card">')
        out.append(
            f"<h3>{html.escape(e['name'])} — {e['count']} sebutan</h3>"
        )
        for ex in e.get("examples", []):
            out.append(f"<blockquote>{html.escape(ex)}</blockquote>")
        out.append("</div>")
    return "\n".join(out)


def _html_slang(slang: list[dict]) -> str:
    if not slang:
        return "<p><i>(tiada slang signifikan)</i></p>"
    out = ['<ul class="slang-list">']
    for s in slang:
        out.append(
            f'<li><span class="slang-word">{html.escape(s["word"])}</span> '
            f"<span>({s['count']}x) — {html.escape(s['note'])}</span></li>"
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

    print("=== TEMPLATE v2 SELF-TEST (B2B structure) ===")
    data = load_all()
    picked = pick_all(data)

    narrative = {
        "headline": "Test headline — placeholder sahaja.",
        "cerita_utama": (
            "Ini exec summary paragraph pertama. Ringkas dan tinggi level.\n\n"
            "Ini body paragraph kedua. Lebih detail tentang data.\n\n"
            "Ini body paragraph ketiga. Insight tambahan."
        ),
        "insight": "Insight test paragraph.",
        "rekomendasi": "Rekomendasi test paragraph.",
        "_meta": {"model": "placeholder", "fallback": True},
    }

    paths = write_report(data, picked, narrative, meta={"date": "17 Oktober 2026"})
    print(f"OK report.md   → {paths['md']}")
    print(f"OK report.html → {paths['html']}")
    print()
    print("Preview markdown (15 baris pertama):")
    with open(paths["md"], encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 15:
                break
            print(f"  {line.rstrip()}")