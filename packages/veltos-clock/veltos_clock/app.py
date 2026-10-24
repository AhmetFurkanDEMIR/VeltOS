"""VeltOS Clock: Python backend for the QML window (Windows 11 Clock layout).

    veltos-clock [focus|timer|alarm|stopwatch|world]

Alarms, timers and world clocks live in clock.json (store.py), which the
alarm agent (agent.py) reads to ring while the app is closed. The
stopwatch runs in the window only.
"""

import configparser
import datetime
import os
import sys
import time
import zoneinfo
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import store, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
PAGES = ("focus", "timer", "alarm", "stopwatch", "world")


def kde_value(group, key):
    """A kdeglobals value as the session sees it (user, kdedefaults, /etc/xdg)."""
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for path in (home / "kdeglobals", home / "kdedefaults/kdeglobals", Path("/etc/xdg/kdeglobals")):
        parser = configparser.RawConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            continue
        if parser.has_option(group, key):
            return parser.get(group, key)
    return ""


def text_scale():
    """Text size chosen in Settings > Accessibility (the KDE font size over
    its default of 10 pt)."""
    parts = kde_value("General", "font").split(",")
    try:
        return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
    except ValueError:
        return 1.0


def accent_colour():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def city_name(zone):
    return zone.split("/")[-1].replace("_", " ")


REGION_ORDER = ("Europe", "America", "Asia", "Africa", "Australia", "Pacific", "Indian", "Atlantic",
                "Antarctica", "Arctic")


def zone_list():
    """[{zone, city, region}] of the time zones with a city name. tzdata
    keeps old names as links (Asia/Istanbul for Europe/Istanbul): one entry
    per city, the usual region first."""
    found = {}
    for zone in sorted(zoneinfo.available_timezones()):
        if "/" not in zone or zone.startswith(("Etc/", "SystemV/", "US/", "posix", "right")):
            continue
        region = zone.split("/")[0]
        rank = REGION_ORDER.index(region) if region in REGION_ORDER else len(REGION_ORDER)
        city = city_name(zone)
        if city not in found or rank < found[city][0]:
            found[city] = (rank, {"zone": zone, "city": city, "region": region})
    return sorted((entry for _rank, entry in found.values()), key=lambda z: z["zone"])


def offset_text(zone, now, lang):
    """"3 hours ahead", "Same as local time", with the day where it differs."""
    try:
        there = now.astimezone(zoneinfo.ZoneInfo(zone))
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        return "", "", ""
    local = now.astimezone()
    diff = (there.utcoffset() - local.utcoffset()).total_seconds() / 3600
    hours = abs(diff)
    hours_text = f"{hours:g}"
    if diff == 0:
        offset = strings.text(lang, "same_time")
    elif diff > 0:
        offset = strings.text(lang, "hour_ahead") if hours == 1 else strings.text(lang, "hours_ahead", h=hours_text)
    else:
        offset = strings.text(lang, "hour_behind") if hours == 1 else strings.text(lang, "hours_behind", h=hours_text)
    day = ""
    if there.date() > local.date():
        day = strings.text(lang, "tomorrow")
    elif there.date() < local.date():
        day = strings.text(lang, "yesterday")
    return there.strftime("%H:%M"), offset, day


