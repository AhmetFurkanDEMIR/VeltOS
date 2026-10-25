"""VeltOS Store window (offscreen, English and Turkish) and install jobs
with a stand-in for pkcon."""

import os
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QML_DISABLE_DISK_CACHE"] = "1"

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from veltos_store import app as store  # noqa: E402
from veltos_store import packages  # noqa: E402

from test_catalog import ENTRIES  # noqa: E402

APP = QGuiApplication.instance() or QGuiApplication([])
MESSAGES = []
qInstallMessageHandler(lambda _type, _context, message: MESSAGES.append(message))


def wait(condition, timeout=5000):
    loop = QEventLoop()
    timer = QTimer()
    timer.timeout.connect(lambda: loop.quit() if condition() else None)
    timer.start(20)
    QTimer.singleShot(timeout, loop.quit)
    loop.exec()
    timer.stop()
    return condition()


def details(app_id):
    return {"description": "<p>A <em>fine</em> app.</p>", "screenshots": []}


class FakeJobs(packages.Jobs):
    """Records jobs instead of running pkcon."""

    def __init__(self):
        super().__init__()
        self.added = []

    def add(self, action, package):
        self.added.append((action, package))


class WindowTests(unittest.TestCase):
    def make_backend(self, lang, installed=frozenset({"vlc"}), jobs=None):
        return store.Backend(lang=lang, loader=lambda: (ENTRIES, details), installed=lambda: set(installed),
                             jobs=jobs, start=self.started.append, update_checker=lambda: 3, background=False,
                             refresher=lambda: False, protected=lambda pkg: pkg == "firefox-esr",
                             names=lambda entries, lang: entries)

    def setUp(self):
        self.started = []
        MESSAGES.clear()

    def tearDown(self):
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        APP.processEvents()

    def load(self, backend):
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(QUrl.fromLocalFile(str(store.QML_DIR / "Main.qml")))
        self.assertTrue(engine.rootObjects(), MESSAGES)
        APP.processEvents()
        return engine, engine.rootObjects()[0]

    def test_pages_load_without_warnings(self):
        for lang in ("en", "tr"):
            backend = self.make_backend(lang)
            engine, window = self.load(backend)
            self.assertEqual(window.property("title"), "VeltOS Mağaza" if lang == "tr" else "VeltOS Store")
            for page in ("apps", "games", "library", "home"):
                window.setProperty("page", page)
                APP.processEvents()
            window.setProperty("query", "ink")
            window.setProperty("page", "search")
            APP.processEvents()
            window.setProperty("openApp", "org.gimp.GIMP")
            APP.processEvents()
            window.setProperty("openApp", "")
            APP.processEvents()
            problems = [m for m in MESSAGES if "qml" in m.lower() or "error" in m.lower()
                        or "warning" in m.lower() or "undefined" in m.lower() or "TypeError" in m]
            self.assertEqual(problems, [], lang)
            # Bindings complain about the missing context while the engine is
            # torn down; that is not the window's fault.
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            del engine
            MESSAGES.clear()

    def test_home_states_and_actions(self):
        jobs = FakeJobs()
        backend = self.make_backend("en", jobs=jobs)
        home = backend.home
        self.assertTrue(home["hero"])
        self.assertIn("start", home["hero"][0])
        self.assertEqual(backend.state("vlc", 0), "installed")
        self.assertEqual(backend.state("gimp", 0), "")
        self.assertEqual([a["pkg"] for a in backend.library], ["vlc"])
        backend.install("gimp")
        backend.uninstall("vlc")
        backend.uninstall("firefox-esr")      # part of VeltOS: refused
        self.assertTrue(wait(lambda: len(jobs.added) == 2 and backend.isProtected("firefox-esr", 0)))
        self.assertEqual(jobs.added, [("install", "gimp"), ("remove", "vlc")])
        backend.open("org.videolan.vlc")
        self.assertEqual(self.started, [["gtk-launch", "org.videolan.vlc"]])
        page = backend.details("org.gimp.GIMP")
        self.assertEqual(page["developer"], "Community")
        self.assertIn("<em>fine</em>", page["description"])

    def test_failed_install_is_reported(self):
        jobs = FakeJobs()
        backend = self.make_backend("en", jobs=jobs)
        backend._job_finished("install", "gimp", False)
        self.assertEqual(backend.state("gimp", 0), "failed")
        backend.install("gimp")
        self.assertEqual(backend.state("gimp", 0), "")

    def test_refused_uninstall_keeps_the_app_installed(self):
        # The password prompt cancelled while uninstalling: the app stays
        # installed (Open / Uninstall), with the reason for the uninstall.
        jobs = FakeJobs()
        backend = self.make_backend("en", jobs=jobs)
        jobs.error = "Fatal error: Failed to obtain authentication."
        backend._job_finished("remove", "vlc", False)
        self.assertEqual(backend.state("vlc", 0), "installed")
        self.assertTrue(backend.hasFailure("vlc", 0))
        self.assertIn("to uninstall", backend.failureText("vlc", 0))
        backend._job_finished("install", "gimp", False)
        self.assertIn("to install", backend.failureText("gimp", 0))

    def test_old_catalogue_is_refreshed_and_reloaded(self):
        loads = []

        def loader():
            loads.append(1)
            return (ENTRIES[:len(loads)], details)

        backend = store.Backend(lang="en", loader=loader, installed=set, background=False,
                                refresher=lambda: True, names=lambda entries, lang: entries)
        self.assertEqual(len(loads), 2)
        self.assertEqual(backend.appCount, 2)

    def test_update_check(self):
        backend = self.make_backend("en")
        backend.checkUpdates()
        self.assertTrue(wait(lambda: backend.updates == 3))
        self.assertFalse(backend.checkingUpdates)


