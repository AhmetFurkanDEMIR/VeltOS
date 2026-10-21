"""Tests for the pages that replace KDE's settings modules: prefs.py,
accounts.py, inputs.py, apps.py and the systemsettings/kcmshell6 redirect
(fake commands, temporary folders; no KDE needed)."""

import importlib.machinery
import importlib.util
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
        self.assertEqual(accounts.Accounts(runner, me="velt").add_user("Bad Name", "", "pw", False), "bad_username")
        self.assertEqual(accounts.Accounts(runner, me="velt").add_user("ali", "", "", False), "password_missing")
        self.assertFalse(any("CreateUser" in " ".join(c) for c in runner.commands))

    def test_cannot_remove_oneself(self):
        self.assertFalse(accounts.Accounts(self.runner(), me="velt").remove_user("velt"))

    @unittest.skipUnless(os.name == "posix", "needs a pseudo terminal")
    def test_change_password_through_passwd(self):
        fake = Path(tempfile.mkdtemp()) / "passwd"
        fake.write_text("#!/bin/sh\n"
                        "printf 'Current password: '; read a\n"
                        "printf 'New password: '; read b\n"
                        "printf 'Retype new password: '; read c\n"
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
            self.assertEqual(groups["browser"]["current"], "")
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


if __name__ == "__main__":
    unittest.main()
