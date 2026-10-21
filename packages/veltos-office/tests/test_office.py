"""Tests of the VeltOS Office start screen: texts in both languages,
LibreOffice's recent list, pins and options, the template catalogue with
thumbnails, the LibreOffice command lines, and the window loaded offscreen
in English and Turkish for each app (any QML warning fails)."""

import datetime
import os
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_office import recent, strings, templates  # noqa: E402

XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Common/Misc"><prop oor:name="FirstRun" oor:op="fuse"><value>false</value></prop></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/ItemList"><node oor:name="file:///{home}/Documents/Letter%20to%20Ada.docx" oor:op="replace"><prop oor:name="Title" oor:op="fuse"><value>Letter to Ada</value></prop><prop oor:name="Filter" oor:op="fuse"><value>MS Word 2007 XML</value></prop></node></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/ItemList"><node oor:name="file:///{home}/Documents/budget.xlsx" oor:op="replace"><prop oor:name="Title" oor:op="fuse"><value>budget</value></prop><prop oor:name="Filter" oor:op="fuse"><value>Calc MS Excel 2007 XML</value></prop></node></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/ItemList"><node oor:name="file:///{home}/Documents/notes.txt" oor:op="replace"><prop oor:name="Title" oor:op="fuse"><value>notes</value></prop><prop oor:name="Filter" oor:op="fuse"><value>Text</value></prop></node></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/ItemList"><node oor:name="file:///{home}/Documents/gone.docx" oor:op="replace"><prop oor:name="Title" oor:op="fuse"><value>gone</value></prop><prop oor:name="Filter" oor:op="fuse"><value>MS Word 2007 XML</value></prop></node></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/OrderList"><node oor:name="0" oor:op="replace"><prop oor:name="HistoryItemRef" oor:op="fuse"><value>file:///{home}/Documents/notes.txt</value></prop></node></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/OrderList"><node oor:name="1" oor:op="replace"><prop oor:name="HistoryItemRef" oor:op="fuse"><value>file:///{home}/Documents/Letter%20to%20Ada.docx</value></prop></node></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/OrderList"><node oor:name="2" oor:op="replace"><prop oor:name="HistoryItemRef" oor:op="fuse"><value>file:///{home}/Documents/budget.xlsx</value></prop></node></item>
<item oor:path="/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/OrderList"><node oor:name="3" oor:op="replace"><prop oor:name="HistoryItemRef" oor:op="fuse"><value>file:///{home}/Documents/gone.docx</value></prop></node></item>
</oor:items>
"""

NOW = datetime.datetime(2026, 10, 21, 15, 30)


def png(width=4, height=4, colour=(24, 90, 189)):
    """A real (tiny) PNG, so QML can decode the thumbnail."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(colour) * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def make_template(path, with_thumbnail=True, member="Thumbnails/thumbnail.png"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.text-template")
        archive.writestr("content.xml", "<x/>")
        if with_thumbnail:
            archive.writestr(member, png())


TEMPLATE_SUFFIX = {"word": ".ott", "sheet": ".ots", "slides": ".otp"}


class TextTests(unittest.TestCase):
    def test_every_key_in_both_languages(self):
        for key, pair in strings.TEXTS.items():
            self.assertEqual(len(pair), 2, key)
            self.assertTrue(pair[0] and pair[1], key)
        for stem, pair in strings.TEMPLATE_NAMES.items():
            self.assertTrue(pair[0] and pair[1], stem)
        self.assertEqual(strings.template_name("tr", "Monthly_budget"), "Aylık bütçe")
        self.assertEqual(strings.template_name("en", "Some_new-file"), "Some new file")

    def test_language(self):
        self.assertEqual(strings.language({"LANGUAGE": "tr_TR:en"}), "tr")
        self.assertEqual(strings.language({"LANG": "en_US.UTF-8"}), "en")
        self.assertEqual(strings.language({}), "en")


class RecentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / "Documents").mkdir(parents=True)
        for name in ("Letter to Ada.docx", "budget.xlsx", "notes.txt"):
            (self.home / "Documents" / name).write_text("x")
        self.xcu = self.home / "registrymodifications.xcu"
        # file:///home/... on Linux, file:///C:/... on a Windows host.
        self.xcu.write_text(XCU.replace("file:///{home}", self.home.as_uri()), encoding="utf-8")
        self.store = recent.Store(self.home / "office" / "word.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_picklist_order_and_kinds(self):
        items = recent.picklist(self.xcu)
        self.assertEqual([Path(i["path"]).name for i in items], ["notes.txt", "Letter to Ada.docx", "budget.xlsx", "gone.docx"])
        self.assertEqual(recent.kind_of(items[1]["path"], items[1]["filter"]), "word")
        self.assertEqual(recent.kind_of(items[2]["path"]), "sheet")
        self.assertEqual(recent.kind_of("/x/y.pptx"), "slides")
        self.assertEqual(recent.kind_of("/x/y.unknown", "Impress MS PowerPoint 2007 XML"), "slides")
        self.assertEqual(recent.kind_of("/x/y.unknown"), "")
        self.assertEqual(recent.picklist(self.home / "missing.xcu"), [])

    def test_recent_files_of_an_app(self):
        files = recent.recent_files("word", "en", self.store, xcu_path=self.xcu, now=NOW, home=self.home)
        self.assertEqual([f["name"] for f in files], ["notes.txt", "Letter to Ada.docx"])   # gone.docx is gone
        self.assertEqual(files[0]["folder"], "~" + os.sep + "Documents")
        self.assertEqual(files[0]["icon"], "x-office-document")
        self.assertFalse(files[0]["pinned"])
        sheets = recent.recent_files("sheet", "en", self.store, xcu_path=self.xcu, now=NOW, home=self.home)
        self.assertEqual([f["name"] for f in sheets], ["budget.xlsx"])

    def test_own_opened_files_come_first_and_pins_are_kept(self):
        mine = self.home / "Documents" / "mine.odt"
        mine.write_text("x")
        self.store.note_opened(str(mine))
        self.store.pin(str(self.home / "Documents" / "Letter to Ada.docx"))
        files = recent.recent_files("word", "en", self.store, xcu_path=self.xcu, now=NOW, home=self.home)
        self.assertEqual([f["name"] for f in files], ["mine.odt", "notes.txt", "Letter to Ada.docx"])
        self.assertTrue(files[2]["pinned"])
        again = recent.Store(self.store.path)
        self.assertEqual(again.pinned, [str(self.home / "Documents" / "Letter to Ada.docx")])
        self.assertTrue(again.show_home)
        again.set_show_home(False)
        self.assertFalse(recent.Store(self.store.path).show_home)
        again.forget(str(mine))
        self.assertEqual(again.own_recent(), [])

    def test_modified_texts(self):
        self.assertEqual(recent.modified_text(NOW - datetime.timedelta(minutes=12), "en", NOW), "12m ago")
        self.assertEqual(recent.modified_text(NOW - datetime.timedelta(minutes=12), "tr", NOW), "12 dk önce")
        self.assertEqual(recent.modified_text(NOW - datetime.timedelta(hours=3), "en", NOW), "3h ago")
        self.assertEqual(recent.modified_text(NOW - datetime.timedelta(days=1), "en", NOW), "Yesterday at 3:30 PM")
        self.assertEqual(recent.modified_text(NOW - datetime.timedelta(days=1), "tr", NOW), "Dün 15:30")
        self.assertEqual(recent.modified_text(NOW - datetime.timedelta(days=2), "en", NOW), "Monday at 3:30 PM")
        self.assertEqual(recent.modified_text(datetime.datetime(2026, 9, 3, 9, 0), "en", NOW), "September 3")
        self.assertEqual(recent.modified_text(datetime.datetime(2025, 9, 3, 9, 0), "tr", NOW), "3 Eylül 2025")
        self.assertEqual(recent.group_of(NOW - datetime.timedelta(days=2), NOW), "this_week")
        self.assertEqual(recent.group_of(NOW - datetime.timedelta(days=5), NOW), "last_week")
        self.assertEqual(recent.group_of(NOW - datetime.timedelta(days=40), NOW), "older")


class TemplateTests(unittest.TestCase):
    def test_catalogue_with_thumbnails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_template(root / "veltos/Meeting_notes.ott")
            make_template(root / "lo/personal/CV.ott")
            make_template(root / "lo/officorr/Modern_business_letter_serif.ott", with_thumbnail=False)
            make_template(root / "user/My_letter.dotx", member="docProps/thumbnail.jpeg")
            make_template(root / "user/Sheet.ots")       # not a word template
            items = templates.catalogue("word", "tr", veltos_dir=root / "veltos", libreoffice_dir=root / "lo",
                                        user_dir=root / "user", cache=root / "cache")
            self.assertEqual([i["name"] for i in items],
                             ["Toplantı notları", "Modern iş mektubu (serif)", "Özgeçmiş (CV)", "My letter"])
            self.assertEqual([i["source"] for i in items], ["veltos", "libreoffice", "libreoffice", "you"])
            self.assertTrue(items[0]["thumbnail"].startswith("file://"))
            self.assertTrue(items[0]["thumbnail"].endswith(".png"))
            self.assertEqual(items[1]["thumbnail"], "")
            self.assertTrue(items[3]["thumbnail"].endswith(".jpeg"))
            self.assertEqual(len(list((root / "cache").iterdir())), 3)
            # A second listing uses the cache.
            again = templates.catalogue("word", "en", veltos_dir=root / "veltos", libreoffice_dir=root / "lo",
                                        user_dir=root / "user", cache=root / "cache")
            self.assertEqual(again[0]["thumbnail"], items[0]["thumbnail"])
            self.assertEqual([i["name"] for i in templates.search(again, "cv")], ["Curriculum vitae"])
            self.assertEqual(templates.search(again, ""), again)


class CommandTests(unittest.TestCase):
    def test_launch_commands(self):
        from veltos_office import app
        self.assertEqual(app.launch_command("word"), ["libreoffice", "--nologo", "--writer"])
        self.assertEqual(app.launch_command("sheet", files=["/a.xlsx"]), ["libreoffice", "--nologo", "--calc", "/a.xlsx"])
        self.assertEqual(app.launch_command("slides", template="/t.otp"),
                         ["libreoffice", "--nologo", "--impress", "-n", "/t.otp"])
        self.assertEqual(app.parse_args(["x", "word", "--blank"]), ("word", [], True))
        self.assertEqual(app.parse_args(["x", "sheet", "a.xlsx", "b.csv"]), ("sheet", ["a.xlsx", "b.csv"], False))
        with self.assertRaises(SystemExit):
            app.parse_args(["x", "nothing"])
        self.assertEqual(app.local_path("file:///home/velt/a%20b.docx"), "/home/velt/a b.docx")
        self.assertEqual(app.greeting_key(9), "good_morning")
        self.assertEqual(app.greeting_key(13), "good_afternoon")
        self.assertEqual(app.greeting_key(20), "good_evening")
        with tempfile.TemporaryDirectory() as tmp:
            rc = Path(tmp) / "bootstraprc"
            rc.write_text("[Bootstrap]\nProductKey=LibreOffice 25.2\n")
            self.assertEqual(app.libreoffice_version(rc), "25.2")
            self.assertEqual(app.libreoffice_version(Path(tmp) / "none"), "")

    def test_make_templates_sources_are_well_formed(self):
        import importlib.util
        import xml.etree.ElementTree as ET
        tool = Path(__file__).resolve().parent.parent / "tools" / "make-templates.py"
        spec = importlib.util.spec_from_file_location("make_templates", tool)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, maker in list(module.WORD.items()) + list(module.SHEET.items()):
            root = ET.fromstring(maker().xml())
            self.assertTrue(root.tag.endswith("document"), name)
            self.assertIn(name, strings.TEMPLATE_NAMES)
        budget = module.monthly_budget().xml()
        self.assertIn('table:formula="of:=SUM([.B14:.B23])"', budget)
        self.assertIn("Monthly budget", budget)


try:
    from PySide6.QtCore import QCoreApplication, QEvent, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:  # pragma: no cover
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6")
class WindowTests(unittest.TestCase):
    lang = "en"
    kind = "word"

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower() or "warning" in m.lower()]

    def test_pages_open_and_actions_run(self):
        from veltos_office import app as office
        self.messages.clear()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            (home / "Documents").mkdir(parents=True)
            document = home / "Documents" / "Plan.docx"
            document.write_text("x")
            root = Path(tmp)
            template = root / "veltos" / ("Meeting_notes" + TEMPLATE_SUFFIX[self.kind])
            make_template(template)
            store = recent.Store(home / "office.json")
            store.note_opened(str(document))
            commands = []
            backend = office.Backend(self.kind, lang=self.lang, store=store, launcher=commands.append, home=home,
                                     xcu_path=home / "none.xcu", now=NOW,
                                     template_dirs=dict(veltos_dir=root / "veltos", libreoffice_dir=root / "lo",
                                                        user_dir=root / "user", cache=root / "cache"))
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("backend", backend)
            engine.load(QUrl.fromLocalFile(str(office.QML_DIR / "Main.qml")))
            self.app.processEvents()
            self.assertTrue(engine.rootObjects(), self.messages)
            window = engine.rootObjects()[0]
            self.assertEqual(window.property("title"), strings.app_title(self.lang, self.kind))
            self.assertEqual(backend.greeting, "İyi günler" if self.lang == "tr" else "Good afternoon")
            self.assertEqual([t["name"] for t in backend.templates], ["Toplantı notları" if self.lang == "tr" else "Meeting notes"])
            self.assertEqual([f["name"] for f in backend.recent], ["Plan.docx"] if self.kind == "word" else [])
            for page in ("new", "open", "account", "options", "home"):
                backend.setPage(page)
                self.app.processEvents()
                self.assertEqual(backend.page, page)
            backend.pin(str(document), True)
            self.assertEqual([f["name"] for f in backend.pinned], ["Plan.docx"] if self.kind == "word" else [])
            backend.newBlank()
            backend.newFromTemplate(str(template))
            backend.openFile(str(document))
            backend.openFile(str(home / "missing.docx"))
            self.app.processEvents()
            self.assertEqual(commands, [
                office.launch_command(self.kind),
                office.launch_command(self.kind, template=str(template)),
                office.launch_command(self.kind, files=[str(document)]),
            ])
            self.assertTrue(backend.busy)
            backend.setShowHome(False)
            self.assertFalse(recent.Store(store.path).show_home)
            backend.clearRecent()
            # Pinned files stay.
            self.assertEqual([f["name"] for f in backend.recent], ["Plan.docx"] if self.kind == "word" else [])
            # The engine (and the Theme singleton reading the backend) must go
            # before the backend: processEvents() alone leaves deferred
            # deletes for the exit, where the bindings then find no backend.
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.app.processEvents()
            backend.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.app.processEvents()
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6")
class TurkishSheetWindowTests(WindowTests):
    lang = "tr"
    kind = "sheet"


@unittest.skipUnless(HAVE_QT, "needs PySide6")
class SlidesWindowTests(WindowTests):
    kind = "slides"


if __name__ == "__main__":
    unittest.main()
