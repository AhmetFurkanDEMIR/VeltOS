"""File Explorer's org.freedesktop.FileManager1 service and opening a
file's folder with the file selected."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QGuiApplication
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class FileManager1Tests(unittest.TestCase):
    def test_requests_open_file_explorer(self):
        from veltos_explorer import filemanager1
        started = []
        service = filemanager1.FileManager1(start=started.append)
        service.ShowItems(["file:///home/velt/Downloads/a.zip"], "")
        service.ShowFolders(["file:///home/velt/Music"], "")
        service.ShowItemProperties([], "")
        self.assertEqual(started, [["veltos-explorer", "file:///home/velt/Downloads/a.zip"],
                                   ["veltos-explorer", "file:///home/velt/Music"]])

    def test_file_argument_selects_the_file_in_its_folder(self):
        from veltos_explorer import app as explorer
        QGuiApplication.instance() or QGuiApplication([])
        folder = Path(tempfile.mkdtemp())
        for name in ("a.txt", "b.txt", "c.txt"):
            (folder / name).write_text("x", encoding="utf-8")
        backend = explorer.Backend(lang="en", threaded=False, start=lambda *a, **k: None,
                                   runner=lambda command, timeout=20: (1, ""),
                                   open_paths=[(folder / "b.txt").as_uri()])
        tab = backend.current
        self.assertEqual(tab.location, str(folder))
        selected = [tab.items.get(r)["name"] for r in range(tab.items.count) if tab.items.get(r)["selected"]]
        self.assertEqual(selected, ["b.txt"])

    def test_dbus_service_file(self):
        text = (Path(__file__).resolve().parent.parent / "data/org.freedesktop.FileManager1.service").read_text()
        self.assertIn("Name=org.freedesktop.FileManager1", text)
        self.assertIn("Exec=/usr/bin/veltos-explorer --filemanager1", text)


if __name__ == "__main__":
    unittest.main()
