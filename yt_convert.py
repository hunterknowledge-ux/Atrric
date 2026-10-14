#!/usr/bin/env python3
"""
Convert yt-dlp .info.json -> Atrric raw format.

Auto-skips if the video title already exists in output file.

Usage:
  python yt_convert.py <input.json> <output.txt>
  python yt_convert.py <input.json> <output.txt> --force   # allow duplicate
"""

import json
import sys
import re
from pathlib import Path

MIN_LENGTH = 20
URL_RE = re.compile(r'https?://\S+')


def clean_text(text):
    if not text:
        return ""
    text = text.replace('\\r\\n', ' ').replace('\\n', ' ')
    text = text.replace('\r\n', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


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


def next_post_num(output_path):
    if not Path(output_path).exists():
        return 1
    with open(output_path, encoding='utf-8') as f:
        matches = re.findall(r'\[Post (\d+)\]', f.read())
    return max((int(m) for m in matches), default=0) + 1


def already_converted(output_path, title):
    """Check if OP with this title already exists in output file."""
    p = Path(output_path)
    if not p.exists():
        return False
    content = p.read_text(encoding='utf-8')
    cleaned = clean_text(title)
    # Match 'OP: <title>' pattern
    return f'OP: {cleaned}' in content


def convert(input_path, output_path, force=False):
    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)

    title = data.get('title', 'Untitled')

    if not force and already_converted(output_path, title):
        print(f'SKIP  Already exists in {output_path}')
        print(f'      Title: {clean_text(title)[:80]}')
        print(f'      Use --force to override.')
        return

    comments = data.get('comments', [])

    kept = [c for c in comments if passes_filter(c)]
    top = [c for c in kept if c.get('parent') == 'root']
    replies_by_parent = {}
    for c in kept:
        p = c.get('parent')
        if p and p != 'root':
            replies_by_parent.setdefault(p, []).append(c)

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

    n_replies = sum(len(v) for v in replies_by_parent.values())
    print(f"OK    Post {post_num}: {len(top)} top + {n_replies} replies  ->  {output_path}")


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv

    if len(args) < 2:
        print("Usage: python yt_convert.py <input.json> <output.txt> [--force]")
        sys.exit(1)

    convert(args[0], args[1], force=force)