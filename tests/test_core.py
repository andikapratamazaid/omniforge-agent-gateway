import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from omniforge import cron as cron_mod
from omniforge.agent_core import AgentCore
from omniforge.messages import Message
from omniforge.store import Store
from omniforge.transcribe import Transcriber


class TestCore(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.core = AgentCore(store=Store(self.tmp / "t.db"))

    def test_memo_suara_berlabel_simulasi(self):
        r = self.core.handle(Message("telegram", "u1", "c1", kind="voice", media_id="v1"))
        self.assertIn("SIMULASI", r.text)

    def test_transkripsi_deterministik(self):
        t = Transcriber()
        self.assertEqual(t.transcribe("abc"), t.transcribe("abc"))
        self.assertTrue(t.transcribe("abc")["simulated"])

    def test_ingat_dan_status(self):
        self.core.handle(Message("cli", "u1", "c", text="/ingat warna favorit biru"))
        mem = self.core.memory.read("MEMORY.md")
        self.assertIn("warna favorit biru", mem)
        status = self.core.handle(Message("cli", "u1", "c", text="/status"))
        self.assertIn("identitas", status.text)

    def test_cron_due(self):
        now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(cron_mod.is_due({"schedule": "every:60", "last_run": ""}, now))
        self.assertTrue(cron_mod.is_due({"schedule": "daily:00:00", "last_run": ""}, now))
        self.assertFalse(cron_mod.is_due({"schedule": "daily:01:00", "last_run": ""}, now))

    def test_cron_tambah_dan_jalan(self):
        r = self.core.handle(Message("cli", "u1", "c", text="/cron tambah every:30 buat ringkasan"))
        self.assertIn("dibuat", r.text)
        jobs = self.core.store.list_cron()
        self.assertEqual(len(jobs), 1)
        reply = self.core.run_cron_job(jobs[0])
        self.assertTrue(reply.text)


if __name__ == "__main__":
    unittest.main()
