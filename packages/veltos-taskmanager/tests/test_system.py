"""Process grouping, start-up apps, performance figures and End task, with a
recorded process list (tests/fakepsutil.py)."""

import signal
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fakepsutil import FakePsutil  # noqa: E402
from veltos_taskmanager import system  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def app_index():
    apps = Path(tempfile.mkdtemp())
    write(apps / "firefox-esr.desktop",
          "[Desktop Entry]\nType=Application\nName=Firefox\nExec=/usr/lib/firefox-esr/firefox-esr %u\nIcon=firefox-esr\n")
    write(apps / "veltos-settings.desktop",
          "[Desktop Entry]\nType=Application\nName=Settings\nName[tr]=Ayarlar\nExec=veltos-settings\nIcon=veltos-settings\n")
    write(apps / "org.kde.kded.desktop",
          "[Desktop Entry]\nType=Application\nName=KDE Daemon\nExec=kded6\nNoDisplay=true\n")
    return apps


def sample_processes():
    ps = FakePsutil(uid=1000)
    ps.add(1, 0, "systemd", ["/sbin/init"], uid=0, rss=12 << 20)
    ps.add(2, 0, "kthreadd", [], uid=0, rss=0)                          # kernel thread
    ps.add(500, 1, "NetworkManager", uid=0, rss=20 << 20, cpu=4.0)
    ps.add(1000, 1, "plasmashell", rss=300 << 20, cpu=8.0)
    ps.add(1100, 1000, "firefox-esr", ["/usr/lib/firefox-esr/firefox-esr"], rss=400 << 20, cpu=20.0)
    ps.add(1101, 1100, "Isolated Web Co", ["/usr/lib/firefox-esr/firefox-esr", "-contentproc"],
           rss=200 << 20, cpu=12.0)
    ps.add(1200, 1000, "python3", ["/usr/bin/python3", "/usr/bin/veltos-settings"], rss=80 << 20)
    ps.add(1300, 1000, "kded6", rss=60 << 20)
    return ps


class GroupingTests(unittest.TestCase):
    def setUp(self):
        self.ps = sample_processes()
        self.procs = system.Processes(self.ps, apps=system.AppIndex(dirs=[app_index()], lang="tr"), uid=1000)

    def test_windows_groups(self):
        self.procs.snapshot()                        # first sample starts the CPU measurement
        groups = system.group(self.procs.snapshot())
        apps = {a["name"]: a for a in groups["apps"]}
        self.assertEqual(sorted(apps), ["Ayarlar", "Firefox"])
        firefox = apps["Firefox"]
        self.assertEqual(sorted(firefox["pids"]), [1100, 1101])     # its child process too
        self.assertAlmostEqual(firefox["cpu"], (20.0 + 12.0) / 4)   # % of all four CPUs
        self.assertEqual(firefox["memory"], 600 << 20)
        self.assertEqual(firefox["count"], 2)
        background = [b["name"] for b in groups["background"]]
        self.assertIn("plasmashell", background)
        self.assertIn("KDE Daemon", background)                       # hidden app: background
        system_names = [s["name"] for s in groups["system"]]
        self.assertEqual(sorted(system_names), ["NetworkManager", "systemd"])
        self.assertNotIn("kthreadd", system_names + background)       # kernel threads left out

    def test_first_sample_shows_no_cpu(self):
        rows = self.procs.snapshot()
        self.assertTrue(all(r["cpu"] == 0.0 for r in rows))

    def test_program_of_scripts(self):
        self.assertEqual(system.program_of("python3", ["/usr/bin/python3", "-I", "/usr/bin/veltos-run"]),
                         "veltos-run")
        self.assertEqual(system.program_of("firefox-esr", ["firefox-esr"]), "firefox-esr")
        # The kernel cuts process names to 15 characters; scripts run by
        # their #! line show the script name.
        self.assertEqual(system.program_of("veltos-taskman", ["/usr/bin/python3", "/usr/bin/veltos-taskmanager"]),
                         "veltos-taskmanager")
        self.assertEqual(system.program_of("gnome-control-c", ["/usr/bin/gnome-control-center"]),
                         "gnome-control-center")
        self.assertEqual(system.program_of("Isolated Web Co", ["/usr/lib/firefox-esr/firefox-esr", "-contentproc"]),
                         "Isolated Web Co")

    def test_end_task_terminates_then_kills(self):
        ps = sample_processes()
        ps.stubborn = {1101}
        self.assertEqual(system.end_task([1100, 1101, 9999], ps, wait=0), 2)
        self.assertEqual(ps.procs[1100].signals, [signal.SIGTERM])
        self.assertEqual(ps.procs[1101].signals, [signal.SIGTERM, "kill"])


class PerformanceTests(unittest.TestCase):
    def test_rates_between_samples(self):
        ps = FakePsutil()
        clock = iter([10.0, 12.0])
        perf = system.Performance(ps, clock=lambda: next(clock))
        first = perf.sample()
        self.assertEqual(first["diskRead"], 0.0)
        ps.disk = ps.disk._replace(read_bytes=4 << 20, busy_time=500)
        ps.net = ps.net._replace(bytes_recv=2 << 20)
        second = perf.sample()
        self.assertEqual(second["diskRead"], 2 << 20)
        self.assertEqual(second["netReceived"], 1 << 20)
        self.assertAlmostEqual(second["disk"], 25.0)
        self.assertEqual(second["memoryUsed"], 2 << 30)

    def test_texts(self):
        self.assertEqual(system.human_bytes(1536 << 20, "tr"), "1,5 GB")
        self.assertEqual(system.uptime_text(90061), "1:01:01:01")


class StartupTests(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp())
        self.system_dir = base / "etc"
        self.user_dir = base / "user"
        write(self.system_dir / "org.kde.discover.notifier.desktop",
              "[Desktop Entry]\nType=Application\nName=Discover\nIcon=plasmadiscover\nExec=x\n")
        write(self.system_dir / "veltos-session-fixups.desktop",
              "[Desktop Entry]\nType=Application\nName=Fixups\nNoDisplay=true\nExec=y\n")
        write(self.system_dir / "gnome-only.desktop",
              "[Desktop Entry]\nType=Application\nName=GNOME thing\nOnlyShowIn=GNOME;\nExec=z\n")
        self.startup = system.StartupApps(self.system_dir, self.user_dir)

    def test_lists_apps_only(self):
        self.assertEqual([e["name"] for e in self.startup.list()], ["Discover"])
        self.assertTrue(self.startup.list()[0]["enabled"])

    def test_disable_and_enable(self):
        self.startup.set_enabled("org.kde.discover.notifier.desktop", False)
        user = self.user_dir / "org.kde.discover.notifier.desktop"
        self.assertIn("Hidden=true", user.read_text())
        self.assertFalse(self.startup.list()[0]["enabled"])
        self.startup.set_enabled("org.kde.discover.notifier.desktop", True)
        self.assertFalse(user.exists())
        self.assertTrue(self.startup.list()[0]["enabled"])

    def test_rejects_paths(self):
        with self.assertRaises(ValueError):
            self.startup.set_enabled("../evil.desktop", False)


if __name__ == "__main__":
    unittest.main()
