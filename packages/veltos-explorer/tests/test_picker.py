"""The file dialog (picker.py), the "open with" window (openwith.py) and
the file chooser portal backend's request/answer mapping (portal.py).
The windows are loaded offscreen; any QML warning fails the test."""

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from veltos_explorer import openwith, picker, portal  # noqa: E402

try:
    from PySide6.QtCore import QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class DecisionTests(unittest.TestCase):
    """What the accept button does, without any window."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        (self.folder / "a.txt").write_text("a")
        (self.folder / "b.txt").write_text("b")
        (self.folder / "Sub").mkdir()
        self.text = {"name": "Text", "patterns": ["*.txt"], "mimes": []}

    def test_open(self):
        f = str(self.folder)
        self.assertEqual(picker.decide("open", f, "a.txt", [], False), ("paths", [str(self.folder / "a.txt")]))
        self.assertEqual(picker.decide("open", f, '"a.txt" "b.txt"', [], True),
                         ("paths", [str(self.folder / "a.txt"), str(self.folder / "b.txt")]))
        self.assertEqual(picker.decide("open", f, '"a.txt" "b.txt"', [], False), ("paths", [str(self.folder / "a.txt")]))
        self.assertEqual(picker.decide("open", f, "Sub", [], False), ("navigate", str(self.folder / "Sub")))
        self.assertEqual(picker.decide("open", f, "missing.txt", [], False), ("error", "file_not_found"))
        selected = [{"path": str(self.folder / "b.txt"), "isDir": False}, {"path": str(self.folder / "Sub"), "isDir": True}]
        self.assertEqual(picker.decide("open", f, "", selected, False), ("paths", [str(self.folder / "b.txt")]))
        self.assertEqual(picker.decide("open", f, "", [], False), ("error", "file_name_missing"))
        self.assertEqual(picker.decide("open", "/elsewhere", str(self.folder / "a.txt"), [], False),
                         ("paths", [str(self.folder / "a.txt")]))

    def test_save(self):
        f = str(self.folder)
        self.assertEqual(picker.decide("save", f, "new", [], False, self.text), ("paths", [str(self.folder / "new.txt")]))
        self.assertEqual(picker.decide("save", f, "a.txt", [], False, self.text), ("confirm", str(self.folder / "a.txt")))
        self.assertEqual(picker.decide("save", f, "a", [], False, self.text), ("confirm", str(self.folder / "a.txt")))
        self.assertEqual(picker.decide("save", f, "Sub", [], False, self.text), ("navigate", str(self.folder / "Sub")))
        self.assertEqual(picker.decide("save", f, "", [], False, self.text), ("error", "file_name_missing"))
        self.assertEqual(picker.decide("save", f, "nowhere/x.txt", [], False, self.text), ("error", "folder_not_found"))
        everything = {"name": "All", "patterns": ["*"], "mimes": []}
        self.assertEqual(picker.decide("save", f, "noext", [], False, everything), ("paths", [str(self.folder / "noext")]))

    def test_folder(self):
        f = str(self.folder)
        self.assertEqual(picker.decide("folder", f, "", [], False), ("paths", [f]))
        sub = [{"path": str(self.folder / "Sub"), "isDir": True}]
        self.assertEqual(picker.decide("folder", f, "", sub, False), ("paths", [str(self.folder / "Sub")]))
        self.assertEqual(picker.decide("folder", f, "Sub", [], False), ("paths", [str(self.folder / "Sub")]))
        self.assertEqual(picker.decide("folder", f, "Nope", [], False), ("error", "folder_not_found"))

    def test_filters_and_names(self):
        filters = picker.normalise_filters([{"name": "Pictures", "patterns": ["*.PNG", "*.jpg"]},
                                            {"patterns": ["*.txt"]}, "junk"], "All files")
        self.assertEqual([f["name"] for f in filters], ["Pictures", "*.txt"])
        self.assertEqual(picker.normalise_filters(None, "All files"), [{"name": "All files", "patterns": ["*"], "mimes": []}])
        self.assertTrue(picker.matches({"name": "Photo.png", "isDir": False, "mime": "image/png"}, filters[0]))
        self.assertFalse(picker.matches({"name": "notes.txt", "isDir": False, "mime": "text/plain"}, filters[0]))
        self.assertTrue(picker.matches({"name": "Sub", "isDir": True, "mime": ""}, filters[0]))
        by_mime = {"name": "Images", "patterns": [], "mimes": ["image/*"]}
        self.assertTrue(picker.matches({"name": "x.webp", "isDir": False, "mime": "image/webp"}, by_mime))
        self.assertFalse(picker.matches({"name": "x.txt", "isDir": False, "mime": "text/plain"}, by_mime))
        self.assertEqual(picker.split_names('"one two.txt" "three.txt"'), ["one two.txt", "three.txt"])
        self.assertEqual(picker.split_names("  plain name.txt "), ["plain name.txt"])
        self.assertEqual(picker.split_names(""), [])
        self.assertEqual(picker.default_suffix({"patterns": ["*.txt", "*.TXT"]}), ".txt")
        self.assertEqual(picker.default_suffix({"patterns": ["*.jpg", "*.png"]}), "")

    def test_start_folder(self):
        documents = self.folder / "Documents"
        documents.mkdir()
        self.assertEqual(picker.start_folder({"current_folder": str(self.folder / "Sub")}), str(self.folder / "Sub"))
        self.assertEqual(picker.start_folder({"current_file": str(self.folder / "Sub" / "x.txt")}), str(self.folder / "Sub"))

        class Prefs:
            def get(self, _key, default=None):
                return str(documents)
        self.assertEqual(picker.start_folder({"current_folder": "/does/not/exist"}, Prefs()), str(documents))


class FakeInvocation:
    def __init__(self):
        self.replies = []

    def return_value(self, value):
        self.replies.append(value)


class FakeVariant:
    def __init__(self, signature, value):
        self.signature, self.value = signature, value

    def unpack(self):
        return self.value


class FakeGLib:
    PRIORITY_DEFAULT = 0
    Variant = FakeVariant

    def __init__(self):
        self.watches = []

    def child_watch_add(self, _priority, pid, callback):
        self.watches.append((pid, callback))


class FakeGio:
    class DBusNodeInfo:
        @staticmethod
        def new_for_xml(_xml):
            class Node:
                interfaces = [None]
            return Node()


class FakeConnection:
    def __init__(self):
        self.registered = {}
        self.next_id = 1

    def register_object(self, path, _iface, *_args):
        self.registered[self.next_id] = path
        self.next_id += 1
        return self.next_id - 1

    def unregister_object(self, registration):
        self.registered.pop(registration, None)


class FakeProcess:
    """A dialog process that answers when `end` is called."""
    instances = []

    def __init__(self, *_args, **_kwargs):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO()
        self.pid = 1000 + len(FakeProcess.instances)
        self.returncode = None
        self.terminated = False
        FakeProcess.instances.append(self)

    def end(self, answer):
        self.stdout = io.StringIO(json.dumps(answer))
        self.returncode = 0

    def poll(self):
        return self.returncode

    def wait(self):
        return 0

    def terminate(self):
        self.terminated = True
        self.returncode = -15


class PortalServiceTests(unittest.TestCase):
    """The backend object with stand-ins for GDBus: identical requests of
    one window share one dialog (LibreOffice asks twice per Ctrl+O)."""

    def setUp(self):
        FakeProcess.instances = []
        self.glib = FakeGLib()
        self.connection = FakeConnection()
        self.original_popen = portal.subprocess.Popen
        portal.subprocess.Popen = FakeProcess
        # The session's language comes from systemd (session_environment,
        # tested in test_portal_theme); not asked here.
        self.original_environment = portal.session_environment
        portal.session_environment = lambda: dict(os.environ)
        self.service = portal.Service(None, self.connection, FakeGio, self.glib)

    def tearDown(self):
        portal.subprocess.Popen = self.original_popen
        portal.session_environment = self.original_environment

    def call(self, handle, title, parent="wayland:1", method="OpenFile", options=None):
        invocation = FakeInvocation()
        self.service.handle_call(None, ":1.5", "/", "", method,
                                 FakeVariant("(ossa{sv})", (handle, "", parent, title, options or {})), invocation)
        return invocation

    def test_identical_requests_share_one_dialog(self):
        first = self.call("/req/1", "Open")
        second = self.call("/req/2", "Open")
        other = self.call("/req/3", "Save As", method="SaveFile")
        self.assertEqual(len(FakeProcess.instances), 2)             # one dialog for the twins, one for Save As
        FakeProcess.instances[0].end({"paths": ["/home/velt/a.txt"], "filter": 0})
        self.glib.watches[0][1](FakeProcess.instances[0].pid, 0)
        self.assertEqual(first.replies[0].value[0], portal.SUCCESS)
        self.assertEqual(second.replies[0].value[0], portal.SUCCESS)
        self.assertEqual(second.replies[0].value[1]["uris"].value, ["file:///home/velt/a.txt"])
        self.assertEqual(other.replies, [])                           # still open
        # Only the Save As request object is left (besides the portal object itself).
        self.assertEqual([p for p in self.connection.registered.values() if p.startswith("/req/")], ["/req/3"])

    def test_closing_one_request_keeps_the_dialog_for_the_other(self):
        first = self.call("/req/1", "Open")
        second = self.call("/req/2", "Open")
        close = FakeInvocation()
        self.service.close_request("/req/1", None, ":1.5", "/req/1", "", "Close", None, close)
        self.assertEqual(first.replies[0].value[0], portal.CANCELLED)
        self.assertFalse(FakeProcess.instances[0].terminated)        # the second request still waits
        self.service.close_request("/req/2", None, ":1.5", "/req/2", "", "Close", None, FakeInvocation())
        self.assertTrue(FakeProcess.instances[0].terminated)
        self.assertEqual(second.replies[0].value[0], portal.CANCELLED)
        self.assertEqual(close.replies, [None])


class PortalTests(unittest.TestCase):
    def test_open_file_request_and_results(self):
        options = {"multiple": True, "accept_label": "_Pick",
                   "filters": [("Pictures", [(0, "*.png"), (1, "image/jpeg")]), ("All", [(0, "*")])],
                   "current_filter": ("All", [(0, "*")]),
                   "current_folder": list(b"/home/velt/Pictures\0")}
        request = portal.to_request("OpenFile", "Open picture", options)
        self.assertEqual(request["mode"], "open")
        self.assertTrue(request["multiple"])
        self.assertEqual(request["accept_label"], "_Pick")
        self.assertEqual(request["current_folder"], "/home/velt/Pictures")
        self.assertEqual(request["filters"][0], {"name": "Pictures", "patterns": ["*.png"], "mimes": ["image/jpeg"]})
        self.assertEqual(request["current_filter"], 1)
        code, results = portal.to_results("OpenFile", request, {"paths": ["/home/velt/Pictures/a b.png"], "filter": 0})
        self.assertEqual(code, portal.SUCCESS)
        self.assertEqual(results["uris"], ["file:///home/velt/Pictures/a%20b.png"])
        self.assertEqual(results["current_filter"], ("Pictures", [(0, "*.png"), (1, "image/jpeg")]))
        self.assertEqual(portal.to_results("OpenFile", request, {"paths": []}), (portal.CANCELLED, {}))
        folder = portal.to_request("OpenFile", "", {"directory": True})
        self.assertEqual(folder["mode"], "folder")

    def test_save_requests(self):
        request = portal.to_request("SaveFile", "Save", {"current_name": "notes.txt",
                                                         "current_file": b"/home/velt/old.txt\0"})
        self.assertEqual((request["mode"], request["current_name"], request["current_file"]),
                         ("save", "notes.txt", "/home/velt/old.txt"))
        many = portal.to_request("SaveFiles", "Save", {"files": [b"one.txt\0", b"two.txt\0"]})
        self.assertEqual(many["mode"], "folder")
        code, results = portal.to_results("SaveFiles", many, {"paths": ["/tmp/out"]})
        self.assertEqual((code, results["uris"]), (portal.SUCCESS, ["file:///tmp/out/one.txt", "file:///tmp/out/two.txt"]))


class OpenWithTests(unittest.TestCase):
    def test_default_app_is_recorded_keeping_the_file(self):
        home = Path(tempfile.mkdtemp())
        (home / "mimeapps.list").write_text("[Added Associations]\ntext/html=x.desktop;\n\n"
                                            "[Default Applications]\nimage/png=old.desktop;\n")
        self.assertTrue(openwith.set_default_app("image/png", "veltos-photos.desktop", home))
        self.assertTrue(openwith.set_default_app("text/plain", "veltos-notepad.desktop", home))
        text = (home / "mimeapps.list").read_text()
        self.assertIn("[Added Associations]\ntext/html=x.desktop;", text)
        self.assertIn("image/png=veltos-photos.desktop;", text)
        self.assertNotIn("old.desktop", text)
        self.assertIn("text/plain=veltos-notepad.desktop;", text)
        self.assertFalse(openwith.set_default_app("text/plain", "../evil.desktop", home))


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class PickerWindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.home = Path(tempfile.mkdtemp())
        os.environ["HOME"] = str(cls.home)
        os.environ["XDG_CONFIG_HOME"] = str(cls.home / ".config")
        os.environ["XDG_DATA_HOME"] = str(cls.home / ".local/share")
        os.environ["XDG_CACHE_HOME"] = str(cls.home / ".cache")
        for name in ("Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"):
            (cls.home / name).mkdir()
        (cls.home / "Documents" / "report.txt").write_text("hello", encoding="utf-8")
        (cls.home / "Documents" / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (cls.home / "Documents" / "Old").mkdir()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        QGuiApplication.clipboard().clear()
        cls.app.processEvents()
        qInstallMessageHandler(None)

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def open_picker(self, request):
        from veltos_explorer import app as explorer, places
        places.HOME = self.home
        self.messages.clear()
        self.out = io.StringIO()
        self.picker = picker.Picker(request, lang=self.lang, out=self.out)
        self.backend = explorer.Backend(lang=self.lang, threaded=False,
                                        start=lambda command, cwd=None: None,
                                        runner=lambda command, timeout=20: (1, ""),
                                        open_paths=[request.get("current_folder", str(self.home / "Documents"))],
                                        item_filter=self.picker.filter_items)
        self.backend.picker = self.picker
        self.picker.backend = self.backend
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.rootContext().setContextProperty("picker", self.picker)
        self.engine.load(QUrl.fromLocalFile(str(explorer.QML_DIR / "Picker.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    def tearDown(self):
        # The window goes first and at once (Python owns the engine), then
        # the objects it showed; otherwise bindings on a dropped picker
        # print "Cannot read property of null" during the next test.
        self.window = None
        self.engine = None
        self.app.processEvents()
        self.backend.deleteLater()
        self.app.processEvents()
        self.picker = None

    def answer(self):
        return json.loads(self.out.getvalue().strip().splitlines()[-1])

    def test_open_filters_and_double_click(self):
        self.open_picker({"mode": "open", "current_folder": str(self.home / "Documents"),
                          "filters": [{"name": "Text", "patterns": ["*.txt"]}, {"name": "All files", "patterns": ["*"]}]})
        tab = self.backend.current
        self.assertEqual(tab.kind, "folder")
        self.assertEqual([i["name"] for i in tab.items.items], ["Old", "report.txt"])   # photo.png filtered out
        self.assertEqual(self.window.property("title"), "Open")
        self.picker.setFilter(1)
        self.app.processEvents()
        self.assertEqual([i["name"] for i in tab.items.items], ["Old", "photo.png", "report.txt"])
        tab.items.select(2, "single")
        self.app.processEvents()
        self.assertEqual(self.picker.selectionText(), "report.txt")
        self.backend.openSelection()                   # a double-click: the answer
        self.assertEqual(self.answer(), {"paths": [str(self.home / "Documents" / "report.txt")], "filter": 1})
        self.assertEqual(self.problems(), [])

    def test_save_asks_before_replacing(self):
        self.open_picker({"mode": "save", "current_name": "report.txt",
                          "current_folder": str(self.home / "Documents")})
        asked = []
        self.picker.confirmReplace.connect(lambda path, name: asked.append((path, name)))
        self.assertEqual(self.window.property("title"), "Save As")
        self.picker.accept("report.txt")
        self.assertEqual(asked, [(str(self.home / "Documents" / "report.txt"), "report.txt")])
        self.picker.accept("fresh.txt")
        self.assertEqual(self.answer()["paths"], [str(self.home / "Documents" / "fresh.txt")])
        self.assertEqual(self.problems(), [])

    def test_folder_mode_and_cancel(self):
        self.open_picker({"mode": "folder", "current_folder": str(self.home / "Documents"), "title": "Pick"})
        tab = self.backend.current
        self.assertEqual([i["name"] for i in tab.items.items], ["Old"])
        self.assertEqual(self.window.property("title"), "Pick")
        self.picker.accept("")
        self.assertEqual(self.answer(), {"paths": [str(self.home / "Documents")], "filter": 0})
        self.open_picker({"mode": "open"})
        self.picker.cancel()
        self.assertEqual(self.answer(), {"paths": []})
        self.assertEqual(self.problems(), [])


class TurkishPickerWindowTests(PickerWindowTests):
    lang = "tr"

    def test_open_filters_and_double_click(self):
        self.open_picker({"mode": "open", "current_folder": str(self.home / "Documents")})
        self.assertEqual(self.window.property("title"), "Aç")
        self.assertEqual(self.picker.acceptLabel, "Aç")
        self.assertEqual(self.picker.filterNames, ["Tüm dosyalar"])
        self.assertEqual(self.problems(), [])

    def test_save_asks_before_replacing(self):
        self.open_picker({"mode": "save"})
        self.assertEqual(self.window.property("title"), "Farklı Kaydet")
        self.assertEqual(self.problems(), [])

    def test_folder_mode_and_cancel(self):
        self.open_picker({"mode": "folder"})
        self.assertEqual(self.window.property("title"), "Klasör Seç")
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class OpenWithWindowTests(unittest.TestCase):
    def test_window_lists_apps_and_opens(self):
        from veltos_explorer import places
        home = Path(tempfile.mkdtemp())
        apps = home / "applications"
        apps.mkdir()
        (apps / "editor.desktop").write_text("[Desktop Entry]\nType=Application\nName=Editor\nName[tr]=Düzenleyici\n"
                                             "Icon=text-editor\nExec=editor %f\nMimeType=text/plain;\n")
        (apps / "other.desktop").write_text("[Desktop Entry]\nType=Application\nName=Other\nExec=other %U\n")
        os.environ["XDG_DATA_DIRS"] = str(home)
        os.environ["XDG_DATA_HOME"] = str(home / "none")
        note = home / "note.txt"
        note.write_text("hi")
        started = []
        app = QGuiApplication.instance() or QGuiApplication([])
        messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: messages.append(msg))
        try:
            opener = openwith.Opener(str(note), lang="tr", start=started.append, config_home=home)
            self.assertEqual([a["id"] for a in opener.apps], ["editor.desktop"])
            self.assertEqual(opener.apps[0]["name"], "Düzenleyici")
            self.assertTrue(opener.hasMore)
            self.assertIn(".txt", opener.heading)
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("backend", opener)
            engine.rootContext().setContextProperty("opener", opener)
            engine.load(QUrl.fromLocalFile(str(openwith.QML_DIR / "OpenWith.qml")))
            app.processEvents()
            self.assertTrue(engine.rootObjects(), messages)
            opener.showMore()
            self.assertEqual([a["id"] for a in opener.apps], ["editor.desktop", "other.desktop"])
            self.assertEqual(opener.selected, 0)
            opener.open(0, True)
            self.assertEqual(started, [["editor", str(note)]])
            self.assertIn("text/plain=editor.desktop;", (home / "mimeapps.list").read_text())
            app.processEvents()
            # The window goes before the objects it shows (Python deletes
            # locals in any order; bindings on a deleted opener print errors).
            del engine
            app.processEvents()
            problems = [m for m in messages if "qml" in m.lower() or "error" in m.lower() or "warning" in m.lower()]
            self.assertEqual(problems, [])
        finally:
            qInstallMessageHandler(None)
            places.HOME = Path.home()


if __name__ == "__main__":
    unittest.main()
