"""The Recycle Bin, deleting and starting programs without KIO's windows
(removal.py, runprogram.py; product owner, 2026-10-31: no more KDE windows
with the Wayland "W" icon)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_explorer import places, removal, runprogram, transfer  # noqa: E402


class Result:
    def __init__(self, code):
        self.returncode = code


class RemovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_trash_through_gio(self):
        item = self.dir / "a.txt"
        item.write_text("a", encoding="utf-8")
        calls = []
        self.assertEqual(removal.trash([item], run=lambda c, **k: calls.append(c) or Result(0)), [])
        self.assertEqual(calls, [["gio", "trash", "--", str(item)]])

    def test_what_cannot_be_trashed_is_returned(self):
        item = self.dir / "a.txt"
        item.write_text("a", encoding="utf-8")
        self.assertEqual(removal.trash([item], run=lambda c, **k: Result(1)), [str(item)])

        def missing_gio(*_args, **_kwargs):
            raise OSError("no gio")
        self.assertEqual(removal.trash([item], run=missing_gio), [str(item)])
        # Gone anyway (another program removed it): nothing to ask about.
        self.assertEqual(removal.trash([self.dir / "gone.txt"], run=lambda c, **k: Result(1)), [])

    def test_remove_files_folders_and_links(self):
        (self.dir / "folder" / "sub").mkdir(parents=True)
        (self.dir / "folder" / "sub" / "x.txt").write_text("x", encoding="utf-8")
        (self.dir / "file.txt").write_text("y", encoding="utf-8")
        os.symlink(self.dir / "folder", self.dir / "link")
        problems = removal.remove([self.dir / "link", self.dir / "folder", self.dir / "file.txt",
                                   self.dir / "missing"])
        self.assertEqual(problems, [])
        self.assertEqual(os.listdir(self.dir), [])

    def test_remove_reports_problems(self):
        (self.dir / "file.txt").write_text("y", encoding="utf-8")
        with mock.patch("os.remove", side_effect=PermissionError(13, "Permission denied")):
            problems = removal.remove([self.dir / "file.txt"])
        self.assertEqual(problems, [(str(self.dir / "file.txt"), "Permission denied")])

    def make_trash(self):
        trash = self.dir / "Trash"
        (trash / "files").mkdir(parents=True)
        (trash / "info").mkdir()
        (trash / "files" / "a.txt").write_text("a", encoding="utf-8")
        (trash / "info" / "a.txt.trashinfo").write_text(
            "[Trash Info]\nPath=/home/u/a.txt\nDeletionDate=2026-10-31T10:00:00\n", encoding="utf-8")
        return trash

    def test_deleting_from_the_bin_drops_its_info(self):
        trash = self.make_trash()
        self.assertEqual(removal.remove([trash / "files" / "a.txt"]), [])
        self.assertFalse((trash / "info" / "a.txt.trashinfo").exists())

    def test_moving_out_of_the_bin_drops_its_info(self):
        trash = self.make_trash()
        target = self.dir / "Documents"
        target.mkdir()
        job = transfer.Transfer([str(trash / "files" / "a.txt")], str(target), mode="move")
        job.run()
        self.assertTrue((target / "a.txt").exists())
        self.assertFalse((trash / "info" / "a.txt.trashinfo").exists())

    def test_drives_have_their_own_trash(self):
        drive = self.dir / "USB DRIVE"
        uid = os.getuid()
        folder = drive / f".Trash-{uid}"
        (folder / "files").mkdir(parents=True)
        (folder / "info").mkdir()
        (folder / "files" / "photo.jpg").write_text("p", encoding="utf-8")
        (folder / "info" / "photo.jpg.trashinfo").write_text(
            "[Trash Info]\nPath=Pictures/photo.jpg\nDeletionDate=2026-10-31T10:00:00\n", encoding="utf-8")
        mounts = self.dir / "mounts"
        escaped = str(drive).replace(" ", "\\040")
        mounts.write_text(f"/dev/sdb1 {escaped} vfat rw 0 0\nproc /proc proc rw 0 0\n/dev/sda2 / ext4 rw 0 0\n",
                          encoding="utf-8")
        self.assertEqual(places.mounted_drives(mounts), [str(drive)])
        with mock.patch.object(places, "trash_dir", return_value=self.dir / "home-trash"):
            items = places.trash_items(mounts=mounts)
        self.assertEqual([(i["name"], i["original"]) for i in items],
                         [("photo.jpg", str(drive / "Pictures" / "photo.jpg"))])


class RunProgramTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        patcher = mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.dir / "data"),
                                               "XDG_DATA_DIRS": str(self.dir / "share"),
                                               "XDG_CONFIG_HOME": str(self.dir / "config"),
                                               "XDG_CONFIG_DIRS": str(self.dir / "etc")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def launcher(self, folder, name="app.desktop", text="[Desktop Entry]\nType=Application\nName=Hello\n"
                                                         "Name[tr]=Merhaba\nExec=hello\n"):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_launchers_in_application_folders_are_trusted(self):
        self.assertTrue(runprogram.trusted(self.launcher(self.dir / "data" / "applications")))
        self.assertTrue(runprogram.trusted(self.launcher(self.dir / "share" / "applications")))
        self.assertTrue(runprogram.trusted(self.launcher(self.dir / "config" / "autostart")))

    def test_downloaded_launcher_asks_until_marked_executable(self):
        path = self.launcher(self.dir / "Downloads")
        path.chmod(0o644)
        self.assertFalse(runprogram.trusted(path))
        path.chmod(0o755)
        self.assertTrue(runprogram.trusted(path))

    def test_programs_outside_system_folders_ask(self):
        program = self.dir / "tool"
        program.write_text("#!/bin/sh\n", encoding="utf-8")
        program.chmod(0o755)
        self.assertFalse(runprogram.trusted(program))
        self.assertTrue(runprogram.trusted("/usr/bin/env"))

    def test_how_it_starts(self):
        app = self.launcher(self.dir / "Downloads")
        self.assertEqual(runprogram.command(app), (["gio", "launch", str(app)], None, None))
        link = self.launcher(self.dir / "Downloads", "site.desktop",
                             "[Desktop Entry]\nType=Link\nName=Site\nURL=https://example.org/\n")
        self.assertEqual(runprogram.command(link), (None, None, "https://example.org/"))
        opened = []
        self.assertTrue(runprogram.start(link, open_url=lambda url: opened.append(url) or True))
        self.assertEqual(opened, ["https://example.org/"])
        program = self.dir / "tool"
        self.assertEqual(runprogram.command(program), ([str(program)], str(self.dir), None))
        self.assertEqual(runprogram.display_name(app, "tr"), "Merhaba")
        self.assertEqual(runprogram.display_name(program), "tool")


if __name__ == "__main__":
    unittest.main()
