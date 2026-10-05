"""
core/llm.py - LLM wrapper using llama-cli.

Calls llama-cli in non-conversation mode, sends a prompt,
and returns the generated text (cleaned).
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class LLMError(Exception):
    """Raised when LLM generation fails."""
    pass


# Flags that disable interactive chat mode. Different llama.cpp
# builds name this differently, so we try both and use whichever works.
_NON_CONVERSATION_FLAGS = ("-no-cnv", "--no-conversation")

# Markers where the generated text ends.
_STOP_MARKERS = (
    "\n[ Prompt:",
    "\n[ Generation:",
    "\nExiting",
    "\n\n> ",
)

# Answer prefixes. Last occurrence wins (model may echo prompt first).
_ANSWER_MARKERS = ("Jawapan:", "Answer:")


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
        ValueError: If prompt is empty.
        LLMError: If subprocess fails or output is empty.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Cannot generate from empty prompt")

    n = max_tokens if max_tokens is not None else config.MAX_TOKENS

    base_cmd = [
        str(config.LLAMA_CLI),
        "-m", str(config.SMOLLM_MODEL),
        "-p", prompt,
        "-n", str(n),
        "-t", str(config.THREADS),
        "-c", str(config.CONTEXT_SIZE),
    ]

    stdout, stderr = _run_with_flag_fallback(base_cmd, timeout)

    if stdout is None:
        raise LLMError(
            f"llama-cli failed with all flag variants. "
            f"Last stderr: {stderr[-300:] if stderr else 'none'}"
        )

    text = _clean_output(stdout, prompt)

    if not text:
        raise LLMError(
            f"No generated text found.\n"
            f"STDOUT tail: {stdout[-400:]}"
        )

    return text


def _run_with_flag_fallback(
    base_cmd: List[str],
    timeout: int,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Try each non-conversation flag until one works.

    Returns (stdout, stderr). stdout is None if every attempt failed.
    """
    last_stderr: Optional[str] = None

    for flag in _NON_CONVERSATION_FLAGS:
        cmd = base_cmd + [flag]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise LLMError(f"Generation timed out after {timeout}s")
        except FileNotFoundError:
            raise LLMError(f"Binary not found: {config.LLAMA_CLI}")

        if result.returncode != 0 and "unknown" in result.stderr.lower():
            last_stderr = result.stderr
            continue

        if result.returncode != 0:
            raise LLMError(
                f"llama-cli exited with code {result.returncode}\n"
                f"STDERR: {result.stderr[-300:]}"
            )

        return result.stdout, result.stderr

    return None, last_stderr


def _clean_output(raw: str, prompt: str) -> str:
    """
    Extract generated text from llama-cli output.

    llama-cli may echo the prompt, print timing stats, and
    leave interactive-mode artifacts. We isolate the answer.
    """
    # Strip ANSI escape codes
    raw = re.sub(r"\x1b\[[0-9;]*m", "", raw)

    # Remove interactive prompt prefixes at line starts
    raw = re.sub(r"^> ", "", raw, flags=re.MULTILINE)

    # Find the LAST answer marker (model sometimes echoes prompt)
    tail = raw
    for marker in _ANSWER_MARKERS:
        idx = raw.rfind(marker)
        if idx != -1:
            tail = raw[idx + len(marker):]
            break

    # Cut at stats / exit / next prompt
    for stop in _STOP_MARKERS:
        idx = tail.find(stop)
        if idx != -1:
            tail = tail[:idx]

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