class JobTests(unittest.TestCase):
    def test_jobs_run_one_after_another(self):
        tmp = Path(tempfile.mkdtemp())
        fake = tmp / "pkcon"
        fake.write_text("#!/bin/sh\n"
                        "echo \"$*\" >> \"$(dirname \"$0\")/calls\"\n"
                        "printf 'Status: \\tDownloading packages\\nPercentage:\\t50\\n'\n"
                        "sleep 0.2\n"
                        "printf 'Percentage:\\t100\\n'\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        jobs = packages.Jobs(program=str(fake), needs_refresh=lambda: False)
        done = []
        jobs.finished.connect(lambda action, package, ok: done.append((action, package, ok)))
        jobs.add("install", "gimp")
        jobs.add("install", "gimp")          # already queued: ignored
        jobs.add("remove", "vlc")
        self.assertEqual(jobs.state("vlc"), "waiting")
        self.assertTrue(wait(lambda: jobs.percent == 50 or len(done) > 0))
        self.assertTrue(wait(lambda: len(done) == 2))
        self.assertEqual(done, [("install", "gimp", True), ("remove", "vlc", True)])
        self.assertEqual((tmp / "calls").read_text().splitlines(),
                         ["-p install gimp", "-p remove vlc"])

    def test_old_lists_are_refreshed_before_an_install(self):
        tmp = Path(tempfile.mkdtemp())
        fake = tmp / "pkcon"
        fake.write_text("#!/bin/sh\necho \"$*\" >> \"$(dirname \"$0\")/calls\"\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        jobs = packages.Jobs(program=str(fake), needs_refresh=lambda: True)
        done = []
        jobs.finished.connect(lambda action, package, ok: done.append(action))
        jobs.add("install", "gimp")
        jobs.add("install", "vlc")          # one refresh for both
        self.assertEqual(jobs.state("gimp"), "refreshing")
        self.assertTrue(wait(lambda: len(done) == 3))
        self.assertEqual(done, ["refresh", "install", "install"])
        self.assertEqual((tmp / "calls").read_text().splitlines(),
                         ["-p refresh", "-p install gimp", "-p install vlc"])
        lists = tmp / "lists"
        lists.mkdir()
        self.assertTrue(packages.lists_need_refresh(str(lists)))                      # no lists at all
        (lists / "deb.debian.org_debian_dists_trixie_main_binary-amd64_Packages").write_text("")
        self.assertFalse(packages.lists_need_refresh(str(lists)))
        self.assertTrue(packages.lists_need_refresh(str(lists), now=time.time() + 10 * 86400))

    def test_failure_texts(self):
        self.assertEqual(packages.failure_key("Failed to obtain authentication."), "failed_auth")
        self.assertEqual(packages.failure_key("could not find vlc"), "failed_not_found")
        self.assertEqual(packages.failure_key("Failed to fetch http://deb.debian.org/..."), "failed_network")
        self.assertEqual(packages.failure_key("Could not get lock /var/lib/dpkg/lock"), "failed_busy")
        self.assertEqual(packages.failure_key("something odd"), "")

    def test_pkcon_is_answered_in_a_terminal(self):
        # pkcon reads its confirmation from the controlling terminal; ptyrun
        # gives it one, says yes to the changes and no to anything else
        # (unsigned packages), and passes the exit code on.
        from veltos_store import ptyrun
        tmp = Path(tempfile.mkdtemp())
        fake = tmp / "pkcon"
        fake.write_text("#!/bin/sh\n"
                        "printf 'Proceed with changes? [N/y] '\n"
                        "read first < /dev/tty\n"
                        "printf 'Do you want to allow installing of unsigned software? [N/y] '\n"
                        "read second < /dev/tty\n"
                        "echo \"answers=$first,$second\"\n"
                        "exit 3\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        with tempfile.TemporaryFile() as out:
            self.assertEqual(ptyrun.run([str(fake)], out), 3)
            out.seek(0)
            self.assertIn(b"answers=y,n", out.read())
        self.assertIsNone(ptyrun.answer_for(b"Percentage:\t40\n"))

    def test_missing_pkcon(self):
        jobs = packages.Jobs(program="/nonexistent/pkcon")
        done = []
        jobs.finished.connect(lambda action, package, ok: done.append(ok))
        jobs.add("install", "gimp")
        self.assertTrue(wait(lambda: done == [False]))


if __name__ == "__main__":
    unittest.main()
