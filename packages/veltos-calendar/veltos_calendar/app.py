"""VeltOS Calendar: Windows 11's Calendar app.

The left pane has "New event", a small month calendar and the calendars;
the main area shows a day, the work week, a week, a month or a year, with
"Today" and the previous / next arrows above it. Clicking a free time or a
day opens Windows' quick "New event" card; an event opens its card with
Edit and Delete; "More details" is the full editor (place, all day, repeat,
reminder, description). Events live in an iCalendar file (store.py); VeltOS
Clock's background agent shows the reminders while Calendar is closed.

The grids are computed here and handed to Main.qml as plain lists.
"""

import datetime
import os
import sys
from pathlib import Path

from PySide6.QtCore import (Property, QDate, QDateTime, QFileSystemWatcher, QLocale, QObject, QTime, QTimer,
                            QUrl, Signal, Slot)
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import store, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
VIEWS = ("day", "workweek", "week", "month", "year")
MONTH_CHIPS = 3            # events shown in a month cell before "+N more"
# Two-letter weekday names of the small month calendar, Monday to Sunday,
# as in the taskbar clock's calendar (CLDR's short forms). Qt has no such
# format, and cutting its Turkish abbreviations to two letters gave "Pz"
# (Pzt) for Monday, which reads as Sunday (Pazar); other languages keep the
# first two letters of the abbreviation ("Mo", "Tu").
TWO_LETTER_DAYS = {"tr": ("Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pa")}


