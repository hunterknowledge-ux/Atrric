"""
core/embed.py - Embedding wrapper using llama-embedding.

Calls the llama-embedding binary with the configured model,
parses the output, and returns a vector as a list of floats.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Add repo root to path so `import config` works
sys.path.insert(0, str(Path(__file__).parent.parent))

import config

# Expected embedding dimension (hourai2-50m = 384)
EXPECTED_DIM = 128


class EmbedError(Exception):
    """Raised when embedding fails."""
    pass


def embed(text: str, timeout: int = 120) -> List[float]:
    """
    Generate an embedding vector for the given text.

    Args:
        text: Input text to embed.
        timeout: Max seconds to wait for llama-embedding.

    Returns:
        List of floats representing the embedding vector.

    Raises:
        ValueError: If text is empty.
        EmbedError: If subprocess fails, times out, or output is unparsable.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")

    cmd = [
        str(config.LLAMA_EMBED),
        "-m", str(config.EMBED_MODEL),
        "-p", text,
        "--pooling", "mean",
        "-c", str(config.CONTEXT_SIZE),
        "-t", str(config.THREADS),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise EmbedError(f"Embedding timed out after {timeout}s") from e
    except FileNotFoundError as e:
        raise EmbedError(f"Binary not found: {config.LLAMA_EMBED}") from e

    if result.returncode != 0:
        raise EmbedError(
            f"llama-embedding exited with code {result.returncode}\n"
            f"STDERR: {result.stderr[-300:]}"
        )

    vector = _parse_embedding(result.stdout)

    if vector is None:
        raise EmbedError(
            f"No embedding line found in output.\n"
            f"STDOUT: {result.stdout[-300:]}"
        )

    if len(vector) != EXPECTED_DIM:
        raise EmbedError(
            f"Expected {EXPECTED_DIM} dims, got {len(vector)}. "
            f"Check EMBED_MODEL in config.py."
        )

    return vector



   
def _parse_embedding(stdout: str) -> Optional[List[float]]:
    """
    Extract embedding vector from llama-embedding stdout.

    Strategy: scan all lines, find the line (or set of lines)
    with the most floats. Return that as the vector.
    """
    import re
    pattern = r"-?\d+\.\d+(?:[eE][+-]?\d+)?"

    best: List[float] = []

    for line in stdout.splitlines():
        nums = [float(x) for x in re.findall(pattern, line)]
        if len(nums) > len(best):
            best = nums
        elif nums and len(best) < EXPECTED_DIM:
            # Try accumulating across lines
            combined = best + nums
            if len(combined) <= EXPECTED_DIM * 2:
                best = combined

    return best if best else None
    return None


if __name__ == "__main__":
    vec = embed("Gen Z Malaysia")
    print(f"Vector length: {len(vec)}")
    print(f"First 3 values: {vec[:3]}")