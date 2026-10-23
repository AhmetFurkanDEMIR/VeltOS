"""VeltOS Calendar: the iCalendar file, repeating events, reminders and the
window (offscreen, English and Turkish)."""

import datetime
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from veltos_calendar import store, strings  # noqa: E402

D = datetime.datetime


class StoreTests(unittest.TestCase):
    def test_round_trip_through_icalendar(self):
        events = [
            store.Event("Doktor; kontrol, 2. kat", D(2026, 10, 22, 9, 30), D(2026, 10, 22, 10, 15),
                        location="Ankara", notes="Satır 1\nSatır 2", reminder=30, repeat="weekly"),
            store.Event("Bayram", D(2026, 10, 29), D(2026, 10, 30), all_day=True, reminder=-1),
        ]
        text = store.to_ics(events)
        self.assertIn("SUMMARY:Doktor\\; kontrol\\, 2. kat", text)
        self.assertIn("DTSTART;VALUE=DATE:20261029", text)
        self.assertIn("RRULE:FREQ=WEEKLY", text)
        self.assertIn("TRIGGER:-PT30M", text)
        self.assertTrue(all(len(line.encode()) <= 75 for line in text.split("\r\n")))
        again = store.from_ics(text)
        self.assertEqual([(e.title, e.start, e.end, e.all_day, e.location, e.notes, e.repeat, e.reminder, e.uid)
                          for e in again],
                         [(e.title, e.start, e.end, e.all_day, e.location, e.notes, e.repeat, e.reminder, e.uid)
                          for e in events])

    def test_reads_other_programs_files(self):
        text = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:x1\r\nDTSTART:20261022T070000Z\r\n"
                "DTEND:20261022T080000Z\r\nSUMMARY:A very long title that continues on the next\r\n  line\r\n"
                "RRULE:FREQ=MONTHLY;COUNT=3\r\nBEGIN:VALARM\r\nTRIGGER:-P1D\r\nEND:VALARM\r\nEND:VEVENT\r\n"
                "BEGIN:VEVENT\r\nUID:x2\r\nDTSTART;VALUE=DATE:20261101\r\nSUMMARY:No end\r\nEND:VEVENT\r\n"
                "END:VCALENDAR\r\n")
        first, second = store.from_ics(text)
        self.assertEqual(first.title, "A very long title that continues on the next line")
        self.assertEqual((first.repeat, first.reminder), ("monthly", 1440))
        self.assertEqual(first.duration(), datetime.timedelta(hours=1))
        self.assertEqual((second.all_day, second.end - second.start, second.reminder),
                         (True, datetime.timedelta(days=1), -1))

    def test_saving_and_loading_the_file(self):
        path = Path(tempfile.mkdtemp()) / "sub" / "calendar.ics"
        store.save([store.Event("A", D(2026, 1, 1, 8), D(2026, 1, 1, 9))], path)
        self.assertEqual([e.title for e in store.load(path)], ["A"])
        self.assertEqual(store.load(path.parent / "missing.ics"), [])

    def test_repeating_events(self):
        weekly = store.Event("Ders", D(2026, 10, 5, 10), D(2026, 10, 5, 11), repeat="weekly")
        monthly = store.Event("Kira", D(2026, 1, 31), D(2026, 2, 1), all_day=True, repeat="monthly")
        found = store.occurrences([weekly, monthly], D(2026, 10, 1), D(2026, 11, 1))
        self.assertEqual([s.day for e, s, _ in found if e is weekly], [5, 12, 19, 26])
        # The 31st: months without one are skipped, as Windows does.
        months = store.occurrences([monthly], D(2026, 1, 1), D(2027, 1, 1))
        self.assertEqual([s.month for _e, s, _end in months], [1, 3, 5, 7, 8, 10, 12])
        yearly = store.Event("Doğum günü", D(2024, 2, 29), D(2024, 3, 1), all_day=True, repeat="yearly")
        self.assertEqual([s.year for _e, s, _end in store.occurrences([yearly], D(2024, 1, 1), D(2033, 1, 1))],
                         [2024, 2028, 2032])
        daily = store.Event("İlaç", D(2025, 1, 1, 21), D(2025, 1, 1, 21, 5), repeat="daily")
        self.assertEqual(len(store.occurrences([daily], D(2026, 10, 1), D(2026, 10, 8))), 7)

    def test_reminders(self):
        event = store.Event("Toplantı", D(2026, 10, 22, 14), D(2026, 10, 22, 15), reminder=15)
        whole_day = store.Event("Tatil", D(2026, 10, 23), D(2026, 10, 24), all_day=True, reminder=1440)
        self.assertEqual(store.due_reminders([event, whole_day], D(2026, 10, 22, 13, 40), D(2026, 10, 22, 13, 45)),
                         [(event, D(2026, 10, 22, 14))])
        self.assertEqual(store.due_reminders([event], D(2026, 10, 22, 13, 45), D(2026, 10, 22, 13, 50)), [])
        self.assertEqual(store.due_reminders([whole_day], D(2026, 10, 21, 23, 59), D(2026, 10, 22, 0, 0)),
                         [(whole_day, D(2026, 10, 23))])
        self.assertEqual(store.next_reminder([event], D(2026, 10, 22, 12)), D(2026, 10, 22, 13, 45))
        self.assertIsNone(store.next_reminder([store.Event("x", D(2026, 1, 1), D(2026, 1, 2), reminder=-1)],
                                              D(2026, 10, 22)))

    def test_texts_in_both_languages(self):
        for key, (english, turkish) in strings.TEXTS.items():
            self.assertTrue(english and turkish, key)
        self.assertEqual(strings.language({"LANGUAGE": "tr@veltos:tr"}), "tr")


