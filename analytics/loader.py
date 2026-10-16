import re
from pathlib import Path
from .normalize import clean

_D = [(re.compile(r"^\s*>{2,}\s*"), 2), (re.compile(r"^\s*>\s*"), 1),
      (re.compile(r"^\s*R:\s*", re.I), 1), (re.compile(r"^\s*OP:\s*", re.I), 0)]

_HEADER_RE = re.compile(r"^\s*\[[^\]]+\]\s*$")

def _depth(l):
    for pat, d in _D:
        if pat.match(l):
            return d, pat.sub("", l).strip()
    lead = len(l) - len(l.lstrip(" "))
    if lead >= 4:
        return 2, l.strip()
    if lead >= 2:
        return 1, l.strip()
    return 0, l.strip()

def load_all(raw_root="raw_data"):
    root = Path(raw_root)
    out = []
    for sub in ["raw_data", "threads", "youtube"]:
        d = root / sub
        if not d.exists():
            continue
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
                        "id": f"{sub}_{f.stem}_{i:04d}",
                        "source": f.name,
                        "depth": depth,
                        "text": text,
                    })
    return out