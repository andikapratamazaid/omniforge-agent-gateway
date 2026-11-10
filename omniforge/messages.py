"""Model pesan terpadu: semua platform diterjemahkan ke format ini."""

from __future__ import annotations

from dataclasses import dataclass, field

PLATFORMS = ("telegram", "discord", "slack", "whatsapp", "signal", "cli")


@dataclass
class Message:
    platform: str
    user_id: str
    chat_id: str
    kind: str = "text"          # "text" atau "voice"
    text: str = ""
    media_id: str = ""          # id berkas suara di platform asal
    display_name: str = ""
    raw: dict = field(default_factory=dict)

    def label(self) -> str:
        return f"{self.platform}:{self.user_id}"


@dataclass
class Reply:
    text: str
    platform: str = ""
    chat_id: str = ""

    def as_dict(self) -> dict:
        return {"platform": self.platform, "chat_id": self.chat_id, "text": self.text}
