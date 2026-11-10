"""Harness evaluasi OmniForge: 10 pemeriksaan ujung-ke-ujung deterministik."""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from omniforge import cron as cron_mod
from omniforge.agent_core import AgentCore
from omniforge.gateway.server import dispatch
from omniforge.importers import IMPORTERS
from omniforge.messages import Message
from omniforge.store import Store

SAMPLES = ROOT / "data" / "samples" / "payloads"


def load(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def fresh_core():
    tmp = Path(tempfile.mkdtemp())
    return AgentCore(store=Store(tmp / "eval.db"))


def run() -> dict:
    results = {}

    core = fresh_core()
    ok = True
    for platform, file in (("telegram", "telegram_update.json"), ("whatsapp", "whatsapp_message.json"),
                           ("slack", "slack_event.json"), ("discord", "discord_message.json"),
                           ("signal", "signal_message.json")):
        r = dispatch(core, platform, load(file))
        ok = ok and bool(r.get("reply"))
    ok = ok and bool(dispatch(core, "cli", {"text": "halo"})["reply"])
    results["parse_enam_platform"] = ok

    core = fresh_core()
    r = dispatch(core, "telegram", load("telegram_voice.json"))
    results["memo_suara_tertranskrip_simulasi"] = "SIMULASI" in r["reply"]

    core = fresh_core()
    core.handle(Message("telegram", "u1", "c1", text="halo"))
    link = core.handle(Message("telegram", "u1", "c1", text="/link"))
    code = link.text.split("Kode tautanmu: ")[1].split()[0]
    core.handle(Message("whatsapp", "u2", "c2", text=f"/link {code}"))
    lanjut = core.handle(Message("whatsapp", "u2", "c2", text="lanjutkan"))
    results["kelanjutan_lintas_platform_setelah_link"] = "telegram" in lanjut.text

    core = fresh_core()
    r = core.handle(Message("whatsapp", "u9", "c9", text="/link XXXXXX"))
    results["kode_link_salah_ditolak"] = "tidak dikenal" in r.text

    core = fresh_core()
    r = core.handle(Message("cli", "u1", "c", text="/jalan echo evaluasi"))
    results["eksekusi_diizinkan_berjalan"] = "evaluasi" in r.text and "berhasil" in r.text
    r = core.handle(Message("cli", "u1", "c", text="/jalan rm -rf /"))
    results["eksekusi_berbahaya_ditolak"] = "DITOLAK" in r.text

    plan = IMPORTERS["openclaw"](str(ROOT / "data/samples/imports/openclaw")).plan()
    results["impor_openclaw_dry_run_lengkap"] = (
        sum(1 for i in plan if i["action"] == "copy") >= 5
        and any(i["action"] == "merge" for i in plan))
    plan = IMPORTERS["n8n"](str(ROOT / "data/samples/imports/n8n")).plan()
    results["impor_n8n_menghasilkan_skill"] = len(plan) == 1 and plan[0]["action"] == "generate"

    now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
    results["cron_every_due_dan_tertunda"] = (
        cron_mod.is_due({"schedule": "every:60", "last_run": ""}, now)
        and not cron_mod.is_due({"schedule": "daily:01:00", "last_run": ""}, now))

    core = fresh_core()
    core.handle(Message("cli", "u1", "c", text="/ingat evaluasi dicatat"))
    results["memori_ingat_tersimpan"] = "evaluasi dicatat" in core.memory.read("MEMORY.md")

    passed = sum(1 for v in results.values() if v)
    return {"passed": passed, "total": len(results), "results": results}


if __name__ == "__main__":
    out = run()
    (ROOT / "evaluation" / "results.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    raise SystemExit(0 if out["passed"] == out["total"] else 1)
