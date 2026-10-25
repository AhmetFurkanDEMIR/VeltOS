"""Tests for user folders, pins, drives, the Recycle Bin, recent files and
applications (places.py) and for the file operations (ops.py)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_explorer import ops, places  # noqa: E402

LSBLK = {"blockdevices": [
    {"name": "nvme0n1", "path": "/dev/nvme0n1", "label": None, "size": 512110190592, "fstype": None,
     "mountpoints": [None], "rm": False, "hotplug": False, "type": "disk", "fssize": None, "fsused": None,
     "parttype": None, "children": [
         {"name": "nvme0n1p1", "path": "/dev/nvme0n1p1", "label": None, "size": 536870912, "fstype": "vfat",
          "mountpoints": ["/boot/efi"], "rm": False, "hotplug": False, "type": "part", "fssize": 535805952,
          "fsused": 6123520, "parttype": "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"},
         {"name": "nvme0n1p2", "path": "/dev/nvme0n1p2", "label": None, "size": 494927257600, "fstype": "ext4",
          "mountpoints": ["/"], "rm": False, "hotplug": False, "type": "part", "fssize": 486993551360,
          "fsused": 23170711552, "parttype": "0fc63daf-8483-4772-8e79-3d69d8477de4"},
         {"name": "nvme0n1p3", "path": "/dev/nvme0n1p3", "label": None, "size": 16000000000, "fstype": "swap",
          "mountpoints": ["[SWAP]"], "rm": False, "hotplug": False, "type": "part", "fssize": None,
          "fsused": None, "parttype": None}]},
    {"name": "sda", "path": "/dev/sda", "label": None, "size": 32010928128, "fstype": None,
     "mountpoints": [None], "rm": True, "hotplug": True, "type": "disk", "fssize": None, "fsused": None,
     "parttype": None, "children": [
         {"name": "sda1", "path": "/dev/sda1", "label": "PHOTOS", "size": 32009879552, "fstype": "exfat",
          "mountpoints": ["/media/velt/PHOTOS"], "rm": True, "hotplug": True, "type": "part",
          "fssize": 32001753088, "fsused": 1048576, "parttype": None}]},
    {"name": "sdb", "path": "/dev/sdb", "label": None, "size": 1000204886016, "fstype": None,
     "mountpoints": [None], "rm": False, "hotplug": False, "type": "disk", "fssize": None, "fsused": None,
     "parttype": None, "children": [
         {"name": "sdb1", "path": "/dev/sdb1", "label": "Data", "size": 1000202788864, "fstype": "ntfs",
          "mountpoints": [None], "rm": False, "hotplug": False, "type": "part", "fssize": None,
          "fsused": None, "parttype": None},
         {"name": "sdb2", "path": "/dev/sdb2", "label": None, "size": 900000000, "fstype": "ntfs",
          "mountpoints": [None], "rm": False, "hotplug": False, "type": "part", "fssize": None,
          "fsused": None, "parttype": "de94bba4-06d1-4d40-a16a-bfd50179d6ac"}]},
]}


class Runner:
    def __init__(self, outputs):
        self.outputs = outputs
        self.commands = []

    def __call__(self, command, timeout=20):
        self.commands.append(command)
        return self.outputs.get(command[0], (0, ""))


class DriveTests(unittest.TestCase):
    def test_drives_for_this_pc(self):
        runner = Runner({"lsblk": (0, json.dumps(LSBLK))})
        drives = places.drives(runner, live=False)
        self.assertEqual([d["device"] for d in drives], ["/dev/nvme0n1p2", "/dev/sdb1", "/dev/sda1"])
        system, data, usb = drives
        self.assertTrue(system["system"])
        self.assertEqual(system["mount"], "/")
        self.assertEqual(data["mount"], "")          # can be mounted from This PC
        self.assertTrue(usb["removable"])
        self.assertEqual(usb["label"], "PHOTOS")
        # Windows drives are marked (icon), Windows' recovery partition is not listed.
        self.assertTrue(data["windows"])
        self.assertEqual(data["icon"], "drive-harddisk-windows")
        self.assertEqual(usb["icon"], "drive-removable-media-usb")
        self.assertFalse(system["windows"])

    def test_usb_stick_with_ntfs_shows_the_usb_drive(self):
        self.assertEqual(places.drive_icon({"removable": True, "windows": True}), "drive-removable-media-usb")
        self.assertEqual(places.drive_icon({"removable": False, "windows": True}), "drive-harddisk-windows")
        self.assertEqual(places.drive_icon({"removable": False, "windows": False}), "drive-harddisk")

    def test_read_only_mounts_are_reported(self):
        tree = {"blockdevices": [{"name": "sdc1", "path": "/dev/sdc1", "label": "W", "size": 10 ** 10,
                                  "fstype": "ntfs", "mountpoints": ["/media/velt/W x"], "rm": False,
                                  "hotplug": False, "type": "part", "fssize": 10 ** 10, "fsused": 10 ** 9,
                                  "parttype": None}]}
        mounts = "/dev/sdc1 /media/velt/W\\040x fuseblk ro,nosuid,nodev,relatime 0 0\n"
        drive = places.drives(Runner({"lsblk": (0, json.dumps(tree))}), live=False, mounts_text=mounts)[0]
        self.assertTrue(drive["readonly"])

    def test_live_root_is_shown(self):
        drives = places.drives(Runner({"lsblk": (0, json.dumps({"blockdevices": []}))}), live=True)
        self.assertEqual(len(drives), 1)
        self.assertTrue(drives[0]["system"])

    def test_broken_lsblk(self):
        self.assertEqual(places.drives(Runner({"lsblk": (1, "")}), live=False), [])

    def test_mount_and_eject(self):
        runner = Runner({"udisksctl": (0, "Mounted /dev/sdb1 at /media/velt/Data\n")})
        self.assertEqual(places.mount("/dev/sdb1", runner), ("/media/velt/Data", False))
        self.assertTrue(places.eject("/dev/sda1", runner))
        self.assertEqual(runner.commands[-1], ["udisksctl", "power-off", "-b", "/dev/sda"])


class HibernatedWindowsTests(unittest.TestCase):
    def test_windows_that_did_not_shut_down_opens_read_only(self):
        class Refusing(Runner):
            def __call__(self, command, timeout=20):
                self.commands.append(command)
                if command[-2:] == ["-o", "ro"]:
                    return 0, "Mounted /dev/sdb1 at /media/velt/Windows\n"
                return 1, "Error mounting: wrong fs type (Windows is hibernated, refused to mount)"
        runner = Refusing({})
        self.assertEqual(places.mount("/dev/sdb1", runner, windows=True), ("/media/velt/Windows", True))
        self.assertEqual(places.mount("/dev/sdb1", Refusing({}), windows=False), ("", False))
        # ntfs-3g mounted it read only by itself.
        runner = Runner({"udisksctl": (0, "Mounted /dev/sdb1 at /media/velt/Windows\n")})
        mounts = "/dev/sdb1 /media/velt/Windows fuseblk ro,nosuid 0 0\n"
        self.assertEqual(places.mount("/dev/sdb1", runner, windows=True, mounts_text=mounts),
                         ("/media/velt/Windows", True))


class PinTests(unittest.TestCase):
    def test_defaults_then_changes_are_saved(self):
        tmp = Path(tempfile.mkdtemp())
        pins = places.Pins(tmp / "explorer.json")
        defaults = pins.pinned()
        self.assertTrue(any(p.endswith("Downloads") for p in defaults))
        pins.pin("/srv/projects")
        pins.unpin(defaults[0])
        again = places.Pins(tmp / "explorer.json").pinned()
        self.assertEqual(again, defaults[1:] + ["/srv/projects"])
        pins.set("show_hidden", True)
        self.assertTrue(places.Pins(tmp / "explorer.json").get("show_hidden"))

    def test_user_dirs_from_xdg(self):
        tmp = Path(tempfile.mkdtemp())
        old = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(tmp)
        try:
            (tmp / "user-dirs.dirs").write_text('XDG_DOWNLOAD_DIR="$HOME/İndirilenler"\n'
                                                'XDG_PUBLICSHARE_DIR="$HOME/"\n', encoding="utf-8")
            dirs = dict((k, p) for k, p, _i in places.user_dirs("/home/u"))
            self.assertEqual(dirs["DOWNLOAD"], "/home/u/İndirilenler")
            self.assertEqual(dirs["DESKTOP"], "/home/u/Desktop")
            self.assertEqual(places.folder_icon("/home/u/İndirilenler", "/home/u"), "folder-download")
            self.assertEqual(places.folder_icon("/home/u", "/home/u"), "user-home")
        finally:
            if old is None:
                os.environ.pop("XDG_CONFIG_HOME")
            else:
                os.environ["XDG_CONFIG_HOME"] = old


class TrashTests(unittest.TestCase):
    def test_items_and_restore(self):
        tmp = Path(tempfile.mkdtemp())
        trash = tmp / "Trash"
        (trash / "files").mkdir(parents=True)
        (trash / "info").mkdir()
        original = tmp / "Documents" / "notes old.txt"
        (trash / "files" / "notes old.txt").write_text("x", encoding="utf-8")
        (trash / "info" / "notes old.txt.trashinfo").write_text(
            "[Trash Info]\nPath=" + str(original).replace(" ", "%20") +
            "\nDeletionDate=2026-10-19T10:00:00\n", encoding="utf-8")
        items = places.trash_items(trash)
        self.assertEqual(items[0]["original"], str(original))
        self.assertEqual(items[0]["deleted"], "2026-10-19T10:00:00")
        self.assertEqual(places.restore(items[0]["path"], trash), "")
        self.assertTrue(original.exists())
        self.assertEqual(places.trash_items(trash), [])

    def test_restore_does_not_replace(self):
        tmp = Path(tempfile.mkdtemp())
        trash = tmp / "Trash"
        (trash / "files").mkdir(parents=True)
        (trash / "info").mkdir()
        (tmp / "a.txt").write_text("new", encoding="utf-8")
        (trash / "files" / "a.txt").write_text("old", encoding="utf-8")
        (trash / "info" / "a.txt.trashinfo").write_text(f"[Trash Info]\nPath={tmp}/a.txt\n", encoding="utf-8")
        self.assertEqual(places.restore(str(trash / "files" / "a.txt"), trash), "exists")
        self.assertEqual((tmp / "a.txt").read_text(encoding="utf-8"), "new")


class ApplicationTests(unittest.TestCase):
    def test_apps_for_a_type_and_their_command(self):
        tmp = Path(tempfile.mkdtemp())
        apps = tmp / "applications"
        apps.mkdir()
        (apps / "viewer.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=Photos\nName[tr]=Fotoğraflar\n"
            "Exec=gwenview %U\nIcon=gwenview\nMimeType=image/png;image/jpeg;\n", encoding="utf-8")
        (apps / "hidden.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=X\nExec=x %f\nNoDisplay=true\nMimeType=image/png;\n",
            encoding="utf-8")
        old = os.environ.get("XDG_DATA_DIRS")
        os.environ["XDG_DATA_DIRS"] = str(tmp)
        try:
            found = places.applications_for("image/png", "tr")
        finally:
            if old is None:
                os.environ.pop("XDG_DATA_DIRS")
            else:
                os.environ["XDG_DATA_DIRS"] = old
        self.assertEqual([a["name"] for a in found], ["Fotoğraflar"])
        self.assertEqual(places.exec_command(found[0]["path"], ["/a b.png", "/c.png"]),
                         ["gwenview", "/a b.png", "/c.png"])


class OperationTests(unittest.TestCase):
    def setUp(self):
        self.started = []
        self.ops = ops.Operations(start=lambda command, cwd=None: self.started.append(command))
        self.dir = Path(tempfile.mkdtemp())

    def test_kio_commands(self):
        self.ops.trash(["/home/u/a.txt"])
        self.ops.delete(["/home/u/b.txt"])
        self.ops.move(["/home/u/c.txt"], "/home/u/Documents")
        self.ops.copy(["/home/u/d.txt"], "/home/u/Documents")
        self.assertEqual(self.started, [
            ["kioclient", "--interactive", "move", "/home/u/a.txt", "trash:/"],
            ["kioclient", "--interactive", "remove", "/home/u/b.txt"],
            ["kioclient", "--interactive", "move", "/home/u/c.txt", "/home/u/Documents/"],
            ["kioclient", "--interactive", "copy", "/home/u/d.txt", "/home/u/Documents/"]])

    def test_documents_through_the_portal_programs_through_kio(self):
        # Documents go to the portal with an activation token, so an open
        # app comes to the front; KIO starts launchers and programs.
        opened = []
        operations = ops.Operations(start=self.started.append, open_document=opened.append)
        document = self.dir / "Letter.txt"
        document.write_text("hello", encoding="utf-8")
        script = self.dir / "run.sh"
        script.write_text("#!/bin/sh\necho\n", encoding="utf-8")
        script.chmod(0o755)
        executable_text = self.dir / "notes.txt"           # NTFS drives give every file the execute bit
        executable_text.write_text("plain text", encoding="utf-8")
        executable_text.chmod(0o755)
        for path in (document, script, executable_text, self.dir / "Setup.EXE", self.dir / "app.desktop"):
            operations.open(path)
        self.assertEqual(opened, [str(document), str(executable_text)])
        self.assertEqual(self.started, [["kioclient", "exec", str(script)],
                                        ["kioclient", "exec", str(self.dir / "Setup.EXE")],
                                        ["kioclient", "exec", str(self.dir / "app.desktop")]])

    def test_copy_into_the_same_folder_makes_a_copy(self):
        (self.dir / "a.txt").write_text("", encoding="utf-8")
        self.ops.copy([str(self.dir / "a.txt")], str(self.dir))
        self.assertEqual(self.started[-1][-1], str(self.dir / "a - Copy.txt"))

    def test_move_into_itself_or_same_folder_is_ignored(self):
        self.ops.move([str(self.dir / "x")], str(self.dir))
        self.ops.move([str(self.dir)], str(self.dir / "sub"))
        self.assertEqual(self.started, [])

    def test_new_and_rename(self):
        name = self.ops.new_folder(self.dir, "New folder")
        self.assertEqual(self.ops.new_folder(self.dir, "New folder"), "New folder (2)")
        self.assertEqual(self.ops.new_file(self.dir, "New Text Document.txt"), "New Text Document.txt")
        self.assertEqual(self.ops.rename(self.dir / name, "Holiday"), "")
        self.assertTrue((self.dir / "Holiday").is_dir())
        self.assertEqual(self.ops.rename(self.dir / "Holiday", "New folder (2)"), "exists")
        self.assertEqual(self.ops.rename(self.dir / "Holiday", ""), "empty")
        self.assertEqual(self.ops.rename(self.dir / "Holiday", "holiday"), "")
        self.assertTrue((self.dir / "holiday").is_dir())


if __name__ == "__main__":
    unittest.main()