try:
    from PySide6.QtGui import QGuiApplication
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []

        def handler(kind, _context, message):
            if kind != QtMsgType.QtDebugMsg:
                cls.messages.append(message)
        qInstallMessageHandler(handler)

    def setUp(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlApplicationEngine
        # So that the root object comes back as a QQuickWindow (contentItem()).
        from PySide6.QtQuick import QQuickWindow  # noqa: F401
        from veltos_calendar import app
        self.messages.clear()
        self.path = Path(tempfile.mkdtemp()) / "calendar.ics"
        store.save([store.Event("Ders", D(2026, 10, 5, 10), D(2026, 10, 5, 11), repeat="weekly"),
                    store.Event("Tatil", D(2026, 10, 29), D(2026, 10, 30), all_day=True)], self.path)
        self.backend = app.Backend(lang=self.lang, path=self.path, today=datetime.date(2026, 10, 22))
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.window = self.engine.rootObjects()[0]
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.engine.deleteLater()
        from PySide6.QtCore import QCoreApplication, QEvent
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower() or "undefined" in m.lower()]

    @staticmethod
    def find_item(item, name):
        """An item by objectName in the visual tree."""
        if item.objectName() == name:
            return item
        for child in item.childItems():
            found = WindowTests.find_item(child, name)
            if found is not None:
                return found
        return None

    def test_left_pane_keeps_its_width(self):
        # The left pane's layout expanded (its children fill their width)
        # and left the calendar a strip at the window's edge (VM, 2026-10-23).
        self.window.resize(1180, 760)
        self.app.processEvents()
        self.window.grabWindow()                    # lays the window out
        pane = self.find_item(self.window.contentItem(), "sidePane")
        view = self.find_item(self.window.contentItem(), "calendarView")
        self.assertIsNotNone(pane)
        self.assertIsNotNone(view)
        self.assertLessEqual(pane.width(), 288)
        self.assertGreater(view.width(), 800)

    def test_every_view_loads(self):
        for view in ("month", "week", "workweek", "day", "year"):
            self.backend.setView(view)
            self.app.processEvents()
            self.assertEqual(self.problems(), [], view)
        cells = self.backend.monthCells
        self.assertEqual(len(cells), 42)
        today = next(c for c in cells if c["today"])
        self.assertEqual(today["date"], "2026-10-22")
        days_with_lesson = [c["day"] for c in cells if any(e["title"] == "Ders" for e in c["events"])]
        self.assertTrue({5, 12, 19, 26} <= set(days_with_lesson))

    def test_new_event_saved_and_deleted(self):
        draft = self.backend.draft("2026-10-23", 9 * 60)
        self.assertEqual((draft["startTime"], draft["endTime"], draft["allDay"]), ("09:00", "09:30", False))
        draft["title"] = "Diş hekimi"
        self.assertTrue(self.backend.save(draft))
        saved = [e for e in store.load(self.path) if e.title == "Diş hekimi"]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].start, D(2026, 10, 23, 9))
        whole = self.backend.draft("2026-10-24", -1)
        whole.update(title="Gezi", endDate="2026-10-25")
        self.assertTrue(self.backend.save(whole))
        trip = next(e for e in store.load(self.path) if e.title == "Gezi")
        self.assertEqual((trip.start, trip.end, trip.all_day), (D(2026, 10, 24), D(2026, 10, 26), True))
        self.backend.remove(saved[0].uid)
        self.assertEqual([e.title for e in store.load(self.path) if e.title == "Diş hekimi"], [])
        self.assertFalse(self.backend.save({"title": "broken"}))
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_moving_one_occurrence_moves_the_series(self):
        form = self.backend.eventForm(next(e.uid for e in self.backend.events if e.title == "Ders"),
                                      "2026-10-19T10:00")
        self.assertEqual(form["startDate"], "2026-10-19")
        form["startTime"], form["endTime"] = "11:00", "12:00"
        self.assertTrue(self.backend.save(form))
        lesson = next(e for e in store.load(self.path) if e.title == "Ders")
        self.assertEqual((lesson.start, lesson.end), (D(2026, 10, 5, 11), D(2026, 10, 5, 12)))

    def test_navigation(self):
        self.backend.step(1)
        self.assertEqual(self.backend.cursor, "2026-11-01")
        self.backend.setView("week")
        self.backend.step(-1)
        self.assertEqual(self.backend.cursor, "2026-10-25")
        self.backend.goToday()
        self.assertEqual(self.backend.cursor, "2026-10-22")
        self.assertIn("2026", self.backend.title)

    def test_small_calendar_day_letters(self):
        self.assertEqual([d["mini"] for d in self.backend.weekDayNames],
                         ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"])


class TurkishWindowTests(WindowTests):
    lang = "tr"

    def test_turkish_names(self):
        self.assertEqual(self.backend.weekDayNames[0]["long"], "Pazartesi")     # weeks start on Monday
        self.assertTrue(self.backend.title.startswith("Ekim"))

    def test_small_calendar_day_letters(self):
        # Not "Pz" for Monday: Qt's "Pzt" cut to two letters reads as Pazar (Sunday).
        self.assertEqual([d["mini"] for d in self.backend.weekDayNames],
                         ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pa"])


if __name__ == "__main__":
    unittest.main()
