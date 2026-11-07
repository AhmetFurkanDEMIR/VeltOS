"""Static checks for the VeltOS installer configuration (run by dh_auto_test)."""

import configparser
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parent.parent
CALAMARES = PKG / "calamares"

# Modules shipped by the calamares 3.3.14 package in Debian trixie.
BUILTIN_MODULES = {
    "bootloader", "contextualprocess", "displaymanager", "dracut", "dracutlukscfg",
    "dummycpp", "dummyprocess", "dummypython", "finished", "finishedq", "fsresizer",
    "fstab", "grubcfg", "hostinfo", "hwclock", "initcpio", "initcpiocfg", "initramfs",
    "initramfscfg", "interactiveterminal", "keyboard", "keyboardq", "license", "locale",
    "localecfg", "localeq", "luksbootkeyfile", "luksopenswaphookcfg", "machineid",
    "mkinitfs", "mount", "netinstall", "networkcfg", "notesqml", "oemid",
    "openrcdmcryptcfg", "packagechooser", "packagechooserq", "packages", "partition",
    "plymouthcfg", "preservefiles", "rawfs", "removeuser", "services-openrc",
    "services-systemd", "shellprocess", "summary", "summaryq", "tracking", "umount",
    "unpackfs", "unpackfsc", "users", "usersq", "welcome", "welcomeq", "zfs", "zfshostid",
}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.settings = load(CALAMARES / "settings.conf")
        self.custom = {p.parent.name: load(p) for p in (PKG / "modules").glob("*/module.desc")}

    def test_all_yaml_parses(self):
        files = list(CALAMARES.rglob("*.conf")) + list(CALAMARES.rglob("*.desc")) + \
            list((PKG / "modules").rglob("module.desc"))
        self.assertGreater(len(files), 10)
        for path in files:
            with self.subTest(path=path.name):
                self.assertIsInstance(load(path), dict)

    def test_sequence_modules_exist(self):
        instances = {f"{i['module']}@{i['id']}": i for i in self.settings.get("instances", [])}
        for step in self.settings["sequence"]:
            for module in next(iter(step.values())):
                with self.subTest(module=module):
                    if "@" in module:
                        self.assertIn(module, instances)
                        self.assertTrue((CALAMARES / "modules" / instances[module]["config"]).is_file())
                        module = module.split("@")[0]
                    self.assertTrue(module in BUILTIN_MODULES or module in self.custom,
                                    f"unknown module {module}")

    def test_no_commands_or_logs_on_screen(self):
        # The product owner: never show code or logs while installing.
        shown = [m for step in self.settings["sequence"] for m in step.get("show", [])]
        self.assertNotIn("summary", shown)          # it listed partition commands
        self.assertTrue(self.settings["prompt-install"])   # still asks before changing the disk
        qss = (CALAMARES / "branding/veltos/stylesheet-light.qss").read_text(encoding="utf-8")
        self.assertRegex(qss, r"QLabel#exec-message \{[^}]*max-height: 0px")
        self.assertRegex(qss, r"QToolBar \{[^}]*max-height: 0px")

    def test_branding(self):
        self.assertEqual(self.settings["branding"], "veltos")
        branding = load(CALAMARES / "branding/veltos/branding.desc")
        self.assertEqual(branding["componentName"], "veltos")
        self.assertEqual(branding["strings"]["productName"], "VeltOS")
        # Text, not a number: an unquoted 1.0 is the YAML number 1, and the
        # installer's sidebar said "VeltOS 1" (2026-10-27). Same as os-release.
        # The version is the release's (build/scripts/release-bump.py writes it
        # with os-release's; release-check.py checks it). Built alone, outside
        # the repository, only its form can be checked: this test once
        # expected "1.0" there, and 1.1's installer said "VeltOS 1.0".
        expected = str(branding["strings"]["version"])
        self.assertRegex(expected, r"^\d+\.\d+$")
        os_release = (PKG.parent / "veltos-base/os-release")
        if os_release.exists():         # the package is also built outside the repository
            self.assertEqual(expected, next(line.split("=", 1)[1].strip('"')
                                            for line in os_release.read_text().splitlines()
                                            if line.startswith("VERSION_ID=")))
        for key in ("version", "shortVersion"):
            self.assertEqual(branding["strings"][key], expected, key)
        self.assertEqual(branding["strings"]["versionedName"], f"VeltOS {expected}")
        self.assertEqual(branding["strings"]["shortVersionedName"], f"VeltOS {expected}")

    def test_custom_job_commands_are_shipped(self):
        for name, desc in self.custom.items():
            with self.subTest(module=name):
                self.assertEqual(desc["name"], name)
                if desc.get("interface") == "python":
                    self.assertTrue((PKG / "modules" / name / desc["script"]).is_file())
                    continue
                script = desc["command"].split()[0]
                self.assertTrue(script.startswith("/usr/libexec/veltos-installer/"))
                self.assertTrue((PKG / "helpers" / Path(script).name).is_file())

    def test_pages_are_veltos_qml(self):
        # Every page except partitioning (a C++ page, styled by the QSS) is a
        # Calamares QML module whose QML comes from the VeltOS branding.
        shown = [m for step in self.settings["sequence"] for m in step.get("show", [])]
        self.assertEqual(shown, ["welcomeq", "localeq", "keyboardq", "partition", "usersq",
                                 "notesqml@recovery", "packagechooserq@windowsapps", "finishedq"])
        executed = [m for step in self.settings["sequence"] for m in step.get("exec", [])]
        for name in ("localeq", "keyboardq", "usersq"):
            self.assertIn(name, executed)
        for name in ("locale", "keyboard", "users", "welcome", "finished"):
            self.assertNotIn(name, shown + executed)
            self.assertFalse((CALAMARES / "modules" / f"{name}.conf").exists(), name)
        conf_names = {f"{i['module']}@{i['id']}": i["config"] for i in self.settings.get("instances", [])}
        for page in [m for m in shown if m.split("@")[0].endswith("q")]:
            name = page.split("@")[0]
            with self.subTest(page=page):
                conf = load(CALAMARES / "modules" / conf_names.get(page, f"{name}.conf"))
                self.assertEqual(conf["qmlSearch"], "both")
                self.assertTrue((CALAMARES / "branding/veltos" / f"{name}.qml").is_file())

    def test_qml_pictures_are_shipped(self):
        branding = CALAMARES / "branding/veltos"
        for path in branding.glob("*.qml"):
            for name in re.findall(r'"(images/[A-Za-z0-9_.-]+)"', path.read_text(encoding="utf-8")):
                with self.subTest(qml=path.name, picture=name):
                    self.assertTrue((branding / name).is_file())
            for name in re.findall(r'picture: "([A-Za-z0-9_.-]+\.svg)"', path.read_text(encoding="utf-8")):
                with self.subTest(qml=path.name, picture=name):
                    self.assertTrue((branding / "images" / name).is_file())

    def test_windows_programs_choice(self):
        """Wine or Bottles (product owner, 2026-10-27): the page offers both,
        the job writes the choice to the new system after usersq."""
        import importlib.util
        import sys
        import tempfile
        import types
        conf = load(CALAMARES / "modules/packagechooserq-windowsapps.conf")
        self.assertEqual([i["id"] for i in conf["items"]], ["wine", "bottles"])
        self.assertEqual((conf["method"], conf["default"]), ("legacy", "wine"))
        qml = (CALAMARES / "branding/veltos/packagechooserq.qml").read_text(encoding="utf-8")
        self.assertIn('config.packageChoice = choice', qml)
        self.assertIn('value: "bottles"', qml)
        executed = [m for step in self.settings["sequence"] for m in step.get("exec", [])]
        self.assertLess(executed.index("usersq"), executed.index("windows-apps"))
        root = tempfile.mkdtemp()
        values = {"rootMountPoint": root}
        fake = types.SimpleNamespace(globalstorage=types.SimpleNamespace(value=values.get),
                                     utils=types.SimpleNamespace(debug=lambda *a: None))
        sys.modules["libcalamares"] = fake
        try:
            spec = importlib.util.spec_from_file_location("windows_apps", PKG / "modules/windows-apps/main.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for choice, runner in ((None, "wine"), ("bottles", "bottles"), ("wine", "wine"), ("odd", "wine")):
                values["packagechooser_windowsapps"] = choice
                self.assertIsNone(module.run())
                text = (Path(root) / "etc/veltos/windows-apps.conf").read_text()
                self.assertIn(f"runner={runner}\n", text)
        finally:
            del sys.modules["libcalamares"]

    def test_password_hint_and_reset_drive(self):
        """"If you forget your password" (product owner, 2026-11-01): a
        page after the account page; the job, after the user exists, writes
        the hint and makes the drive with veltos-auth, never failing the
        installation."""
        import importlib.util
        import sys
        import tempfile
        import types
        shown = [m for step in self.settings["sequence"] for m in step.get("show", [])]
        self.assertEqual(shown.index("notesqml@recovery"), shown.index("usersq") + 1)
        instance = next(i for i in self.settings["instances"] if i["id"] == "recovery")
        self.assertEqual((instance["module"], instance["config"]), ("notesqml", "notesqml-recovery.conf"))
        conf = load(CALAMARES / "modules/notesqml-recovery.conf")
        self.assertEqual(conf["qmlFilename"], "recovery")
        self.assertTrue((CALAMARES / "branding/veltos/recovery.qml").is_file())
        qml = (CALAMARES / "branding/veltos/recovery.qml").read_text(encoding="utf-8")
        # Calamares 3.3.14's QML cannot write global storage: the page posts
        # its choices to install-veltos' helper, the job reads them.
        self.assertNotIn("Global.insert(", qml)
        self.assertIn('request.open("POST", "http://127.0.0.1:47823/choices")', qml)
        self.assertIn("Without a password reset USB, a forgotten password can't be reset.", qml)
        executed = [m for step in self.settings["sequence"] for m in step.get("exec", [])]
        self.assertEqual(executed.index("password-recovery"), executed.index("usersq") + 1)

        root = tempfile.mkdtemp()
        choices = Path(tempfile.mkdtemp()) / "veltos-installer.json"
        choices.write_text(json.dumps({"hint": "  first cat", "device": "/dev/sdb1", "exclude": "/dev/nvme0n1"}))
        values = {"rootMountPoint": root, "username": "ayse", "hostname": "ayse-pc"}
        inserted, warnings = {}, []
        fake = types.SimpleNamespace(
            globalstorage=types.SimpleNamespace(value=values.get, insert=inserted.__setitem__),
            utils=types.SimpleNamespace(debug=lambda *a: None, warning=warnings.append))
        sys.modules["libcalamares"] = fake
        os.environ["VELTOS_CHOICES"] = str(choices)
        self.addCleanup(os.environ.pop, "VELTOS_CHOICES", None)
        try:
            spec = importlib.util.spec_from_file_location("password_recovery", PKG / "modules/password-recovery/main.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            calls = []

            def runner(command, **_kwargs):
                calls.append(command)
                return types.SimpleNamespace(returncode=1, stdout='{"error": "bad-drive"}', stderr="")
            module.make_drive.__defaults__ = (runner,)
            self.assertIsNone(module.run())
            self.assertEqual(calls, [["/usr/libexec/veltos/password-recovery", "create", "ayse", "/dev/sdb1",
                                      "--root", root, "--host", "ayse-pc", "--exclude", "/dev/nvme0n1"]])
            self.assertEqual(inserted["veltosRecoveryResult"], "failed")
            accounts = Path(root) / "var/lib/AccountsService/users/ayse"
            self.assertEqual(accounts.read_text(), "[User]\nPasswordHint=first cat\n")
            # AccountsService's own keys stay; the hint is replaced.
            self.assertEqual(module.with_hint("[User]\nIcon=/x\nPasswordHint=old\n", "new"),
                             "[User]\nPasswordHint=new\nIcon=/x\n")
            # The helper's file is found through pkexec's user.
            self.assertEqual(module.page_choices({"PKEXEC_UID": "../x"}), {})
            self.assertEqual(module.page_choices({"VELTOS_CHOICES": str(choices)})["device"], "/dev/sdb1")
        finally:
            del sys.modules["libcalamares"]

    def test_install_screen_like_windows_setup(self):
        # While installing: slideshow and progress only, no buttons.
        self.assertTrue(self.settings["hide-back-and-next-during-exec"])
        self.assertTrue(self.settings["disable-cancel-during-exec"])

    def test_any_nonempty_password(self):
        # libpwquality refused anything under 6 characters and dictionary
        # words even with minlen=0; VeltOS accepts any non-empty password.
        users = load(CALAMARES / "modules/usersq.conf")
        self.assertEqual(users["passwordRequirements"], {"minLength": 1, "maxLength": -1})
        self.assertFalse(users["allowWeakPasswords"])
        self.assertFalse(users["setRootPassword"])

    def test_no_kurdish_keyboard_variants(self):
        # Product owner, 2026-10-22: the keyboard page does not offer them.
        qml = (CALAMARES / "branding/veltos/keyboardq.qml").read_text(encoding="utf-8")
        self.assertIn('return key !== "ku" && !key.startsWith("ku_");', qml)
        self.assertIn("if (!isOffered(key))", qml)
        self.assertIn("model: variantList", qml)

    def test_error_window_gets_the_style_sheet(self):
        # Calamares styles only its main window; its parentless error
        # window gets the sheet through Qt's -stylesheet option, which
        # start-calamares passes (run by install-veltos through pkexec).
        launcher = (PKG / "bin/install-veltos").read_text(encoding="utf-8")
        self.assertIn("pkexec /usr/libexec/veltos-installer/start-calamares $theme", launcher)
        start = (PKG / "helpers/start-calamares").read_text(encoding="utf-8")
        self.assertIn('-style veltos-installer -stylesheet "$run_dir/stylesheet.qss"', start)
        # Calamares also applies the branding's stylesheet.qss to its main
        # window: a link to the same generated sheet (light or dark).
        links = (PKG / "debian/calamares-settings-veltos.links").read_text(encoding="utf-8").splitlines()
        self.assertIn("run/veltos-installer/stylesheet.qss etc/calamares/branding/veltos/stylesheet.qss", links)
        self.assertFalse((CALAMARES / "branding/veltos/stylesheet.qss").exists())
        qss = (CALAMARES / "branding/veltos/stylesheet-light.qss").read_text(encoding="utf-8")
        self.assertRegex(qss, r'QDialog#ErrorDialog QTextBrowser#detailsBrowser \{[^}]*font-family: "Cascadia Mono"')

    def test_old_loading_spinner_is_hidden(self):
        # The first page draws Windows 11's ring in the middle instead.
        qss = (CALAMARES / "branding/veltos/stylesheet-light.qss").read_text(encoding="utf-8")
        self.assertRegex(qss, r"\.QWidget > WaitingSpinnerWidget \{\s*color: transparent;")
        welcome = (CALAMARES / "branding/veltos/welcomeq.qml").read_text(encoding="utf-8")
        self.assertIn('source: "WelcomePage.qml"', welcome)
        self.assertIn("asynchronous: true", welcome)

    def test_side_bar_names_every_step(self):
        # The side bar names the steps itself (Calamares' names were never
        # translated there), in the order of the sequence: each page, and
        # the installation as one step.
        names = {"welcomeq": "Welcome", "localeq": "Location", "keyboardq": "Keyboard",
                 "partition": "Disk", "usersq": "Account", "notesqml@recovery": "Password reset",
                 "packagechooserq@windowsapps": ".exe programs",
                 "finishedq": "Finish"}
        expected = []
        for step in self.settings["sequence"]:
            if "show" in step:
                expected += [names[m] for m in step["show"]]
            else:
                expected.append("Install")
        sidebar = (CALAMARES / "branding/veltos/calamares-sidebar.qml").read_text(encoding="utf-8")
        steps = re.findall(r'\["([^"]+)", "([^"]+)"\]', sidebar)
        self.assertEqual([english for english, _turkish in steps], expected)
        self.assertEqual([turkish for _english, turkish in steps][:2], ["Hoş geldiniz", "Konum"])

    def test_secure_boot_keeps_debian_efi_directory(self):
        bootloader = load(CALAMARES / "modules/bootloader.conf")
        self.assertEqual(bootloader["efiBootloaderId"], "debian")
        sequence = next(iter(self.settings["sequence"][1].values()))
        self.assertEqual(sequence.index("efi-label"), sequence.index("bootloader") + 1)


class UserVisibleTextTests(unittest.TestCase):
    """The user must never see "Debian" in the installer."""

    def test_branding_strings(self):
        branding = load(CALAMARES / "branding/veltos/branding.desc")
        for key, value in branding["strings"].items():
            self.assertNotIn("debian", str(value).lower(), key)

    def test_slideshow_and_desktop_files(self):
        files = list((CALAMARES / "branding/veltos").glob("*.qml")) + list((PKG / "data").glob("*.desktop"))
        for path in files:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".desktop":
                parser = configparser.ConfigParser(interpolation=None)
                parser.optionxform = str
                parser.read_string(text)
                text = "\n".join(v for k, v in parser["Desktop Entry"].items()
                                 if re.match(r"(Name|GenericName|Comment)(\[|$)", k))
            self.assertNotIn("debian", text.lower(), path.name)


class ScriptTests(unittest.TestCase):
    def test_shell_syntax(self):
        for path in list((PKG / "helpers").iterdir()) + list((PKG / "bin").iterdir()):
            if path.read_text(encoding="utf-8").startswith("#!/usr/bin/python3"):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
                continue
            with self.subTest(script=path.name):
                subprocess.run(["sh", "-n", str(path)], check=True)


if __name__ == "__main__":
    unittest.main()
