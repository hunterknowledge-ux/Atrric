"""
core/llm.py — Back-compat shim for LLM calls.

Redirects to ILMU API. Supports system prompt + prefill.

Old llama-cli implementation: core/llm_llama_backup.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ilmu_llm import IlmuLLM, IlmuError

LLMError = IlmuError

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = IlmuLLM()
    return _llm


def generate(prompt, max_tokens=None, timeout=None, system="", prefill="", **kwargs):
    """
    Back-compat wrapper. Supports system + prefill.

    Args:
        prompt: user prompt
        max_tokens: max output tokens
        timeout: timeout seconds
        system: system prompt
        prefill: partial assistant message to force start
        **kwargs: passthrough (temperature, etc.)

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
    if prefill:
        kw["prefill"] = prefill
    kw.update(kwargs)

    return _get_llm().generate(prompt, **kw)

import json as _json
import re as _re

_FENCE = _re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", _re.M)

def generate_json(prompt, system="", max_tokens=None, **kw):
    """generate() + strip markdown fence + parse JSON.
    Return dict, atau None kalau parse fail."""
    raw = generate(prompt, system=system, max_tokens=max_tokens, **kw)
    if not raw:
        return None
    s = _FENCE.sub("", raw).strip()
    if not s.startswith("{"):
        i, j = s.find("{"), s.rfind("}")
        if i >= 0 and j > i:
            s = s[i:j+1]
    try:
        return _json.loads(s)
    except _json.JSONDecodeError:
        return None