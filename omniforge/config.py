"""Konfigurasi OmniForge dari environment dan file .env sederhana."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def mode() -> str:
    return get("OMNIFORGE_MODE", "demo").lower()


def is_live() -> bool:
    return mode() == "live"


def data_dir() -> Path:
    """Direktori data runtime (memori, skills, allowlist). Dibuat bila belum ada."""
    d = ROOT / "data" / "live"
    (d / "memory").mkdir(parents=True, exist_ok=True)
    (d / "skills").mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return ROOT / "db" / "omniforge.db"


def port() -> int:
    try:
        return int(get("OMNIFORGE_PORT", "8787"))
    except ValueError:
        return 8787
