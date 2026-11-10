"""Transkripsi memo suara.

Mode live: memanggil API kompatibel OpenAI /audio/transcriptions bila
OPENAI_API_KEY terisi. Mode demo: transkripsi deterministik berlabel
SIMULASI, jujur sebagai pengganti, tidak berpura-pura menjadi hasil ASR.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
import uuid

from . import config

DEMO_PHRASES = [
    "tolong ingatkan saya rapat besok jam sembilan pagi",
    "catat pengeluaran operasional hari ini sudah dibayar",
    "buatkan ringkasan penjualan minggu ini",
    "jadwalkan laporan harian setiap jam tujuh pagi",
]


class Transcriber:
    def transcribe(self, media_id: str, audio: bytes | None = None) -> dict:
        if config.is_live() and config.get("OPENAI_API_KEY") and audio:
            return {"text": self._whisper(audio), "simulated": False}
        digest = int(hashlib.sha256((media_id or "kosong").encode()).hexdigest(), 16)
        text = DEMO_PHRASES[digest % len(DEMO_PHRASES)]
        return {"text": text, "simulated": True}

    def _whisper(self, audio: bytes) -> str:
        boundary = "----omniforge" + uuid.uuid4().hex
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n'
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="memo.ogg"\r\n'
            "Content-Type: audio/ogg\r\n\r\n"
        ).encode() + audio + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/transcriptions",
            data=body,
            headers={
                "Authorization": f"Bearer {config.get('OPENAI_API_KEY')}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8")).get("text", "")
