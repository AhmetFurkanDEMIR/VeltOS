"""The notice after a crash: which app crashed (from systemd's record), the
texts, and that background programs stay silent."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_taskmanager import crash, strings  # noqa: E402

# Fields of a systemd-coredump record as DrKonqi's processor forwards them.
KONSOLE = {"COREDUMP_EXE": "/usr/bin/konsole", "COREDUMP_PID": "48606", "COREDUMP_COMM": "konsole",
           "COREDUMP_CMDLINE": "konsole --notransparency", "_BOOT_ID": "bf8f36e0c2284d5d8a48ace58824c4b0",
           "COREDUMP_USER_UNIT": "app-org.kde.konsole-48606.scope"}
CALCULATOR = {"COREDUMP_EXE": "/usr/bin/python3.13", "COREDUMP_PID": "5100", "COREDUMP_COMM": "veltos-calculat",
              "COREDUMP_CMDLINE": "/usr/bin/python3 /usr/bin/veltos-calculator",
              "COREDUMP_USER_UNIT": "app-veltos\\x2dcalculator@8ef3d47a0dbb4825a78ec65de17018be.service"}
DAEMON = {"COREDUMP_EXE": "/usr/bin/kded6", "COREDUMP_PID": "77", "COREDUMP_COMM": "kded6",
          "COREDUMP_CMDLINE": "/usr/bin/kded6", "COREDUMP_USER_UNIT": "plasma-kded6.service"}


def applications():
    folder = Path(tempfile.mkdtemp())
    (folder / "org.kde.konsole.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Terminal\nName[tr]=Terminal\nExec=konsole\nIcon=utilities-terminal\n")
    (folder / "veltos-calculator.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Calculator\nName[tr]=Hesap Makinesi\nExec=veltos-calculator\n"
        "Icon=veltos-calculator\n")
    (folder / "kded6.desktop").write_text("[Desktop Entry]\nType=Application\nName=KDED\nExec=kded6\nNoDisplay=true\n")
    return folder


class AppTests(unittest.TestCase):
    def test_desktop_id_from_the_unit(self):
        self.assertEqual(crash.desktop_id(KONSOLE), "org.kde.konsole")
        self.assertEqual(crash.desktop_id(CALCULATOR), "veltos-calculator")
        self.assertEqual(crash.desktop_id(DAEMON), "")

    def test_find_app(self):
        folder = applications()
        app = crash.find_app(KONSOLE, "en", dirs=[folder])
        self.assertEqual((app["id"], app["name"], app["icon"]), ("org.kde.konsole", "Terminal", "utilities-terminal"))
        app = crash.find_app(CALCULATOR, "tr", dirs=[folder])
        self.assertEqual(app["name"], "Hesap Makinesi")
        self.assertEqual(app["path"], str(folder / "veltos-calculator.desktop"))
        # Without the unit: the program (the script for Python) is matched.
        app = crash.find_app(dict(CALCULATOR, COREDUMP_USER_UNIT=""), "en", dirs=[folder])
        self.assertEqual(app["id"], "veltos-calculator")
        # A background service (hidden desktop file, or none) gets no notice.
        self.assertIsNone(crash.find_app(DAEMON, "en", dirs=[folder]))

    def test_kcrash_metadata_removed(self):
        cache = Path(tempfile.mkdtemp())
        (cache / "kcrash-metadata").mkdir()
        leftover = cache / "kcrash-metadata/konsole.bf8f36e0c2284d5d8a48ace58824c4b0.48606.ini"
        leftover.write_text("[KCrash]\n")
        crash.forget_kcrash_metadata(KONSOLE, cache)
        self.assertFalse(leftover.exists())

    def test_notification_texts(self):
        app = {"id": "org.kde.konsole", "name": "Terminal", "icon": "utilities-terminal", "path": "/x"}
        name, icon, title, body, actions, hints = crash.notification(app, strings.texts("tr"))
        self.assertEqual((name, icon, title), ("Terminal", "utilities-terminal", "Terminal beklenmedik şekilde kapandı"))
        self.assertEqual(actions, ["restart", "Yeniden başlat"])
        self.assertEqual(hints, {"desktop-entry": "org.kde.konsole"})
        self.assertEqual(crash.notification(app, strings.texts("en"))[2], "Terminal closed unexpectedly")

    def test_main_notifies_apps_only(self):
        shown = []
        old = crash.system.APPLICATION_DIRS
        crash.system.APPLICATION_DIRS = [applications()]
        os.environ["XDG_CACHE_HOME"] = tempfile.mkdtemp()
        try:
            crash.main(read=lambda: KONSOLE, notify=lambda app, texts, launch: shown.append(app["name"]))
            crash.main(read=lambda: DAEMON, notify=lambda app, texts, launch: shown.append(app["name"]))
            # Earlier crashes picked up at sign-in are not announced again.
            crash.main(read=lambda: dict(KONSOLE, _DRKONQI_PICKUP="TRUE"),
                       notify=lambda app, texts, launch: shown.append("again"))
            crash.main(read=lambda: (_ for _ in ()).throw(ValueError("empty")), notify=None)
        finally:
            crash.system.APPLICATION_DIRS = old
        self.assertEqual(shown, ["Terminal"])


if __name__ == "__main__":
    unittest.main()
