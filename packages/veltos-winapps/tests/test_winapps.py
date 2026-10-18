"""Unit tests for veltos-winapps (run by dh_auto_test, no Wine or display needed)."""

import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_winapps import exeinfo, shortcuts, strings, winenv  # noqa: E402


def minimal_pe(machine=0x8664, subsystem=2, extra=b""):
    """Smallest valid PE32+ image pefile accepts: headers + one empty section."""
    dos = b"MZ" + b"\0" * 58 + struct.pack("<I", 0x40)
    coff = struct.pack("<HHIIIHH", machine, 1, 0, 0, 0, 240, 0x22)
    opt = struct.pack("<HBBIIIII", 0x20B, 14, 0, 0x200, 0, 0, 0x1000, 0x1000)
    opt += struct.pack("<Q", 0x140000000)
    opt += struct.pack("<IIHHHHHHIIIIHH", 0x1000, 0x200, 6, 0, 0, 0, 6, 0, 0, 0x2000, 0x200, 0,
                       subsystem, 0)
    opt += struct.pack("<QQQQ", 0x100000, 0x1000, 0x100000, 0x1000)
    opt += struct.pack("<II", 0, 16) + b"\0" * 128
    assert len(opt) == 240
    section = struct.pack("<8sIIIIIIHHI", b".text", 0x10, 0x1000, 0x200, 0x200, 0, 0, 0, 0, 0x60000020)
    headers = dos + b"PE\0\0" + coff + opt + section
    return headers.ljust(0x200, b"\0") + b"\xC3".ljust(0x200, b"\0") + extra


class ExeInfoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def write(self, name, data):
        path = self.tmp / name
        path.write_bytes(data)
        return path

    def test_portable_64bit_gui_program(self):
        info = exeinfo.inspect(self.write("Paint Tool.exe", minimal_pe()))
        self.assertTrue(info.valid)
        self.assertEqual(info.arch, "x64")
        self.assertTrue(info.gui)
        self.assertFalse(info.dotnet)
        self.assertFalse(info.is_installer)
        self.assertEqual(info.name, "Paint Tool")

    def test_32bit_console_program(self):
        info = exeinfo.inspect(self.write("tool.exe", minimal_pe(machine=0x14C, subsystem=3)))
        self.assertEqual(info.arch, "x86")
        self.assertFalse(info.gui)

    def test_installer_detected_by_engine_signature(self):
        info = exeinfo.inspect(self.write("app.exe", minimal_pe(extra=b"..Inno Setup Setup Data..")))
        self.assertEqual(info.installer, "Inno Setup")

    def test_installer_detected_by_file_name(self):
        info = exeinfo.inspect(self.write("ProductSetup_x64.exe", minimal_pe()))
        self.assertTrue(info.is_installer)

    def test_msi_is_always_an_installer(self):
        info = exeinfo.inspect(self.write("tool.msi", b"\xd0\xcf\x11\xe0"))
        self.assertEqual((info.kind, info.installer), ("msi", "MSI"))

    def test_garbage_file_is_reported_not_raised(self):
        info = exeinfo.inspect(self.write("broken.exe", b"not a program"))
        self.assertFalse(info.valid)


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["XDG_DATA_HOME"] = self.tmp

    def test_slugify(self):
        self.assertEqual(winenv.slugify("Notepad++ 8.6 (x64)"), "notepad-8-6-x64")
        self.assertEqual(winenv.slugify("???"), "app")

    def test_new_apps_get_unique_environments(self):
        first = winenv.Environment.for_new_app("My App")
        first.save_record(name="My App")
        second = winenv.Environment.for_new_app("My App")
        self.assertEqual((first.slug, second.slug), ("my-app", "my-app-2"))
        self.assertNotEqual(winenv.Environment.for_new_app("Shared").slug, winenv.SHARED)

    def test_environment_variables(self):
        env = winenv.Environment.for_new_app("Game").env({})
        self.assertTrue(env["WINEPREFIX"].endswith("veltos/windows-apps/game/prefix"))
        self.assertEqual(env["WINEARCH"], "win64")

    def test_commands(self):
        env = winenv.Environment.shared()
        self.assertIn("msiexec", env.run_command(Path("/x/a.msi"), "msi"))
        self.assertEqual(env.run_command(Path("/x/a.exe"), "exe")[1:4], ["start", "/wait", "/unix"])
        self.assertEqual(len(env.setup_commands(vulkan=True)), 2)
        self.assertEqual(len(env.setup_commands(vulkan=False)), 1)


class ShortcutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        os.environ["XDG_DATA_HOME"] = str(self.tmp)

    def test_exec_quoting(self):
        self.assertEqual(shortcuts.quote_exec_arg("wine"), "wine")
        self.assertEqual(shortcuts.quote_exec_arg("/a b/c.exe"), '"/a b/c.exe"')
        self.assertEqual(shortcuts.quote_exec_arg('x"$'), '"x\\"\\$"')

    def test_finds_only_new_shortcuts_of_this_prefix(self):
        apps = self.tmp / "applications/wine/Programs"
        apps.mkdir(parents=True)
        before = shortcuts.snapshot([self.tmp])
        (apps / "Foo.desktop").write_text(
            '[Desktop Entry]\nName=Foo\nExec=env WINEPREFIX="/p/foo/prefix" wine x.lnk\n')
        (apps / "Bar.desktop").write_text(
            '[Desktop Entry]\nName=Bar\nExec=env WINEPREFIX="/p/bar/prefix" wine y.lnk\n')
        found = shortcuts.entries_for_prefix(
            shortcuts.changed(before, shortcuts.snapshot([self.tmp])), "/p/foo/prefix")
        self.assertEqual([e["name"] for e in found], ["Foo"])

    def test_launcher_for_portable_program(self):
        path = shortcuts.write_launcher("shared-tool", "Tool", Path("/home/u/My Apps/tool.exe"),
                                        Path("/home/u/.local/share/veltos/windows-apps/shared/prefix"))
        entry = shortcuts.read_entry(path)
        self.assertEqual(entry["name"], "Tool")
        self.assertIn('"/home/u/My Apps/tool.exe"', entry["exec"])


class StringTests(unittest.TestCase):
    def test_turkish_has_every_key(self):
        self.assertEqual(set(strings.TEXTS["tr"]), set(strings.TEXTS["en"]))

    def test_placeholders_match(self):
        import re
        for key, english in strings.TEXTS["en"].items():
            self.assertEqual(sorted(re.findall(r"{\w+}", english)),
                             sorted(re.findall(r"{\w+}", strings.TEXTS["tr"][key])), key)


if __name__ == "__main__":
    unittest.main()
