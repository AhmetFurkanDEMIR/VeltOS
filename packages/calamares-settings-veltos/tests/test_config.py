"""Static checks for the VeltOS installer configuration (run by dh_auto_test)."""

import configparser
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
        for step in self.settings["sequence"]:
            for module in next(iter(step.values())):
                with self.subTest(module=module):
                    self.assertTrue(module in BUILTIN_MODULES or module in self.custom,
                                    f"unknown module {module}")

    def test_no_commands_or_logs_on_screen(self):
        # The product owner: never show code or logs while installing.
        shown = [m for step in self.settings["sequence"] for m in step.get("show", [])]
        self.assertNotIn("summary", shown)          # it listed partition commands
        self.assertTrue(self.settings["prompt-install"])   # still asks before changing the disk
        qss = (CALAMARES / "branding/veltos/stylesheet.qss").read_text(encoding="utf-8")
        self.assertRegex(qss, r"QLabel#exec-message \{[^}]*max-height: 0px")
        self.assertRegex(qss, r"QToolBar \{[^}]*max-height: 0px")

    def test_branding(self):
        self.assertEqual(self.settings["branding"], "veltos")
        branding = load(CALAMARES / "branding/veltos/branding.desc")
        self.assertEqual(branding["componentName"], "veltos")
        self.assertEqual(branding["strings"]["productName"], "VeltOS")

    def test_custom_job_commands_are_shipped(self):
        for name, desc in self.custom.items():
            with self.subTest(module=name):
                self.assertEqual(desc["name"], name)
                script = desc["command"].split()[0]
                self.assertTrue(script.startswith("/usr/libexec/veltos-installer/"))
                self.assertTrue((PKG / "helpers" / Path(script).name).is_file())

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
            with self.subTest(script=path.name):
                subprocess.run(["sh", "-n", str(path)], check=True)


if __name__ == "__main__":
    unittest.main()
