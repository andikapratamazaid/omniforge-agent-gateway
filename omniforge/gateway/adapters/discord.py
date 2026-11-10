"""Adapter Discord (pesan channel lewat webhook/gateway payload).

parse menerima payload pesan standar Discord: author.id, channel_id,
content. send memakai DISCORD_WEBHOOK_URL bila terisi (mode live).
"""

from __future__ import annotations

import json
import urllib.request

from ... import config
from ...messages import Message

OUTBOX: list[dict] = []


def parse(payload: dict) -> Message | None:
    author = payload.get("author") or {}
    if author.get("bot"):
        return None
    text = payload.get("content", "")
    if not text:
        return None
    return Message(platform="discord", user_id=str(author.get("id", "")),
                   chat_id=str(payload.get("channel_id", "")), text=text,
                   display_name=author.get("username", ""), raw=payload)


def send(chat_id: str, text: str) -> dict:
    url = config.get("DISCORD_WEBHOOK_URL")
    if config.is_live() and url:
        body = json.dumps({"content": text}).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"delivered": True, "status": resp.status}
    OUTBOX.append({"platform": "discord", "chat_id": chat_id, "text": text})
    return {"delivered": False, "queued": True}
