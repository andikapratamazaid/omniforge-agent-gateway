"""Adapter Telegram (Bot API).

parse: update webhook -> Message. send: api.telegram.org bila token
terisi (mode live); selain itu balasan dicatat ke outbox (mode demo).
"""

from __future__ import annotations

import json
import urllib.request

from ... import config
from ...messages import Message

OUTBOX: list[dict] = []


def parse(payload: dict) -> Message | None:
    msg = payload.get("message") or payload.get("edited_message") or {}
    if not msg:
        return None
    chat = msg.get("chat", {})
    user = msg.get("from", {})
    if "voice" in msg:
        return Message(platform="telegram", user_id=str(user.get("id", "")),
                       chat_id=str(chat.get("id", "")), kind="voice",
                       media_id=str(msg["voice"].get("file_id", "")),
                       display_name=user.get("first_name", ""), raw=payload)
    text = msg.get("text", "")
    if not text:
        return None
    return Message(platform="telegram", user_id=str(user.get("id", "")),
                   chat_id=str(chat.get("id", "")), text=text,
                   display_name=user.get("first_name", ""), raw=payload)


def send(chat_id: str, text: str) -> dict:
    token = config.get("TELEGRAM_BOT_TOKEN")
    if config.is_live() and token:
        body = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"delivered": True, "status": resp.status}
    OUTBOX.append({"platform": "telegram", "chat_id": chat_id, "text": text})
    return {"delivered": False, "queued": True}
