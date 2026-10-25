"""Unit tests for veltos-winapps (run by dh_auto_test, no Wine or display needed)."""

import os
import struct
import sys
import tempfile
import unittest
import unittest.mock
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

    def test_batch_files(self):
        for name in ("Start Server.bat", "build.CMD"):
            info = exeinfo.inspect(self.write(name, b"@echo off\r\necho VeltOS\r\npause\r\n"))
            self.assertEqual((info.kind, info.name, info.valid), ("batch", name, True))
            self.assertFalse(info.is_installer)
        self.assertFalse(exeinfo.inspect(self.write("odd.bat", minimal_pe())).valid)

    def test_batch_files_open_with_the_runner(self):
        data = Path(__file__).resolve().parent.parent / "data"
        self.assertIn('<glob pattern="*.cmd"/>', (data / "veltos-winapps.xml").read_text(encoding="utf-8"))
        self.assertIn("application/x-bat;", (data / "veltos-run.desktop").read_text(encoding="utf-8"))
        self.assertIn("application/x-bat=veltos-run.desktop\n", (data / "mimeapps.list").read_text(encoding="utf-8"))


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["XDG_DATA_HOME"] = self.tmp

    def test_slugify(self):
        self.assertEqual(winenv.slugify("Notepad++ 8.6 (x64)"), "notepad-8-6-x64")
        self.assertEqual(winenv.slugify("???"), "app")

    def test_one_shared_environment(self):
        env = winenv.Environment()
        self.assertTrue(str(env.prefix).endswith("veltos/windows/prefix"))
        self.assertEqual(env.env({})["WINEPREFIX"], str(env.prefix))
        self.assertEqual(env.env({})["WINEARCH"], "win64")

    def test_setup_runs_without_display(self):
        env = winenv.Environment().setup_env({"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0", "HOME": "/h"})
        self.assertNotIn("DISPLAY", env)
        self.assertEqual(env["WAYLAND_DISPLAY"], "veltos-no-display")
        self.assertEqual(env["HOME"], "/h")

    def test_setup_strips_and_themes(self):
        env = winenv.Environment()
        commands = env.setup_commands(vulkan=False)
        flat = [" ".join(c) for c in commands]
        self.assertTrue(any("x86_64-w64-mingw32-strip --strip-debug" in c for c in flat))
        self.assertTrue(any("i686-w64-mingw32-strip --strip-debug" in c for c in flat))
        self.assertTrue(any("regedit" in c for c in flat))
        self.assertFalse(any("dxvk-setup" in c for c in flat))
        self.assertTrue(any("dxvk-setup" in " ".join(c) for c in env.setup_commands(vulkan=True)))
        reg = env.write_setup_files().read_text()
        self.assertIn("light.msstyles", reg)

    def test_commands(self):
        env = winenv.Environment()
        self.assertIn("msiexec", env.run_command(Path("/x/a.msi"), "msi"))
        self.assertEqual(env.run_command(Path("/x/a.exe"), "exe")[1:4], ["start", "/wait", "/unix"])
        self.assertEqual(env.run_command(Path("/x/a.bat"), "batch")[1:], ["start", "/wait", "/unix", "/x/a.bat"])

    def test_records(self):
        env = winenv.Environment()
        env.save_record("My App", installed_at="2026-01-01T00:00:00")
        env.save_record("Other", installed_at="2026-02-01T00:00:00")
        self.assertEqual([r["name"] for r in winenv.installed_apps(env)], ["Other", "My App"])

    def test_space_check(self):
        env = winenv.Environment()
        ok, needed = env.enough_space()
        self.assertEqual(needed, winenv.SETUP_SPACE)
        self.assertIsInstance(ok, bool)


class ShortcutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        os.environ["XDG_DATA_HOME"] = str(self.tmp)

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


# Exec lines as winemenubuilder writes them (dev VM, 7-Zip 26.04): desktop
# entry escaping on top of the shell quoting of the .lnk's Windows path.
PREFIX = "/home/velt/.local/share/veltos/windows/prefix"
MENU_EXEC = (r'env WINEPREFIX="/home/velt/.local/share/veltos/windows/prefix" wine-stable '
             r'C:\\\\ProgramData\\\\Microsoft\\\\Windows\\\\Start\\ Menu\\\\Programs\\\\7-Zip\\\\'
             r'7-Zip\\ File\\ Manager.lnk')
