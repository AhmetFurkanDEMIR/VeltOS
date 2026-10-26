"""Load the real Maps window offscreen without network access."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import qtapp  # noqa: E402
from veltos_maps import app as maps_app  # noqa: E402
from veltos_maps.app import Backend  # noqa: E402

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl, qInstallMessageHandler  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402


class Runner:
    def __init__(self):
        self.enabled = False

    def __call__(self, command, **_kwargs):
        import subprocess
        if command[0] == "kreadconfig6":
            value = "true\n" if self.enabled else "false\n"
            return subprocess.CompletedProcess(command, 0, value, "")
        self.enabled = command[-1] == "true"
        value = ""
        return subprocess.CompletedProcess(command, 0, value, "")


class MapsWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qtapp.application()
        cls.messages = []
        qInstallMessageHandler(lambda _type, _ctx, message: cls.messages.append(message))

    def setUp(self):
        self.messages.clear()
        self.runner = Runner()
        import tempfile
        self.backend = Backend(
            settings_dir=tempfile.mkdtemp(),
            lang="en",
            runner=self.runner,
            start_url="about:blank",
            location_provider=lambda _cancel_event: (37.422, -122.084),
        )
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(maps_app.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)

    def tearDown(self):
        from PySide6.QtCore import QCoreApplication, QEvent
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def test_window_loads_and_defaults_location_off(self):
        window = self.engine.rootObjects()[0]
        self.assertEqual(window.title(), "Maps")
        self.assertFalse(self.backend.locationEnabled)
        window.grabWindow()
        self.app.processEvents()
        self.backend.setLocationEnabled(True)
        self.app.processEvents()
        self.assertTrue(self.backend.locationEnabled)
        self.backend.setLocationEnabled(False)
        self.app.processEvents()
        self.assertFalse(self.backend.locationEnabled)
        self.runner.enabled = True
        self.backend.refreshLocation()
        self.app.processEvents()
        self.assertTrue(self.backend.locationEnabled)
        errors = [message for message in self.messages
                  if "qml" in message.lower() or "error" in message.lower()
                  or "warning" in message.lower() or "undefined" in message.lower()]
        self.assertEqual(errors, [])

    def test_my_location_button_uses_the_opt_in_provider(self):
        window = self.engine.rootObjects()[0]
        button = window.findChild(QObject, "currentLocationButton")
        self.assertIsNotNone(button)
        self.assertFalse(button.isEnabled())

        self.backend.setLocationEnabled(True)
        self.assertTrue(button.isEnabled())
        loop = QEventLoop()
        self.backend.mapUrlChanged.connect(loop.quit)
        QTimer.singleShot(3000, loop.quit)
        self.backend.requestCurrentLocation()
        loop.exec()

        self.assertEqual(self.backend.mapUrl, "https://www.google.com/maps/@37.422000,-122.084000,16z?hl=en")
        self.assertEqual(self.backend.status, "Showing your current location.")

    def test_messages_and_default_location_bar(self):
        window = self.engine.rootObjects()[0]
        privacy = window.findChild(QObject, "privacyBar")
        self.assertTrue(privacy.property("visible"))
        self.backend.dismissPrivacyNote()
        self.app.processEvents()
        self.assertFalse(privacy.property("visible"))
        bar = window.findChild(QObject, "setDefaultBar")
        self.assertFalse(bar.property("visible"))
        self.backend.startSettingDefault()
        self.app.processEvents()
        self.assertTrue(bar.property("visible"))
        self.backend.cancelSettingDefault()
        self.backend.requestCurrentLocation()      # location off: an error bar
        self.app.processEvents()
        self.assertTrue(window.findChild(QObject, "statusBar").property("visible"))
        window.grabWindow()
        errors = [message for message in self.messages
                  if "qml" in message.lower() or "error" in message.lower()
                  or "warning" in message.lower() or "undefined" in message.lower()]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
