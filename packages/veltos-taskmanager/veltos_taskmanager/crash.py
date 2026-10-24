"""A Windows 11 style notice when a program closes unexpectedly, instead of
KDE's crash handler DrKonqi (product owner, 2026-10-23: the "x closed
unexpectedly" notification in Windows 11's design).

systemd-coredump records every crash; DrKonqi's system service
(drkonqi-coredump-processor) passes the record of a user's crash, as JSON,
to that user's socket drkonqi-coredump-launcher.socket, which starts one
drkonqi-coredump-launcher@.service per crash. veltos-taskmanager replaces
that service's program with this one (a drop-in): for a program the user
started from an app (a .desktop file), one notification with the app's
name and icon, "<App> closed unexpectedly", and "Restart"; crashes of
background services stay silent, as on Windows. DrKonqi's window, its
"Report Bug" (to KDE's bug tracker) and its tray icon are not shown.
"""

import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

from . import strings, system

UNIT = re.compile(r"^app-(?P<id>.+?)(?:-\d+\.scope|@[^.]*\.service|\.scope|\.service)$")
WAIT_SECONDS = 300


def read_dump(fd=3):
    """The crash record systemd hands over on the accepted socket."""
    sock = socket.socket(fileno=fd)
    data = bytearray()
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        data += chunk
    sock.close()
    return json.loads(bytes(data).decode("utf-8", "replace"))


def unescape(name):
    """systemd's unit name escaping: "veltos\\x2dclock" -> "veltos-clock"."""
    return re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), name)


def desktop_id(dump):
    """The app a crashed process belonged to, from the unit Plasma started
    it in ("app-org.kde.konsole-48606.scope" -> "org.kde.konsole")."""
    match = UNIT.match(unescape(str(dump.get("COREDUMP_USER_UNIT", ""))))
    return match.group("id") if match else ""


def find_app(dump, lang="en", dirs=None):
    """{id, name, icon, path} of the crashed program's app, or None for a
    program without one (a background service)."""
    dirs = [Path(d) for d in (dirs or system.APPLICATION_DIRS)]
    wanted = desktop_id(dump)
    if not wanted:
        cmdline = str(dump.get("COREDUMP_CMDLINE", "")).split()
        program = system.program_of(str(dump.get("COREDUMP_COMM", "")), cmdline)
        app = system.AppIndex(dirs=dirs, lang=lang).lookup(program)
        if not app or app["hidden"]:
            return None
        wanted = app["id"].removesuffix(".desktop")
    for directory in dirs:
        path = directory / f"{wanted}.desktop"
        entry = system.read_desktop(path)
        if not entry:
            continue
        if entry.get("Type", "Application") != "Application":
            return None
        return {"id": wanted, "name": system.localized(entry, "Name", lang) or wanted,
                "icon": entry.get("Icon", "application-x-executable"), "path": str(path)}
    return None


def forget_kcrash_metadata(dump, cache=None):
    """KCrash leaves ~/.cache/kcrash-metadata/<program>.<boot>.<pid>.ini for
    DrKonqi; it is not needed any more."""
    cache = Path(cache or os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "kcrash-metadata"
    name = os.path.basename(str(dump.get("COREDUMP_EXE", "")))
    path = cache / f"{name}.{dump.get('_BOOT_ID', '')}.{dump.get('COREDUMP_PID', '')}.ini"
    try:
        path.unlink()
    except OSError:
        pass


def notification(app, texts):
    """(app name, icon, title, body, actions, hints) for Notify."""
    return (app["name"], app["icon"], texts["crash_title"].replace("{app}", app["name"]), texts["crash_body"],
            ["restart", texts["crash_restart"]], {"desktop-entry": app["id"]})


def notify_and_wait(app, texts, launch, wait=WAIT_SECONDS):
    """Shows the notice and restarts the app when "Restart" is chosen."""
    from gi.repository import Gio, GLib
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    name, icon, title, body, actions, hints = notification(app, texts)
    reply = bus.call_sync("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
                          "org.freedesktop.Notifications", "Notify",
                          GLib.Variant("(susssasa{sv}i)", (name, 0, icon, title, body, actions,
                                                          {k: GLib.Variant("s", v) for k, v in hints.items()}, -1)),
                          GLib.VariantType("(u)"), Gio.DBusCallFlags.NONE, -1, None)
    nid = reply.unpack()[0]
    loop = GLib.MainLoop()

    def on_signal(_bus, _sender, _path, _interface, signal, params):
        values = params.unpack()
        if values[0] != nid:
            return
        if signal == "ActionInvoked" and values[1] == "restart":
            launch(app)
        loop.quit()

    bus.signal_subscribe("org.freedesktop.Notifications", "org.freedesktop.Notifications", None,
                         "/org/freedesktop/Notifications", None, Gio.DBusSignalFlags.NONE, on_signal)
    GLib.timeout_add_seconds(wait, loop.quit)
    loop.run()


def launch(app):
    """Starts the app again through KIO, which gives it a unit of its own.
    Waits for kioclient: systemd ends everything left in this service's
    unit when it exits (a detached kioclient was killed before it started
    the app)."""
    try:
        subprocess.run(["kioclient", "exec", app["path"]], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        print(f"crash-notice: could not start {app['path']}: {error}", file=sys.stderr)


def main(argv=None, read=read_dump, notify=notify_and_wait):
    try:
        dump = read()
    except (OSError, ValueError) as error:
        print(f"crash-notice: no crash record: {error}", file=sys.stderr)
        return 0
    forget_kcrash_metadata(dump)
    if dump.get("_DRKONQI_PICKUP"):
        # DrKonqi's sign-in pick-up of earlier crashes (veltos-taskmanager
        # also turns that service off): Windows does not announce them again.
        return 0
    lang = strings.language()
    app = find_app(dump, lang)
    if app is None:
        print(f"crash-notice: {dump.get('COREDUMP_EXE', '?')} (pid {dump.get('COREDUMP_PID', '?')}) closed; "
              "no app of the user, no notice", file=sys.stderr)
        return 0
    notify(app, strings.texts(lang), launch)
    return 0