class Backend(QObject):
    changed = Signal()
    tick = Signal()                  # once a second: clocks, timers
    focusChanged = Signal()
    message = Signal(str, str)       # notification (summary, body) the window shows

    def __init__(self, lang=None, path=None, start_page="focus", parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.path = path or store.data_path()
        self.data = store.load(self.path)
        self._page = start_page if start_page in PAGES else "focus"
        self._zones = None
        self._focus_end = 0.0
        self._focus_minutes = int(self.data.get("focus", {}).get("minutes", 30) or 30)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def save(self):
        store.save(self.data, self.path)
        self.changed.emit()

    def _on_tick(self):
        now = time.time()
        if self._focus_end and now >= self._focus_end:
            self._focus_end = 0.0
            self.focusChanged.emit()
            self.message.emit(self.text("focus_done"), self.text("focus_done_body"))
        self.tick.emit()

    # --- texts and look --------------------------------------------------------------

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Slot(str, str, str, result=str)
    def format(self, key, field, value):
        return strings.text(self.lang, key).replace("{" + field + "}", value)

    @Property(bool, constant=True)
    def darkMode(self):
        return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")

    @Property(str, constant=True)
    def accent(self):
        return accent_colour()

    @Property(float, constant=True)
    def textScale(self):
        return text_scale()

    @Property(str, constant=True)
    def startPage(self):
        return self._page

    @Property(bool, constant=True)
    def twelveHour(self):
        return self.lang != "tr"

    @Slot(str, result=str)
    def clockText(self, hhmm):
        """"07:30" as the locale shows it ("7:30 AM" in English)."""
        parsed = store.parse_time(hhmm)
        if parsed is None:
            return hhmm
        hours, minutes = parsed
        if not self.twelveHour:
            return f"{hours:02d}:{minutes:02d}"
        suffix = "AM" if hours < 12 else "PM"
        return f"{hours % 12 or 12}:{minutes:02d} {suffix}"

    # --- alarms ----------------------------------------------------------------------

    @Property("QVariantList", notify=changed)
    def alarms(self):
        now = datetime.datetime.now()
        result = []
        for alarm in self.data["alarms"]:
            when = store.next_ring(alarm, now)
            result.append(dict(alarm, repeatText=store.repeat_text(alarm.get("days", []), self.lang),
                               ringsIn=self._rings_in(when, now) if when else self.text("off"),
                               clockText=self.clockText(alarm.get("time", ""))))
        return sorted(result, key=lambda a: a.get("time", ""))

    def _rings_in(self, when, now):
        delta = max(0, int((when - now).total_seconds() // 60))
        days, rest = divmod(delta, 24 * 60)
        hours, minutes = divmod(rest, 60)
        if days:
            value = strings.text(self.lang, "days_hours", d=days, h=hours)
        elif hours:
            value = strings.text(self.lang, "hours_minutes", h=hours, m=minutes)
        else:
            value = strings.text(self.lang, "minutes_only", m=minutes)
        return strings.text(self.lang, "rings_in", time=value)

    @Slot(str, str, str, list, int)
    def saveAlarm(self, alarm_id, hhmm, name, days, snooze):
        if store.parse_time(hhmm) is None:
            return
        days = sorted({int(d) for d in days if 0 <= int(d) <= 6})
        for alarm in self.data["alarms"]:
            if alarm.get("id") == alarm_id:
                alarm.update({"time": hhmm, "name": name.strip(), "days": days, "snooze": int(snooze) or 10,
                              "enabled": True})
                alarm.pop("fired", None)
                alarm.pop("snoozed", None)
                break
        else:
            self.data["alarms"].append({"id": store.new_id(), "time": hhmm, "name": name.strip(), "days": days,
                                        "enabled": True, "snooze": int(snooze) or 10})
        self.save()

    @Slot(str, bool)
    def enableAlarm(self, alarm_id, on):
        for alarm in self.data["alarms"]:
            if alarm.get("id") == alarm_id:
                alarm["enabled"] = bool(on)
                alarm.pop("fired", None)
                alarm.pop("snoozed", None)
        self.save()

    @Slot(str)
    def deleteAlarm(self, alarm_id):
        self.data["alarms"] = [a for a in self.data["alarms"] if a.get("id") != alarm_id]
        self.save()

    # --- timers ----------------------------------------------------------------------

    @Property("QVariantList", notify=changed)
    def timers(self):
        return [dict(t) for t in self.data["timers"]]

    @Slot(str, result=float)
    def timerLeft(self, timer_id):
        for timer in self.data["timers"]:
            if timer.get("id") == timer_id:
                return store.timer_left(timer, time.time())
        return 0.0

    @Slot(float, result=str)
    def durationText(self, seconds):
        return store.format_duration(seconds)

    @Slot(str, int, str)
    def saveTimer(self, timer_id, seconds, name):
        seconds = max(1, int(seconds))
        for timer in self.data["timers"]:
            if timer.get("id") == timer_id:
                timer.update({"seconds": seconds, "name": name.strip()})
                store.reset_timer(timer)
                break
        else:
            self.data["timers"].append({"id": store.new_id(), "seconds": seconds, "name": name.strip(),
                                        "state": "idle"})
        self.save()

    @Slot(str, str)
    def timerAction(self, timer_id, action):
        now = time.time()
        for timer in self.data["timers"]:
            if timer.get("id") != timer_id:
                continue
            if action == "start":
                store.start_timer(timer, now)
            elif action == "pause":
                store.pause_timer(timer, now)
            elif action == "reset":
                store.reset_timer(timer)
            elif action == "delete":
                self.data["timers"].remove(timer)
            break
        self.save()

    # --- world clock -----------------------------------------------------------------

    @Property("QVariantList", notify=changed)
    def clocks(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        result = []
        for clock in self.data["clocks"]:
            zone = clock.get("zone", "")
            time_text, offset, day = offset_text(zone, now, self.lang)
            result.append({"zone": zone, "city": city_name(zone), "time": time_text, "offset": offset, "day": day})
        return result

    @Slot(str, result="QVariantList")
    def clockTimes(self, _tick):
        """Fresh times for the clocks list (called on every tick)."""
        return self.clocks

    @Slot(str, result="QVariantList")
    def searchZones(self, query):
        if self._zones is None:
            self._zones = zone_list()
        query = query.strip().casefold()
        if not query:
            return []

        def rank(zone):
            """Cities that start with the words typed come first ("ista":
            Istanbul before Boa Vista)."""
            city = zone["city"].casefold()
            if city.startswith(query):
                return 0
            if any(word.startswith(query) for word in city.split()):
                return 1
            return 2 if query in city else 3
        found = [z for z in self._zones if query in z["city"].casefold() or query in z["zone"].casefold()]
        found.sort(key=lambda z: (rank(z), z["city"]))
        return found[:12]

    @Slot(str)
    def addClock(self, zone):
        if zone and zone not in [c.get("zone") for c in self.data["clocks"]]:
            try:
                zoneinfo.ZoneInfo(zone)
            except (zoneinfo.ZoneInfoNotFoundError, ValueError):
                return
            self.data["clocks"].append({"zone": zone})
            self.save()

    @Slot(str)
    def removeClock(self, zone):
        self.data["clocks"] = [c for c in self.data["clocks"] if c.get("zone") != zone]
        self.save()

    @Property(str, notify=tick)
    def localTime(self):
        return datetime.datetime.now().strftime("%H:%M")

    @Property(str, notify=tick)
    def localDate(self):
        now = datetime.datetime.now()
        return now.strftime("%d %B %Y" if self.lang == "tr" else "%B %d, %Y")

    # --- focus sessions ---------------------------------------------------------------

    @Property(int, notify=focusChanged)
    def focusMinutes(self):
        return self._focus_minutes

    @Slot(int)
    def setFocusMinutes(self, minutes):
        self._focus_minutes = max(5, min(240, int(minutes)))
        self.data["focus"]["minutes"] = self._focus_minutes
        self.save()
        self.focusChanged.emit()

    @Property(bool, notify=focusChanged)
    def focusRunning(self):
        return self._focus_end > 0

    @Property(float, notify=tick)
    def focusLeft(self):
        return max(0.0, self._focus_end - time.time()) if self._focus_end else 0.0

    @Slot()
    def startFocus(self):
        self._focus_end = time.time() + self._focus_minutes * 60
        self._do_not_disturb(True)
        self.focusChanged.emit()

    @Slot()
    def endFocus(self):
        self._focus_end = 0.0
        self._do_not_disturb(False)
        self.focusChanged.emit()

    def _do_not_disturb(self, on):
        """Plasma's do-not-disturb (an end time; a far one means "until
        turned off"), as the clock flyout's focus session sets it."""
        import subprocess
        value = "2999,12,31,0,0,0" if on else ""
        try:
            subprocess.run(["kwriteconfig6", "--notify", "--file", "plasmanotifyrc", "--group", "DoNotDisturb",
                            "--key", "Until", value], capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass


def main(argv=None):
    argv = sys.argv if argv is None else argv
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")
    os.environ["QML_DISABLE_DISK_CACHE"] = "1"
    app = QGuiApplication(argv)
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-clock")
    app.setApplicationDisplayName(strings.text(strings.language(), "app_title"))
    app.setDesktopFileName("veltos-clock")
    app.setWindowIcon(QIcon.fromTheme("veltos-clock"))
    page = next((a for a in argv[1:] if a in PAGES), "focus")
    backend = Backend(start_page=page)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    code = app.exec()
    # The QML goes first: deleted after the objects it reads, its bindings
    # ran once more against dead ones ("Cannot call method ... of null").
    del engine
    return code
