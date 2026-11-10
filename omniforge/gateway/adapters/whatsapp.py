"""Adapter WhatsApp (Cloud API resmi Meta).

parse: webhook entry.changes.value.messages -> Message (teks atau audio).
send: graph.facebook.com bila WHATSAPP_TOKEN dan WHATSAPP_PHONE_ID terisi.
"""

from __future__ import annotations

import json
import urllib.request

from ... import config
from ...messages import Message

OUTBOX: list[dict] = []


def parse(payload: dict) -> Message | None:
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        msg = value["messages"][0]
    except (KeyError, IndexError, TypeError):
        return None
    user_id = str(msg.get("from", ""))
    if msg.get("type") == "audio":
        return Message(platform="whatsapp", user_id=user_id, chat_id=user_id,
                       kind="voice", media_id=str(msg["audio"].get("id", "")), raw=payload)
    text = (msg.get("text") or {}).get("body", "")
    if not text:
        return None
    return Message(platform="whatsapp", user_id=user_id, chat_id=user_id,
                   text=text, raw=payload)


def send(chat_id: str, text: str) -> dict:
    token = config.get("WHATSAPP_TOKEN")
    phone_id = config.get("WHATSAPP_PHONE_ID")
    if config.is_live() and token and phone_id:
        body = json.dumps({"messaging_product": "whatsapp", "to": chat_id,
                           "type": "text", "text": {"body": text}}).encode()
        req = urllib.request.Request(
            f"https://graph.facebook.com/v21.0/{phone_id}/messages",
            data=body, headers={"Content-Type": "application/json",
                                "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"delivered": True, "status": resp.status}
    OUTBOX.append({"platform": "whatsapp", "chat_id": chat_id, "text": text})
    return {"delivered": False, "queued": True}
