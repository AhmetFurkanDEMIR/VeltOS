"""The installer's look follows the live session's theme: the dark style
sheet, installer-theme, start-calamares, the website helper, VeltTheme.js
and the progress ring (run by dh_auto_test)."""

import http.client
import importlib.machinery
import json
import importlib.util
import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
BRANDING = PKG / "calamares/branding/veltos"
HELPERS = PKG / "helpers"
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

loader = importlib.machinery.SourceFileLoader("dark_stylesheet", str(PKG / "tools/dark-stylesheet.py"))
spec = importlib.util.spec_from_loader("dark_stylesheet", loader)
dark_stylesheet = importlib.util.module_from_spec(spec)
loader.exec_module(dark_stylesheet)

try:
    from PySide6.QtCore import QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


def script(path, text):
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)
    return path


class DarkStyleSheetTests(unittest.TestCase):
    def setUp(self):
        self.light = (BRANDING / "stylesheet-light.qss").read_text(encoding="utf-8")
        self.dark = dark_stylesheet.convert(self.light)

    def test_every_light_colour_has_a_dark_one(self):
        for colour in ("#F3F5FA", "#E3E6EE", "#1B1D24", "#5D6475", "#D5DAE5"):
            with self.subTest(colour=colour):
                self.assertIn(colour, self.light)
                self.assertNotIn(colour, self.dark)
        self.assertRegex(self.dark, r"#mainApp, QDialog, QMessageBox \{\s*background-color: #1C1E24;\s*color: #F3F4F8;")

    def test_accent_and_text_on_it_stay(self):
        self.assertRegex(self.dark, r"QPushButton:default, QPushButton:checked \{\s*background-color: #2F5EE6;"
                                    r"\s*border: 1px solid #2A55D4;\s*color: #FFFFFF;")
        self.assertIn("image: url(/etc/calamares/branding/veltos/images/chevron-down-dark.svg);", self.dark)
        self.assertTrue((BRANDING / "images/chevron-down-dark.svg").is_file())
        # The disk page's picture has a dark variant too.
        self.assertIn("background-image: url(/etc/calamares/branding/veltos/images/ill-disk-dark.svg);", self.dark)
        self.assertTrue((BRANDING / "images/ill-disk-dark.svg").is_file())
        # The failed step's log keeps its terminal colours.
        self.assertIn("background-color: #0C0C0C;", self.dark)

    def test_unknown_colour_stops_the_build(self):
        with self.assertRaises(SystemExit):
            dark_stylesheet.convert("QLabel { background-color: #123456; }")


