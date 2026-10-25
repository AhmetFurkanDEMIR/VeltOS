"""Tests for the pages that replace KDE's settings modules: prefs.py,
accounts.py, inputs.py, apps.py and the systemsettings/kcmshell6 redirect
(fake commands, temporary folders; no KDE needed)."""

import importlib.machinery
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fakesystem import FakeSystem  # noqa: E402
from veltos_settings import accounts, apps, catalog, inputs, prefs  # noqa: E402

PKG = Path(__file__).resolve().parent.parent


def config_dirs(user="", system=""):
    home, etc = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    return home, [etc]


class PrefsTests(unittest.TestCase):
    def setUp(self):
        self.home, self.system_dirs = config_dirs()
        self.dirs = (self.home, self.system_dirs)
        self.runner = FakeSystem()
        self.prefs = prefs.Preferences(self.runner, self.dirs)

    def test_user_value_wins_over_system(self):
        (self.system_dirs[0] / "kscreenlockerrc").write_text("[Daemon]\nTimeout=10\nAutolock=false\n")
        self.assertEqual(self.prefs.get("lockAfter"), 10)
        self.assertFalse(self.prefs.get("autoLock"))
        (self.home / "kscreenlockerrc").write_text("[Daemon]\nTimeout=3\n")
        self.assertEqual(self.prefs.get("lockAfter"), 3)
        self.assertEqual(self.prefs.get("lockOnResume"), True)        # default

    def test_lock_never_turns_the_automatic_lock_off(self):
        self.prefs.set("lockAfter", 0)
        commands = [" ".join(c) for c in self.runner.commands]
        self.assertIn("kwriteconfig6 --notify --file kscreenlockerrc --group Daemon --type bool --key Autolock false",
                      commands)
        self.assertFalse(any("--key Timeout" in c for c in commands))
        self.prefs.set("lockAfter", 15)
        commands = [" ".join(c) for c in self.runner.commands]
        self.assertIn("kwriteconfig6 --notify --file kscreenlockerrc --group Daemon --type bool --key Autolock true",
                      commands)
        self.assertIn("kwriteconfig6 --notify --file kscreenlockerrc --group Daemon --key Timeout 15", commands)
        (self.home / "kscreenlockerrc").write_text("[Daemon]\nTimeout=10\nAutolock=false\n")
        with mock.patch.object(prefs, "has_battery", return_value=False):
            self.assertEqual(self.prefs.state()["lockAfter"], 0)

    def test_file_search_is_its_setting_not_the_running_indexer(self):
        self.assertTrue(self.prefs.file_search())                        # KDE's default: on
        (self.home / "baloofilerc").write_text("[Basic Settings]\nIndexing-Enabled=false\n")
        self.assertFalse(self.prefs.file_search())
        self.assertTrue(self.prefs.set_file_search(True))
        self.assertIn(["balooctl6", "enable"], self.runner.commands)
        self.runner.fail.add("balooctl6")
        self.assertTrue(self.prefs.set_file_search(False))              # recorded even without balooctl6
        self.assertIn("kwriteconfig6 --notify --file baloofilerc --group Basic Settings --type bool "
                      "--key Indexing-Enabled false", [" ".join(c) for c in self.runner.commands])

    def test_nested_groups(self):
        (self.home / "powerdevilrc").write_text("[AC][Display]\nTurnOffDisplayIdleTimeoutSec=300\n")
        self.assertEqual(self.prefs.get("screenOffAC"), 300)

    def test_set_writes_and_reloads(self):
        self.prefs.set("sleepAC", 1800)
        self.prefs.set("powerButton", 1)
        self.prefs.set("nightLight", True)
        commands = [" ".join(c) for c in self.runner.commands]
        self.assertIn("kwriteconfig6 --notify --file powerdevilrc --group AC --group SuspendAndShutdown "
                      "--key AutoSuspendIdleTimeoutSec 1800", commands)
        self.assertIn("kwriteconfig6 --notify --file powerdevilrc --group Battery --group SuspendAndShutdown "
                      "--key PowerButtonAction 1", commands)
        self.assertTrue(any("reparseConfiguration" in c for c in commands))
        self.assertIn("kwriteconfig6 --notify --file kwinrc --group NightColor --type bool --key Active true",
                      commands)
        self.assertIn("kwriteconfig6 --notify --file kwinrc --group NightColor --key Mode Constant", commands)
        self.assertTrue(any("org.kde.KWin.reconfigure" in c for c in commands))

    def test_do_not_disturb(self):
        self.assertFalse(self.prefs.do_not_disturb())
        (self.home / "plasmanotifyrc").write_text("[DoNotDisturb]\nUntil=2999,12,31,0,0,0\n")
        self.assertTrue(self.prefs.do_not_disturb())
        self.prefs.set_do_not_disturb(False)
        self.assertIn(["kwriteconfig6", "--notify", "--file", "plasmanotifyrc", "--group", "DoNotDisturb",
                       "--key", "Until", ""], self.runner.commands)

    def test_text_size_and_layouts(self):
        (self.home / "kdeglobals").write_text("[General]\nfont=Inter,12.5,-1,5,400,0,0,0,0,0,0,0,0,0,0,1\n")
        self.assertEqual(self.prefs.text_size(), 125)
        self.prefs.set_text_size(150)
        self.assertTrue(any("font Inter,15,-1" in " ".join(c) for c in self.runner.commands))
        self.assertEqual(self.prefs.layouts(), ["us"])
        self.assertTrue(self.prefs.set_layouts(["tr", "tr(f)", "bad layout!"]))
        self.assertIn(["kwriteconfig6", "--notify", "--file", "kxkbrc", "--group", "Layout", "--key",
                       "LayoutList", "tr,tr(f)"], self.runner.commands)
        self.assertFalse(self.prefs.set_layouts(["; rm -rf /"]))

    def test_language_and_formats(self):
        self.assertTrue(self.prefs.set_language("tr"))
        self.assertFalse(self.prefs.set_language("xx"))
        runner = FakeSystem({("locale", "-a"): "C\nC.utf8\nde_DE.utf8\nPOSIX\n"})
        formats = prefs.Preferences(runner, self.dirs).available_formats()
        self.assertEqual(formats, ["de_DE", "en_US", "tr_TR"])
        self.assertFalse(self.prefs.set_formats("xx_YY", formats))
        self.assertTrue(self.prefs.set_formats("de_DE", formats))
        # Every format key Plasma exports, so LC_* lines of /etc/default/locale
        # (an English installation in Turkey: LC_TIME=tr_TR) do not win.
        written = {c[-2]: c[-1] for c in self.runner.commands if c[:4] == ["kwriteconfig6", "--notify", "--file",
                                                                             "plasma-localerc"] and "Formats" in c}
        self.assertEqual(written["LC_TIME"], "de_DE.UTF-8")
        self.assertEqual(set(written), set(prefs.FORMAT_KEYS))

    def test_formats_follow_the_language(self):
        # The taskbar's date stayed English after Turkish was chosen
        # (product owner, 2026-10-23): formats that went with the old
        # language follow the new one, as Windows' "Recommended" format does.
        (self.home / "plasma-localerc").write_text("[Formats]\nLANG=en_US.UTF-8\n\n[Translations]\nLANGUAGE=en_US\n")
        with mock.patch.dict(os.environ, {"LANG": "en_US.UTF-8"}, clear=True):
            self.assertTrue(self.prefs.set_language("tr"))
            # The system's LC_TIME (installer: English in Turkey) decides
            # what the date looks like while plasma-localerc names none.
            with mock.patch.dict(os.environ, {"LC_TIME": "tr_TR.UTF-8"}):
                self.assertEqual(self.prefs.formats(), "tr_TR")
        commands = [" ".join(c) for c in self.runner.commands]
        self.assertIn("kwriteconfig6 --notify --file plasma-localerc --group Translations --key LANGUAGE tr", commands)
        self.assertIn("kwriteconfig6 --notify --file plasma-localerc --group Formats --key LC_TIME tr_TR.UTF-8",
                      commands)
        # Formats the user chose themselves stay.
        self.runner.commands.clear()
        (self.home / "plasma-localerc").write_text("[Formats]\nLANG=de_DE.UTF-8\n\n[Translations]\nLANGUAGE=en_US\n")
        with mock.patch.dict(os.environ, {"LANG": "en_US.UTF-8"}, clear=True):
            self.assertTrue(self.prefs.set_language("tr"))
        self.assertFalse(any("Formats" in c for c in self.runner.commands))

    def test_notification_senders(self):
        apps_dir = Path(tempfile.mkdtemp())
        (apps_dir / "org.kde.konsole.desktop").write_text(
            "[Desktop Entry]\nName=Konsole\nName[tr]=Uçbirim\nIcon=utilities-terminal\n")
        (self.home / "plasmanotifyrc").write_text(
            "[Applications][org.kde.konsole]\nSeen=true\nShowPopups=false\n\n"
            "[Applications][removed.app]\nSeen=true\n")
        senders = self.prefs.notification_apps([apps_dir], "tr")
        self.assertEqual(senders, [{"name": "Uçbirim", "icon": "utilities-terminal",
                                    "id": "org.kde.konsole", "banners": False}])
        self.assertFalse(self.prefs.set_app_banners("../../evil", True))

    def test_battery(self):
        root = Path(tempfile.mkdtemp())
        (root / "BAT0").mkdir()
        (root / "BAT0" / "type").write_text("Battery\n")
        self.assertTrue(prefs.has_battery(root))
        (root / "BAT0" / "scope").write_text("Device\n")      # a mouse's battery
        self.assertFalse(prefs.has_battery(root))


