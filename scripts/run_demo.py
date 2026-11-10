"""Demo ujung-ke-ujung tanpa server dan tanpa kunci apa pun.

Skenario: pengguna menyapa dari Telegram, membuat kode tautan,
menautkan WhatsApp, melanjutkan percakapan dari WhatsApp (konteks
menyatu), mengirim memo suara, menjalankan perintah yang diizinkan dan
yang ditolak daftar izin, lalu membuat tugas cron. Semua payload memakai
contoh di data/samples/payloads.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from omniforge.agent_core import AgentCore
from omniforge.gateway.server import dispatch

SAMPLES = ROOT / "data" / "samples" / "payloads"


def load(name: str) -> dict:
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def show(title: str, reply: str) -> None:
    print(f"\n### {title}\n{reply}")


def main() -> int:
    core = AgentCore()
    r = dispatch(core, "telegram", load("telegram_update.json"))
    show("1. Sapaan dari Telegram", r["reply"])

    code_reply = dispatch(core, "cli", {"text": "/link", "user_id": "111"})
    # Kode dibuat untuk identitas telegram:111 lewat payload telegram langsung
    from omniforge.messages import Message
    link = core.handle(Message("telegram", "111", "555", text="/link"))
    code = link.text.split("Kode tautanmu: ")[1].split()[0]
    show("2. Kode tautan dibuat di Telegram", link.text)

    wa = load("whatsapp_message.json")
    wa["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = f"/link {code}"
    r = dispatch(core, "whatsapp", wa)
    show("3. WhatsApp menautkan diri dengan kode itu", r["reply"])

    wa2 = load("whatsapp_message.json")
    wa2["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = \
        "lanjutkan ya, tadi saya menyapa dari telegram"
    r = dispatch(core, "whatsapp", wa2)
    show("4. Percakapan dilanjutkan dari WhatsApp, konteks menyatu", r["reply"])

    r = dispatch(core, "telegram", load("telegram_voice.json"))
    show("5. Memo suara Telegram ditranskrip (SIMULASI pada mode demo)", r["reply"])

    r = dispatch(core, "cli", {"text": "/jalan echo laporan pagi siap", "user_id": "111"})
    show("6. Eksekusi yang diizinkan di backend local", r["reply"])
    r = dispatch(core, "cli", {"text": "/jalan rm -rf /", "user_id": "111"})
    show("7. Eksekusi berbahaya ditolak daftar izin", r["reply"])

    r = dispatch(core, "cli", {"text": "/cron tambah daily:00:00 susun laporan harian", "user_id": "111"})
    show("8. Tugas cron dibuat", r["reply"])
    print("\nDemo selesai. Statistik:", core.store.stats())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
