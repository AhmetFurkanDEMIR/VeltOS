"""The update notification: a toast in the screen's bottom right corner (Plasma's
notifications, VeltOS' slide-in toasts) with "View update", which opens
VeltOS Settings > VeltOS Update. Sent over D-Bus with GLib (python3-gi);
the program waits for the click (an hour at most) and hands Plasma's
activation token to Settings, so its window comes to the front.
"""

import os
import re
import subprocess
from pathlib import Path

TEXTS = {
    "release_title": ("VeltOS {version} is ready", "VeltOS {version} hazır"),
    "release_body": ("New features and fixes are ready to install. Your files and apps stay as they are.",
                     "Yeni özellikler ve düzeltmeler yüklenmeye hazır. Dosyalarınız ve uygulamalarınız olduğu "
                     "gibi kalır."),
    "updates_title": ("Updates are ready", "Güncellemeler hazır"),
    "updates_body": ("{count} updates for your PC, security fixes among them.",
                     "Bilgisayarınız için {count} güncelleme var, güvenlik düzeltmeleri de aralarında."),
    "updates_body_1": ("1 update for your PC.", "Bilgisayarınız için 1 güncelleme var."),
    "view": ("View update", "Güncellemeyi görüntüle"),
    "app": ("VeltOS Update", "VeltOS Güncelleme"),
}
ICON = "software-update-available"


def language(environ=None, home=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable, "")
        if value:
            return "tr" if value.split(":")[0].lower().startswith("tr") else "en"
    # A user service may start without the session's language: Plasma keeps it here.
    try:
        text = (Path(home or Path.home()) / ".config/plasma-localerc").read_text(encoding="utf-8")
        match = re.search(r"^LANGUAGE=(\S+)", text, re.M) or re.search(r"^LANG=(\S+)", text, re.M)
        if match:
            return "tr" if match.group(1).lower().startswith("tr") else "en"
    except OSError:
        pass
    return "en"


def texts(lang):
    index = 1 if lang == "tr" else 0
    return {key: pair[index] for key, pair in TEXTS.items()}


def message(kind, latest, count, lang):
    """(summary, body) of the notification."""
    t = texts(lang)
    if kind == "release":
        return t["release_title"].replace("{version}", latest["version"]), t["release_body"]
    body = t["updates_body_1"] if count == 1 else t["updates_body"].replace("{count}", str(count))
    return t["updates_title"], body


def settings_command(token=""):
    """VeltOS Settings' update page as a user service of its own: the
    check runs in veltos-update-check.service, and systemd stops whatever is
    left in a service's cgroup when its main process ends (Settings opened
    for a moment and closed again, dev VM 2026-11-02). systemd-run returns
    once the unit runs; the user manager has the session's environment."""
    command = ["systemd-run", "--user", "--collect", "--quiet", "--slice=app.slice"]
    if token:
        command.append(f"--setenv=XDG_ACTIVATION_TOKEN={token}")
    return command + ["veltos-settings", "update"]


def open_settings(token="", run=subprocess.run):
    try:
        run(settings_command(token), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass


def send(kind, latest, count, lang=None, wait=3600, opener=open_settings):
    """Shows the notification and waits for its button; True when it was shown."""
    try:
        from gi.repository import Gio, GLib
    except ImportError:
        return False
    lang = lang or language()
    summary, body = message(kind, latest, count, lang)
    t = texts(lang)
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        hints = {"desktop-entry": GLib.Variant("s", "veltos-settings"), "urgency": GLib.Variant("y", 1)}
        reply = bus.call_sync("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
                              "org.freedesktop.Notifications", "Notify",
                              GLib.Variant("(susssasa{sv}i)", (t["app"], 0, ICON, summary, body,
                                                               ["default", t["view"], "view", t["view"]],
                                                               hints, 0)),
                              GLib.VariantType("(u)"), Gio.DBusCallFlags.NONE, -1, None)
    except GLib.Error:
        return False
    nid = reply.unpack()[0]
    loop = GLib.MainLoop()
    token = {"value": ""}

    def on_signal(_conn, _sender, _path, _iface, signal, params):
        values = params.unpack()
        if not values or values[0] != nid:
            return
        if signal == "ActivationToken":
            token["value"] = values[1]
        elif signal == "ActionInvoked":
            opener(token["value"])
            loop.quit()
        elif signal == "NotificationClosed":
            loop.quit()

    bus.signal_subscribe("org.freedesktop.Notifications", "org.freedesktop.Notifications", None,
                         "/org/freedesktop/Notifications", None, Gio.DBusSignalFlags.NONE, on_signal)
    GLib.timeout_add_seconds(wait, loop.quit)
    loop.run()
    return True
