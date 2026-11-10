"""Adapter CLI: platform keenam, berjalan di terminal lokal."""

from __future__ import annotations

from ...messages import Message

OUTBOX: list[dict] = []


def parse(payload: dict) -> Message | None:
    text = (payload.get("text") or "").strip()
    if not text:
        return None
    return Message(platform="cli", user_id=str(payload.get("user_id", "local")),
                   chat_id="terminal", text=text, raw=payload)


def send(chat_id: str, text: str) -> dict:
    OUTBOX.append({"platform": "cli", "chat_id": chat_id, "text": text})
    return {"delivered": True, "channel": "stdout"}
