"""Tests for the desktop guard (system/veltos-desktop-guard), the root
service that keeps This PC, the Recycle Bin and the Store on a desktop.

The tests that change owners need root; the package build runs as root in
the builder container. A fake account (pwd/grp patched) owns a home in a
temporary folder."""

import grp
import importlib.machinery
import importlib.util
import os
import pwd
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PKG = Path(__file__).resolve().parent.parent


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


guard = load("veltos_desktop_guard", PKG / "system/veltos-desktop-guard")

UID = GID = 4242
NEIGHBOUR = 4243
AS_ROOT = os.geteuid() == 0


def account(name, uid, gid, home):
    return pwd.struct_passwd((name, "x", uid, gid, name.title(), str(home), "/bin/bash"))


class FakeAccounts:
    """pwd/grp answers for the guard: "alice" and her private group, plus
    whatever a test adds."""

    def __init__(self, home):
        self.users = [account("alice", UID, GID, home)]
        self.groups = [grp.struct_group(("alice", "x", GID, []))]

    def getpwuid(self, uid):
        for user in self.users:
            if user.pw_uid == uid:
                return user
        raise KeyError(uid)

    def getgrgid(self, gid):
        for group in self.groups:
            if group.gr_gid == gid:
                return group
        raise KeyError(gid)

    def patches(self):
        return [mock.patch.object(guard.pwd, "getpwuid", self.getpwuid),
                mock.patch.object(guard.pwd, "getpwall", lambda: list(self.users)),
                mock.patch.object(guard.grp, "getgrgid", self.getgrgid)]


