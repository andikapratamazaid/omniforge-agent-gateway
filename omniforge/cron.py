"""Penjadwal cron sederhana.

Format jadwal yang didukung:
- "every:<detik>"   berjalan berulang tiap N detik sejak run terakhir
- "daily:<HH:MM>"   berjalan sekali sehari pada jam tersebut (UTC)
Hasil prompt dikirim kembali ke platform dan chat asal lewat gateway.
"""

from __future__ import annotations

from datetime import datetime, timezone


def is_due(job: dict, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    schedule = job.get("schedule", "")
    last = job.get("last_run") or ""
    if schedule.startswith("every:"):
        try:
            seconds = int(schedule.split(":", 1)[1])
        except ValueError:
            return False
        if not last:
            return True
        last_dt = datetime.fromisoformat(last)
        return (now - last_dt).total_seconds() >= seconds
    if schedule.startswith("daily:"):
        hhmm = schedule.split(":", 1)[1]
        if now.strftime("%H:%M") != hhmm:
            return False
        return not last.startswith(now.strftime("%Y-%m-%d"))
    return False
