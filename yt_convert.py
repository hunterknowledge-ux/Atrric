#!/usr/bin/env python3
"""
yt_convert.py — Convert yt-dlp .info.json -> Atrric raw format.

Features:
  - Auto-skip duplicates by title
  - Text trimming (max 2000 chars per comment)
  - Filter: promo, pinned, short comments
  - --force    : override auto-skip
  - --dry-run  : test without writing
  - --stats    : show file stats
  - --dedupe   : scan + remove duplicate posts

Usage:
  python yt_convert.py <input.json> <output.txt>
  python yt_convert.py <input.json> <output.txt> --force
  python yt_convert.py --stats <output.txt>
  python yt_convert.py --dedupe <output.txt>
"""

import json
import re
import sys
from pathlib import Path

MIN_LENGTH = 20
MAX_LENGTH = 2000
URL_RE = re.compile(r'https?://\S+')


# ─────────────────────────────────────────────────────────────
# Text helpers
# ─────────────────────────────────────────────────────────────

def clean_text(text):
    if not text:
        return ""
    text = text.replace('\\r\\n', ' ').replace('\\n', ' ')
    text = text.replace('\r\n', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH].rstrip() + '...'
    return text


def is_promo(text):
    return len(URL_RE.findall(text)) >= 3


def passes_filter(c):
    if c.get('author_is_uploader'):
        return False
    if c.get('is_pinned'):
        return False
    text = clean_text(c.get('text', ''))
    if len(text) < MIN_LENGTH:
        return False
    if is_promo(text):
        return False
    return True


# ─────────────────────────────────────────────────────────────
# File helpers
# ─────────────────────────────────────────────────────────────

def load_output(output_path):
    p = Path(output_path)
    if not p.exists():
        return ""
    return p.read_text(encoding='utf-8')


def next_post_num(output_path):
    content = load_output(output_path)
    matches = re.findall(r'\[Post (\d+)\]', content)
    return max((int(m) for m in matches), default=0) + 1


def already_converted(output_path, title):
    content = load_output(output_path)
    if not content:
        return False
    cleaned = clean_text(title)
    return f'OP: {cleaned}' in content


def split_posts(content):
    """Split file content into [Post n] blocks."""
    parts = re.split(r'(?=\[Post \d+\])', content)
    return [p for p in parts if p.strip()]


# ─────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────

def cmd_stats(output_path):
    content = load_output(output_path)
    if not content:
        print(f"File empty or not found: {output_path}")
        return
    posts = split_posts(content)
    print(f"File: {output_path}")
    print(f"Total posts: {len(posts)}")
    print()
    for p in posts:
        m = re.search(r'\[Post (\d+)\]', p)
        op = re.search(r'OP: (.+?)(?:\n|$)', p)
        r_count = len(re.findall(r'^R:', p, re.MULTILINE))
        rr_count = len(re.findall(r'^R:R:', p, re.MULTILINE))
        n = m.group(1) if m else '?'
        title = op.group(1)[:70] if op else '?'
        print(f"  Post {n}: {r_count} top + {rr_count} replies")
        print(f"    {title}")


def cmd_dedupe(output_path):
    content = load_output(output_path)
    if not content:
        print(f"File empty: {output_path}")
        return

    posts = split_posts(content)
    seen_titles = set()
    kept = []
    dropped = 0

    for p in posts:
        op = re.search(r'OP: (.+?)(?:\n|$)', p)
        title = op.group(1).strip() if op else ''

        if title in seen_titles:
            print(f"Dropping duplicate: {title[:70]}")
            dropped += 1
            continue

        seen_titles.add(title)
        kept.append(p)

    if dropped == 0:
        print("No duplicates found.")
        return

    # Renumber
    counter = [0]
    def renum(m):
        counter[0] += 1
        return f'[Post {counter[0]}]'

    result = ''.join(kept)
    result = re.sub(r'\[Post \d+\]', renum, result)

    Path(output_path).write_text(result, encoding='utf-8')
    print(f"\nDropped {dropped} duplicates. Kept {counter[0]} posts.")
    print(f"Saved: {output_path}")


def cmd_convert(input_path, output_path, force=False, dry_run=False):
    # Load input
    try:
        with open(input_path, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {input_path}")
        print(f"       {e}")
        sys.exit(1)

    title = data.get('title', 'Untitled')
    comments = data.get('comments', [])

    if not comments:
        print(f"WARN: No comments in {input_path}")
        print(f"      Title: {clean_text(title)[:80]}")
        print("      (Video mungkin takde komen atau comments disabled)")
        return

    # Duplicate check
    if not force and already_converted(output_path, title):
        print(f"SKIP  Already exists in {output_path}")
        print(f"      Title: {clean_text(title)[:80]}")
        print("      Use --force to override.")
        return

    # Process
    kept = [c for c in comments if passes_filter(c)]
    top = [c for c in kept if c.get('parent') == 'root']
    replies_by_parent = {}
    for c in kept:
        p = c.get('parent')
        if p and p != 'root':
            replies_by_parent.setdefault(p, []).append(c)

    n_replies = sum(len(v) for v in replies_by_parent.values())

    if dry_run:
        print(f"DRY-RUN  Would add Post {next_post_num(output_path)}")
        print(f"         Title: {clean_text(title)[:80]}")
        print(f"         Comments: {len(top)} top + {n_replies} replies")
        print(f"         Total kept: {len(kept)} / {len(comments)} raw")
        return

    # Build output
    post_num = next_post_num(output_path)
    lines = [f"[Post {post_num}]", f"OP: {clean_text(title)}", ""]
    for t in top:
        lines.append(f"R: {clean_text(t.get('text', ''))}")
        for r in replies_by_parent.get(t['id'], []):
            lines.append(f"R:R: {clean_text(r.get('text', ''))}")
    lines.extend(["", "---", ""])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"OK    Post {post_num}: {len(top)} top + {n_replies} replies")
    print(f"      Saved to {output_path}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith('--')}
    positional = [a for a in args if not a.startswith('--')]

    if '--stats' in flags:
        if not positional:
            print("Usage: python yt_convert.py --stats <output.txt>")
            sys.exit(1)
        cmd_stats(positional[0])
        return

    if '--dedupe' in flags:
        if not positional:
            print("Usage: python yt_convert.py --dedupe <output.txt>")
            sys.exit(1)
        cmd_dedupe(positional[0])
        return

    if len(positional) < 2:
        print("Usage:")
        print("  python yt_convert.py <input.json> <output.txt> [--force] [--dry-run]")
        print("  python yt_convert.py --stats <output.txt>")
        print("  python yt_convert.py --dedupe <output.txt>")
        sys.exit(1)

    cmd_convert(
        positional[0],
        positional[1],
        force='--force' in flags,
        dry_run='--dry-run' in flags,
    )


if __name__ == '__main__':
    main()