class DesktopPartsTests(unittest.TestCase):
    """Where the desktop is, from the user's own user-dirs.dirs."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home)

    def parts(self, line=None):
        config = self.home / ".config"
        config.mkdir(exist_ok=True)
        if line is not None:
            (config / "user-dirs.dirs").write_bytes(line.encode() + b"\n")
        fd = os.open(self.home, guard.DIRECTORY_FLAGS)
        try:
            return guard.desktop_parts(fd)
        finally:
            os.close(fd)

    def test_follows_the_users_desktop_folder(self):
        self.assertEqual(self.parts('XDG_DESKTOP_DIR="$HOME/Masaüstü"'), ["Masaüstü"])
        self.assertEqual(self.parts('XDG_DESKTOP_DIR="$HOME/a/b/"'), ["a", "b"])

    def test_only_folders_in_the_home(self):
        self.assertEqual(self.parts(), ["Desktop"])
        for value in ('"/etc"', '"$HOME/../bob/Desktop"', '"$HOME/"', '"$HOME/a/./b"'):
            with self.subTest(value=value):
                self.assertEqual(self.parts("XDG_DESKTOP_DIR=" + value), ["Desktop"])

    def test_configuration_behind_a_link_is_ignored(self):
        elsewhere = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, elsewhere)
        (elsewhere / "user-dirs.dirs").write_bytes(b'XDG_DESKTOP_DIR="$HOME/Elsewhere"\n')
        (self.home / ".config").symlink_to(elsewhere)
        fd = os.open(self.home, guard.DIRECTORY_FLAGS)
        try:
            self.assertEqual(guard.desktop_parts(fd), ["Desktop"])
        finally:
            os.close(fd)

    def test_folders_are_never_opened_through_links(self):
        (self.home / "real").mkdir()
        (self.home / "link").symlink_to(self.home / "real")
        fd = os.open(self.home, guard.DIRECTORY_FLAGS)
        try:
            with self.assertRaises(OSError):
                guard.open_path(fd, ["link"])
            with self.assertRaises(guard.Refused):
                guard.open_path(fd, [".."])
        finally:
            os.close(fd)


class AccountTests(unittest.TestCase):
    """Which accounts the guard acts for; nothing on disk is touched."""

    def setUp(self):
        self.fake = FakeAccounts("/nonexistent")
        for patch in self.fake.patches():
            patch.start()
            self.addCleanup(patch.stop)

    def test_system_accounts_are_refused(self):
        for uid in (0, 999, 65534):
            with self.subTest(uid=uid), self.assertRaises(guard.Refused):
                guard.protect(uid)

    def test_shared_groups_are_refused(self):
        # The desktop would become writable for everybody in "users".
        self.fake.users[0] = account("alice", UID, 100, "/nonexistent")
        self.fake.groups.append(grp.struct_group(("users", "x", 100, [])))
        with self.assertRaisesRegex(guard.Refused, "shared"):
            guard.protect(UID)

    def test_private_group_with_other_members_is_refused(self):
        self.fake.groups[0] = grp.struct_group(("alice", "x", GID, ["bob"]))
        with self.assertRaisesRegex(guard.Refused, "shared"):
            guard.protect(UID)

    def test_group_that_is_another_accounts_primary_group_is_refused(self):
        self.fake.users.append(account("bob", NEIGHBOUR, GID, "/nonexistent"))
        with self.assertRaisesRegex(guard.Refused, "shared"):
            guard.protect(UID)


@unittest.skipUnless(AS_ROOT, "changes owners: needs root (the package build runs as root)")
class ProtectTests(unittest.TestCase):
    """The guard at work on a fake account's home."""

    def setUp(self):
        self.root = Path(os.path.realpath(tempfile.mkdtemp()))
        self.addCleanup(shutil.rmtree, self.root)
        self.home = self.root / "home" / "alice"
        self.desktop = self.home / "Desktop"
        self.desktop.mkdir(parents=True)
        for path in (self.home, self.desktop):
            os.chown(path, UID, GID)
        self.source = self.root / "source"
        self.source.mkdir()
        for name in guard.LAUNCHERS:
            (self.source / name).write_bytes(f"[Desktop Entry]\nName={name}\n".encode())
        self.fake = FakeAccounts(self.home)
        for patch in self.fake.patches() + [mock.patch.object(guard, "SOURCE", str(self.source))]:
            patch.start()
            self.addCleanup(patch.stop)

    def test_desktop_and_launchers_are_guarded(self):
        mine = self.desktop / "notes.txt"
        mine.write_bytes(b"mine")
        os.chown(mine, UID, GID)
        self.assertEqual(guard.protect(UID), "ok")
        info = self.desktop.stat()
        self.assertEqual((info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode)), (0, GID, 0o1775))
        for name, when in guard.LAUNCHERS.items():
            launcher = (self.desktop / name).stat()
            self.assertEqual((launcher.st_uid, launcher.st_gid, stat.S_IMODE(launcher.st_mode)),
                             (0, 0, 0o755), name)
            self.assertEqual(launcher.st_mtime_ns, int(when * 1e9), name)
            self.assertEqual((self.desktop / name).read_bytes(), (self.source / name).read_bytes())
        self.assertEqual(mine.stat().st_uid, UID)               # the user's own files stay theirs
        self.assertEqual(guard.protect(UID), "ok")              # and again, nothing to change

    def test_links_are_replaced_never_written_through(self):
        victim = self.root / "victim"
        victim.write_bytes(b"not yours")
        (self.desktop / "this-pc.desktop").symlink_to(victim)
        os.link(victim, self.desktop / "recycle-bin.desktop")   # a hard link (as the user could make)
        self.assertEqual(guard.protect(UID), "ok")
        self.assertEqual(victim.read_bytes(), b"not yours")
        self.assertEqual(victim.stat().st_nlink, 1)
        for name in ("this-pc.desktop", "recycle-bin.desktop"):
            path = self.desktop / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(path.read_bytes(), (self.source / name).read_bytes())

    def test_desktop_behind_a_link_is_refused(self):
        other = self.root / "other"
        other.mkdir()
        os.chown(other, UID, GID)
        shutil.rmtree(self.desktop)
        self.desktop.symlink_to(other)
        with self.assertRaises(OSError):
            guard.protect(UID)
        self.assertEqual(other.stat().st_uid, UID)

    def test_somebody_elses_folder_is_refused(self):
        os.chown(self.desktop, NEIGHBOUR, NEIGHBOUR)
        with self.assertRaisesRegex(guard.Refused, "somebody else"):
            guard.protect(UID)
        self.assertEqual(self.desktop.stat().st_uid, NEIGHBOUR)

    def test_home_of_somebody_else_is_refused(self):
        os.chown(self.home, NEIGHBOUR, NEIGHBOUR)
        with self.assertRaises(guard.Refused):
            guard.protect(UID)

    def test_no_desktop_yet(self):
        shutil.rmtree(self.desktop)
        self.assertEqual(guard.protect(UID), "no-desktop")

    def test_recycle_bin_date_alternates(self):
        guard.protect(UID)
        launcher = self.desktop / "recycle-bin.desktop"
        self.assertEqual(guard.touch_recycle_bin(UID), "ok")
        self.assertEqual(launcher.stat().st_mtime_ns, int(2.5e9))
        self.assertEqual(guard.touch_recycle_bin(UID), "ok")
        self.assertEqual(launcher.stat().st_mtime_ns, int(2e9))


if __name__ == "__main__":
    unittest.main()