DESKTOP_EXEC = (r'env WINEPREFIX="/home/velt/.local/share/veltos/windows/prefix" wine-stable start /unix '
                r'/home/velt/.local/share/veltos/windows/prefix/drive_c/users/Public/Desktop/7-Zip\\ File\\ Manager.lnk')
TYPE_EXEC = 'env WINEPREFIX="/home/velt/.local/share/veltos/windows/prefix" wine start /ProgIDOpen 7-Zip.7z %f'


class UninstalledShortcutTests(unittest.TestCase):
    """After an uninstall Wine's menu builder leaves its Start menu entries,
    menus, folders and icons behind; VeltOS removes them (product owner's
    item 18, 2026-10-23: the app still showed after it was uninstalled)."""

    def test_windows_target(self):
        self.assertEqual(shortcuts.windows_target(MENU_EXEC, PREFIX),
                         Path(PREFIX) / "drive_c/ProgramData/Microsoft/Windows/Start Menu/Programs/7-Zip"
                         / "7-Zip File Manager.lnk")
        self.assertEqual(shortcuts.windows_target(DESKTOP_EXEC, PREFIX),
                         Path(PREFIX) / "drive_c/users/Public/Desktop/7-Zip File Manager.lnk")
        self.assertIsNone(shortcuts.windows_target(TYPE_EXEC, PREFIX))
        self.assertIsNone(shortcuts.windows_target(MENU_EXEC, "/home/velt/other/prefix"))
        self.assertIsNone(shortcuts.windows_target("veltos-explorer shell:mycomputer", PREFIX))
        self.assertEqual(shortcuts.file_type(TYPE_EXEC, PREFIX), "7-Zip.7z")

    def make_home(self):
        home = Path(tempfile.mkdtemp())
        prefix = home / ".local/share/veltos/windows/prefix"
        lnk = prefix / "drive_c/ProgramData/Microsoft/Windows/Start Menu/Programs/Kept/kept.lnk"
        lnk.parent.mkdir(parents=True)
        lnk.write_bytes(b"L")
        # A ProgID written only with its subkeys still counts; 7-Zip's is gone.
        (prefix / "system.reg").write_text("WINE REGISTRY Version 2\n\n"
                                           "[Software\\\\Classes\\\\Kept.File\\\\shell\\\\open] 1\n"
                                           "[Software\\\\Classes\\\\.txt] 1\n")
        apps = home / ".local/share/applications"
        menu = apps / "wine/Programs/7-Zip"
        menu.mkdir(parents=True)
        (apps / "wine/Programs/Kept").mkdir()

        def entry(path, name, exec_line, icon):
            path.write_text(f"[Desktop Entry]\nName={name}\nExec={exec_line}\nType=Application\nIcon={icon}\n")

        entry(menu / "7-Zip File Manager.desktop", "7-Zip File Manager", MENU_EXEC.replace(PREFIX, str(prefix)),
              "EA23_7zFM.0")
        entry(apps / "wine/Programs/Kept/kept.desktop", "Kept",
              f'env WINEPREFIX="{prefix}" wine C:\\\\\\\\ProgramData\\\\\\\\Microsoft\\\\\\\\Windows\\\\\\\\'
              f'Start\\\\ Menu\\\\\\\\Programs\\\\\\\\Kept\\\\\\\\kept.lnk', "1DA0_kept.0")
        entry(apps / "wine-extension-7z.desktop", "7-Zip", TYPE_EXEC.replace(PREFIX, str(prefix)), "EA23_7zFM.0")
        entry(apps / "wine-extension-kept.desktop", "Kept", TYPE_EXEC.replace(PREFIX, str(prefix))
              .replace("7-Zip.7z", "Kept.File"), "1DA0_kept.0")
        entry(apps / "firefox.desktop", "Firefox", "firefox %u", "firefox")
        desktop = home / "Desktop"
        desktop.mkdir()
        entry(desktop / "7-Zip File Manager.desktop", "7-Zip File Manager",
              DESKTOP_EXEC.replace(PREFIX, str(prefix)), "EA23_7zFM.0")
        entry(desktop / "thispc.desktop", "This PC", "veltos-explorer shell:mycomputer", "computer")
        merged = home / ".config/menus/applications-merged"
        merged.mkdir(parents=True)
        for name in ("wine-Programs-7-Zip-7-Zip File Manager.menu", "wine-Programs-Kept-kept.menu"):
            (merged / name).write_text("<Menu/>\n")
        directories = home / ".local/share/desktop-directories"
        directories.mkdir(parents=True)
        for name in ("wine-Programs.directory", "wine-Programs-7-Zip.directory", "wine-Programs-Kept.directory"):
            (directories / name).write_text("[Desktop Entry]\n")
        icons = home / ".local/share/icons/hicolor"
        for size in ("32x32", "48x48"):
            (icons / size / "apps").mkdir(parents=True)
            for icon in ("EA23_7zFM.0", "1DA0_kept.0", "firefox"):
                (icons / size / "apps" / f"{icon}.png").write_bytes(b"P")
        packages = home / ".local/share/mime/packages"
        packages.mkdir(parents=True)
        (packages / "x-wine-extension-7z.xml").write_text("<mime-info/>\n")
        return home, prefix, desktop

    def test_removes_what_the_uninstaller_left(self):
        home, prefix, desktop = self.make_home()
        removed = shortcuts.remove_stale(prefix, home=home, desktop=desktop)
        data = home / ".local/share"
        self.assertEqual(sorted(Path(p).name for p in removed),
                         ["7-Zip File Manager.desktop", "7-Zip File Manager.desktop", "wine-extension-7z.desktop"])
        self.assertFalse((data / "applications/wine/Programs/7-Zip").exists())
        self.assertFalse((home / ".config/menus/applications-merged/wine-Programs-7-Zip-7-Zip File Manager.menu")
                         .exists())
        self.assertFalse((data / "desktop-directories/wine-Programs-7-Zip.directory").exists())
        self.assertFalse((data / "mime/packages/x-wine-extension-7z.xml").exists())
        self.assertEqual(list((data / "icons/hicolor").glob("*/apps/EA23_7zFM.0.png")), [])
        # Everything of the program that is still installed, and of others, stays.
        for kept in ("applications/wine/Programs/Kept/kept.desktop", "applications/wine-extension-kept.desktop",
                     "applications/firefox.desktop", "desktop-directories/wine-Programs.directory",
                     "desktop-directories/wine-Programs-Kept.directory", "icons/hicolor/48x48/apps/1DA0_kept.0.png",
                     "icons/hicolor/48x48/apps/firefox.png"):
            self.assertTrue((data / kept).exists(), kept)
        self.assertTrue((home / ".config/menus/applications-merged/wine-Programs-Kept-kept.menu").exists())
        self.assertTrue((desktop / "thispc.desktop").exists())
        self.assertEqual(shortcuts.remove_stale(prefix, home=home, desktop=desktop), [])

    def test_shortcut_names_ignore_case(self):
        home, prefix, desktop = self.make_home()
        lnk = prefix / "drive_c/ProgramData/Microsoft/Windows/Start Menu/Programs/Kept/kept.lnk"
        lnk.rename(lnk.with_name("KEPT.LNK"))
        shortcuts.remove_stale(prefix, home=home, desktop=desktop)
        self.assertTrue((home / ".local/share/applications/wine/Programs/Kept/kept.desktop").exists())

    def test_forget_removed_drops_the_record(self):
        from veltos_winapps import programs
        home, prefix, desktop = self.make_home()
        old = {key: os.environ.get(key) for key in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "HOME")}
        os.environ.update(XDG_DATA_HOME=str(home / ".local/share"), XDG_CONFIG_HOME=str(home / ".config"),
                          HOME=str(home))
        try:
            environment = winenv.Environment(prefix.parent)
            gone = environment.save_record("7-Zip", shortcuts=[
                str(home / ".local/share/applications/wine/Programs/7-Zip/7-Zip File Manager.desktop")])
            kept = environment.save_record("Kept", shortcuts=[
                str(home / ".local/share/applications/wine/Programs/Kept/kept.desktop")])
            portable = environment.save_record("Portable", shortcuts=[])
            with unittest.mock.patch.object(shortcuts, "desktop_dir", return_value=desktop):
                removed = programs.forget_removed(environment)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.assertIn(str(gone), removed)
        self.assertFalse(gone.exists())
        self.assertTrue(kept.exists())
        self.assertTrue(portable.exists())
        self.assertFalse((desktop / "7-Zip File Manager.desktop").exists())