class InstallerThemeTests(unittest.TestCase):
    """installer-theme reads the user's theme (fake kreadconfig6, eglinfo)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def run_theme(self, values, renderer):
        cases = "\n".join(f'    "{group} {key}") echo "{value}" ;;' for (group, key), value in values.items())
        kread = script(self.tmp / "kreadconfig6",
                       '#!/bin/sh\n# --file kdeglobals --group G --key K\ncase "$4 $6" in\n'
                       f"{cases}\n    *) exit 1 ;;\nesac\n")
        egl = script(self.tmp / "eglinfo",
                     "#!/bin/sh\necho 'GBM platform:'\n"
                     f"echo 'OpenGL core profile renderer: {renderer}'\necho 'Device platform:'\n")
        env = {"PATH": "/usr/bin:/bin", "VELTOS_KREADCONFIG": str(kread), "VELTOS_EGLINFO": str(egl)}
        return subprocess.run(["sh", str(HELPERS / "installer-theme")], capture_output=True, text=True,
                              env=env, check=True).stdout.strip()

    def test_dark_theme_accent_and_software(self):
        out = self.run_theme({("KDE", "LookAndFeelPackage"): "org.veltos.desktop.dark",
                              ("General", "AccentColor"): "232,17,35"}, "llvmpipe (LLVM 19.1.7, 256 bits)")
        self.assertEqual(out, "--dark --accent #E81123 --software")

    def test_light_theme_on_a_real_gpu(self):
        out = self.run_theme({("KDE", "LookAndFeelPackage"): "org.veltos.desktop",
                              ("General", "AccentColor"): "#12949b"}, "Mesa Intel(R) Graphics (ADL GT2)")
        self.assertEqual(out, "--light --accent #12949B")

    def test_scheme_colour_then_default(self):
        out = self.run_theme({("General", "ColorScheme"): "VeltOSDark",
                              ("Colors:Selection", "BackgroundNormal"): "91,63,224"}, "SVGA3D")
        self.assertEqual(out, "--dark --accent #5B3FE0")
        out = self.run_theme({("General", "AccentColor"): "300,1,1; rm -rf /"}, "")
        self.assertEqual(out, "--light --accent #2F5EE6 --software")


class StartCalamaresTests(unittest.TestCase):
    """start-calamares with a stand-in for Calamares."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.branding = self.tmp / "branding"
        self.branding.mkdir()
        light = (BRANDING / "stylesheet-light.qss").read_text(encoding="utf-8")
        (self.branding / "stylesheet-light.qss").write_text(light, encoding="utf-8")
        (self.branding / "stylesheet-dark.qss").write_text(dark_stylesheet.convert(light), encoding="utf-8")
        self.log = self.tmp / "calamares.log"
        self.calamares = script(self.tmp / "calamares",
                                f'#!/bin/sh\necho "backend=${{QT_QUICK_BACKEND:-}}" > "{self.log}"\n'
                                f'for arg in "$@"; do echo "$arg" >> "{self.log}"; done\n')

    def start(self, *options):
        env = {"PATH": "/usr/bin:/bin", "VELTOS_BRANDING": str(self.branding),
               "VELTOS_RUN_DIR": str(self.tmp / "run"), "VELTOS_ROOT_CONFIG": str(self.tmp / "root"),
               "VELTOS_CALAMARES": str(self.calamares)}
        subprocess.run(["sh", str(HELPERS / "start-calamares"), *options], env=env, check=True)
        lines = self.log.read_text(encoding="utf-8").splitlines()
        sheet = (self.tmp / "run/stylesheet.qss").read_text(encoding="utf-8")
        kvantum = (self.tmp / "root/Kvantum/kvantum.kvconfig").read_text(encoding="utf-8")
        return lines, sheet, kvantum

    def test_dark_with_the_users_accent_in_software(self):
        lines, sheet, kvantum = self.start("--dark", "--accent", "#E81123", "--software")
        self.assertEqual(lines[0], "backend=software")
        self.assertEqual(lines[1:5], ["-style", "veltos-installer", "-stylesheet", str(self.tmp / "run/stylesheet.qss")])
        self.assertEqual(lines[5], "veltos-theme=dark=1;accent=#E81123;software=1")
        self.assertIn("background-color: #1C1E24;", sheet)
        self.assertIn("background-color: #E81123;", sheet)
        self.assertIn("border: 1px solid #CE0F1F;", sheet)        # 89 % of the accent
        self.assertNotIn("#2F5EE6", sheet)
        self.assertIn("theme=VeltOSDark", kvantum)

    def test_light_by_default_and_bad_values_ignored(self):
        lines, sheet, kvantum = self.start("--light", "--accent", "red;reboot")
        self.assertEqual(lines[0], "backend=")
        self.assertEqual(lines[5], "veltos-theme=dark=0;accent=#2F5EE6;software=0")
        self.assertIn("background-color: #F3F5FA;", sheet)
        self.assertIn("theme=VeltOS\n", kvantum)

    def test_unknown_options_are_refused(self):
        env = {"PATH": "/usr/bin:/bin", "VELTOS_CALAMARES": str(self.calamares)}
        result = subprocess.run(["sh", str(HELPERS / "start-calamares"), "--stylesheet", "/etc/shadow"],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())


