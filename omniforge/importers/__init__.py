"""Importer agent lain: OpenClaw, Claude Code, Codex CLI, Cursor, n8n.

Semua importer bekerja dalam dua tahap: plan() menyusun rencana
(kind, source, dest, action) tanpa menulis apa pun, apply() mengeksekusi
rencana ke data/live. Berkas persona dan memori (SOUL.md, MEMORY.md,
USER.md, AGENTS.md) masuk ke data/live/memory, skills masuk ke
data/live/skills/<sumber>-imports, daftar izin perintah digabung ke
allowlist, dan workflow n8n diubah menjadi skill penjelasan + kandidat
jadwal cron. Mode --dry-run berhenti di plan().
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .. import allowlist, config

MEMORY_FILES = ("SOUL.md", "MEMORY.md", "USER.md", "AGENTS.md")


class BaseImporter:
    name = "base"
    default_home = ""

    def __init__(self, path: str | None = None):
        self.home = Path(path).expanduser() if path else Path(self.default_home).expanduser()

    def _memory_items(self) -> list[dict]:
        items = []
        for name in MEMORY_FILES:
            src = self.home / name
            items.append({
                "kind": "memori", "source": str(src),
                "dest": str(config.data_dir() / "memory" / name),
                "action": "copy" if src.exists() else "missing",
                "_src": src, "_dest": config.data_dir() / "memory" / name,
            })
        return items

    def _skill_items(self, skills_dir: Path) -> list[dict]:
        items = []
        if skills_dir.exists():
            for folder in sorted(skills_dir.iterdir()):
                file = folder / "SKILL.md"
                if folder.is_dir() and file.exists():
                    dest = config.data_dir() / "skills" / f"{self.name}-imports" / folder.name
                    items.append({
                        "kind": "skill", "source": str(folder),
                        "dest": str(dest), "action": "copy",
                        "_src": folder, "_dest": dest,
                    })
        return items

    def _allowlist_item(self, candidates: list[Path]) -> list[dict]:
        for cand in candidates:
            if cand.exists():
                patterns = [ln.strip() for ln in cand.read_text(encoding="utf-8").splitlines()
                            if ln.strip() and not ln.startswith("#")]
                return [{
                    "kind": "allowlist", "source": str(cand),
                    "dest": str(config.data_dir() / "allowlist.json"),
                    "action": "merge", "_patterns": patterns,
                }]
        return []

    def plan(self) -> list[dict]:
        return self._memory_items()

    def apply(self, plan: list[dict]) -> list[str]:
        report = []
        for item in plan:
            if item["action"] == "copy":
                dest = Path(item["_dest"])
                if item["kind"] == "skill":
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item["_src"], dest)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(item["_src"], dest)
                report.append(f"disalin: {item['source']} -> {item['dest']}")
            elif item["action"] == "merge":
                merged = allowlist.merge_patterns(item.get("_patterns", []))
                report.append(f"allowlist digabung dari {item['source']}: kini {len(merged)} pola")
            elif item["action"] == "generate":
                dest = Path(item["_dest"])
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(item["_content"], encoding="utf-8")
                report.append(f"dibuat: {item['dest']} ({item['kind']})")
            else:
                report.append(f"dilewati ({item['action']}): {item['source']}")
        return report


class OpenClawImporter(BaseImporter):
    name = "openclaw"
    default_home = "~/.openclaw"

    def plan(self) -> list[dict]:
        items = self._memory_items()
        items += self._skill_items(self.home / "skills")
        items += self._allowlist_item([self.home / "allowlist.txt",
                                       self.home / "command-allowlist.txt"])
        return items


class ClaudeCodeImporter(BaseImporter):
    name = "claude-code"
    default_home = "~/.claude"

    def plan(self) -> list[dict]:
        items = self._memory_items()
        claude_md = self.home / "CLAUDE.md"
        if claude_md.exists():
            items.append({
                "kind": "memori", "source": str(claude_md),
                "dest": str(config.data_dir() / "memory" / "AGENTS.md"),
                "action": "copy", "_src": claude_md,
                "_dest": config.data_dir() / "memory" / "AGENTS.md",
            })
        items += self._skill_items(self.home / "skills")
        return items


class CodexImporter(BaseImporter):
    name = "codex"
    default_home = "~/.codex"

    def plan(self) -> list[dict]:
        items = self._memory_items()
        items += self._skill_items(self.home / "skills")
        return items


class CursorImporter(BaseImporter):
    name = "cursor"
    default_home = "~/.cursor"

    def plan(self) -> list[dict]:
        items = self._memory_items()
        items += self._skill_items(self.home / "skills")
        rules = self.home / "rules"
        if rules.exists():
            for file in sorted(rules.glob("*.md")):
                items.append({
                    "kind": "memori", "source": str(file),
                    "dest": str(config.data_dir() / "memory" / file.name),
                    "action": "copy", "_src": file,
                    "_dest": config.data_dir() / "memory" / file.name,
                })
        return items


class N8nImporter(BaseImporter):
    """Mengimpor ekspor workflow n8n (satu file JSON atau folder berisi JSON).

    Tiap workflow menjadi skill penjelasan (langkah, node, koneksi) di
    data/live/skills/n8n-imports, dan node pemicu jadwal dicatat sebagai
    kandidat cron di laporan.
    """
    name = "n8n"
    default_home = "~/n8n-exports"

    def _workflow_files(self) -> list[Path]:
        if self.home.is_file():
            return [self.home]
        if self.home.exists():
            return sorted(self.home.glob("*.json"))
        return []

    def plan(self) -> list[dict]:
        items = []
        for file in self._workflow_files():
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                items.append({"kind": "workflow", "source": str(file),
                              "dest": "", "action": "missing"})
                continue
            workflows = data if isinstance(data, list) else [data]
            for wf in workflows:
                name = wf.get("name", file.stem)
                slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
                nodes = wf.get("nodes", [])
                triggers = [n.get("type", "") for n in nodes
                            if "trigger" in str(n.get("type", "")).lower()
                            or "cron" in str(n.get("type", "")).lower()]
                lines = [f"# Workflow n8n: {name}", "",
                         f"Diimpor dari {file.name}. Berisi {len(nodes)} node:"]
                for n in nodes:
                    lines.append(f"- {n.get('name', '?')} ({n.get('type', '?')})")
                if triggers:
                    lines.append("")
                    lines.append(f"Pemicu jadwal terdeteksi: {', '.join(triggers)}. "
                                 "Jadikan tugas cron OmniForge dengan /cron tambah bila diinginkan.")
                dest = (config.data_dir() / "skills" / "n8n-imports" / slug / "SKILL.md")
                items.append({
                    "kind": "workflow", "source": str(file),
                    "dest": str(dest), "action": "generate",
                    "_dest": dest,
                    "_content": (f"---\nname: Workflow {name}\n"
                                 f"description: workflow n8n hasil impor, {len(nodes)} node\n---\n\n"
                                 + "\n".join(lines) + "\n"),
                })
        return items


IMPORTERS = {
    "openclaw": OpenClawImporter,
    "claude-code": ClaudeCodeImporter,
    "codex": CodexImporter,
    "cursor": CursorImporter,
    "n8n": N8nImporter,
}
