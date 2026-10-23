"""org.freedesktop.FileManager1 for File Explorer: programs ask the file
manager to show a folder or a file in its folder ("Show in folder" in
Firefox's downloads, for example). D-Bus starts this service on demand
(veltos-explorer --filemanager1); each request opens a File Explorer
window, a file selected in its folder. The service ends after a minute
without requests.
"""

import subprocess
import sys

from PySide6.QtCore import ClassInfo, QCoreApplication, QObject, QTimer, Slot

SERVICE = "org.freedesktop.FileManager1"
PATH = "/org/freedesktop/FileManager1"
IDLE_MS = 60000


def detached(command):
    subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@ClassInfo({"D-Bus Interface": SERVICE})
class FileManager1(QObject):
    def __init__(self, start=detached, idle=None):
        super().__init__()
        self.start = start
        self.idle = idle

    def _open(self, uris):
        if self.idle is not None:
            self.idle.start()
        uris = [u for u in uris if u]
        if uris:
            self.start(["veltos-explorer", *uris])

    @Slot("QStringList", str)
    def ShowFolders(self, uris, startup_id):  # noqa: N802 (D-Bus method names)
        self._open(uris)

    @Slot("QStringList", str)
    def ShowItems(self, uris, startup_id):  # noqa: N802
        self._open(uris)

    @Slot("QStringList", str)
    def ShowItemProperties(self, uris, startup_id):  # noqa: N802
        # Windows 11's Properties window (properties.py), not a folder.
        if self.idle is not None:
            self.idle.start()
        uris = [u for u in uris if u]
        if uris:
            self.start(["veltos-explorer", "--properties", *uris])


def serve(argv=None):
    from PySide6.QtDBus import QDBusConnection

    app = QCoreApplication(argv or sys.argv)
    idle = QTimer()
    idle.setSingleShot(True)
    idle.setInterval(IDLE_MS)
    idle.timeout.connect(app.quit)
    bus = QDBusConnection.sessionBus()
    service = FileManager1(idle=idle)
    if not bus.registerObject(PATH, service, QDBusConnection.RegisterOption.ExportAllSlots):
        return 1
    if not bus.registerService(SERVICE):
        return 1
    idle.start()
    return app.exec()
