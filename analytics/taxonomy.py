import json
from pathlib import Path

_SCHEMA = Path(__file__).parent.parent / "core" / "ontology_schema.json"
_cache = None
def load():
    global _cache
    if _cache is None:
        _cache = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    return _cache
def attributes():
    return load().get("attributes", [])