class ProgramListTests(unittest.TestCase):
    """Settings > Apps lists the installed Windows programs from the
    registry files, without starting Wine."""

    def setUp(self):
        from veltos_winapps import programs
        self.programs = programs
        self.root = Path(tempfile.mkdtemp())
        self.env = winenv.Environment(self.root)
        self.env.prefix.mkdir(parents=True)
        data = Path(__file__).resolve().parent / "data" / "system.reg"
        (self.env.prefix / "system.reg").write_bytes(data.read_bytes())
        icon = self.env.prefix / "drive_c" / "Program Files" / "7-Zip" / "7zFM.exe"
        icon.parent.mkdir(parents=True)
        icon.write_bytes(b"MZ")

    def test_lists_the_programs_users_installed(self):
        found = self.programs.installed_programs(self.env)
        self.assertEqual([p["key"] for p in found], ["Notepad++", "7-Zip"])     # newest first
        notepad, seven = found
        self.assertEqual(notepad["name"], "Notepad++ (32-bit) çalış")
        self.assertEqual((notepad["publisher"], notepad["date"]), ("Notepad++ Team", "2026-10-22"))
        self.assertEqual((seven["version"], seven["sizeKb"]), ("23.01", 0x16A8))
        self.assertEqual(Path(seven["icon"]).parts[-4:], ("drive_c", "Program Files", "7-Zip", "7zFM.exe"))
        self.assertEqual(notepad["icon"], "")

    def test_no_environment_no_programs(self):
        self.assertEqual(self.programs.installed_programs(winenv.Environment(self.root / "none")), [])

    def test_uninstall_runs_the_programs_own_uninstaller(self):
        command = self.programs.uninstall_command("7-Zip")
        self.assertEqual(command[:4], ["sh", "-c", '"$1" uninstaller --remove "$2"; "$3" -w', "sh"])
        self.assertEqual(command[5], "7-Zip")
        self.assertIsNone(self.programs.uninstall_command("a\\b"))
        self.assertIsNone(self.programs.uninstall_command(""))