GETALL = ("({'UserName': <'ayse'>, 'RealName': <'Ayşe \\'Ayşe\\' Yılmaz'>, 'AccountType': <0>, "
          "'IconFile': <''>, 'Uid': <uint64 1001>},)")


class AccountsTests(unittest.TestCase):
    def runner(self):
        return FakeSystem({
            ("getent", "passwd"): "root:x:0:0:root:/root:/bin/bash\nvelt:x:1000:1000:Velt,,,:/home/velt:/bin/bash\n"
                                  "ayse:x:1001:1001::/home/ayse:/bin/bash\nnobody:x:65534:65534::/:/usr/sbin/nologin\n",
            ("getent", "group", "sudo"): "sudo:x:27:velt\n",
            tuple(accounts.gdbus("--object-path", accounts.ROOT, "--method",
                                 f"{accounts.BUS}.FindUserByName", "ayse")):
                "(objectpath '/org/freedesktop/Accounts/User1001',)\n",
            tuple(accounts.gdbus("--object-path", "/org/freedesktop/Accounts/User1001", "--method",
                                 "org.freedesktop.DBus.Properties.GetAll", accounts.USER_IFACE)): GETALL,
        })

    def test_users_and_me(self):
        state = accounts.Accounts(self.runner(), me="velt").state()
        self.assertEqual(state["me"]["name"], "velt")
        self.assertTrue(state["me"]["admin"])                       # sudo group (no AccountsService data)
        self.assertEqual([u["name"] for u in state["others"]], ["ayse"])
        self.assertFalse(state["others"][0]["admin"])
        self.assertEqual(state["others"][0]["realName"], "Ayşe 'Ayşe' Yılmaz")

    def test_add_user_checks_the_name(self):
        runner = self.runner()
        self.assertEqual(accounts.Accounts(runner, me="velt").add_user("!!!", "", "pw", False), "bad_username")
        self.assertEqual(accounts.Accounts(runner, me="velt").add_user("ali", "", "", False), "password_missing")
        self.assertEqual(accounts.Accounts(runner, me="velt").add_user("ayse", "", "pw", False), "user_exists")
        self.assertFalse(any("CreateUser" in " ".join(c) for c in runner.commands))

    def test_login_names_like_windows_accepts_them(self):
        self.assertEqual(accounts.login_name("Ayşe Yılmaz"), "ayseyilmaz")
        self.assertEqual(accounts.login_name("İLKER"), "ilker")
        self.assertEqual(accounts.login_name("  Çağrı.Öztürk  "), "cagriozturk")
        self.assertEqual(accounts.login_name("2nd user"), "nduser")
        self.assertEqual(accounts.login_name("José"), "jose")
        self.assertEqual(accounts.login_name("!!!"), "")
        self.assertEqual(len(accounts.login_name("a" * 50)), 32)

    def test_add_user_asks_for_the_password_once(self):
        # Creating the user and setting its password run in one process
        # (admin_calls), so polkit asks once; two `gdbus` calls asked twice
        # on an installed system (VM, 2026-10-23). The password's hash goes
        # through standard input, never the command line.
        runner = self.runner()
        account = accounts.Accounts(runner, me="velt")
        with mock.patch.object(accounts, "hash_password", lambda pw: "$6$salt$hash"):
            self.assertEqual(account.add_user("Ali Veli", "", "pw", True), "")
        command, data = runner.inputs[-1]
        self.assertEqual(command[1:], ["-m", "veltos_settings.admin_calls"])
        self.assertNotIn("$6$salt$hash", " ".join(command))
        create, password = json.loads(data)
        self.assertEqual((create["method"], create["args"]), ("CreateUser", ["aliveli", "Ali Veli", 1]))
        self.assertEqual((password["path"], password["method"]), ("@created", "SetPassword"))
        self.assertEqual(password["args"], ["$6$salt$hash", ""])
        self.assertFalse(any("CreateUser" in " ".join(c) for c in runner.commands if c[0] == "gdbus"))

    def test_admin_calls_use_one_connection_and_the_created_path(self):
        try:
            from gi.repository import GLib
        except ImportError:
            self.skipTest("needs python3-gi")
        from veltos_settings import admin_calls
        made = []

        class FakeBus:
            def call_sync(self, bus, path, interface, method, args, reply_type, flags, timeout, cancellable):
                made.append((path, method, args.unpack(), flags, timeout))
                if method == "CreateUser":
                    return GLib.Variant("(o)", ("/org/freedesktop/Accounts/User1005",))
                return GLib.Variant("()", ())
        calls = [{"path": "/org/freedesktop/Accounts", "interface": "org.freedesktop.Accounts",
                  "method": "CreateUser", "signature": "(ssi)", "args": ["ali", "Ali", 0]},
                 {"path": "@created", "interface": "org.freedesktop.Accounts.User",
                  "method": "SetPassword", "signature": "(ss)", "args": ["$6$x", ""]}]
        self.assertEqual(admin_calls.main(io.StringIO(json.dumps(calls)), FakeBus()), 0)
        self.assertEqual([m[:3] for m in made],
                         [("/org/freedesktop/Accounts", "CreateUser", ("ali", "Ali", 0)),
                          ("/org/freedesktop/Accounts/User1005", "SetPassword", ("$6$x", ""))])
        from gi.repository import Gio
        self.assertTrue(all(m[3] & Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION for m in made))

    def test_cannot_remove_oneself(self):
        self.assertFalse(accounts.Accounts(self.runner(), me="velt").remove_user("velt"))

    @unittest.skipUnless(os.name == "posix", "needs a pseudo terminal")
    def test_change_password_through_passwd(self):
        # Like the real passwd: echo off while a password is typed, a newline
        # after each answer, a pause while the old one is checked (the pause
        # with echo on is where an answer sent too early was echoed and the
        # last prompt stayed unanswered, VM 2026-10-21).
        fake = Path(tempfile.mkdtemp()) / "passwd"
        fake.write_text("#!/bin/sh\n"
                        "prompt() { stty -echo 2>/dev/null; printf '%s' \"$1\"; read ans; stty echo 2>/dev/null; echo; }\n"
                        "prompt 'Current password: '; a=$ans; sleep 0.3\n"
                        "prompt 'New password: '; b=$ans\n"
                        "prompt 'Retype new password: '; c=$ans\n"
                        "[ \"$a\" = old ] || { echo 'passwd: Authentication token manipulation error'; exit 1; }\n"
                        "[ \"$b\" = \"$c\" ] && [ ${#b} -ge 6 ] || { echo 'BAD PASSWORD: it is too short'; exit 10; }\n"
                        "echo 'passwd: password updated successfully'\n")
        fake.chmod(0o755)
        self.assertEqual(accounts.change_password("old", "new secret", [str(fake)], timeout=10), "")
        self.assertEqual(accounts.change_password("wrong", "new secret", [str(fake)], timeout=10), "wrong_password")
        self.assertEqual(accounts.change_password("old", "abc", [str(fake)], timeout=10), "weak_password")


