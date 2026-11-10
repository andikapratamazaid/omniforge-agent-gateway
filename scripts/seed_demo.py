"""Isi database contoh: satu identitas tertaut di 3 platform, riwayat
lintas platform, satu tugas cron, dan log eksekusi. Memaksa alur demo
deterministik, tidak memanggil API apa pun.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from omniforge import backends
from omniforge.agent_core import SESSION_KEY
from omniforge.messages import Message
from omniforge.agent_core import AgentCore


def main() -> int:
    core = AgentCore()
    core.handle(Message("telegram", "111", "555", text="halo, mulai sesi laporan minggu ini"))
    link = core.handle(Message("telegram", "111", "555", text="/link"))
    code = link.text.split("Kode tautanmu: ")[1].split()[0]
    core.handle(Message("whatsapp", "6285714447951", "6285714447951", text=f"/link {code}"))
    core.handle(Message("whatsapp", "6285714447951", "6285714447951",
                        text="penjualan minggu ini naik, tolong siapkan ringkasannya"))
    core.handle(Message("cli", "local", "terminal", text="/jalan echo ringkasan disiapkan"))
    identity = core.store.resolve_identity("telegram", "111")
    core.store.add_cron(identity, "whatsapp", "6285714447951",
                        "daily:00:00", "susun laporan harian dan kirim ringkasannya")
    backends.run("local", "echo seed selesai", store=core.store)
    print("Seed selesai:", core.store.stats())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
