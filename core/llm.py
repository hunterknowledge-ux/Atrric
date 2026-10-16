"""
core/llm.py — Back-compat shim for LLM calls.

Redirects to ILMU API (cloud). Supports system prompt.

Old llama-cli implementation: core/llm_llama_backup.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ilmu_llm import IlmuLLM, IlmuError

# Back-compat: old code that catches LLMError still works
LLMError = IlmuError

_llm = None


def _get_llm():
    """Lazy singleton for IlmuLLM."""
    global _llm
    if _llm is None:
        _llm = IlmuLLM()
    return _llm


def generate(prompt, max_tokens=None, timeout=None, system="", **kwargs):
    """
    Back-compat wrapper. Matches old llm.generate() signature.

    Args:
        prompt: user prompt
        max_tokens: max output tokens
        timeout: request timeout seconds
        system: optional system prompt
        **kwargs: passthrough

    Returns:
        Generated text string.
    """
    kw = {}
    if max_tokens is not None:
        kw["max_tokens"] = max_tokens
    if timeout is not None:
        kw["timeout"] = timeout
    if system:
        kw["system"] = system
    kw.update(kwargs)

    return _get_llm().generate(prompt, **kw)