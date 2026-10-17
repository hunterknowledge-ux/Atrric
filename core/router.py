import json
from pathlib import Path

_SETTINGS_PATH = Path(__file__).parent.parent / "analytics" / "settings.json"

def get_model(task: str = "default") -> str:
    """Return model name based on task from analytics/settings.json."""
    if not _SETTINGS_PATH.exists():
        return "ilmu-mini-v3.3" # Fallback
    
    try:
        data = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        routing = data.get("routing", {})
        return routing.get(task, routing.get("default", "ilmu-mini-v3.3"))
    except Exception:
        return "ilmu-mini-v3.3"