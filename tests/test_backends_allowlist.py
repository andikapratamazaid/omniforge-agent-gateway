import unittest

from omniforge import allowlist, backends


class TestAllowlist(unittest.TestCase):
    def test_echo_diizinkan(self):
        self.assertTrue(allowlist.check("echo halo")[0])

    def test_rm_ditolak(self):
        self.assertFalse(allowlist.check("rm -rf /")[0])

    def test_run_local(self):
        result = backends.run("local", "echo uji backend")
        self.assertTrue(result["ok"])
        self.assertIn("uji backend", result["output"])

    def test_run_ditolak_tidak_eksekusi(self):
        result = backends.run("local", "rm -rf /")
        self.assertFalse(result["ok"])
        self.assertIn("DITOLAK", result["output"])

    def test_serverless_tanpa_kredensial_jelas(self):
        result = backends.run("modal", "echo halo")
        self.assertFalse(result["ok"])
        self.assertIn("belum dikonfigurasi", result["output"])


if __name__ == "__main__":
    unittest.main()
