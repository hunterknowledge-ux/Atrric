import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ilmu_llm import IlmuLLM, IlmuError
from core.router import get_model

LLMError = IlmuError

_instances = {}

def _get_llm(model_name: str) -> IlmuLLM:
    global _instances
    if model_name not in _instances:
        _instances[model_name] = IlmuLLM(model=model_name)
    return _instances[model_name]

def generate(prompt, max_tokens=None, timeout=None, system="", prefills="", task="default", model=None, **kwargs):
    target_model = model or get_model(task)
    
    kw = {}
    if max_tokens is not None: kw["max_tokens"] = max_tokens
    if timeout is not None: kw["timeout"] = timeout
    if system: kw["system"] = system
    if prefills: kw["prefill"] = prefills
    kw.update(kwargs)

    return _get_llm(target_model).generate(prompt, **kw)

def _extract_json(text):
    """Cari JSON block pertama dalam teks, walaupun LLM tambah ayat lain."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
    return None

def generate_json(prompt, system="", max_tokens=None, task="default", model=None, **kw):
    try:
        raw = generate(prompt, system=system, max_tokens=max_tokens, task=task, model=model, **kw)
    except Exception as e:
        print(f"[llm] API ERROR: {type(e).__name__} - {e}")
        return None
        
    if not raw:
        print("[llm] EMPTY RESPONSE dari API")
        return None
        
    # Cari JSON block
    s = _extract_json(raw)
    if not s:
        print(f"[llm] NO JSON FOUND. Raw: {raw[:100]}...")
        return None
        
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        print(f"[llm] JSON PARSE FAIL: {e}. Raw block: {s[:100]}...")
        return None