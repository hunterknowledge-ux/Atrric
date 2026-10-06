"""
core/llm.py - LLM wrapper using llama-cli.

Runs llama-cli via `script` (pseudo-terminal) to capture output,
then extracts the generated answer from SmolLM2 chat template.
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


# SmolLM2 chat template markers
_IM_START = "<|im_start|>"
_IM_END = "<|im_end|>"


def generate(
    prompt: str,
    max_tokens: Optional[int] = None,
    timeout: int = 300,
) -> str:
    """
    Generate text via llama-cli using pseudo-terminal capture.

    Args:
        prompt: The input prompt (should already use chat template).
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

    base = Path(config.VECTOR_STORE_FILE).parent
    prompt_file = base / "_tmp_prompt.txt"
    output_file = base / "_tmp_output.txt"

    prompt_file.write_text(prompt, encoding="utf-8")

    inner_cmd = (
        f'"{config.LLAMA_CLI}" '
        f'-m "{config.SMOLLM_MODEL}" '
        f'-f "{prompt_file}" '
        f'-n {n} '
        f'-t {config.THREADS} '
        f'-c {config.CONTEXT_SIZE} '
        f'-r "{_IM_END}" '
        f'< /dev/null'
    )

    cmd = f'script -q -c \'{inner_cmd}\' "{output_file}"'

    try:
        subprocess.run(cmd, shell=True, timeout=timeout, capture_output=True)
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
    """
    Extract assistant response from chat template output.

    Looks for the last '<|im_start|>assistant' marker and takes
    everything up to the next '<|im_end|>' or stats line.
    """
    raw = re.sub(r"\x1b\[[0-9;]*m", "", raw)

    marker = f"{_IM_START}assistant"
    idx = raw.rfind(marker)

    if idx != -1:
        tail = raw[idx + len(marker):]
    else:
        # Fallback: try "Jawapan:"
        idx = raw.rfind("Jawapan:")
        if idx != -1:
            tail = raw[idx + len("Jawapan:"):]
        else:
            tail = raw

    # Cut at stop markers
    for stop in (
        _IM_END,
        "\n[ Prompt:",
        "\n[ Generation:",
        "\nExiting",
        "\n\n> ",
    ):
        stop_idx = tail.find(stop)
        if stop_idx != -1:
            tail = tail[:stop_idx]

    return tail.strip()


if __name__ == "__main__":
    test_prompt = (
        f"{_IM_START}user\n"
        f"Apa itu Gen Z?\n"
        f"{_IM_END}\n"
        f"{_IM_START}assistant\n"
    )
    out = generate(test_prompt, max_tokens=40)
    print("--- Generated ---")
    print(out)