class WebsiteHelperTests(unittest.TestCase):
    """open-website opens only VeltOS' page, at most once in two seconds."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.opened = self.tmp / "opened"
        opener = script(self.tmp / "xdg-open", f'#!/bin/sh\necho "$@" >> "{self.opened}"\n')
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            self.port = probe.getsockname()[1]
        env = dict(os.environ, VELTOS_WEBSITE_PORT=str(self.port), VELTOS_XDG_OPEN=str(opener))
        self.helper = subprocess.Popen(["python3", str(HELPERS / "open-website")], env=env)
        self.addCleanup(self.helper.wait)
        self.addCleanup(self.helper.terminate)
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)

    def get(self, path):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request("GET", path)
        status = connection.getresponse().status
        connection.close()
        return status

    def test_opens_the_website_once(self):
        self.assertEqual(self.get("/website"), 204)
        self.assertEqual(self.get("/website"), 204)        # within two seconds: ignored
        self.assertEqual(self.get("/elsewhere?url=file:///etc"), 404)
        for _ in range(50):
            if self.opened.exists():
                break
            time.sleep(0.1)
        time.sleep(0.3)
        self.assertEqual(self.opened.read_text().splitlines(), ["https://veltos.ahmetfurkandemir.com/"])


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class QmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _kind, _context, message: cls.messages.append(message))

    def setUp(self):
        self.messages.clear()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def create(self, qml):
        path = self.tmp / "Test.qml"
        path.write_text(qml, encoding="utf-8")
        # Keep the engine and component alive, and keep the object from the
        # QML garbage collector (a created root object belongs to QML).
        self.engine = QQmlEngine()
        self.component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(path)))
        item = self.component.create()
        self.assertIsNotNone(item, self.component.errorString())
        QQmlEngine.setObjectOwnership(item, QQmlEngine.ObjectOwnership.CppOwnership)
        self.item = item
        return item

    def tearDown(self):
        from PySide6.QtCore import QCoreApplication, QEvent
        if getattr(self, "item", None) is not None:
            self.item.deleteLater()
        if getattr(self, "engine", None) is not None:
            self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_theme_argument(self):
        theme = QUrl.fromLocalFile(str(BRANDING / "VeltTheme.js")).toString()
        item = self.create(f'''
import QtQuick
import "{theme}" as Theme
Item {{
    property string dark: JSON.stringify(Theme.parse(["calamares", "veltos-theme=dark=1;accent=#e81123;software=1"]))
    property string bad: JSON.stringify(Theme.parse(["veltos-theme=dark=yes;accent=url(x);software"]))
    property bool defaultDark: Theme.dark
    property string defaultAccent: Theme.accent
    property string onYellow: Theme.luminance("#FFB900") > 0.45 ? "dark" : "light"
    property string onBlue: Theme.luminance("#2F5EE6") > 0.45 ? "dark" : "light"
}}''')
        self.assertEqual(json.loads(item.property("dark")), {"dark": True, "accent": "#E81123", "software": True})
        self.assertEqual(json.loads(item.property("bad")), {"dark": False, "accent": "#2F5EE6", "software": False})
        self.assertFalse(item.property("defaultDark"))              # no argument: the light look
        self.assertEqual(item.property("defaultAccent"), "#2F5EE6")
        self.assertEqual((item.property("onYellow"), item.property("onBlue")), ("dark", "light"))

    def test_progress_ring_loads_and_turns(self):
        item = self.create(f'''
import QtQuick
import "{BRANDING.as_uri()}"
VeltSpinner {{ width: 40; height: 40 }}''')
        start = item.property("phase")
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.02)
        self.assertGreater(item.property("phase"), start)
        item.setProperty("running", False)                  # stopped, it stays still
        self.app.processEvents()
        stopped = item.property("phase")
        time.sleep(0.2)
        self.app.processEvents()
        self.assertEqual(item.property("phase"), stopped)
        self.assertEqual([m for m in self.messages if "qml" in m.lower() or "error" in m.lower()], [])


if __name__ == "__main__":
    unittest.main()
