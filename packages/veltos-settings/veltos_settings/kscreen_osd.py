"""The display chooser that appears when a screen is plugged in.

KScreen (kded) asks the D-Bus service org.kde.kscreen.osdService to "show
the action selector" when a second screen is connected and to hide it when
it is gone. Plasma's own service drew KDE's old row of pictures (Switch to
external screen, Extend to left ...). VeltOS takes that bus name instead
(a drop-in for plasma-kscreen-osd.service starts this program) and shows
Windows 11's Project flyout, `veltos-settings --project` (project.py), so
plugging in a screen gives the same choices as Windows + P (product owner,
2026-10-26: "the options that come up are still Debian's").

The interface is KScreen's own (osd/org.kde.kscreen.osdService.xml,
kscreen 6.3): showActionSelector() and hideOsd(), no arguments. The program
ends after a minute without a flyout; D-Bus starts it again when needed.
"""

import subprocess
import sys

BUS_NAME = "org.kde.kscreen.osdService"
OBJECT_PATH = "/org/kde/kscreen/osdService"
INTERFACE = """<node>
  <interface name="org.kde.kscreen.osdService">
    <method name="hideOsd"/>
    <method name="showActionSelector"/>
  </interface>
</node>"""
FLYOUT = ["veltos-settings", "--project"]
IDLE_SECONDS = 60


class OsdService:
    """showActionSelector / hideOsd on the flyout's process."""

    def __init__(self, start=None):
        self._start = start or (lambda command: subprocess.Popen(command, start_new_session=True,
                                                                  stdin=subprocess.DEVNULL))
        self.flyout = None

    def showing(self):
        return self.flyout is not None and self.flyout.poll() is None

    def show(self):
        # A flyout already open keeps its place (KScreen may ask twice).
        if not self.showing():
            self.flyout = self._start(FLYOUT)

    def hide(self):
        if self.showing():
            self.flyout.terminate()
        self.flyout = None

    def call(self, method):
        if method == "showActionSelector":
            self.show()
        elif method == "hideOsd":
            self.hide()
        else:
            raise ValueError(method)


def main():
    from gi.repository import Gio, GLib

    service = OsdService()
    loop = GLib.MainLoop()
    node = Gio.DBusNodeInfo.new_for_xml(INTERFACE)
    idle = {"seconds": 0}

    def on_call(connection, sender, path, interface, method, parameters, invocation):
        try:
            service.call(method)
        except (OSError, ValueError) as error:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.Failed", str(error))
            return
        idle["seconds"] = 0
        invocation.return_value(None)

    def on_bus(connection, name):
        connection.register_object(OBJECT_PATH, node.interfaces[0], on_call, None, None)

    def tick():
        idle["seconds"] = 0 if service.showing() else idle["seconds"] + 5
        if idle["seconds"] >= IDLE_SECONDS:
            loop.quit()
            return False
        return True

    Gio.bus_own_name(Gio.BusType.SESSION, BUS_NAME, Gio.BusNameOwnerFlags.NONE,
                     on_bus, None, lambda *_: loop.quit())
    GLib.timeout_add_seconds(5, tick)
    loop.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
