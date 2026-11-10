"""Adapter Signal lewat jembatan signal-cli REST (standar komunitas).

parse membaca envelope hasil signal-cli: source/sourceNumber dan
dataMessage.message atau lampiran suara. send memakai endpoint
/v2/send pada SIGNAL_API_BASE bila mode live.
"""

from __future__ import annotations

import json
import urllib.request

from ... import config
from ...messages import Message

OUTBOX: list[dict] = []


def parse(payload: dict) -> Message | None:
    env = payload.get("envelope") or payload
    data = env.get("dataMessage") or {}
    user_id = str(env.get("sourceNumber") or env.get("source") or "")
    if not user_id:
        return None
    attachments = data.get("attachments") or []
    voice = next((a for a in attachments
                  if str(a.get("contentType", "")).startswith("audio")), None)
    if voice:
        return Message(platform="signal", user_id=user_id, chat_id=user_id,
                       kind="voice", media_id=str(voice.get("id", "")), raw=payload)
    text = data.get("message", "")
    if not text:
        return None
    return Message(platform="signal", user_id=user_id, chat_id=user_id,
                   text=text, raw=payload)


def send(chat_id: str, text: str) -> dict:
    base = config.get("SIGNAL_API_BASE")
    number = config.get("SIGNAL_NUMBER")
    if config.is_live() and base and number:
        body = json.dumps({"message": text, "number": number,
                           "recipients": [chat_id]}).encode()
        req = urllib.request.Request(base.rstrip("/") + "/v2/send", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"delivered": True, "status": resp.status}
    OUTBOX.append({"platform": "signal", "chat_id": chat_id, "text": text})
    return {"delivered": False, "queued": True}
