"""When alarms and timers ring (store.py), the texts, and the window
loaded offscreen (English and Turkish; any QML warning fails)."""

import datetime
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from veltos_clock import store, strings  # noqa: E402

try:
    from PySide6.QtCore import QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

MONDAY = datetime.datetime(2026, 10, 19, 6, 0)      # a Monday, 06:00


class AlarmTests(unittest.TestCase):
    def test_one_time_alarm_rings_today_or_tomorrow(self):
        alarm = {"id": "a", "time": "07:30", "enabled": True, "days": []}
        self.assertEqual(store.next_ring(alarm, MONDAY), datetime.datetime(2026, 10, 19, 7, 30))
        later = MONDAY.replace(hour=8)
        self.assertEqual(store.next_ring(alarm, later), datetime.datetime(2026, 10, 20, 7, 30))
        alarm["enabled"] = False
        self.assertIsNone(store.next_ring(alarm, MONDAY))

    def test_repeating_alarm_picks_its_days(self):
        alarm = {"id": "a", "time": "07:30", "enabled": True, "days": [5, 6]}     # weekends
        self.assertEqual(store.next_ring(alarm, MONDAY), datetime.datetime(2026, 10, 24, 7, 30))
        weekdays = {"id": "b", "time": "05:00", "enabled": True, "days": [0, 1, 2, 3, 4]}
        self.assertEqual(store.next_ring(weekdays, MONDAY), datetime.datetime(2026, 10, 20, 5, 0))  # 05:00 passed

    def test_due_rings_once_and_one_time_alarm_switches_off(self):
        data = store.empty()
        data["alarms"].append({"id": "a", "time": "07:30", "enabled": True, "days": []})
        now = datetime.datetime(2026, 10, 19, 7, 31)
        due = store.due_alarms(data, now)
        self.assertEqual([a["id"] for a, _when in due], ["a"])
        store.ring(*due[0])
        self.assertFalse(data["alarms"][0]["enabled"])
        self.assertEqual(store.due_alarms(data, now), [])
        # A repeating alarm stays on and does not ring twice at the same time.
        data["alarms"] = [{"id": "r", "time": "07:30", "enabled": True, "days": list(range(7))}]
        due = store.due_alarms(data, now)
        store.ring(*due[0])
        self.assertTrue(data["alarms"][0]["enabled"])
        self.assertEqual(store.due_alarms(data, now), [])
        self.assertEqual(store.next_ring(data["alarms"][0], now), datetime.datetime(2026, 10, 20, 7, 30))
        # Missed by hours (the PC slept): not rung late.
        data["alarms"] = [{"id": "m", "time": "01:00", "enabled": True, "days": []}]
        self.assertEqual(store.due_alarms(data, now), [])

    def test_snooze(self):
        alarm = {"id": "a", "time": "07:30", "enabled": True, "days": [], "snooze": 10}
        now = datetime.datetime(2026, 10, 19, 7, 31)
        store.snooze(alarm, now)
        self.assertEqual(store.next_ring(alarm, now), datetime.datetime(2026, 10, 19, 7, 41))
        self.assertEqual(store.due_alarms({"alarms": [alarm]}, now + datetime.timedelta(minutes=10)),
                         [(alarm, datetime.datetime(2026, 10, 19, 7, 41))])

    def test_repeat_text(self):
        self.assertEqual(store.repeat_text([]), "Only once")
        self.assertEqual(store.repeat_text(list(range(7)), "tr"), "Her gün")
        self.assertEqual(store.repeat_text([0, 1, 2, 3, 4]), "Weekdays")
        self.assertEqual(store.repeat_text([5, 6], "tr"), "Hafta sonu")
        self.assertEqual(store.repeat_text([0, 2]), "Mon, Wed")


class TimerTests(unittest.TestCase):
    def test_start_pause_reset_and_due(self):
        timer = {"id": "t", "seconds": 90, "state": "idle"}
        store.start_timer(timer, 1000.0)
        self.assertEqual(store.timer_left(timer, 1030.0), 60.0)
        store.pause_timer(timer, 1030.0)
        self.assertEqual(store.timer_left(timer, 1500.0), 60.0)
        store.start_timer(timer, 1500.0)
        self.assertEqual(timer["end"], 1560.0)
        self.assertEqual(store.due_timers({"timers": [timer]}, 1559.0), [])
        self.assertEqual(store.due_timers({"timers": [timer]}, 1561.0), [timer])
        timer["rang"] = True
        self.assertEqual(store.due_timers({"timers": [timer]}, 1600.0), [])
        store.reset_timer(timer)
        self.assertEqual(store.timer_left(timer, 2000.0), 90.0)
        self.assertEqual(store.format_duration(3661), "1:01:01")
        self.assertEqual(store.format_duration(59.6), "01:00")

    def test_load_and_save(self):
        path = Path(tempfile.mkdtemp()) / "clock.json"
        self.assertEqual(store.load(path), store.empty())
        data = store.empty()
        data["alarms"].append({"id": "a", "time": "07:30", "enabled": True, "days": []})
        store.save(data, path)
        self.assertEqual(store.load(path)["alarms"][0]["time"], "07:30")
        path.write_text("junk", encoding="utf-8")
        self.assertEqual(store.load(path), store.empty())


class TextTests(unittest.TestCase):
    def test_every_key_in_both_languages(self):
        for key, pair in strings.TEXTS.items():
            self.assertEqual(len(pair), 2, key)
            self.assertTrue(pair[0] and pair[1], key)
        self.assertEqual(strings.text("tr", "alarm_notification"), "Alarm")


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower() or "warning" in m.lower()]

    def test_pages_and_actions(self):
        from veltos_clock import app as clock
        self.messages.clear()
        path = Path(tempfile.mkdtemp()) / "clock.json"
        backend = clock.Backend(lang=self.lang, path=path, start_page="alarm")
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(QUrl.fromLocalFile(str(clock.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(engine.rootObjects(), self.messages)
        window = engine.rootObjects()[0]
        self.assertEqual(window.property("title"), "Saat" if self.lang == "tr" else "Clock")
        backend.saveAlarm("", "07:30", "Work", [0, 1, 2, 3, 4], 10)
        backend.saveTimer("", 90, "Tea")
        backend.timerAction(backend.timers[0]["id"], "start")
        backend.addClock("Europe/Istanbul")
        backend.addClock("Nowhere/Nothing")
        self.app.processEvents()
        self.assertEqual(len(backend.alarms), 1)
        self.assertEqual(backend.alarms[0]["clockText"], "07:30" if self.lang == "tr" else "7:30 AM")
        self.assertEqual(backend.alarms[0]["repeatText"], "Hafta içi" if self.lang == "tr" else "Weekdays")
        self.assertGreater(backend.timerLeft(backend.timers[0]["id"]), 80)
        self.assertEqual([c["city"] for c in backend.clocks], ["Istanbul"])
        self.assertEqual(backend.searchZones("ista")[0]["zone"], "Europe/Istanbul")
        for page in ("timer", "stopwatch", "world", "focus"):
            window.setProperty("page", page)
            self.app.processEvents()
        backend.setFocusMinutes(25)
        self.assertEqual(backend.focusMinutes, 25)
        saved = store.load(path)
        self.assertEqual(saved["focus"]["minutes"], 25)
        self.assertEqual(len(saved["timers"]), 1)
        engine.deleteLater()
        self.app.processEvents()
        backend.deleteLater()
        self.app.processEvents()
        self.assertEqual(self.problems(), [])


class TurkishWindowTests(WindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
