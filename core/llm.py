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


def generate(
    prompt: str,
    max_tokens: Optional[int] = None,
    timeout: int = 300,
) -> str:
    """Generate text via llama-cli, using file redirect to bypass tty issue."""
    if not prompt or not prompt.strip():
        raise ValueError("Cannot generate from empty prompt")

    n = max_tokens if max_tokens is not None else config.MAX_TOKENS

    base = Path(config.VECTOR_STORE_FILE).parent
    prompt_file = base / "_tmp_prompt.txt"
    output_file = base / "_tmp_output.txt"

    prompt_file.write_text(prompt, encoding="utf-8")

    cmd = (
        f'"{config.LLAMA_CLI}" -m "{config.SMOLLM_MODEL}" '
        f'-f "{prompt_file}" -n {n} -t {config.THREADS} '
        f'-c {config.CONTEXT_SIZE} < /dev/null '
        f'> "{output_file}" 2>&1'
    )

    try:
        subprocess.run(cmd, shell=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise LLMError(f"Generation timed out after {timeout}s")

    if not output_file.exists():
        raise LLMError("No output file created")

    raw = output_file.read_text(encoding="utf-8")

    prompt_file.unlink(missing_ok=True)
    output_file.unlink(missing_ok=True)

    text = _clean_output(raw, prompt)

    if not text:
        raise LLMError(f"No generated text. Raw tail: {raw[-400:]}")

    return text


def _clean_output(raw: str, prompt: str) -> str:
    """Extract text after last 'Jawapan:' marker."""
    raw = re.sub(r"\x1b\[[0-9;]*m", "", raw)

    idx = raw.rfind("Jawapan:")
    if idx == -1:
        return raw.strip()[:500]

    tail = raw[idx + len("Jawapan:"):]

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