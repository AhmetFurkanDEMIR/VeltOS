"""Loads the real Graphics Cards window offscreen with recorded cards and
runs installations through a stand-in for pkcon (a shell script that
records its arguments). Any QML warning or error fails the test."""

import os
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

try:
    from PySide6.QtCore import (Q_ARG, Q_RETURN_ARG, QCoreApplication, QEvent, QMetaObject, QUrl,
                                qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import PySide6.QtQuick  # noqa: F401  (rootObjects()[0] as a QQuickWindow)
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from veltos_graphics import gpus  # noqa: E402
import samples  # noqa: E402

OPEN_STACK = {"firmware-amd-graphics": "20250410-2", "firmware-intel-graphics": "20250410-2",
              "mesa-vulkan-drivers": "25.0.7-2+deb13u1", "libgl1-mesa-dri": "25.0.7-2+deb13u1"}
# Stand-in for pkcon: records the arguments, reports progress like `pkcon -p`
# and, for changes, asks "Proceed with changes?" on its terminal as pkcon
# does without -y (ptyrun answers it; without an answer it gives up).
FAKE_PKCON = ('#!/bin/sh\n'
              'echo "$*" >> "$(dirname "$0")/calls"\n'
              'echo "Status:\tRunning"\n'
              'case "$*" in *install*|*update*|*remove*)\n'
              '  printf "Proceed with changes? [N/y] "; read answer\n'
              '  [ "$answer" = y ] || exit 4\n'
              '  echo "$answer" >> "$(dirname "$0")/answers";;\n'
              'esac\n'
              'echo "Percentage:\t40"\n'
              'if [ -n "$FAKE_PKCON_ERROR" ]; then echo "Fatal error: $FAKE_PKCON_ERROR"; exit 1; fi\n'
              'exit 0\n')


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def make(self, lspci=samples.LSPCI_NVIDIA_INTEL, installed=None, modules=("i915", "nouveau"),
             recommend="nvidia-driver", secure_boot=False, key_enrolled=True, outdated=list):
        from veltos_graphics import app
        folder = Path(tempfile.mkdtemp())
        self.fake = folder / "pkcon"
        self.fake.write_text(FAKE_PKCON, encoding="utf-8", newline="\n")
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IXUSR)
        self.calls_file = folder / "calls"
        self.installed = dict(OPEN_STACK) if installed is None else installed
        self.started = []
        self.backend = app.Backend(
            lang=self.lang, detect=lambda: gpus.parse_lspci(lspci), installed=lambda: dict(self.installed),
            modules=lambda: set(modules), recommend=lambda: recommend, available=lambda package: True,
            renderer=lambda: gpus.renderer(runner=lambda command, timeout=20: (0, samples.EGLINFO)),
            vulkan=lambda: ["llvmpipe (LLVM 19.1.7, 256 bits)"], secure_boot=lambda: secure_boot,
            key_enrolled=lambda: key_enrolled, memory=lambda slot: 8 << 30 if slot == "01:00.0" else 0,
            version=lambda driver: "550.163.01" if driver == "nvidia" else "",
            is_boot=lambda slot: slot == "00:02.0", start=self.started.append, program=str(self.fake),
            needs_refresh=lambda: False, outdated=outdated, arch="amd64", threaded=False,
            nvidia_packages=lambda: ["nvidia-driver:amd64", "nvidia-kernel-dkms:amd64", "libnvidia-glcore:i386"])
        self.messages.clear()
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]
        self.addCleanup(self.dispose, self.engine)
        self.backend.refresh()
        self.app.processEvents()
        return self.backend

    def dispose(self, engine):
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def call(self, name, *args):
        result = QMetaObject.invokeMethod(self.window, name, *[Q_ARG("QVariant", a) for a in args])
        self.app.processEvents()
        return result

    def wait(self):
        deadline = time.monotonic() + 20
        while self.backend.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertEqual(self.backend.busy, "")
        self.app.processEvents()

    def calls(self):
        return self.calls_file.read_text().splitlines() if self.calls_file.exists() else []

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def card(self, slot):
        return next(c for c in self.backend.cards if c["slot"] == slot)

    def test_window_lists_cards(self):
        backend = self.make()
        self.assertTrue(backend.loaded)
        self.assertEqual([c["kind"] for c in backend.cards], ["intel", "nvidia"])
        intel, nvidia = backend.cards
        self.assertEqual(intel["state"], "ready")
        self.assertEqual(intel["driverName"], backend.texts["drv_i915"])
        self.assertEqual(nvidia["state"], "available")
        self.assertEqual(nvidia["driverName"], backend.texts["drv_nouveau"])
        # The renderer belongs to the card the PC draws with (Intel here).
        labels = [p["label"] for p in intel["properties"]]
        self.assertIn(backend.texts["p_renderer"], labels)
        self.assertNotIn(backend.texts["p_renderer"], [p["label"] for p in nvidia["properties"]])
        memory = next(p["value"] for p in nvidia["properties"] if p["label"] == backend.texts["p_memory"])
        self.assertEqual(memory, "8.0 GB" if self.lang == "en" else "8,0 GB")
        self.assertEqual(self.window.property("title"), backend.texts["app_title"])
        self.assertEqual(self.call_text("buttonTexts", 0), backend.texts["update_driver"])
        self.assertEqual(self.call_text("buttonTexts", 1), backend.texts["install_driver"])
        for slot in ("00:02.0", "01:00.0"):
            self.call("toggle", slot)
        self.window.setProperty("width", 640)
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def call_text(self, name, *args):
        return QMetaObject.invokeMethod(self.window, name, Q_RETURN_ARG("QVariant"),
                                        *[Q_ARG("QVariant", a) for a in args])

    def test_install_nvidia_driver(self):
        backend = self.make()
        self.call("press", "01:00.0", "install")
        self.wait()
        self.assertEqual(self.calls(), ["-p install nvidia-detect:amd64",
                                        "-p install nvidia-driver:amd64 linux-headers-amd64:amd64"])
        # Interactive transactions (no -y), so polkit asks for the password.
        self.assertEqual((self.fake.parent / "answers").read_text().split(), ["y", "y"])
        nvidia = self.card("01:00.0")
        self.assertEqual(nvidia["message"], backend.texts["done_install"])
        self.assertTrue(nvidia["messageOk"])
        self.assertEqual(self.problems(), [])

    def test_installed_driver_asks_for_restart_and_key(self):
        backend = self.make(installed=dict(OPEN_STACK, **{"nvidia-driver": "550.163.01-2", "nvidia-detect": "1"}),
                            secure_boot=True, key_enrolled=False)
        nvidia = self.card("01:00.0")
        self.assertEqual(nvidia["state"], "restart")
        self.assertTrue(nvidia["needsKey"])
        self.assertEqual(self.call_text("buttonTexts", 1), backend.texts["restart_now"])
        self.call("press", "01:00.0", "restart")
        from veltos_graphics.app import REBOOT
        self.assertEqual(self.started, [REBOOT])
        backend.registerKey("one", "two")
        self.assertEqual(backend.keyMessage, backend.texts["sb_mismatch"])
        self.call("toggle", "01:00.0")
        self.assertEqual(self.problems(), [])

    def test_driver_in_use_updates_and_goes_back(self):
        lspci = samples.LSPCI_NVIDIA_INTEL.replace("Driver:\tnouveau", "Driver:\tnvidia")
        backend = self.make(lspci=lspci, installed=dict(OPEN_STACK, **{"nvidia-driver": "550.163.01-2",
                                                                       "nvidia-kernel-dkms": "550.163.01-2"}),
                            modules=("i915", "nvidia"))
        nvidia = self.card("01:00.0")
        self.assertEqual((nvidia["state"], nvidia["driverName"]), ("proprietary", backend.texts["drv_nvidia"]))
        values = {p["label"]: p["value"] for p in nvidia["properties"]}
        self.assertEqual(values[backend.texts["p_driver_version"]], "550.163.01")
        self.assertEqual(values[backend.texts["p_package"]], "nvidia-driver 550.163.01-2")
        self.call("press", "01:00.0", "update")
        self.wait()
        self.assertEqual(self.calls(), ["-p refresh", "-p update nvidia-driver:amd64"])
        self.assertEqual(self.card("01:00.0")["message"], backend.texts["done_update"])
        self.calls_file.unlink()
        self.call("press", "01:00.0", "open")
        self.wait()
        self.assertEqual(self.calls(), ["-p remove nvidia-driver:amd64 nvidia-kernel-dkms:amd64 libnvidia-glcore:i386"])
        self.assertEqual(self.problems(), [])

    def test_up_to_date(self):
        backend = self.make(lspci=samples.LSPCI_AMD, outdated=lambda packages: [])
        self.call("press", "03:00.0", "update")
        self.wait()
        self.assertEqual(self.calls(), ["-p refresh"])
        self.assertEqual(self.card("03:00.0")["message"], backend.texts["done_current"])
        self.assertTrue(self.card("03:00.0")["messageOk"])
        self.calls_file.unlink()
        backend._outdated = lambda packages: ["mesa-vulkan-drivers"]
        self.call("press", "03:00.0", "update")
        self.wait()
        self.assertEqual(self.calls(), ["-p refresh", "-p update mesa-vulkan-drivers:amd64"])
        self.assertEqual(self.card("03:00.0")["message"], backend.texts["done_update"])
        self.assertEqual(self.problems(), [])

    def test_failed_installation(self):
        backend = self.make(installed={"mesa-vulkan-drivers": "1", "libgl1-mesa-dri": "1"},
                            lspci=samples.LSPCI_AMD)
        (card,) = backend.cards
        self.assertEqual(card["state"], "missing")
        self.assertIn("firmware-amd-graphics", card["stateText"])
        os.environ["FAKE_PKCON_ERROR"] = "Not authorized"
        try:
            self.call("press", "03:00.0", "install")
            self.wait()
        finally:
            del os.environ["FAKE_PKCON_ERROR"]
        self.assertEqual(self.calls(), ["-p install firmware-amd-graphics:amd64"])
        (card,) = backend.cards
        self.assertFalse(card["messageOk"])
        self.assertIn(backend.texts["failed_auth"], card["message"])
        self.assertEqual(self.problems(), [])

    def test_legacy_card(self):
        backend = self.make(lspci=samples.LSPCI_OLD_NVIDIA, installed={}, recommend="unsupported")
        (card,) = backend.cards
        self.assertEqual((card["state"], card["action"]), ("unsupported", ""))
        self.assertEqual(self.call_text("buttonTexts", 0), "")
        self.assertEqual(self.problems(), [])

    def test_virtual_card(self):
        backend = self.make(lspci=samples.LSPCI_VIRTIO)
        (card,) = backend.cards
        self.assertEqual((card["state"], card["driverName"]), ("virtual", backend.texts["drv_virtual"]))
        self.assertEqual(self.problems(), [])

    def test_no_cards(self):
        backend = self.make(lspci="")
        self.assertEqual(backend.cards, [])
        self.assertEqual(self.problems(), [])


class TurkishWindowTests(WindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
