"""The package installer window: a real .deb built here with dpkg-deb, read
by debfile.py, shown offscreen (English and Turkish) and installed through
a stand-in for pkcon."""

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QML_DISABLE_DISK_CACHE"] = "1"

from PySide6.QtCore import QCoreApplication, QEvent, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from veltos_store import debfile, installer, packages  # noqa: E402

from test_ui import APP, MESSAGES, wait  # noqa: E402,F401

ICON = b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16"/></svg>'
DESKTOP = ("[Desktop Entry]\nType=Application\nName=Hello World\nName[tr]=Merhaba\nExec=hello\n"
           "Icon=hello-world\n")
FAKE_PKCON = ('#!/bin/sh\n'
              'echo "$*" >> "$(dirname "$0")/calls"\n'
              'printf "Status:\\tInstalling packages\\nPercentage:\\t60\\n"\n'
              'if [ -f "$(dirname "$0")/fail" ]; then echo "Fatal error: Failed to obtain authentication."; exit 1; fi\n')
HAVE_DPKG = shutil.which("dpkg-deb") is not None


def build_deb(folder, arch="all", version="1.2-1", desktop=True):
    root = Path(folder) / "root"
    (root / "DEBIAN").mkdir(parents=True)
    (root / "DEBIAN/control").write_text(
        f"Package: veltos-test-hello\nVersion: {version}\nArchitecture: {arch}\n"
        "Maintainer: Hello Publisher <hello@example.com>\nInstalled-Size: 2048\n"
        "Description: Says hello\n A small test program.\n .\n It says hello.\n")
    if desktop:
        apps = root / "usr/share/applications"
        apps.mkdir(parents=True)
        (apps / "hello-world.desktop").write_text(DESKTOP)
        for size, data in (("48x48", b"\x89PNG small"), ("scalable", ICON)):
            icons = root / f"usr/share/icons/hicolor/{size}/apps"
            icons.mkdir(parents=True)
            (icons / ("hello-world.svg" if size == "scalable" else "hello-world.png")).write_bytes(data)
    path = Path(folder) / f"hello_{version}_{arch}.deb"
    subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(root), str(path)], check=True,
                   capture_output=True)
    return path


@unittest.skipUnless(HAVE_DPKG, "needs dpkg-deb")
class DebFileTests(unittest.TestCase):
    def test_read_a_package(self):
        info = debfile.read(build_deb(tempfile.mkdtemp()))
        self.assertEqual((info["package"], info["version"], info["arch"]), ("veltos-test-hello", "1.2-1", "all"))
        self.assertEqual(info["publisher"], "Hello Publisher")
        self.assertEqual(info["summary"], "Says hello")
        self.assertEqual(info["description"], "A small test program.\n\nIt says hello.")
        self.assertEqual(info["size"], 2048 * 1024)
        self.assertEqual(info["displayName"], "Hello World")
        self.assertEqual(info["apps"], [{"id": "hello-world.desktop", "name": "Hello World"}])
        # The scalable icon wins over the 48 px one.
        self.assertEqual((info["iconName"], info["iconData"]), ("hello-world.svg", ICON))
        self.assertEqual((info["status"], info["archOk"]), ("new", True))

    def test_not_a_package(self):
        path = Path(tempfile.mkdtemp()) / "broken.deb"
        path.write_bytes(b"not a package")
        self.assertIsNone(debfile.read(path))

    def test_versions(self):
        self.assertEqual(debfile.compare("", "1.0"), "new")
        self.assertEqual(debfile.compare("1.0", "1.0"), "same")
        self.assertEqual(debfile.compare("1.0", "1.1"), "newer")
        self.assertEqual(debfile.compare("2.0", "1.1"), "older")
        self.assertEqual(debfile.compare("1.0~rc1", "1.0"), "newer")
        self.assertEqual(debfile.publisher("Ayşe Yılmaz <a@example.com>"), "Ayşe Yılmaz")


