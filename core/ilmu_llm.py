"""
core/ilmu_llm.py — ILMU API LLM adapter.

Interface sama dengan core/llm.py (local) dan EchoLLM:
    .generate(prompt, *, system="", timeout=None) -> str

Guna urllib (built-in) — zero deps, ARMv7-safe.
"""

import json
import os
import urllib.error
import urllib.request


class IlmuError(Exception):
    pass


class IlmuLLM:
    DEFAULT_URL = "https://api.ilmu.ai/v1"
    DEFAULT_MODEL = "ilmu-mini-v3.3"

    def __init__(self, model=None, api_key=None, base_url=None):
        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key or os.environ.get("ILMU_API_KEY")
        if not self.api_key:
            raise IlmuError("ILMU_API_KEY tak set. Set dalam .env atau env var.")
        self.base_url = (base_url or self.DEFAULT_URL).rstrip("/")
        self.last_usage = {}

    def generate(self, prompt, *, system="", timeout=None, max_tokens=400, temperature=0.3):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout or 60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_err = e.read().decode("utf-8", errors="replace")[:300]
            raise IlmuError(f"HTTP {e.code}: {body_err}") from e
        except urllib.error.URLError as e:
            raise IlmuError(f"Connection failed: {e}") from e

        self.last_usage = data.get("usage", {})
        choices = data.get("choices", [])
        if not choices:
            raise IlmuError(f"No choices in response: {data}")
        return choices[0]["message"]["content"]

    def cost_estimate(self):
        """Return (input_rm, output_rm) for last call."""
        u = self.last_usage
        p = u.get("prompt_tokens", 0) * 0.20 / 1_000_000
        c = u.get("completion_tokens", 0) * 1.20 / 1_000_000
        return p, c