class StringTests(unittest.TestCase):
    def test_turkish_has_every_key(self):
        self.assertEqual(set(strings.TEXTS["tr"]), set(strings.TEXTS["en"]))

    def test_placeholders_match(self):
        import re
        for key, english in strings.TEXTS["en"].items():
            self.assertEqual(sorted(re.findall(r"{\w+}", english)),
                             sorted(re.findall(r"{\w+}", strings.TEXTS["tr"][key])), key)


class StripWineDllsTests(unittest.TestCase):
    """bin/strip-wine-dlls with stand-ins for MinGW's strip."""

    def setUp(self):
        import shutil
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.log = self.tmp / "stripped"
        tools = self.tmp / "bin"
        tools.mkdir()
        tool = tools / "x86_64-w64-mingw32-strip"
        tool.write_text(f'#!/bin/sh\nfor f in "$@"; do case "$f" in -*) ;; *) echo "$f" >> "{self.log}" ;; esac; done\n')
        tool.chmod(0o755)
        self.dlls = self.tmp / "x86_64-windows"
        self.dlls.mkdir()
        for name in ("kernel32.dll", "notepad.exe", "WINSPOOL.DRV", "stdole2.tlb", "readme.txt"):
            (self.dlls / name).write_bytes(b"MZ")
        self.env = {"PATH": f"{tools}:/usr/bin:/bin",
                    "VELTOS_WINE_DLL_DIRS": f"{self.dlls}:x86_64-w64-mingw32-strip "
                                            f"{self.tmp / 'i386-windows'}:i686-w64-mingw32-strip"}

    def run_strip(self):
        import subprocess
        script = Path(__file__).resolve().parent.parent / "bin/strip-wine-dlls"
        return subprocess.run(["sh", str(script)], env=self.env, capture_output=True, text=True)

    def test_only_windows_programs_and_libraries(self):
        result = self.run_strip()
        self.assertEqual(result.returncode, 0, result.stderr)
        stripped = sorted(Path(line).name for line in self.log.read_text().splitlines())
        self.assertEqual(stripped, ["WINSPOOL.DRV", "kernel32.dll", "notepad.exe", "stdole2.tlb"])

    def test_missing_tool_or_folder_changes_nothing(self):
        (self.tmp / "i386-windows").mkdir()
        self.env["PATH"] = "/usr/bin:/bin"
        result = self.run_strip()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists())
        self.assertIn("is missing", result.stdout)

    def test_runs_when_wine_changes(self):
        debian = Path(__file__).resolve().parent.parent / "debian"
        triggers = (debian / "veltos-winapps.triggers").read_text().split()
        self.assertIn("/usr/lib/x86_64-linux-gnu/wine/x86_64-windows", triggers)
        self.assertIn("/usr/lib/i386-linux-gnu/wine/i386-windows", triggers)
        self.assertIn("configure|triggered)", (debian / "veltos-winapps.postinst").read_text())


if __name__ == "__main__":
    unittest.main()