@unittest.skipUnless(HAVE_DPKG, "needs dpkg-deb")
class InstallerWindowTests(unittest.TestCase):
    lang = "en"

    def setUp(self):
        MESSAGES.clear()
        self.folder = Path(tempfile.mkdtemp())
        self.fake = self.folder / "pkcon"
        self.fake.write_text(FAKE_PKCON, encoding="utf-8", newline="\n")
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IEXEC)
        self.applications = self.folder / "applications"
        self.applications.mkdir()
        self.started = []

    def tearDown(self):
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        APP.processEvents()

    def open(self, path, reader=debfile.read):
        jobs = packages.Jobs(program=str(self.fake), needs_refresh=lambda: False)
        backend = installer.Installer(path, lang=self.lang, reader=reader, jobs=jobs, start=self.started.append,
                                      desktop_dirs=(str(self.applications),))
        self.addCleanup(backend.cleanup)
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(QUrl.fromLocalFile(str(installer.QML_DIR / "PackageInstaller.qml")))
        self.assertTrue(engine.rootObjects(), MESSAGES)
        self.addCleanup(engine.deleteLater)
        APP.processEvents()
        window = engine.rootObjects()[0]
        window.grabWindow()
        return backend, window

    def problems(self):
        return [m for m in MESSAGES if "qml" in m.lower() or "warning" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower()]

    def calls(self):
        path = self.folder / "calls"
        return path.read_text().splitlines() if path.exists() else []

    def test_install_and_open(self):
        deb = build_deb(self.folder)
        backend, window = self.open(deb)
        t = backend.texts
        self.assertEqual(backend.page, "ready")
        self.assertEqual(backend.title, t["pkg_install_q"].replace("{name}", "Hello World"))
        self.assertIn(t["pkg_publisher"].replace("{value}", "Hello Publisher"), backend.details)
        self.assertEqual(backend.primaryText, t["install"])
        self.assertTrue(backend.iconUrl.endswith("hello-world.svg"))
        backend.install()
        self.assertEqual(backend.page, "working")
        # The package's files appear while pkcon installs it.
        (self.applications / "hello-world.desktop").write_text(DESKTOP)
        self.assertTrue(wait(lambda: backend.page != "working"))
        self.assertEqual(backend.page, "done")
        self.assertEqual(self.calls(), [f"-p --allow-untrusted install-local {deb}"])
        # "Launch when ready" (on by default) opened the app.
        self.assertEqual(self.started, [["gtk-launch", "hello-world"]])
        self.assertEqual(backend.title, t["pkg_done_title"].replace("{name}", "Hello World"))
        self.assertEqual(len(backend.apps), 1)
        window.grabWindow()
        self.assertEqual(self.problems(), [])

    def test_installed_and_older_versions(self):
        deb = build_deb(self.folder)
        info = debfile.read(deb)
        backend, _window = self.open(deb, reader=lambda path: dict(info, installed="1.2-1", status="same"))
        self.assertEqual(backend.primaryText, backend.texts["pkg_reinstall"])
        (self.applications / "hello-world.desktop").write_text(DESKTOP)
        self.assertEqual(len(backend.apps), 1)          # Open, as it is installed
        backend.install()
        self.assertTrue(wait(lambda: backend.page != "working"))
        self.assertEqual(self.calls(), [f"-p --allow-untrusted --allow-reinstall install-local {deb}"])
        backend, _window = self.open(deb, reader=lambda path: dict(info, installed="2.0", status="older"))
        self.assertEqual(backend.title, backend.texts["pkg_newer_installed"].replace("{name}", "Hello World"))
        self.assertIn(backend.texts["pkg_installed_version"].replace("{value}", "2.0"), backend.details)
        self.assertEqual(self.problems(), [])

    def test_failed_install_shows_details(self):
        (self.folder / "fail").write_text("")
        backend, window = self.open(build_deb(self.folder))
        backend.launch = False
        backend.install()
        self.assertTrue(wait(lambda: backend.page != "working"))
        self.assertEqual(backend.page, "failed")
        self.assertIn(backend.texts["pkg_failed_auth"], backend.body)
        self.assertIn("Fatal error", backend.log)
        backend.toggleLog()
        window.grabWindow()
        self.assertTrue(backend.showLog)
        self.assertEqual(self.started, [])
        self.assertEqual(self.problems(), [])

    def test_wrong_architecture_and_broken_file(self):
        backend, _window = self.open(build_deb(self.folder, arch="riscv64"))
        self.assertEqual(backend.page, "wrongarch")
        self.assertIn("riscv64", backend.body)
        broken = self.folder / "broken.deb"
        broken.write_bytes(b"x")
        backend, _window = self.open(broken)
        self.assertEqual((backend.page, backend.title), ("invalid", backend.texts["pkg_invalid_title"]))
        self.assertEqual(self.problems(), [])


class TurkishInstallerWindowTests(InstallerWindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