DEVICE = ("({'name': <'USB Mouse'>, 'pointer': <true>, 'keyboard': <false>, 'touchpad': <false>, "
          "'leftHanded': <true>, 'pointerAcceleration': <-0.25>, 'scrollFactor': <1.5>, 'naturalScroll': <false>, "
          "'vendor': <uint32 1133>, 'product': <uint32 49271>, 'supportsLeftHanded': <true>},)")


class InputsTests(unittest.TestCase):
    def runner(self):
        return FakeSystem({
            tuple(inputs.session_gdbus("--object-path", inputs.DEVICE_ROOT, "--method",
                                       "org.freedesktop.DBus.Properties.Get", "org.kde.KWin.InputDeviceManager",
                                       "devicesSysNames")): "(<['event3', 'event0']>,)\n",
            tuple(inputs.session_gdbus("--object-path", inputs.DEVICE_ROOT + "/event3", "--method",
                                       "org.freedesktop.DBus.Properties.GetAll", inputs.IFACE)): DEVICE,
            tuple(inputs.session_gdbus("--object-path", inputs.DEVICE_ROOT + "/event0", "--method",
                                       "org.freedesktop.DBus.Properties.GetAll", inputs.IFACE)):
                "({'name': <'Keyboard'>, 'pointer': <false>, 'keyboard': <true>},)",
        })

    def test_state(self):
        state = inputs.Inputs(self.runner()).state()
        self.assertTrue(state["hasMouse"])
        self.assertFalse(state["hasTouchpad"])
        self.assertTrue(state["leftHanded"])
        self.assertEqual(state["speed"], -0.25)
        self.assertEqual(state["scrollFactor"], 1.5)

    def test_set_applies_now_and_for_next_start(self):
        runner = self.runner()
        self.assertTrue(inputs.Inputs(runner).set("pointerAcceleration", 2, touchpad=False))
        commands = [" ".join(c) for c in runner.commands]
        self.assertTrue(any("Properties.Set org.kde.KWin.InputDevice pointerAcceleration <1.000>" in c
                            for c in commands))
        self.assertIn("kwriteconfig6 --file kcminputrc --group Libinput --group 1133 --group 49271 "
                      "--group USB Mouse --key PointerAcceleration 1.000", commands)
        self.assertFalse(inputs.Inputs(runner).set("evil", 1))


