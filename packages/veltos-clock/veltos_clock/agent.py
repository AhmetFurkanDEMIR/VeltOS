"""VeltOS Clock alarm agent: rings alarms and timers while the Clock app
is closed, as Windows' Clock does in the background.

    veltos-clock-agent         (started with the Plasma session)

Every 15 seconds (and whenever the app saves its file) it loads
clock.json (store.py), announces due alarms and finished timers with a
notification (Snooze / Dismiss for alarms) and plays the VeltOS alarm
sound until the notification is answered or two minutes have passed.
GLib and GDBus only (python3-gi): a small resident process with no
window, kept because an alarm has to ring with the app closed.

It also shows VeltOS Calendar's reminders (veltos-calendar, when it is
installed): one resident process for both, as Windows' notifications
come from the system, not from each app.
"""

import datetime
import os
import signal
import subprocess
import sys
import time

from . import store, strings

NOTIFY_BUS = "org.freedesktop.Notifications"
NOTIFY_PATH = "/org/freedesktop/Notifications"
CHECK_SECONDS = 15
RING_SECONDS = 120
SOUND_PATHS = ("/usr/share/sounds/veltos/stereo/alarm-clock-elapsed.wav",
               "/usr/share/sounds/ocean/stereo/alarm-clock-elapsed.oga",
               "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga")
PLAYERS = (["pw-play"], ["pw-cat", "-p"], ["paplay"], ["aplay", "-q"])


def sound_file():
    for path in SOUND_PATHS:
        if os.path.isfile(path):
            return path
    return ""


