"""Sistem skills: folder berisi SKILL.md (front-matter nama/deskripsi + isi).

Kompatibel secara bentuk dengan standar skills terbuka: satu folder per
skill, dipindai dari data/live/skills, termasuk hasil impor agent lain.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import config


@dataclass
class Skill:
    name: str
    description: str
    body: str
    folder: Path


def _parse(text: str, folder: Path) -> Skill:
    name = folder.name
    description = ""
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            header = text[3:end]
            body = text[end + 4:].strip()
            for line in header.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    if key.strip() == "name":
                        name = value.strip()
                    elif key.strip() == "description":
                        description = value.strip()
    return Skill(name=name, description=description, body=body, folder=folder)


class SkillRegistry:
    def __init__(self, base=None):
        self.base = base or (config.data_dir() / "skills")
        self.base.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[Skill]:
        # Rekursif: skills hasil impor berada di subfolder <sumber>-imports/.
        skills = []
        for file in sorted(self.base.rglob("SKILL.md")):
            skills.append(_parse(file.read_text(encoding="utf-8"), file.parent))
        return skills

    def match(self, text: str) -> Skill | None:
        low = text.lower()
        for skill in self.list():
            words = [w for w in skill.name.lower().replace("-", " ").split() if len(w) > 2]
            if any(w in low for w in words):
                return skill
        return None

    def create(self, slug: str, name: str, description: str, body: str) -> Path:
        folder = self.base / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n",
            encoding="utf-8",
        )
        return folder
