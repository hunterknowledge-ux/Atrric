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

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.M)

def generate_json(prompt, system="", max_tokens=None, task="default", model=None, **kw):
    try:
        raw = generate(prompt, system=system, max_tokens=max_tokens, task=task, model=model, **kw)
    except Exception as e:
        print(f"[llm] API ERROR: {type(e).__name__} - {e}")
        return None
        
    if not raw:
        print("[llm] EMPTY RESPONSE dari API")
        return None
        
    s = _FENCE.sub("", raw).strip()
    if not s.startswith("{"):
        i, j = s.find("{"), s.rfind("}")
        if i >= 0 and j > i:
            s = s[i:j+1]
            
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        print(f"[llm] JSON PARSE FAIL. Raw: {s[:100]}...")
        return None