class AppsTests(unittest.TestCase):
    def test_default_apps(self):
        folder, config = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        old = {k: os.environ.get(k) for k in ("XDG_CONFIG_HOME", "XDG_CONFIG_DIRS")}
        os.environ.update(XDG_CONFIG_HOME=str(config), XDG_CONFIG_DIRS=str(Path(tempfile.mkdtemp())))
        try:
            (folder / "firefox-esr.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=Firefox\nIcon=firefox-esr\nExec=firefox-esr %u\n"
                "MimeType=x-scheme-handler/http;text/html;\n")
            (folder / "hidden.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=Hidden\nNoDisplay=true\nExec=hidden\n"
                "MimeType=x-scheme-handler/http;\n")
            # Okular opens PDF through a hidden helper entry of the same program.
            (folder / "org.kde.okular.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=Document Viewer\nIcon=okular\nExec=okular %U\n")
            (folder / "okularApplication_pdf.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=Okular\nNoDisplay=true\nExec=okular %U\n"
                "MimeType=application/pdf;\n")
            (folder / "mimeinfo.cache").write_text("[MIME Cache]\napplication/pdf=okularApplication_pdf.desktop;\n")
            defaults = apps.DefaultApps(FakeSystem(), [folder])
            groups = {g["id"]: g for g in defaults.state()["groups"]}
            self.assertEqual([o["value"] for o in groups["browser"]["options"]], ["firefox-esr.desktop"])
            # Nothing recorded: the only app that opens it is the current one.
            self.assertEqual(groups["browser"]["current"], "firefox-esr.desktop")
            self.assertEqual(groups["email"]["current"], "")                 # nothing installed
            # VeltOS' own defaults next to the applications (kde-mimeapps.list).
            (folder / "kde-mimeapps.list").write_text("[Default Applications]\ntext/plain=editor.desktop;\n")
            (folder / "editor.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=Editor\nExec=editor %f\nMimeType=text/plain;\n")
            (folder / "other.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=Another\nExec=other %f\nMimeType=text/plain;\n")
            self.assertEqual(defaults.current("text/plain"), "editor.desktop")
            self.assertEqual(groups["pdf"]["options"], [{"value": "okularApplication_pdf.desktop",
                                                         "label": "Document Viewer", "icon": "okular"}])
            self.assertEqual(groups["pdf"]["current"], "okularApplication_pdf.desktop")
            (config / "mimeapps.list").write_text("[Added Associations]\ntext/html=x.desktop;\n")
            self.assertTrue(defaults.set_default("browser", "firefox-esr.desktop"))
            text = (config / "mimeapps.list").read_text()
            self.assertIn("[Added Associations]\ntext/html=x.desktop;", text)
            self.assertIn("[Default Applications]\nx-scheme-handler/http=firefox-esr.desktop;", text)
            self.assertEqual(defaults.current("x-scheme-handler/http"), "firefox-esr.desktop")
            self.assertFalse(defaults.set_default("browser", "x; rm.desktop"))
            self.assertFalse(defaults.set_default("browser", "missing.desktop"))
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_startup_apps_on_and_off(self):
        user, system = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        (system / "app.desktop").write_text("[Desktop Entry]\nType=Application\nName=Updater\nExec=x\n")
        (system / "plasma-service.desktop").write_text("[Desktop Entry]\nName=Service\nNoDisplay=true\n")
        (system / "gnome-only.desktop").write_text("[Desktop Entry]\nName=G\nOnlyShowIn=GNOME;\n")
        startup = apps.StartupApps((user, [system]))
        self.assertEqual([(e["id"], e["enabled"]) for e in startup.entries()], [("app.desktop", True)])
        startup.set_enabled("app.desktop", False)
        self.assertIn("Hidden=true", (user / "app.desktop").read_text())
        self.assertFalse(startup.entries()[0]["enabled"])
        startup.set_enabled("app.desktop", True)
        self.assertFalse((user / "app.desktop").exists())
        self.assertTrue(startup.entries()[0]["enabled"])


