"""Qt WebEngine must be initialized before the test QGuiApplication."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")

APP = None


def application():
    global APP
    if APP is None:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtWebEngineQuick import QtWebEngineQuick
        QtWebEngineQuick.initialize()
        APP = QGuiApplication.instance() or QGuiApplication(["veltos-maps-tests"])
    return APP
