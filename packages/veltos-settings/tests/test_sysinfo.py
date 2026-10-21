"""Tests for the system facts shown by VeltOS Settings."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_settings import sysinfo  # noqa: E402

LSPCI = '''\
00:00.0 "Host bridge" "Intel Corporation" "Raptor Lake-P/U 4p+8e cores Host Bridge/DRAM Controller" -r01 "Lenovo" "Device 3c4f"
00:02.0 "VGA compatible controller" "Intel Corporation" "Raptor Lake-P [UHD Graphics]" -r04 "Lenovo" "Device 3c4f"
01:00.0 "VGA compatible controller" "NVIDIA Corporation" "AD106M [GeForce RTX 4070 Max-Q / Mobile]" -ra1 "Lenovo" "Device 3c4f"
03:00.0 "Display controller" "Advanced Micro Devices, Inc. [AMD/ATI]" "Navi 33" -rc0 "" ""
00:1f.3 "Audio device" "Intel Corporation" "Raptor Lake High Definition Audio Controller" -r01 "" ""
'''

MOUNTS = """\
sysfs /sys sysfs rw 0 0
/dev/nvme0n1p2 / ext4 rw,relatime 0 0
/dev/nvme0n1p1 /boot/efi vfat rw 0 0
tmpfs /tmp tmpfs rw 0 0
/dev/nvme0n1p3 /home ext4 rw 0 0
/dev/sdb1 /media/velt/USB\\040STICK vfat rw 0 0
/dev/nvme0n1p2 / ext4 rw 0 0
"""


class FakeRoot:
    """Temporarily point sysinfo at a fake file system."""

    def __init__(self, files):
        self.files = files

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        for path, text in self.files.items():
            target = root / path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        self.patch = mock.patch.object(sysinfo, "ROOT", root)
        self.patch.start()
        return root

    def __exit__(self, *exc):
        self.patch.stop()
        self.tmp.cleanup()


class SysinfoTests(unittest.TestCase):
    def test_gpus(self):
        self.assertEqual(sysinfo.gpus(LSPCI), [
            "Intel Raptor Lake-P [UHD Graphics]",
            "NVIDIA AD106M [GeForce RTX 4070 Max-Q / Mobile]",
            "AMD Navi 33",
        ])
        self.assertEqual(sysinfo.gpus('bad "quote line\n'), [])

    def test_cpu_memory_and_release(self):
        files = {
            "/proc/cpuinfo": "processor : 0\nmodel name : 13th Gen Intel(R) Core(TM)  i7-13620H\n"
                             "processor : 1\nmodel name : 13th Gen Intel(R) Core(TM)  i7-13620H\n",
            "/proc/meminfo": "MemTotal:       32617764 kB\nMemFree: 1 kB\n",
            "/etc/os-release": 'PRETTY_NAME="VeltOS 0.1"\nVERSION="0.1 (dev)"\nID=veltos\n',
            "/etc/machine-info": 'PRETTY_HOSTNAME="Ayşe\'s Laptop"\n',
            "/sys/class/dmi/id/sys_vendor": "LENOVO\n",
            "/sys/class/dmi/id/product_name": "82Y9\n",
        }
        with FakeRoot(files):
            self.assertEqual(sysinfo.cpu_model(), ("13th Gen Intel(R) Core(TM) i7-13620H", 2))
            self.assertEqual(sysinfo.human_size(sysinfo.memory_bytes()), "31.1 GB")
            self.assertEqual(sysinfo.os_release()["ID"], "veltos")
            self.assertEqual(sysinfo.pc_name(), "Ayşe's Laptop")
            self.assertEqual(sysinfo.device_model(), "LENOVO 82Y9")
            with mock.patch.object(sysinfo, "gpus", return_value=["GPU"]):
                about = sysinfo.about()
            self.assertEqual(about["os"], "VeltOS 0.1")
            self.assertEqual(about["gpus"], ["GPU"])

    def test_missing_files_still_give_an_answer(self):
        with FakeRoot({}):
            self.assertEqual(sysinfo.os_release(), {})
            self.assertEqual(sysinfo.memory_bytes(), 0)
            self.assertTrue(sysinfo.pc_name())
            self.assertEqual(sysinfo.device_model(), "")

    def test_placeholder_dmi_names_are_hidden(self):
        with FakeRoot({"/sys/class/dmi/id/sys_vendor": "To Be Filled By O.E.M.\n",
                       "/sys/class/dmi/id/product_name": "To Be Filled By O.E.M.\n"}):
            self.assertEqual(sysinfo.device_model(), "")

    def test_storage_lists_data_drives_once(self):
        usage = {"/": (500e9, 120e9, 380e9), "/home": (1e12, 9.5e11, 5e10),
                 "/media/velt/USB STICK": (32e9, 1e9, 31e9)}
        drives = sysinfo.storage(MOUNTS, usage=lambda p: usage[p])
        self.assertEqual([d["mount"] for d in drives], ["/", "/home", "/media/velt/USB STICK"])
        self.assertTrue(drives[0]["system"])
        self.assertTrue(drives[2]["removable"])
        self.assertEqual(drives[2]["label"], "USB STICK")
        self.assertAlmostEqual(drives[1]["fraction"], 0.95)

    def test_live_root_is_marked(self):
        drives = sysinfo.storage("overlay / overlay rw 0 0\n", usage=lambda p: (4e9, 1e9, 3e9))
        self.assertTrue(drives[0]["live"])

    def test_pc_names(self):
        self.assertTrue(sysinfo.valid_pc_name("Ahmet's PC"))
        self.assertTrue(sysinfo.valid_pc_name("ofis-1"))
        self.assertFalse(sysinfo.valid_pc_name("   "))
        self.assertFalse(sysinfo.valid_pc_name("---"))
        self.assertFalse(sysinfo.valid_pc_name("x" * 64))
        self.assertFalse(sysinfo.valid_pc_name("bad\nname"))

    def test_dark_mode_from_kdeglobals(self):
        with tempfile.TemporaryDirectory() as config:
            Path(config, "kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.veltos.dark\n")
            with mock.patch.dict("os.environ", {"XDG_CONFIG_HOME": config}):
                self.assertTrue(sysinfo.dark_mode())
            Path(config, "kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.veltos.light\n")
            with mock.patch.dict("os.environ", {"XDG_CONFIG_HOME": config}):
                self.assertFalse(sysinfo.dark_mode())

    def test_last_update_check_and_its_text(self):
        import os
        with tempfile.TemporaryDirectory() as lists:
            self.assertEqual(sysinfo.last_update_check(Path(lists)), 0)
            release = Path(lists, "deb.debian.org_debian_dists_trixie_InRelease")
            release.write_text("x")
            os.utime(release, (1000, 1000))
            Path(lists, "partial").mkdir()
            self.assertEqual(sysinfo.last_update_check(Path(lists)), 1000)
        self.assertEqual(sysinfo.ago(0, "en"), "not yet")
        self.assertEqual(sysinfo.ago(1000, "en", now=1030), "just now")
        self.assertEqual(sysinfo.ago(1000, "en", now=1000 + 3600), "1 hour ago")
        self.assertEqual(sysinfo.ago(1000, "tr", now=1000 + 3 * 86400), "3 gün önce")
        self.assertEqual(sysinfo.ago(1000, "en", now=1000 + 5 * 60), "5 minutes ago")


if __name__ == "__main__":
    unittest.main()