class RedirectTests(unittest.TestCase):
    def test_modules_map_to_veltos_pages(self):
        loader = importlib.machinery.SourceFileLoader("redirect", str(PKG / "bin/veltos-settings-redirect"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        redirect = importlib.util.module_from_spec(spec)
        loader.exec_module(redirect)
        self.assertEqual(redirect.module(["--args", "x", "kcm_users"]), "kcm_users")
        self.assertEqual(redirect.module(["--platform", "wayland"]), "")
        self.assertEqual(catalog.page_for_module("kcm_users"), "yourinfo")
        self.assertEqual(catalog.page_for_module("kcm_pulseaudio.desktop"), "sound")
        self.assertEqual(catalog.page_for_module("kcm_unknown"), "home")
        self.assertEqual(catalog.page_for_module("signin"), "signin")
        self.assertEqual(catalog.page_for_module(""), "home")

    def test_every_module_opens_a_real_page(self):
        pages = {entry["id"] for entry in catalog.PAGES} | set(catalog.BUILTIN_PAGES)
        for module, page in catalog.KCM_PAGES.items():
            self.assertIn(page, pages, module)

    def test_info_center_opens_about(self):
        loader = importlib.machinery.SourceFileLoader("redirect", str(PKG / "bin/veltos-settings-redirect"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        redirect = importlib.util.module_from_spec(spec)
        loader.exec_module(redirect)
        calls = []
        with mock.patch.object(redirect.os, "execvp", lambda *args: calls.append(args)),                 mock.patch.object(redirect.sys, "argv", ["/usr/bin/kinfocenter"]):
            redirect.main()
        with mock.patch.object(redirect.os, "execvp", lambda *args: calls.append(args)),                 mock.patch.object(redirect.sys, "argv", ["/usr/bin/kinfocenter", "kcm_energyinfo"]):
            redirect.main()
        with mock.patch.object(redirect.os, "execvp", lambda *args: calls.append(args)),                 mock.patch.object(redirect.sys, "argv", ["/usr/bin/systemsettings"]):
            redirect.main()
        self.assertEqual([c[1][1] for c in calls], ["about", "power", "home"])

    @unittest.skipUnless(sys.platform.startswith("linux"), "symlinks and modes")
    def test_postinst_locks_kde_programs_but_not_the_redirect(self):
        # kinfocenter.kde is KDE's symlink to "systemsettings", which is the
        # redirect: the postinst's chmod followed it and made the redirect
        # root's only ("Permission denied" for users; VM, 2026-10-23).
        import stat
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            usr_bin = root / "usr/bin"
            libexec = root / "usr/libexec/veltos"
            fake_bin = root / "fake-bin"
            for d in (usr_bin, libexec, fake_bin):
                d.mkdir(parents=True)
            redirect = libexec / "settings-redirect"
            redirect.write_text("#!/bin/sh\n")
            redirect.chmod(0o755)
            (usr_bin / "systemsettings").symlink_to("../libexec/veltos/settings-redirect")
            kde = usr_bin / "systemsettings.kde"
            kde.write_text("#!/bin/sh\n")
            kde.chmod(0o755)
            (usr_bin / "kinfocenter.kde").symlink_to("systemsettings")
            calls = root / "calls"
            override = fake_bin / "dpkg-statoverride"
            override.write_text(f'#!/bin/sh\necho "$@" >> {calls}\n[ "$1" != --list ]\n')
            override.chmod(0o755)
            script = (PKG / "debian/veltos-settings.postinst").read_text(encoding="utf-8")
            script = script.replace("#DEBHELPER#", "").replace("/usr/", f"{root}/usr/")
            subprocess.run(["sh", "-c", script, "postinst", "configure"], check=True,
                           env=dict(os.environ, PATH=f"{fake_bin}:/usr/bin:/bin"))
            self.assertEqual(stat.S_IMODE(redirect.stat().st_mode), 0o755)
            self.assertEqual(stat.S_IMODE(kde.stat().st_mode), 0o700)
            self.assertNotIn(f"--add root root 0700 {usr_bin}/kinfocenter.kde", calls.read_text())


if __name__ == "__main__":
    unittest.main()
