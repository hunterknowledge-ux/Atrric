"""
core/llm.py - Back-compat shim.

Redirects LLM calls to ILMU API (cloud, fast).
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
    global _llm
    if _llm is None:
        _llm = IlmuLLM()
    return _llm


def generate(prompt, max_tokens=None, timeout=None, **kwargs):
    """Back-compat wrapper. Matches old llm.generate() signature."""
    kw = {}
    if max_tokens is not None:
        kw["max_tokens"] = max_tokens
    if timeout is not None:
        kw["timeout"] = timeout
    kw.update(kwargs)
    return _get_llm().generate(prompt, **kw)
