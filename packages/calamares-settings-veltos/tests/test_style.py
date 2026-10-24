"""The installer's Qt style "veltos-installer" (style/installerstyle.cpp),
built by debian/rules, against the stand-ins of style_probe.py."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROBE = Path(__file__).resolve().parent / "style_probe.py"
PLUGIN = os.environ.get("VELTOS_STYLE_PLUGIN", "")


@unittest.skipUnless(PLUGIN, "VELTOS_STYLE_PLUGIN is not set (the package build sets it)")
class InstallerStyleTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.plugins = Path(tempfile.mkdtemp())
        (cls.plugins / "styles").mkdir()
        shutil.copy(PLUGIN, cls.plugins / "styles")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.plugins)

    def probe(self, theme, *locale):
        env = dict(os.environ, QT_PLUGIN_PATH=str(self.plugins), QT_QPA_PLATFORM="offscreen")
        result = subprocess.run([sys.executable, str(PROBE), theme, *locale], env=env,
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_light_pictures(self):
        drawn = self.probe("veltos-theme=dark=0;accent=#2F5EE6;software=0")
        self.assertIn("veltos-installer", drawn["keys"])
        self.assertTrue(drawn["created"])
        # Partitions on the disk in calm colours by number, unallocated space
        # hatched, the page's colour around the bar (not Calamares' Breeze
        # colours or a white box).
        self.assertEqual(drawn["bars"]["efi"], "#8764B8")
        self.assertEqual(drawn["bars"]["windows"], "#0E7C86")
        self.assertIn("#E8EBF2", drawn["bars"]["free"])
        self.assertGreater(len(drawn["bars"]["free"]), 1)
        self.assertEqual(drawn["bars"]["background"], "#F3F5FA")
        # VeltOS' new partitions in the accent colour, its helpers lighter.
        self.assertEqual(drawn["new"]["root"], "#2F5EE6")
        self.assertNotEqual(drawn["new"]["boot"], drawn["new"]["root"])
        self.assertNotEqual(drawn["new"]["efi"], drawn["new"]["boot"])
        # The legend: the same colours, no black text, the page's colour.
        self.assertEqual(drawn["legend"]["squares"], ["#8764B8", "#5D6B82", "#0E7C86", "#E8EBF2"])
        self.assertEqual(drawn["legend"]["black"], 0)
        self.assertEqual(drawn["legend"]["background"], "#F3F5FA")
        self.assertGreater(drawn["legend"]["inked"], 20)

    def test_alongside_bar_follows_calamares(self):
        drawn = self.probe("veltos-theme=dark=0;accent=#2F5EE6;software=0")
        splitter = drawn["splitter"]
        # The handle where Calamares' arithmetic puts it, between the
        # shrinking partition and VeltOS' new one.
        self.assertEqual(splitter["thumb"], "#FFFFFF")
        self.assertEqual(splitter["shrunk"], "#0E7C86")
        self.assertEqual(splitter["new"], "#2F5EE6")

    def test_dark_with_the_users_accent(self):
        drawn = self.probe("veltos-theme=dark=1;accent=#E81123;software=0")
        self.assertEqual(drawn["bars"]["background"], "#1C1E24")
        self.assertIn("#33363F", drawn["bars"]["free"])
        self.assertEqual(drawn["new"]["root"], "#E81123")
        self.assertEqual(drawn["legend"]["background"], "#1C1E24")
        self.assertEqual(drawn["legend"]["black"], 0)
        self.assertEqual(drawn["splitter"]["new"], "#E81123")
        self.assertEqual(drawn["splitter"]["thumb"], "#454A55")

    def test_sizes_as_disk_management_writes_them(self):
        drawn = self.probe("veltos-theme=dark=0;accent=#2F5EE6;software=0")
        self.assertEqual(drawn["label"], "/dev/vda3 will be shrunk to 1.59 GB and a new 22.10 GB partition "
                                         "will be created for VeltOS.")
        combo = drawn["combo"]
        self.assertEqual(combo["items"], ["vda - 40.00 GB (/dev/vda)", "sdb - 931.51 GB (/dev/sdb)"])
        # The chosen disk stays chosen and Calamares hears of no change.
        self.assertEqual(combo["text"], "sdb - 931.51 GB (/dev/sdb)")
        self.assertEqual(combo["index"], 1)
        self.assertEqual(combo["changes"], [])
        self.assertEqual(combo["rows"], 2)
        self.assertTrue(combo["delegate"])
        # The list's rows as tall as Windows 11's, the disk icon small.
        self.assertLess(combo["row_height"], 40)
        # The list opens under its box, not over it.
        popup = drawn["popup"]
        self.assertGreaterEqual(popup["top"], popup["box_bottom"])
        self.assertEqual(popup["left"], popup["box_left"])

    def test_turkish_decimal_comma(self):
        drawn = self.probe("veltos-theme=dark=0;accent=#2F5EE6;software=0", "tr_TR")
        self.assertIn("1,59 GB", drawn["label"])
        self.assertIn("22,10 GB", drawn["label"])
        self.assertEqual(drawn["combo"]["text"], "sdb - 931,51 GB (/dev/sdb)")
        # The translation's "1628 MB" (Calamares' MiB) too; small sizes stay.
        self.assertEqual(drawn["translated"], "/dev/vda3, 1,59 GB olarak küçültülecek ve VeltOS için yeni bir "
                                              "22,10 GB  bölüm; 300 MB EFI")


if __name__ == "__main__":
    unittest.main()
