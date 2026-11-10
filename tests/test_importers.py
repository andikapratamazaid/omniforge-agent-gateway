import unittest
from pathlib import Path

from omniforge.importers import IMPORTERS

ROOT = Path(__file__).resolve().parent.parent


class TestImporters(unittest.TestCase):
    def test_openclaw_plan(self):
        imp = IMPORTERS["openclaw"](str(ROOT / "data/samples/imports/openclaw"))
        plan = imp.plan()
        kinds = {i["kind"] for i in plan}
        self.assertIn("memori", kinds)
        self.assertIn("skill", kinds)
        self.assertIn("allowlist", kinds)
        copies = [i for i in plan if i["action"] == "copy"]
        self.assertGreaterEqual(len(copies), 5)

    def test_n8n_plan_generate(self):
        imp = IMPORTERS["n8n"](str(ROOT / "data/samples/imports/n8n"))
        plan = imp.plan()
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["action"], "generate")
        self.assertIn("Laporan Pagi Otomatis", plan[0]["_content"])

    def test_sumber_lain_terdaftar(self):
        for name in ("claude-code", "codex", "cursor"):
            plan = IMPORTERS[name]("/path/tidak/ada").plan()
            self.assertTrue(all(i["action"] == "missing" for i in plan))


if __name__ == "__main__":
    unittest.main()
