"""
core/embed.py — Embedding wrapper using ILMU bge-m3 API.

Zero local deps. Guna urllib sahaja.
Interface sama: embed(text) -> list[float] (1024 dims)
"""

import json
import os
import urllib.error
import urllib.request

# Expected dimension (bge-m3)
EXPECTED_DIM = 1024


class EmbedError(Exception):
    """Raised when embedding fails."""


_DEFAULT_URL = "https://api.ilmu.ai/v1"
_DEFAULT_MODEL = "bge-m3"


def embed(text: str, timeout: int = 60, model: str = None, api_key: str = None) -> list:
    """
    Generate embedding vector via ILMU bge-m3.

    Args:
        text: Input text to embed.
        timeout: Max seconds to wait.
        model: Override model (default: bge-m3).
        api_key: Override key (default: from env ILMU_API_KEY).

    Returns:
        List of 1024 floats.

    Raises:
        ValueError: If text is empty.
        EmbedError: If API fails.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")

    key = api_key or os.environ.get("ILMU_API_KEY")
    if not key:
        raise EmbedError("ILMU_API_KEY tak set. Set dalam .env atau env var.")

    body = {
        "model": model or _DEFAULT_MODEL,
        "input": text,
    }

    req = urllib.request.Request(
        f"{_DEFAULT_URL}/embeddings",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:300]
        raise EmbedError(f"HTTP {e.code}: {err}") from e
    except urllib.error.URLError as e:
        raise EmbedError(f"Connection failed: {e}") from e

    try:
        vec = data["data"][0]["embedding"]
    except (KeyError, IndexError, TypeError) as e:
        raise EmbedError(f"Unexpected response: {str(data)[:300]}") from e

    if len(vec) != EXPECTED_DIM:
        raise EmbedError(
            f"Expected {EXPECTED_DIM} dims, got {len(vec)}. "
            f"Check model in config."
        )

    return vec


if __name__ == "__main__":
    from core.env_loader import load_env
    load_env()
    v = embed("Gen Z Malaysia")
    print(f"Dim: {len(v)}")
    print(f"First 3: {v[:3]}")