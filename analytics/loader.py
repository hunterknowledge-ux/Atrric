import re
from pathlib import Path

from .normalize import clean

_D = [(re.compile(r"^\s*>{2,}\s*"), 2), (re.compile(r"^\s*>\s*"), 1),
      (re.compile(r"^\s*R:\s*", re.IGNORECASE), 1), (re.compile(r"^\s*OP:\s*", re.IGNORECASE), 0)]

_HEADER_RE = re.compile(r"^\s*\[[^\]]+\]\s*$")
_SKIP = {"__pycache__", "discovered", "out", "analytics_out"}

def _depth(l):
    for pat, d in _D:
        if pat.match(l):
            return d, pat.sub("", l).strip()
    lead = len(l) - len(l.lstrip(" "))
    if lead >= 4: return 2, l.strip()
    if lead >= 2: return 1, l.strip()
    return 0, l.strip()

def load_all(raw_root="raw_data"):
    root = Path(raw_root)
    if not root.exists():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if not d.is_dir(): continue
        if d.name.startswith(".") or d.name in _SKIP: continue
        for f in sorted(d.glob("*.txt")):
            lines = [
                l for l in f.read_text(encoding="utf-8", errors="replace").splitlines()
                if l.strip()
                and not l.strip().startswith("#")
                and not _HEADER_RE.match(l)
            ]
            for i, line in enumerate(lines):
                depth, text = _depth(line)
                text = clean(text)
                if text:
                    out.append({
                        "id": f"{d.name}_{f.stem}_{i:04d}",
                        "source": f.name,
                        "depth": depth,
                        "text": text,
                    })
    return out