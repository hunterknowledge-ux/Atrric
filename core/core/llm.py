"""
core/llm.py - LLM wrapper using llama-cli.

Calls llama-cli in non-interactive mode, sends a prompt,
and returns the generated text (cleaned).
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class LLMError(Exception):
    """Raised when LLM generation fails."""
    pass


# Markers that indicate end of generated text
_STOP_MARKERS = (
    "\n[ Prompt:",
    "\n> ",
    "\n\n> ",
    "\n\navailable commands:",
)


def generate(
    prompt: str,
    max_tokens: Optional[int] = None,
    timeout: int = 300,
) -> str:
    """
    Generate text from a prompt using llama-cli.

    Args:
        prompt: The input prompt.
        max_tokens: Max new tokens. Defaults to config.MAX_TOKENS.
        timeout: Max seconds to wait.

    Returns:
        Cleaned generated text (without prompt echo or stats).

    Raises:
        LLMError: If subprocess fails or output is empty.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Cannot generate from empty prompt")

    n = max_tokens if max_tokens is not None else config.MAX_TOKENS

    cmd = [
        str(config.LLAMA_CLI),
        "-m", str(config.SMOLLM_MODEL),
        "-p", prompt,
        "-n", str(n),
        "-t", str(config.THREADS),
        "-c", str(config.CONTEXT_SIZE),
        "--simple-io",
    ]

    try:
        result = subprocess.run(
            cmd,
            input="/exit\n",
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise LLMError(f"Generation timed out after {timeout}s") from e
    except FileNotFoundError as e:
        raise LLMError(f"Binary not found: {config.LLAMA_CLI}") from e

    if result.returncode != 0:
        raise LLMError(
            f"llama-cli exited with code {result.returncode}\n"
            f"STDERR: {result.stderr[-300:]}"
        )

    text = _clean_output(result.stdout, prompt)

    if not text:
        raise LLMError(
            f"No generated text found.\n"
            f"STDOUT tail: {result.stdout[-400:]}"
        )

    return text


def _clean_output(raw: str, prompt: str) -> str:
    """
    Extract generated text from llama-cli output.

    llama-cli echoes the prompt, prints stats, and enters
    interactive mode. We extract only the generated portion.
    """
    # llama-cli may echo the prompt; strip up to last occurrence
    tail = raw
    if prompt in raw:
        tail = raw.rsplit(prompt, 1)[-1]

    # Cut at any stop marker
    cut_at = len(tail)
    for marker in _STOP_MARKERS:
        idx = tail.find(marker)
        if idx != -1 and idx < cut_at:
            cut_at = idx
    tail = tail[:cut_at]

    return tail.strip()


if __name__ == "__main__":
    test_prompt = (
        "Data:\n"
        "Gen Z Malaysia suka TikTok dan Instagram.\n\n"
        "Soalan: Apa platform kegemaran Gen Z?\n"
        "Jawapan:"
    )
    out = generate(test_prompt, max_tokens=40)
    print("--- Generated ---")
    print(out)