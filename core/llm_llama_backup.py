"""
core/llm.py - LLM wrapper using llama-cli with PTY capture.

llama.cpp writes to /dev/tty directly. To capture output, we run it
inside a pseudo-terminal (PTY) that we control from Python.
"""

import os
import pty
import re
import select
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class LLMError(Exception):
    """Raised when LLM generation fails."""
    pass


_IM_END = "<|im_end|>"


def generate(
    prompt: str,
    max_tokens: Optional[int] = None,
    timeout: int = 300,
) -> str:
    """
    Generate text via llama-cli, capturing PTY output.

    Args:
        prompt: Input prompt (chat template format recommended).
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

    master_fd, slave_fd = pty.openpty()
    proc = None

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
        )
        os.close(slave_fd)
        slave_fd = -1

        chunks = []
        deadline = time.time() + timeout
        last_output = time.time()
        exit_sent = False

        while True:
            if time.time() > deadline:
                proc.kill()
                break

            try:
                r, _, _ = select.select([master_fd], [], [], 1.0)
            except (OSError, ValueError):
                break

            if r:
                try:
                    data = os.read(master_fd, 8192)
                    if data:
                        chunks.append(data)
                        last_output = time.time()
                except OSError:
                    break

            if proc.poll() is not None:
                break

            # After 4s idle, assume generation done, send /exit
            if not exit_sent and (time.time() - last_output) > 4:
                try:
                    os.write(master_fd, b"/exit\n")
                    exit_sent = True
                except OSError:
                    break

        # Drain remaining PTY data after process exit
        time.sleep(0.5)
        while True:
            try:
                r, _, _ = select.select([master_fd], [], [], 0.3)
                if not r:
                    break
                data = os.read(master_fd, 8192)
                if not data:
                    break
                chunks.append(data)
            except OSError:
                break

    finally:
        if slave_fd != -1:
            try:
                os.close(slave_fd)
            except OSError:
                pass
        try:
            os.close(master_fd)
        except OSError:
            pass

    if proc is not None:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    raw = b"".join(chunks).decode("utf-8", errors="replace")

    if not raw.strip():
        raise LLMError("llama-cli produced no output")

    text = _clean_output(raw, prompt)

    if not text:
        raise LLMError(f"No text extracted. Raw tail: {raw[-400:]}")

    return text


def _clean_output(raw: str, prompt: str) -> str:
    """Extract assistant response from captured PTY output."""
    # Strip ANSI colors
    raw = re.sub(r"\x1b\[[0-9;]*m", "", raw)

    # Strip interactive prompt prefix at line starts
    raw = re.sub(r"^> ", "", raw, flags=re.MULTILINE)

    # Prefer chat template marker
    marker = "<|im_start|>assistant"
    idx = raw.rfind(marker)

    if idx != -1:
        tail = raw[idx + len(marker):]
    else:
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
        "\n> /exit",
        "\n\n> ",
    ):
        stop_idx = tail.find(stop)
        if stop_idx != -1:
            tail = tail[:stop_idx]

    return tail.strip()


if __name__ == "__main__":
    test_prompt = (
        "<|im_start|>user\n"
        "Apa itu Gen Z?\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    out = generate(test_prompt, max_tokens=40)
    print("--- Generated ---")
    print(out)