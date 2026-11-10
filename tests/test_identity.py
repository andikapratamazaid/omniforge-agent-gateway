import tempfile
import unittest
from pathlib import Path

from omniforge.agent_core import AgentCore
from omniforge.messages import Message
from omniforge.store import Store


class TestIdentity(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.core = AgentCore(store=Store(self.tmp / "t.db"))

    def test_kelanjutan_lintas_platform(self):
        self.core.handle(Message("telegram", "u1", "c1", text="halo"))
        link = self.core.handle(Message("telegram", "u1", "c1", text="/link"))
        code = link.text.split("Kode tautanmu: ")[1].split()[0]
        self.core.handle(Message("whatsapp", "u2", "c2", text="pesan sebelum tautan"))
        joined = self.core.handle(Message("whatsapp", "u2", "c2", text=f"/link {code}"))
        self.assertIn("tertaut", joined.text)
        lanjut = self.core.handle(Message("whatsapp", "u2", "c2", text="lanjutkan"))
        self.assertIn("telegram", lanjut.text)
        plats = self.core.store.platforms_of(
            self.core.store.resolve_identity("telegram", "u1"))
        self.assertEqual(sorted(plats), ["telegram", "whatsapp"])

    def test_kode_salah_ditolak(self):
        r = self.core.handle(Message("whatsapp", "u9", "c9", text="/link ZZZZZZ"))
        self.assertIn("tidak dikenal", r.text)


if __name__ == "__main__":
    unittest.main()
