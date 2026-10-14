#!/usr/bin/env python3
"""
Convert yt-dlp .info.json -> Atrric raw format.

Usage:
  python yt_convert.py <input.json> <output.txt>
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


def convert(input_path, output_path):
    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)

    title = data.get('title', 'Untitled')
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

    with open(output_path, 'a', encoding='utf-8') as f:
        f.write("\n".join(lines))

    n_replies = sum(len(v) for v in replies_by_parent.values())
    print(f"OK  Post {post_num}: {len(top)} top + {n_replies} replies  ->  {output_path}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python yt_convert.py <input.json> <output.txt>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])