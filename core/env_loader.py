"""Auto-load .env into os.environ — no manual export needed."""

import os
from pathlib import Path


def load_env(env_path=None):
    """Load .env file. Don't overwrite existing env vars."""
    if env_path is None:
        env_path = Path(__file__).parent.parent / ".env"
    else:
        env_path = Path(env_path)

    if not env_path.exists():
        return False

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value
    return True