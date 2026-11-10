"""Inti agent: satu otak untuk semua platform.

Alur: pesan terpadu masuk, identitas lintas platform diselesaikan,
memo suara ditranskrip, perintah garis miring ditangani, selain itu
jawaban disusun dari memori file, skills, dan riwayat sesi yang sama
di semua platform (kelanjutan percakapan lintas platform). Pada mode
live, penyusunan jawaban diserahkan ke model lewat Router.
"""

from __future__ import annotations

from . import backends, config
from .memory import Memory
from .messages import Message, Reply
from .router import Router
from .skills import SkillRegistry
from .store import Store
from .transcribe import Transcriber

SESSION_KEY = "utama"
HELP = (
    "Perintah yang tersedia:\n"
    "/baru : mulai sesi baru\n"
    "/link : buat kode tautan akun platform lain\n"
    "/link <KODE> : tautkan akun ini ke identitas pemilik kode\n"
    "/platform : platform yang tertaut ke identitasmu\n"
    "/skills : daftar skills\n"
    "/ingat <catatan> : simpan ke memori\n"
    "/jalan <perintah> : eksekusi di backend aktif (dijaga daftar izin)\n"
    "/backend <nama> : ganti backend eksekusi (local, docker, ssh, modal, daytona, vercel)\n"
    "/cron tambah <jadwal> <prompt> : jadwalkan tugas, contoh /cron tambah daily:00:00 buat laporan harian\n"
    "/cron : daftar tugas terjadwal\n"
    "/status : ringkasan sistem"
)


