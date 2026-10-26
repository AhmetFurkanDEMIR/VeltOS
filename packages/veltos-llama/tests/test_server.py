"""The built llama-server runs and knows the options VeltOS AI passes
(veltos_ai/local.py: -m, --host, --port, -c, -t, --no-webui)."""

import os
import subprocess
import unittest
from pathlib import Path

BIN = os.environ.get("VELTOS_LLAMA_BIN", "")


@unittest.skipUnless(BIN, "VELTOS_LLAMA_BIN not set (debian/rules sets it)")
class ServerTests(unittest.TestCase):
    def run_server(self, *args):
        return subprocess.run([BIN, *args], capture_output=True, text=True, timeout=60)

    def test_version(self):
        result = self.run_server("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("version", (result.stdout + result.stderr).lower())

    def test_options_used_by_veltos_ai(self):
        text = self.run_server("--help").stdout
        for option in ("--host", "--port", "--ctx-size", "--threads", "--no-webui", "--model"):
            self.assertIn(option, text)

    def test_cpu_backends_were_built(self):
        found = [p.name for p in Path(BIN).parent.glob("libggml-cpu*.so")]
        self.assertTrue(found, "no CPU backend")
        self.assertTrue(any("x64" in name or "sse42" in name for name in found), found)

    def test_missing_model_fails_cleanly(self):
        result = self.run_server("-m", "/nonexistent.gguf", "--port", "0")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
