"""
report.__main__ — CLI orchestrator Report Layer.

Usage:
    python -m report                    # full run (semua komen, LLM call)
    python -m report --limit=20         # test dengan 20 komen je
    python -m report --dry-run          # estimate kos, TAK call LLM
    python -m report --no-llm           # guna fallback narrative
    python -m report --model=ilmu-glm-5.3-flash
    python -m report --out=md           # hanya markdown
    python -m report --out=html         # hanya HTML
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from report.generate import _build_narrative_prompt, generate_narrative
from report.loader import load_all
from report.picker import pick_all

# Rate assumption untuk estimate (ilmu-mini-v3.3)
COST_PER_M_TOKEN_RM = 0.38


def _estimate_cost(data: dict, picked: dict) -> dict:
    """Kira estimate kos tanpa call LLM."""
    prompt = _build_narrative_prompt(
    data["summary"], picked, data["meta"]["total_loaded"]
)
    tokens_in = len(prompt) // 4
    tokens_out_max = 1500
    total_tokens = tokens_in + tokens_out_max
    cost_rm = total_tokens * COST_PER_M_TOKEN_RM / 1_000_000
    return {
        "tokens_in": tokens_in,
        "tokens_out_max": tokens_out_max,
        "cost_rm": cost_rm,
        "prompt_chars": len(prompt),
    }


def _fmt_cost(rm: float) -> str:
    if rm < 0.001:
        return f"RM{rm:.6f} (bawah 1 sen)"
    return f"RM{rm:.4f}"


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m report",
        description="ATRRIC Report Layer — generate trend report dari analytics.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Hadkan bilangan komen (untuk testing).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Estimate kos sahaja. Tak call LLM, tak tulis report.",
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="Skip LLM. Guna fallback narrative (numbers still useful).",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Override model (contoh: ilmu-glm-5.3-flash).",
    )
    parser.add_argument(
        "--out", type=str, default="both", choices=["md", "html", "both"],
        help="Output format (default: both).",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip confirmation prompt (untuk automation).",
    )
    args = parser.parse_args()

    t0 = time.time()

    # --- Load ---
    print("[1/4] Loading analytics...")
    try:
        data = load_all(limit=args.limit)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    total = data["meta"]["total_loaded"]
    print(f"      ✓ {total} komen dimuatkan "
          f"({len(data['meta']['sources'])} sumber)")

    # --- Pick ---
    print("[2/4] Picking quotes + insights...")
    picked = pick_all(data)
    print(f"      ✓ {len(picked['top_quotes'])} quote, "
          f"{len(picked['entity_context'])} entity, "
          f"{len(picked['slang_raw'])} slang, "
          f"{len(picked['topic_breakdown'])} topic")

    # --- Dry run: berhenti sini ---
    if args.dry_run:
        est = _estimate_cost(data, picked)
        print()
        print("=== DRY RUN — Estimate Kos ===")
        print(f"  Prompt chars    : {est['prompt_chars']}")
        print(f"  Input tokens    : ~{est['tokens_in']}")
        print(f"  Output max      : ~{est['tokens_out_max']}")
        print(f"  Model           : {args.model or 'default (ilmu-mini-v3.3)'}")
        print(f"  Cost estimate   : {_fmt_cost(est['cost_rm'])}")
        print()
        print("Tiada report dijana (dry-run).")
        return 0

    # --- Confirm sebelum LLM call ---
    if not args.no_llm and not args.yes:
        est = _estimate_cost(data, picked)
        print()
        print(f"⚠ Akan call LLM 1 kali (~{_fmt_cost(est['cost_rm'])}).")
        try:
            ans = input("Teruskan? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            print("Cancelled.")
            return 1
        if ans != "y":
            print("Cancelled.")
            return 1

    # --- Generate narrative ---
    if args.no_llm:
        print("[3/4] Skipping LLM (--no-llm), guna fallback narrative...")
        from report.generate import _fallback
        narrative = _fallback(data["summary"])
        narrative["_meta"] = {
            "model": "fallback (no-llm mode)",
            "fallback": True,
        }
        print("      ✓ Fallback narrative sedia")
    else:
        print("[3/4] Calling LLM untuk naratif...")
        narrative = generate_narrative(data, picked, model=args.model)
        meta = narrative.get("_meta", {})
        if meta.get("fallback"):
            reason = meta.get("reason", "unknown")
            print(f"      ⚠ Fallback triggered: {reason}")
        else:
            print(f"      ✓ Model: {meta.get('model')}")
            print(f"      ✓ Tokens: in~{meta.get('tokens_in_est')} "
                  f"out~{meta.get('tokens_out_est')}")

    # --- Render ---
    print("[4/4] Rendering report...")

    # Cost meta untuk footer
    meta_extra = {"cost_est_rm": None}
    if not args.no_llm and not narrative.get("_meta", {}).get("fallback"):
        # Kira balik dari actual tokens
        m = narrative.get("_meta", {})
        total_tok = (m.get("tokens_in_est", 0) or 0) + \
                    (m.get("tokens_out_est", 0) or 0)
        meta_extra["cost_est_rm"] = total_tok * COST_PER_M_TOKEN_RM / 1_000_000

    # Filter output — kalau --out=md atau html, tulis satu je
    if args.out in ("md", "both"):
        from report.template import render_markdown
        md = render_markdown(data, picked, narrative, meta=meta_extra)
        md_path = Path(__file__).parent / "out" / "report.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(f"      ✓ {md_path}")

    if args.out in ("html", "both"):
        from report.template import render_html
        html_str = render_html(data, picked, narrative, meta=meta_extra)
        html_path = Path(__file__).parent / "out" / "report.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_str, encoding="utf-8")
        print(f"      ✓ {html_path}")

    elapsed = time.time() - t0
    print()
    print(f"✅ Siap dalam {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())