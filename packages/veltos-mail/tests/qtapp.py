"""One Qt application for every test module: Qt WebEngine must be set up
before the first QCoreApplication exists, so whichever test runs first
creates the (offscreen) QGuiApplication here."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
# The package build runs as root in a container: Chromium's sandbox cannot start there.
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")

APP = None


def application():
    global APP
    if APP is None:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtWebEngineQuick import QtWebEngineQuick
        QtWebEngineQuick.initialize()
        APP = QGuiApplication.instance() or QGuiApplication(["veltos-mail-tests"])
    return APP