def kde_value(group, key, default=""):
    """A kdeglobals value (the user's file over /etc/xdg)."""
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for path in (home / "kdeglobals", Path("/etc/xdg/kdeglobals")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        section = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("["):
                section = line
            elif section == f"[{group}]" and line.startswith(key + "="):
                return line.split("=", 1)[1]
    return default


def accent_colour():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def dark_mode():
    for group, key in (("KDE", "LookAndFeelPackage"), ("General", "ColorScheme")):
        if "dark" in kde_value(group, key).lower():
            return True
    return False


def text_scale():
    parts = kde_value("General", "font").split(",")
    try:
        return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
    except ValueError:
        return 1.0


def week_start(day, first_weekday):
    """The first day of the week holding `day` (first_weekday: 1 = Monday ... 7 = Sunday)."""
    return day - datetime.timedelta(days=(day.isoweekday() - first_weekday) % 7)


def iso(day):
    return day.isoformat()


class Backend(QObject):
    changed = Signal()
    eventsChanged = Signal()

    def __init__(self, lang=None, path=None, today=None, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.locale = QLocale(QLocale.Language.Turkish, QLocale.Country.Turkey) if self.lang == "tr" \
            else QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self.first_weekday = int(self.locale.firstDayOfWeek().value)
        self.path = Path(path or store.calendar_path())
        self._fixed_today = today
        self.events = store.load(self.path)
        self._view = "month"
        self.start_new_event = False
        self._cursor = self.today()
        self._mini = self._cursor.replace(day=1)
        self.watcher = QFileSystemWatcher(self)
        self._watch()
        self.watcher.fileChanged.connect(self._reload)
        self.watcher.directoryChanged.connect(self._reload)
        # Midnight: "today" moves.
        self.midnight = QTimer(self)
        self.midnight.setInterval(60000)
        self.midnight.timeout.connect(self._check_day)
        self.midnight.start()
        self._last_day = self.today()

    # --- helpers -------------------------------------------------------------------------

    def today(self):
        return self._fixed_today or datetime.date.today()

    def text(self, key, **values):
        return strings.text(self.lang, key, **values)

    def _watch(self):
        folder = self.path.parent
        folder.mkdir(parents=True, exist_ok=True)
        if str(folder) not in self.watcher.directories():
            self.watcher.addPath(str(folder))
        if self.path.exists() and str(self.path) not in self.watcher.files():
            self.watcher.addPath(str(self.path))

    def _reload(self, _path=""):
        self.events = store.load(self.path)
        self._watch()
        self.eventsChanged.emit()

    def _check_day(self):
        if self.today() != self._last_day:
            self._last_day = self.today()
            self.eventsChanged.emit()

    def time_text(self, moment):
        return self.locale.toString(QTime(moment.hour, moment.minute), QLocale.FormatType.ShortFormat)

    def month_name(self, month, short=False):
        return self.locale.standaloneMonthName(month, QLocale.FormatType.ShortFormat if short
                                               else QLocale.FormatType.LongFormat)

    def day_name(self, weekday, short=False):
        return self.locale.standaloneDayName(weekday, QLocale.FormatType.ShortFormat if short
                                             else QLocale.FormatType.LongFormat)

    def colour(self, event):
        return store.COLOURS[0]

    def chip(self, event, start, end):
        return {"uid": event.uid, "title": event.title or self.text("no_title"),
                "time": "" if event.all_day else self.time_text(start),
                "range": "" if event.all_day else self.text("time_range", start=self.time_text(start),
                                                              end=self.time_text(end)),
                "allDay": event.all_day, "start": start.isoformat(timespec="minutes"),
                "colour": self.colour(event), "location": event.location,
                "repeats": event.repeat != "none"}

    def month_cells(self, first_of_month, with_events=True):
        start = week_start(first_of_month, self.first_weekday)
        days = [start + datetime.timedelta(days=i) for i in range(42)]
        by_day = {day: [] for day in days}
        if with_events:
            range_start = datetime.datetime.combine(days[0], datetime.time())
            range_end = datetime.datetime.combine(days[-1] + datetime.timedelta(days=1), datetime.time())
            for event, s, e in store.occurrences(self.events, range_start, range_end):
                day = max(s.date(), days[0])
                last = (e - datetime.timedelta(microseconds=1)).date()
                while day <= min(last, days[-1]):
                    by_day[day].append(self.chip(event, s, e))
                    day += datetime.timedelta(days=1)
        today = self.today()
        cells = []
        for day in days:
            chips = by_day[day]
            label = str(day.day)
            if day.day == 1:
                label = f"{day.day} {self.month_name(day.month, short=True)}"
            cells.append({"date": iso(day), "day": day.day, "label": label,
                          "inMonth": day.month == first_of_month.month, "today": day == today,
                          "selected": day == self._cursor, "events": chips[:MONTH_CHIPS],
                          "more": max(0, len(chips) - MONTH_CHIPS), "count": len(chips)})
        return cells

    def visible_days(self):
        if self._view == "day":
            return [self._cursor]
        start = week_start(self._cursor, self.first_weekday)
        if self._view == "workweek":
            monday = self._cursor - datetime.timedelta(days=self._cursor.weekday())
            return [monday + datetime.timedelta(days=i) for i in range(5)]
        return [start + datetime.timedelta(days=i) for i in range(7)]

    # --- for QML -------------------------------------------------------------------------

    @Slot(str, result=str)
    def tr(self, key):
        return self.text(key)

    @Slot(str, int, result=str)
    def trCount(self, key, count):
        return self.text(key, count=count)

    @Property(bool, constant=True)
    def darkMode(self):
        return dark_mode()

    @Property(str, constant=True)
    def accent(self):
        return accent_colour()

    @Property(float, constant=True)
    def textScale(self):
        return text_scale()

    @Property(str, notify=changed)
    def view(self):
        return self._view

    @Property(bool, constant=True)
    def startWithNewEvent(self):
        """`veltos-calendar new-event` (the launcher's action) opens the editor."""
        return self.start_new_event

    @Property(str, notify=changed)
    def cursor(self):
        return iso(self._cursor)

    @Property(str, notify=changed)
    def title(self):
        day = self._cursor
        if self._view == "year":
            return str(day.year)
        if self._view == "day":
            return self.locale.toString(QDate(day.year, day.month, day.day), QLocale.FormatType.LongFormat)
        if self._view in ("week", "workweek"):
            days = self.visible_days()
            first, last = days[0], days[-1]
            if first.month == last.month:
                return f"{self.month_name(first.month)} {first.year}"
            if first.year == last.year:
                return f"{self.month_name(first.month)} – {self.month_name(last.month)} {last.year}"
            return f"{self.month_name(first.month)} {first.year} – {self.month_name(last.month)} {last.year}"
        return f"{self.month_name(day.month)} {day.year}"

    @Property("QVariantList", notify=changed)
    def weekDayNames(self):
        names = []
        for i in range(7):
            weekday = (self.first_weekday - 1 + i) % 7 + 1
            short = self.day_name(weekday, short=True)
            mini = TWO_LETTER_DAYS[self.lang][weekday - 1] if self.lang in TWO_LETTER_DAYS else short[:2]
            names.append({"long": self.day_name(weekday), "short": short, "mini": mini,
                          "weekend": weekday in (6, 7)})
        return names

    @Property("QVariantList", notify=eventsChanged)
    def monthCells(self):
        return self.month_cells(self._cursor.replace(day=1))

    @Property("QVariantList", notify=eventsChanged)
    def miniCells(self):
        return self.month_cells(self._mini, with_events=False)

    @Property(str, notify=eventsChanged)
    def miniTitle(self):
        return f"{self.month_name(self._mini.month)} {self._mini.year}"

    @Property("QVariantList", notify=eventsChanged)
    def yearMonths(self):
        months = []
        for month in range(1, 13):
            first = datetime.date(self._cursor.year, month, 1)
            months.append({"month": month, "name": self.month_name(month),
                           "cells": self.month_cells(first, with_events=False)})
        return months

    @Property("QVariantList", notify=eventsChanged)
    def columns(self):
        """The days of the day / week views: all-day events, and timed ones
        with their minutes and side-by-side columns where they overlap."""
        result = []
        today = self.today()
        for day in self.visible_days():
            begin = datetime.datetime.combine(day, datetime.time())
            finish = begin + datetime.timedelta(days=1)
            all_day, timed = [], []
            for event, s, e in store.occurrences(self.events, begin, finish):
                chip = self.chip(event, s, e)
                if event.all_day or (e - s) >= datetime.timedelta(days=1):
                    all_day.append(chip)
                    continue
                chip["from"] = max(0, int((s - begin).total_seconds() // 60))
                chip["to"] = min(24 * 60, int((e - begin).total_seconds() // 60))
                timed.append(chip)
            # Overlapping events share the width, as in Windows.
            groups, ends = [], []
            for chip in timed:
                if groups and chip["from"] < max(ends[-1]):
                    groups[-1].append(chip)
                    ends[-1].append(chip["to"])
                else:
                    groups.append([chip])
                    ends.append([chip["to"]])
            for group in groups:
                lanes = []
                for chip in group:
                    lane = next((i for i, last in enumerate(lanes) if last <= chip["from"]), len(lanes))
                    if lane == len(lanes):
                        lanes.append(0)
                    lanes[lane] = chip["to"]
                    chip["lane"] = lane
                for chip in group:
                    chip["lanes"] = len(lanes)
            result.append({"date": iso(day), "number": day.day,
                           "name": self.day_name(day.isoweekday()),
                           "short": self.day_name(day.isoweekday(), short=True),
                           "today": day == today, "allDay": all_day, "timed": timed})
        return result

    @Property("QVariantList", constant=True)
    def reminderOptions(self):
        options = []
        for minutes in store.REMINDERS:
            if minutes < 0:
                label = self.text("reminder_none")
            elif minutes == 0:
                label = self.text("reminder_0")
            elif minutes < 60:
                label = self.text("reminder_minutes", count=minutes)
            elif minutes == 60:
                label = self.text("reminder_hour")
            elif minutes < 1440:
                label = self.text("reminder_hours", count=minutes // 60)
            elif minutes == 1440:
                label = self.text("reminder_day")
            else:
                label = self.text("reminder_week")
            options.append({"value": minutes, "label": label})
        return options

    @Property("QVariantList", constant=True)
    def repeatOptions(self):
        return [{"value": r, "label": self.text("repeat_" + r)} for r in store.REPEATS]

    @Property("QVariantList", constant=True)
    def timeOptions(self):
        """Every half hour, as Windows' time drop-down offers them."""
        return [{"value": f"{h:02d}:{m:02d}", "label": self.time_text(datetime.datetime(2000, 1, 1, h, m))}
                for h in range(24) for m in (0, 30)]

    @Slot(str)
    def setView(self, view):
        if view in VIEWS:
            self._view = view
            self.changed.emit()
            self.eventsChanged.emit()

    @Slot()
    def goToday(self):
        self.select(iso(self.today()))

    @Slot(str)
    def select(self, day):
        try:
            self._cursor = datetime.date.fromisoformat(day)
        except ValueError:
            return
        self._mini = self._cursor.replace(day=1)
        self.changed.emit()
        self.eventsChanged.emit()

    @Slot(int)
    def step(self, direction):
        """Previous (-1) or next (+1) day, week, month or year."""
        day = self._cursor
        if self._view == "day":
            day += datetime.timedelta(days=direction)
        elif self._view in ("week", "workweek"):
            day += datetime.timedelta(weeks=direction)
        elif self._view == "month":
            month = day.month - 1 + direction
            day = datetime.date(day.year + month // 12, month % 12 + 1, 1)
        else:
            day = datetime.date(day.year + direction, 1, 1)
        self.select(iso(day))

    @Slot(int)
    def stepMini(self, direction):
        month = self._mini.month - 1 + direction
        self._mini = datetime.date(self._mini.year + month // 12, month % 12 + 1, 1)
        self.eventsChanged.emit()

    @Slot(str, int, result="QVariantMap")
    def draft(self, day, minute):
        """A new event on `day` at `minute` (-1: a whole day), as the quick
        card starts it."""
        try:
            date = datetime.date.fromisoformat(day)
        except ValueError:
            date = self._cursor
        if minute < 0:
            start = datetime.datetime.combine(date, datetime.time())
            end = start + datetime.timedelta(days=1)
            all_day = True
        else:
            start = datetime.datetime.combine(date, datetime.time()) + datetime.timedelta(minutes=minute)
            end = start + datetime.timedelta(minutes=30)
            all_day = False
        return self.form(store.Event(title="", start=start, end=end, all_day=all_day, uid=""))

    def form(self, event, occurrence=None):
        start = occurrence or event.start
        end = start + event.duration()
        shown_end = end - datetime.timedelta(days=1) if event.all_day else end
        return {"uid": event.uid, "title": event.title, "location": event.location, "notes": event.notes,
                "allDay": event.all_day, "repeat": event.repeat, "reminder": event.reminder,
                "startDate": iso(start.date()), "startTime": f"{start:%H:%M}",
                "endDate": iso(shown_end.date()), "endTime": f"{end:%H:%M}",
                "when": self.when_text(event, start, end),
                "occurrence": start.isoformat(timespec="minutes")}

    def when_text(self, event, start, end):
        day = self.locale.toString(QDate(start.year, start.month, start.day), "dddd d MMMM yyyy"
                                   if self.lang == "tr" else "dddd, MMMM d, yyyy")
        if event.all_day:
            return day
        return f"{day}  {self.text('time_range', start=self.time_text(start), end=self.time_text(end))}"

    @Slot(str, str, result="QVariantMap")
    def eventForm(self, uid, occurrence):
        event = next((e for e in self.events if e.uid == uid), None)
        if event is None:
            return {}
        try:
            start = datetime.datetime.fromisoformat(occurrence) if occurrence else None
        except ValueError:
            start = None
        return self.form(event, start)

    @Slot("QVariantMap", result=bool)
    def save(self, form):
        """Saves the editor's fields; the date and time pickers give
        "YYYY-MM-DD" and "HH:MM"."""
        try:
            all_day = bool(form.get("allDay"))
            start = f"{form['startDate']}T{'00:00' if all_day else form['startTime']}"
            if all_day:
                end_day = datetime.date.fromisoformat(form["endDate"]) + datetime.timedelta(days=1)
                end = f"{iso(end_day)}T00:00"
            else:
                end = f"{form['endDate']}T{form['endTime']}"
            event = store.event_from_dict({"uid": form.get("uid", ""), "title": form.get("title", ""),
                                           "location": form.get("location", ""), "notes": form.get("notes", ""),
                                           "allDay": all_day, "start": start, "end": end,
                                           "repeat": form.get("repeat", "none"),
                                           "reminder": int(form.get("reminder", 15))})
        except (KeyError, ValueError, TypeError):
            return False
        old = next((e for e in self.events if e.uid == event.uid), None)
        if old is not None and old.repeat != "none" and form.get("occurrence"):
            # One occurrence of a repeating event was edited: the series
            # keeps its first day and moves by as much as the occurrence did
            # (VeltOS keeps a series together).
            try:
                occurrence = datetime.datetime.fromisoformat(form["occurrence"])
            except ValueError:
                occurrence = old.start
            length = event.end - event.start
            event.start = old.start + (event.start - occurrence)
            event.end = event.start + length
        self.events = [e for e in self.events if e.uid != event.uid] + [event]
        store.save(self.events, self.path)
        self._watch()
        self.select(iso(event.start.date()) if old is None else iso(self._cursor))
        return True

    @Slot(str)
    def remove(self, uid):
        self.events = [e for e in self.events if e.uid != uid]
        store.save(self.events, self.path)
        self.eventsChanged.emit()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")
    os.environ["QML_DISABLE_DISK_CACHE"] = "1"
    app = QGuiApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-calendar")
    app.setApplicationDisplayName(strings.text(strings.language(), "app_title"))
    app.setDesktopFileName("veltos-calendar")
    app.setWindowIcon(QIcon.fromTheme("veltos-calendar"))
    backend = Backend()
    if len(argv) > 1 and argv[1] in VIEWS:
        backend.setView(argv[1])
    backend.start_new_event = "new-event" in argv[1:]
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