def play_once(path):
    """Start playing the sound once (a Popen, or None)."""
    if not path:
        return None
    for player in PLAYERS:
        try:
            return subprocess.Popen(player + [path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        except OSError:
            continue
    return None


class Ringer:
    """One ringing alarm or timer: its notification and the repeating sound."""

    def __init__(self, glib, kind, item_id, started):
        self.GLib = glib
        self.kind = kind
        self.item_id = item_id
        self.started = started
        self.notification_id = 0
        self.player = None
        self.stopped = False

    def tick(self, path):
        if self.stopped or time.monotonic() - self.started > RING_SECONDS:
            self.stop()
            return False
        if self.player is None or self.player.poll() is not None:
            self.player = play_once(path)
        return True

    def stop(self):
        self.stopped = True
        if self.player is not None and self.player.poll() is None:
            self.player.terminate()
        self.player = None


class Agent:
    def __init__(self, loop, connection, gio, glib, lang="en", path=None):
        self.loop = loop
        self.connection = connection
        self.Gio, self.GLib = gio, glib
        self.lang = lang
        self.path = path or store.data_path()
        self.ringing = {}            # notification id -> Ringer
        self.sound = sound_file()
        connection.signal_subscribe(None, NOTIFY_BUS, "ActionInvoked", NOTIFY_PATH, None,
                                    gio.DBusSignalFlags.NONE, self.on_action)
        connection.signal_subscribe(None, NOTIFY_BUS, "NotificationClosed", NOTIFY_PATH, None,
                                    gio.DBusSignalFlags.NONE, self.on_closed)
        # Calendar reminders are due after this moment (none from before
        # the session: Windows does not replay missed reminders either).
        self.calendar_checked = datetime.datetime.now()

    def text(self, key, **values):
        return strings.text(self.lang, key, **values)

    def notify(self, summary, body, actions):
        hints = {"urgency": self.GLib.Variant("y", 2), "desktop-entry": self.GLib.Variant("s", "veltos-clock"),
                 "resident": self.GLib.Variant("b", True)}
        reply = self.connection.call_sync(
            NOTIFY_BUS, NOTIFY_PATH, NOTIFY_BUS, "Notify",
            self.GLib.Variant("(susssasa{sv}i)", ("VeltOS Clock", 0, "veltos-clock", summary, body, actions, hints, 0)),
            None, self.Gio.DBusCallFlags.NONE, -1, None)
        return reply.unpack()[0]

    def check(self):
        """Due alarms and timers (called every CHECK_SECONDS and on file changes)."""
        data = store.load(self.path)
        now = datetime.datetime.now()
        changed = False
        for alarm, when in store.due_alarms(data, now):
            name = alarm.get("name") or self.text("alarm_notification")
            summary = f"{self.text('alarm_notification')} · {alarm.get('time', '')}"
            try:
                nid = self.notify(summary, name, ["snooze", self.text("snooze"), "dismiss", self.text("dismiss")])
            except Exception:
                nid = 0
            self.ringing[nid or -len(self.ringing) - 1] = Ringer(self.GLib, "alarm", alarm.get("id"), time.monotonic())
            store.ring(alarm, when)
            changed = True
        now_epoch = time.time()
        for timer in store.due_timers(data, now_epoch):
            name = timer.get("name") or self.text("unnamed_timer")
            try:
                nid = self.notify(self.text("timer_notification") + " · " + self.text("timer_done"),
                                  self.text("timer_body", name=name), ["dismiss", self.text("dismiss")])
            except Exception:
                nid = 0
            self.ringing[nid or -len(self.ringing) - 1] = Ringer(self.GLib, "timer", timer.get("id"), time.monotonic())
            timer["rang"] = True
            changed = True
        if changed:
            store.save(data, self.path)
        self.check_calendar(now)
        for key, ringer in list(self.ringing.items()):
            if not ringer.tick(self.sound):
                del self.ringing[key]
        return True

    def check_calendar(self, now):
        """VeltOS Calendar's reminders that fell due since the last look."""
        try:
            from veltos_calendar import store as calendar, strings as calendar_texts
        except ImportError:
            return
        since, self.calendar_checked = self.calendar_checked, now
        try:
            due = calendar.due_reminders(calendar.load(), since, now)
        except Exception:  # a broken calendar file must not stop the alarms
            return
        for event, start in due:
            title = event.title or calendar_texts.text(self.lang, "no_title")
            if event.all_day:
                body = start.strftime("%d.%m.%Y") if self.lang == "tr" else start.strftime("%B %d, %Y")
            elif abs((start - now).total_seconds()) < 60:
                body = calendar_texts.text(self.lang, "starts_now")
            else:
                body = calendar_texts.text(self.lang, "starts_at", time=start.strftime("%H:%M"))
            if event.location:
                body += "\n" + event.location
            hints = {"desktop-entry": self.GLib.Variant("s", "veltos-calendar")}
            try:
                self.connection.call_sync(
                    NOTIFY_BUS, NOTIFY_PATH, NOTIFY_BUS, "Notify",
                    self.GLib.Variant("(susssasa{sv}i)", (calendar_texts.text(self.lang, "app_title"), 0,
                                                          "veltos-calendar", title, body,
                                                          ["dismiss", calendar_texts.text(self.lang, "dismiss")],
                                                          hints, 0)),
                    None, self.Gio.DBusCallFlags.NONE, -1, None)
            except Exception:
                pass

    def on_action(self, _conn, _sender, _path, _iface, _signal, parameters):
        nid, action = parameters.unpack()
        ringer = self.ringing.pop(nid, None)
        if ringer is None:
            return
        ringer.stop()
        if action == "snooze" and ringer.kind == "alarm":
            data = store.load(self.path)
            for alarm in data["alarms"]:
                if alarm.get("id") == ringer.item_id:
                    store.snooze(alarm, datetime.datetime.now())
            store.save(data, self.path)
        try:
            self.connection.call_sync(NOTIFY_BUS, NOTIFY_PATH, NOTIFY_BUS, "CloseNotification",
                                      self.GLib.Variant("(u)", (nid,)), None, self.Gio.DBusCallFlags.NONE, -1, None)
        except Exception:
            pass

    def on_closed(self, _conn, _sender, _path, _iface, _signal, parameters):
        nid, _reason = parameters.unpack()
        ringer = self.ringing.pop(nid, None)
        if ringer is not None:
            ringer.stop()


def serve(_argv=None):
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    loop = GLib.MainLoop()
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    agent = Agent(loop, connection, Gio, GLib, strings.language())
    GLib.timeout_add_seconds(CHECK_SECONDS, agent.check)
    # A second look one second after the file changes (the app saved).
    folder = Gio.File.new_for_path(str(agent.path.parent))
    agent.path.parent.mkdir(parents=True, exist_ok=True)
    monitor = folder.monitor_directory(Gio.FileMonitorFlags.NONE, None)
    monitor.connect("changed", lambda *_args: GLib.timeout_add_seconds(1, lambda: agent.check() and False))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda *_a: loop.quit() or True)
    agent.check()
    loop.run()
    return 0


if __name__ == "__main__":
    sys.exit(serve(sys.argv))