class AgentCore:
    def __init__(self, store: Store | None = None):
        self.store = store or Store()
        self.memory = Memory()
        self.skills = SkillRegistry()
        self.router = Router()
        self.transcriber = Transcriber()
        self.backend = config.get("OMNIFORGE_BACKEND", "local")

    def handle(self, msg: Message) -> Reply:
        identity_id = self.store.resolve_identity(msg.platform, msg.user_id)
        text = msg.text.strip()
        note = ""
        if msg.kind == "voice":
            result = self.transcriber.transcribe(msg.media_id)
            text = result["text"]
            note = ("[memo suara ditranskrip] " if not result["simulated"]
                    else "[memo suara, transkripsi SIMULASI pada mode demo] ")
        self.store.add_message(identity_id, SESSION_KEY, msg.platform, "user", text)
        reply_text = self._respond(identity_id, msg, text)
        self.store.add_message(identity_id, SESSION_KEY, msg.platform, "assistant", reply_text)
        return Reply(text=note + reply_text, platform=msg.platform, chat_id=msg.chat_id)

    # ---------------- perintah ----------------
    def _respond(self, identity_id: int, msg: Message, text: str) -> str:
        low = text.lower()
        if low in ("/start", "/help", "halo", "hai", "hello"):
            return self._greeting(identity_id)
        if low == "/baru":
            return "Sesi baru dimulai. Riwayat lama tetap tersimpan dan bisa dicari kembali."
        if low == "/link":
            code = self.store.create_link_code(identity_id)
            return (f"Kode tautanmu: {code}\nKirim '/link {code}' dari akunmu di platform lain "
                    "agar kedua akun berbagi identitas, memori, dan riwayat yang sama.")
        if low.startswith("/link "):
            target = self.store.apply_link_code(text.split(None, 1)[1], msg.platform, msg.user_id)
            if target is None:
                return "Kode tautan tidak dikenal atau sudah dipakai."
            return ("Akun ini sekarang tertaut. Riwayat dari kedua platform sudah digabung; "
                    "percakapan bisa dilanjutkan silih berganti di platform mana pun.")
        if low == "/platform":
            plats = self.store.platforms_of(identity_id)
            return "Platform tertaut ke identitasmu: " + ", ".join(plats)
        if low == "/skills":
            skills = self.skills.list()
            if not skills:
                return "Belum ada skill. Skills masuk lewat folder data/live/skills atau hasil impor agent lain."
            return "Skills tersedia:\n" + "\n".join(f"- {s.name}: {s.description}" for s in skills)
        if low.startswith("/ingat "):
            note = text.split(None, 1)[1]
            self.memory.remember(note)
            return f"Disimpan ke memori: {note}"
        if low.startswith("/backend "):
            name = text.split(None, 1)[1].strip().lower()
            if name in backends.BACKENDS:
                self.backend = name
                return f"Backend eksekusi aktif sekarang: {name}"
            return "Backend tidak dikenal. Pilihan: " + ", ".join(backends.BACKENDS)
        if low.startswith("/jalan "):
            command = text.split(None, 1)[1]
            result = backends.run(self.backend, command, store=self.store)
            status = "berhasil" if result["ok"] else "gagal/ditolak"
            return f"Eksekusi di backend {self.backend} ({status}):\n{result['output']}"
        if low == "/cron":
            jobs = self.store.list_cron(identity_id)
            if not jobs:
                return "Belum ada tugas terjadwal."
            return "Tugas terjadwal:\n" + "\n".join(
                f"- #{j['id']} [{j['schedule']}] {j['prompt']}" for j in jobs)
        if low.startswith("/cron tambah "):
            rest = text[len("/cron tambah "):]
            parts = rest.split(None, 1)
            if len(parts) < 2:
                return "Format: /cron tambah <jadwal> <prompt>, contoh /cron tambah daily:00:00 buat laporan harian"
            job_id = self.store.add_cron(identity_id, msg.platform, msg.chat_id, parts[0], parts[1])
            return f"Tugas terjadwal #{job_id} dibuat: [{parts[0]}] {parts[1]}"
        if low == "/status":
            stats = self.store.stats()
            return (f"Mode {config.mode()} | backend {self.backend} | "
                    f"identitas {stats['identities']} | tautan {stats['links']} | "
                    f"pesan tersimpan {stats['messages']} | cron {stats['cron_jobs']} | "
                    f"eksekusi {stats['executions']}")
        return self._answer(identity_id, msg, text)

    def _greeting(self, identity_id: int) -> str:
        name = self.memory.user_name()
        sapaan = f"Halo {name}. " if name and name != "(belum diisi)" else "Halo. "
        return (sapaan + "Saya OmniForge, agent yang sama di semua platformmu. "
                "Ketik /help untuk daftar perintah, atau langsung sampaikan kebutuhanmu.")

    def _answer(self, identity_id: int, msg: Message, text: str) -> str:
        history = self.store.history(identity_id, SESSION_KEY, limit=20)
        live = self.router.complete(
            "gateway",
            "Kamu adalah OmniForge, agent pribadi multi-platform.\n" + self.memory.context(),
            [{"role": h["role"], "content": h["text"]} for h in history],
        )
        if live["live"] and live["text"]:
            return live["text"]
        # Mode demo: jawaban deterministik dari konteks nyata.
        parts = []
        skill = self.skills.match(text)
        user_msgs = [h for h in history if h["role"] == "user"]
        prev_platforms = sorted({h["platform"] for h in user_msgs[:-1]})
        if skill:
            parts.append(f"Skill '{skill.name}' relevan untuk ini. {skill.body.splitlines()[0] if skill.body else ''}")
        parts.append(f"Siap, saya catat dan proses: \"{text}\".")
        if prev_platforms:
            parts.append(
                f"Konteksmu utuh: sesi ini sudah berisi {len(user_msgs)} pesan darimu, "
                f"termasuk dari {', '.join(prev_platforms)}. Lanjutkan saja, saya mengikuti dari platform mana pun."
            )
        else:
            parts.append("Ini pesan pertamamu di sesi ini. Sampaikan lewat platform mana pun, riwayatnya menyatu di sini.")
        name = self.memory.user_name()
        if name and name != "(belum diisi)":
            parts.append(f"Catatan profilmu ({name}) dan memori tersimpan ikut saya pakai sebagai konteks.")
        return " ".join(parts)

    # ---------------- cron ----------------
    def run_cron_job(self, job: dict) -> Reply:
        msg = Message(platform=job["platform"], user_id="cron",
                      chat_id=job["chat_id"], text=job["prompt"])
        identity_id = int(job["identity_id"])
        self.store.add_message(identity_id, SESSION_KEY, job["platform"], "user", job["prompt"])
        reply_text = self._answer(identity_id, msg, job["prompt"])
        self.store.add_message(identity_id, SESSION_KEY, job["platform"], "assistant", reply_text)
        self.store.mark_cron_run(int(job["id"]))
        return Reply(text=reply_text, platform=job["platform"], chat_id=job["chat_id"])
