"""Loads the real Media Player window offscreen with a small library:
pages, playing (queue, next, repeat, shuffle), playlists, settings; any
QML warning fails the test. The Turkish class runs in the Turkish C locale
when it is installed (PySide6 keyword-argument bug, see AGENTS.md)."""

import locale
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from test_library import make_wav  # noqa: E402

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QSettings, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import mutagen  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 and mutagen (Build-Depends)")
class MediaTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        home = Path(tempfile.mkdtemp())
        os.environ["HOME"] = str(home)
        os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
        os.environ["XDG_CACHE_HOME"] = str(home / ".cache")
        cls.home = home
        album = home / "Music/Album"
        album.mkdir(parents=True)
        for n in (1, 2, 3):
            make_wav(album / f"{n:02d}.wav", 1, f"Song {n}", "Artist", "Album", n)
        (home / "Videos").mkdir()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_media import app
        self.messages.clear()
        settings = QSettings(str(self.home / f"{self.id()}.conf"), QSettings.Format.IniFormat)
        self.backend = app.Backend(lang=self.lang, settings=settings, scan=False)
        self.backend.scan_now()
        self.engine = QQmlApplicationEngine()
        self.engine.addImageProvider("thumb", app.ThumbnailProvider())
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.settle()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    def tearDown(self):
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def settle(self):
        for _ in range(20):
            self.app.processEvents()

    def problems(self):
        # Offscreen test machines have no sound device; Qt Multimedia says so.
        return [m for m in self.messages if ("qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()) and "audio" not in m.lower()
                and "pulse" not in m.lower() and "alsa" not in m.lower()]

    def test_pages_load(self):
        for page in ("home", "music", "videos", "queue", "playlists", "settings", "search:song"):
            self.window.setProperty("page", page)
            self.settle()
        self.assertEqual(len(self.backend.songs), 3)
        self.assertEqual([a["title"] for a in self.backend.albums], ["Album"])
        self.assertEqual(len(self.backend.search("song 2")), 1)
        self.assertEqual(self.problems(), [])

    def test_playing_the_queue(self):
        paths = [s["path"] for s in self.backend.songs]
        self.backend.playPaths(paths, 1)
        self.settle()
        self.assertEqual(self.backend.current["title"], "Song 2")
        token = self.backend.playToken
        self.backend.next()
        self.assertEqual(self.backend.current["title"], "Song 3")
        self.assertGreater(self.backend.playToken, token)
        self.assertFalse(self.backend.ended())              # end of the queue, repeat off
        self.backend.cycleRepeat()
        self.assertEqual(self.backend.repeat, "all")
        self.assertTrue(self.backend.ended())
        self.assertEqual(self.backend.current["title"], "Song 1")
        self.backend.setShuffle(True)
        self.assertEqual(self.backend.queueItems[0]["title"], "Song 1")
        self.backend.addToQueue([paths[0]])
        self.assertEqual(len(self.backend.queueItems), 4)
        self.assertEqual(self.backend.recent[0]["title"], "Song 1")
        self.window.setProperty("page", "queue")
        self.settle()
        self.assertEqual(self.problems(), [])

    def test_playlists_and_volume(self):
        name = self.backend.createPlaylist("Road trip")
        self.assertEqual(name, "Road trip")
        self.assertEqual(self.backend.createPlaylist("Road trip"), "Road trip (2)")
        self.backend.addToPlaylist(name, [s["path"] for s in self.backend.songs[:2]])
        self.assertEqual([len(p["items"]) for p in self.backend.playlists], [2, 0])
        self.window.setProperty("page", "playlist:Road trip")
        self.settle()
        self.backend.removeFromPlaylist(name, 0)
        self.backend.deletePlaylist("Road trip (2)")
        self.assertEqual([(p["name"], len(p["items"])) for p in self.backend.playlists], [("Road trip", 1)])
        self.backend.setVolume(35)
        self.backend.setMuted(True)
        self.assertEqual((self.backend.volume, self.backend.muted), (35, True))
        self.settle()
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 and mutagen (Build-Depends)")
class TurkishMediaTests(MediaTests):
    lang = "tr"

    @classmethod
    def setUpClass(cls):
        try:
            locale.setlocale(locale.LC_ALL, "tr_TR.UTF-8")
        except locale.Error:
            pass
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        locale.setlocale(locale.LC_ALL, "C")


if __name__ == "__main__":
    unittest.main()
