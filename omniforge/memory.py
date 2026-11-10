"""Memori persisten berbasis file: SOUL.md, MEMORY.md, USER.md di data/live/memory."""

from __future__ import annotations

from . import config

FILES = ("SOUL.md", "MEMORY.md", "USER.md")
DEFAULTS = {
    "SOUL.md": "# SOUL\n\nOmniForge adalah agent pribadi yang membantu lewat banyak platform sekaligus.\n",
    "MEMORY.md": "# MEMORY\n\n(Belum ada catatan. Memori bertambah lewat perintah /ingat dan hasil impor.)\n",
    "USER.md": "# USER\n\nNama: (belum diisi)\n",
}


class Memory:
    def __init__(self, base=None):
        self.base = base or (config.data_dir() / "memory")
        self.base.mkdir(parents=True, exist_ok=True)
        for name, content in DEFAULTS.items():
            path = self.base / name
            if not path.exists():
                path.write_text(content, encoding="utf-8")

    def read(self, name: str) -> str:
        path = self.base / name
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def context(self) -> str:
        parts = []
        for name in FILES:
            text = self.read(name).strip()
            if text:
                parts.append(f"--- {name} ---\n{text}")
        return "\n\n".join(parts)

    def user_name(self) -> str:
        for line in self.read("USER.md").splitlines():
            if line.lower().startswith("nama:"):
                return line.split(":", 1)[1].strip()
        return ""

    def remember(self, note: str) -> None:
        path = self.base / "MEMORY.md"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"- {note}\n")
