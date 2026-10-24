import json
from pathlib import Path

_DIR = Path(__file__).parent / "discovered"
def _p(name):
    _DIR.mkdir(exist_ok=True)
    return _DIR / f"{name}.json"
def load(name):
    p = _p(name)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
def save(name, data):
    _p(name).write_text(json.dumps(data, ensure_ascii=False, indent=2),
                        encoding="utf-8")
