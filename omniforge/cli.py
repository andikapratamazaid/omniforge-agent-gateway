"""CLI OmniForge.

Perintah:
  omniforge chat                 bicara lewat platform CLI
  omniforge gateway [--port N]   jalankan satu proses gateway semua platform
  omniforge import-agent <sumber> [--path DIR] [--dry-run]
                                 sumber: openclaw, claude-code, codex, cursor, n8n
  omniforge backends             daftar backend eksekusi dan statusnya
  omniforge doctor               ringkasan konfigurasi dan statistik
"""

from __future__ import annotations

import sys

from . import backends, config
from .agent_core import AgentCore
from .messages import Message


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(__doc__)
        return 0
    cmd, rest = args[0], args[1:]
    try:
        if cmd == "chat":
            return _chat()
        if cmd == "gateway":
            from .gateway.server import serve
            port = None
            if "--port" in rest:
                port = int(rest[rest.index("--port") + 1])
            serve(port)
            return 0
        if cmd == "import-agent":
            return _import(rest)
        if cmd == "backends":
            for b in backends.describe():
                print(f"- {b['name']}: {b['status']} ({b['note']})")
            return 0
        if cmd == "doctor":
            core = AgentCore()
            print(f"Mode: {config.mode()} | Backend: {core.backend}")
            print("Statistik:", core.store.stats())
            print("Memori:", "ada" if core.memory.context() else "kosong")
            print("Skills:", len(core.skills.list()))
            return 0
        print(f"Perintah tidak dikenal: {cmd}")
        print(__doc__)
        return 2
    except Exception as exc:
        print(f"Terjadi kesalahan: {exc}")
        return 2


def _chat() -> int:
    core = AgentCore()
    print("OmniForge CLI. Ketik /help untuk perintah, 'keluar' untuk selesai.")
    while True:
        try:
            text = input("kamu> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if text.lower() in ("keluar", "exit", "quit"):
            return 0
        if not text:
            continue
        reply = core.handle(Message(platform="cli", user_id="local",
                                    chat_id="terminal", text=text))
        print("omniforge>", reply.text)


def _import(rest: list[str]) -> int:
    from .importers import IMPORTERS
    if not rest or rest[0] not in IMPORTERS:
        print("Sumber yang didukung:", ", ".join(IMPORTERS))
        return 2
    source = rest[0]
    dry = "--dry-run" in rest
    path = None
    if "--path" in rest:
        path = rest[rest.index("--path") + 1]
    importer = IMPORTERS[source](path)
    plan = importer.plan()
    print(f"Rencana impor dari {source} ({len(plan)} item)"
          + (" [DRY RUN]" if dry else "") + ":")
    for item in plan:
        print(f"- [{item['action']}] {item['kind']}: {item['source']} -> {item['dest']}")
    if dry:
        print("Dry run selesai. Tidak ada berkas yang ditulis.")
        return 0
    report = importer.apply(plan)
    for line in report:
        print(line)
    return 0
