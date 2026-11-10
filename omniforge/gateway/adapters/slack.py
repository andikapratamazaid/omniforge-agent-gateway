"""Adapter Slack (Events API). Pesan bot sendiri diabaikan."""

from __future__ import annotations

import json
import urllib.request

from ... import config
from ...messages import Message

OUTBOX: list[dict] = []


def parse(payload: dict) -> Message | None:
    event = payload.get("event") or {}
    if event.get("type") != "message" or event.get("bot_id"):
        return None
    text = event.get("text", "")
    if not text:
        return None
    return Message(platform="slack", user_id=str(event.get("user", "")),
                   chat_id=str(event.get("channel", "")), text=text, raw=payload)


def send(chat_id: str, text: str) -> dict:
    token = config.get("SLACK_BOT_TOKEN")
    if config.is_live() and token:
        body = json.dumps({"channel": chat_id, "text": text}).encode()
        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=body, headers={"Content-Type": "application/json",
                                "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"delivered": True, "status": resp.status}
    OUTBOX.append({"platform": "slack", "chat_id": chat_id, "text": text})
    return {"delivered": False, "queued": True}
