"""Router model: satu pintu ke banyak provider, tanpa lock-in.

Mode demo: backend deterministik yang menjawab dari konteks nyata
(memori file, skills, dan riwayat sesi lintas platform) tanpa token.
Mode live: memanggil endpoint chat-completions kompatibel OpenAI
(OpenRouter secara default) memakai model per peran dari
config/models.json, dengan fallback berurutan.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from . import config

MODELS_FILE = Path(__file__).resolve().parent.parent / "config" / "models.json"


def load_models() -> dict:
    return json.loads(MODELS_FILE.read_text(encoding="utf-8"))


class Router:
    def __init__(self):
        self.cfg = load_models()

    def model_for(self, role: str) -> str:
        return self.cfg.get("roles", {}).get(role, {}).get("model", "")

    def complete(self, role: str, system: str, messages: list[dict]) -> dict:
        if config.is_live() and config.get("OPENROUTER_API_KEY"):
            return self._live(role, system, messages)
        return {"text": "", "model": "demo", "live": False}

    def _live(self, role: str, system: str, messages: list[dict]) -> dict:
        role_cfg = self.cfg.get("roles", {}).get(role, {})
        candidates = [role_cfg.get("model", "")] + role_cfg.get("fallback", [])
        base = config.get("OMNIFORGE_API_BASE", "https://openrouter.ai/api/v1")
        payload_msgs = [{"role": "system", "content": system}] + messages
        last_error = ""
        for model in [m for m in candidates if m]:
            body = json.dumps({"model": model, "messages": payload_msgs}).encode()
            req = urllib.request.Request(
                base.rstrip("/") + "/chat/completions",
                data=body,
                headers={
                    "Authorization": f"Bearer {config.get('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                return {"text": text, "model": model, "live": True}
            except Exception as exc:  # lanjut ke fallback
                last_error = str(exc)
        return {"text": f"(model live tidak terjangkau: {last_error})", "model": "", "live": True}
