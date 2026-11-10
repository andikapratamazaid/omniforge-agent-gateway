"""Daftar izin perintah: gerbang keamanan sebelum eksekusi di backend mana pun.

Pola disimpan di data/live/allowlist.json sebagai daftar awalan perintah
yang diizinkan, misalnya ["echo", "date", "ls", "whoami"]. Perintah di luar
daftar ditolak dan dicatat. Daftar ini juga diisi oleh importer dari agent
lain (command allowlist OpenClaw dan sejenisnya).
"""

from __future__ import annotations

import json
import shlex

from . import config

DEFAULT_PATTERNS = ["echo", "date", "whoami", "ls", "pwd", "uname"]


def load_patterns() -> list[str]:
    path = config.data_dir() / "allowlist.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [str(p) for p in data]
        except json.JSONDecodeError:
            pass
    return list(DEFAULT_PATTERNS)


def save_patterns(patterns: list[str]) -> None:
    path = config.data_dir() / "allowlist.json"
    path.write_text(json.dumps(patterns, indent=2), encoding="utf-8")


def merge_patterns(new: list[str]) -> list[str]:
    patterns = load_patterns()
    for p in new:
        p = p.strip()
        if p and p not in patterns:
            patterns.append(p)
    save_patterns(patterns)
    return patterns


def check(command: str) -> tuple[bool, str]:
    """Kembalikan (diizinkan, alasan). Pencocokan berbasis token pertama
    dan awalan pola, cukup ketat untuk demo yang aman."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False, "perintah tidak dapat diuraikan"
    if not tokens:
        return False, "perintah kosong"
    for pattern in load_patterns():
        ptoks = shlex.split(pattern)
        if ptoks and tokens[: len(ptoks)] == ptoks:
            return True, f"sesuai pola izin '{pattern}'"
    return False, "tidak ada pola izin yang cocok"
