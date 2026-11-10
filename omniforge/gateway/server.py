"""Server gateway: SATU proses melayani semua platform sekaligus.

Rute:
- POST /webhook/telegram | /webhook/discord | /webhook/slack |
       /webhook/whatsapp | /webhook/signal | /webhook/cli
- GET  /health          status proses dan statistik
- GET  /                dashboard statis
- GET  /api/status      JSON statistik untuk dashboard
Cron diperiksa berkala di thread yang sama.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .. import config, cron as cron_mod
from ..agent_core import AgentCore
from .adapters import cli_adapter, discord, signal, slack, telegram, whatsapp

ADAPTERS = {
    "telegram": telegram,
    "discord": discord,
    "slack": slack,
    "whatsapp": whatsapp,
    "signal": signal,
    "cli": cli_adapter,
}
DASHBOARD = Path(__file__).resolve().parent.parent.parent / "dashboard"


def dispatch(core: AgentCore, platform: str, payload: dict) -> dict:
    adapter = ADAPTERS[platform]
    msg = adapter.parse(payload)
    if msg is None:
        return {"ok": True, "ignored": True}
    reply = core.handle(msg)
    sent = adapter.send(reply.chat_id, reply.text)
    return {"ok": True, "reply": reply.text, "delivery": sent}


def cron_loop(core: AgentCore, stop: threading.Event) -> None:
    while not stop.wait(5):
        for job in core.store.list_cron():
            if cron_mod.is_due(job):
                reply = core.run_cron_job(job)
                ADAPTERS[job["platform"]].send(reply.chat_id, reply.text)


def make_handler(core: AgentCore):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # senyapkan log bawaan
            pass

        def _json(self, code: int, data: dict) -> None:
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._json(200, {"status": "ok", "mode": config.mode(),
                                 "stats": core.store.stats()})
            elif self.path == "/api/status":
                self._json(200, {"mode": config.mode(), "stats": core.store.stats(),
                                 "backends": __import__("omniforge.backends", fromlist=["describe"]).describe()})
            elif self.path in ("/", "/index.html"):
                file = DASHBOARD / "index.html"
                body = file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self._json(404, {"error": "tidak ditemukan"})

        def do_POST(self):
            if not self.path.startswith("/webhook/"):
                self._json(404, {"error": "tidak ditemukan"})
                return
            platform = self.path.split("/")[2]
            if platform not in ADAPTERS:
                self._json(404, {"error": "platform tidak dikenal"})
                return
            length = int(self.headers.get("Content-Length") or 0)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._json(400, {"error": "JSON tidak valid"})
                return
            # Verifikasi GET-style challenge WhatsApp ditangani platform;
            # di sini cukup proses payload pesan.
            self._json(200, dispatch(core, platform, payload))

    return Handler


def serve(port: int | None = None) -> None:
    core = AgentCore()
    stop = threading.Event()
    thread = threading.Thread(target=cron_loop, args=(core, stop), daemon=True)
    thread.start()
    server = ThreadingHTTPServer(("0.0.0.0", port or config.port()), make_handler(core))
    print(f"OmniForge gateway berjalan di port {port or config.port()} "
          f"(mode {config.mode()}), platform: {', '.join(ADAPTERS)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop.set()
        server.shutdown()
