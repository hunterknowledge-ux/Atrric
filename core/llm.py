"""
core/llm.py - LLM wrapper using llama-cli.

Runs llama-cli, feeds the prompt, sends /exit via stdin to close
the interactive session, and returns the cleaned generated text.
"""

import re
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


# Where the generated text ends.
_STOP_MARKERS = (
    "\nSoalan:",
    "\nQuestion:",
    "\nData:",
    "\n[ Prompt:",
    "\n[ Generation:",
    "\nExiting",
    "\n\n> ",
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
        Cleaned generated text.

    Raises:
        ValueError: If prompt is empty.
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
    ]

    try:
        result = subprocess.run(
            cmd,
            input="/exit\n",
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise LLMError(f"Generation timed out after {timeout}s")
    except FileNotFoundError:
        raise LLMError(f"Binary not found: {config.LLAMA_CLI}")

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
    """Extract text after last 'Jawapan:' marker."""
    raw = re.sub(r"\x1b\[[0-9;]*m", "", raw)

    # Find last "Jawapan:" (model answer follows prompt echo)
    idx = raw.rfind("Jawapan:")
    if idx == -1:
        return raw.strip()[:500]

    tail = raw[idx + len("Jawapan:"):]

    # Cut at stats / exit
    for stop in ("\n[ Prompt:", "\n[ Generation:", "\nExiting", "\n\n> "):
        stop_idx = tail.find(stop)
        if stop_idx != -1:
            tail = tail[:stop_idx]

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