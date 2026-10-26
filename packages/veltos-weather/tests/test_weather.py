"""VeltOS Weather without a window: what the numbers mean, Open-Meteo's
URLs, the cache, monthly averages, and the backend on real answers kept
in tests/data (no network)."""

import datetime
import json
import os
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from veltos_weather import conditions, openmeteo, strings  # noqa: E402
from fakenet import FakeNet  # noqa: E402

DATA = Path(__file__).resolve().parent / "data"


class ConditionTests(unittest.TestCase):
    def test_every_wmo_code_has_words_and_a_picture(self):
        icons = Path(__file__).resolve().parent.parent / "veltos_weather/qml/icons"
        for code in conditions.WMO:
            for is_day in (True, False):
                key, picture = conditions.condition(code, is_day)
                self.assertIn(key, strings.TEXTS)
                self.assertIn(picture, conditions.ICONS)
                self.assertTrue((icons / f"{picture}.svg").exists(), picture)
                self.assertIn(picture, conditions.SKIES)
        self.assertEqual(conditions.condition(0, True), ("sunny", "clear-day"))
        self.assertEqual(conditions.condition(0, False), ("clear", "clear-night"))
        self.assertEqual(conditions.condition(81, False), ("rain_showers", "showers-night"))
        self.assertEqual(conditions.condition(42, True), ("cloudy", "cloudy"))     # unknown: cloudy

    def test_units(self):
        self.assertEqual(conditions.degrees(14.0), "14°")
        self.assertEqual(conditions.degrees(14.0, "F"), "57°")
        self.assertEqual(conditions.degrees(-0.4), "0°")
        self.assertEqual(conditions.degrees(None), "--")
        self.assertEqual(conditions.speed(5.8), "6 km/h")
        self.assertEqual(conditions.speed(5.8, "C", "tr"), "6 km/sa")
        self.assertEqual(conditions.speed(16.09344, "F"), "10 mph")
        self.assertEqual(conditions.distance(23520), "24 km")
        self.assertEqual(conditions.distance(3500, "C", "tr"), "3,5 km")
        self.assertEqual(conditions.distance(23520, "F"), "15 mi")
        self.assertEqual(conditions.pressure(1014.9), "1015 mb")
        self.assertEqual(conditions.pressure(1014.9, "F", "tr"), "29,97 in")
        self.assertEqual(conditions.percent(90, "tr"), "%90")
        self.assertEqual(conditions.percent(90), "90%")
        self.assertEqual(conditions.precipitation_amount(2.25, "C", "tr"), "2,2 mm")

    def test_wind_direction(self):
        self.assertEqual(conditions.wind_direction(22), "N")             # 0..22.5: north
        self.assertEqual(conditions.wind_direction(30), "NE")
        self.assertEqual(conditions.wind_direction(350, "tr"), "K")
        self.assertEqual(conditions.wind_direction(180, "tr"), "G")
        self.assertEqual(conditions.wind_direction(None), "")

    def test_bands(self):
        self.assertEqual(conditions.aqi_band(30)[0], "fair")
        self.assertEqual(conditions.aqi_band(10)[0], "good")
        self.assertEqual(conditions.aqi_band(150)[0], "extremely_poor")
        self.assertEqual(conditions.uv_band(0)[0], "low")
        self.assertEqual(conditions.uv_band(6)[0], "high")
        self.assertEqual(conditions.uv_band(12)[0], "extreme")
        self.assertEqual(conditions.humidity_key(90), "humidity_humid")
        self.assertEqual(conditions.visibility_key(2000), "visibility_poor")
        self.assertEqual(conditions.feels_key(14, 13.9), "feels_same")
        self.assertEqual(conditions.feels_key(14, 10), "feels_colder")
        self.assertEqual(conditions.pressure_trend([1010, 1011, 1012]), "pressure_rising")
        for key in ("good", "fair", "moderate", "poor", "very_poor", "extremely_poor"):
            self.assertIn("aqi_" + key, strings.TEXTS)
            self.assertIn("aqi_text_" + key, strings.TEXTS)

    def test_moon(self):
        # Eclipses happen at full and new moon: the total lunar eclipse of
        # 14 March 2025 (about 07:00 UTC) and the total solar eclipse of
        # 8 April 2024 (about 18:20 UTC). The mean month is within about a
        # day of the real phases.
        utc = datetime.timezone.utc
        phase, light, key = conditions.moon(datetime.datetime(2025, 3, 14, 7, 0, tzinfo=utc))
        self.assertAlmostEqual(phase, 0.5, delta=0.04)
        self.assertGreater(light, 0.97)
        self.assertEqual(key, "moon_full")
        phase, light, key = conditions.moon(datetime.datetime(2024, 4, 8, 18, 20, tzinfo=utc))
        self.assertLess(min(phase, 1 - phase), 0.04)
        self.assertLess(light, 0.03)
        self.assertEqual(key, "moon_new")

    def test_words(self):
        self.assertEqual(conditions.summary("en", "sunny", "20°", "12°", 10),
                         "Sunny. The high will be 20°, the low 12°.")
        self.assertEqual(conditions.summary("tr", "rain", "15°", "9°", 80),
                         "Yağmur. En yüksek 15°, en düşük 9° olacak. Yağış bekleniyor (%80).")
        self.assertEqual(conditions.hour_text(datetime.datetime(2026, 1, 1, 14), "en"), "2 PM")
        self.assertEqual(conditions.hour_text(datetime.datetime(2026, 1, 1, 0), "en"), "12 AM")
        self.assertEqual(conditions.hour_text(datetime.datetime(2026, 1, 1, 14), "tr"), "14:00")
        today = datetime.date(2026, 10, 25)
        self.assertEqual(conditions.day_name(today, "tr", today), "Bugün")
        self.assertEqual(conditions.day_name(datetime.date(2026, 10, 26), "tr", today), "Pzt")

    def test_texts_in_both_languages(self):
        for key, pair in strings.TEXTS.items():
            self.assertEqual(len(pair), 2, key)
            self.assertTrue(pair[0] and pair[1], key)
            for field in ("{condition}", "{high}", "{low}", "{chance}", "{time}", "{h}", "{m}", "{percent}",
                          "{speed}", "{direction}", "{amount}", "{n}"):
                self.assertEqual(field in pair[0], field in pair[1], (key, field))
        self.assertEqual(strings.language({"LANG": "tr_TR.UTF-8"}), "tr")


class OpenMeteoTests(unittest.TestCase):
    def test_urls(self):
        url = openmeteo.forecast_url(41.013841234, 28.949661234)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertTrue(url.startswith("https://api.open-meteo.com/v1/forecast?"))
        self.assertEqual(query["latitude"], ["41.0138"])            # four decimals at most
        self.assertEqual(query["longitude"], ["28.9497"])
        self.assertEqual(query["timezone"], ["auto"])
        self.assertEqual(query["forecast_days"], ["10"])
        self.assertIn("weather_code", query["current"][0].split(","))
        self.assertNotIn("apikey", query)
        start, end = openmeteo.archive_range(datetime.date(2026, 10, 25))
        self.assertEqual((start, end), (datetime.date(2021, 10, 1), datetime.date(2026, 9, 30)))
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(openmeteo.geocode_url(" İstanbul ", "tr")).query)
        self.assertEqual((query["name"], query["language"]), (["İstanbul"], ["tr"]))

    def test_user_agent_and_errors(self):
        net = FakeNet()
        openmeteo.get_json(openmeteo.forecast_url(41, 29), net)
        self.assertTrue(net.headers[0]["User-agent"].startswith("VeltOS-Weather/"))
        with self.assertRaises(OSError):
            openmeteo.get_json(openmeteo.forecast_url(41, 29), FakeNet(online=False))

    def test_cache(self):
        clock = [1000.0]
        cache = openmeteo.Cache(tempfile.mkdtemp(), clock=lambda: clock[0])
        net = FakeNet()
        url = openmeteo.forecast_url(41, 29)
        data, fresh, failed = openmeteo.fetch("forecast", 41, 29, url, cache, net)
        self.assertEqual((fresh, failed, len(net.urls)), (True, False, 1))
        clock[0] += 60                                   # young: from the cache
        openmeteo.fetch("forecast", 41, 29, url, cache, net)
        self.assertEqual(len(net.urls), 1)
        clock[0] += 15 * 60                              # old: asked again
        openmeteo.fetch("forecast", 41, 29, url, cache, net)
        self.assertEqual(len(net.urls), 2)
        clock[0] += 3600                                 # offline: the saved answer
        again, fresh, failed = openmeteo.fetch("forecast", 41, 29, url, cache, FakeNet(online=False))
        self.assertEqual((again["current"]["time"], fresh, failed), (data["current"]["time"], False, True))
        self.assertEqual(openmeteo.fetch("air", 1, 1, url, cache, FakeNet(online=False)), (None, False, True))

    def test_places_and_months(self):
        found = openmeteo.places(json.loads((DATA / "geocode.json").read_text(encoding="utf-8")))
        self.assertEqual(found[0]["name"], "İstanbul")
        self.assertEqual(found[0]["timezone"], "Europe/Istanbul")
        self.assertEqual(found[0]["region"], "")          # admin1 is the city itself
        months = openmeteo.monthly_averages(json.loads((DATA / "archive.json").read_text(encoding="utf-8")))
        self.assertEqual([m["month"] for m in months], list(range(1, 13)))
        july, january = months[6], months[0]
        self.assertGreater(july["high"], january["high"] + 10)      # Istanbul: warm summers
        self.assertLessEqual(july["low"], july["high"])
        self.assertGreaterEqual(january["rainyDays"], 1)


class BackendTests(unittest.TestCase):
    """The backend on the saved answers, without a window and without threads."""

    def make(self, lang="en", unit=None, online=True, settings=None):
        from veltos_weather import app
        folder = Path(tempfile.mkdtemp())
        settings_file = folder / "weather.json"
        if settings is not None or unit:
            data = dict(settings or {})
            if unit:
                data["unit"] = unit
            settings_file.write_text(json.dumps(data), encoding="utf-8")
        self.net = FakeNet(online)
        return app.Backend(lang=lang, opener=self.net, cache=openmeteo.Cache(folder / "cache"),
                           settings_file=settings_file, zone="Europe/Istanbul", threaded=False)

    def setUp(self):
        from PySide6.QtCore import QCoreApplication
        self.app = QCoreApplication.instance() or QCoreApplication([])

    def test_first_start_uses_the_time_zone_city(self):
        backend = self.make("tr", "C")
        backend.start()
        self.assertEqual(backend.placeName, "İstanbul")
        self.assertTrue(backend.isHome)
        self.assertIn("name=Istanbul", self.net.urls[0])
        current = backend.current
        self.assertEqual((current["temperature"], current["unit"]), ("14", "°C"))
        self.assertEqual(current["condition"], "Parçalı bulutlu")
        self.assertEqual(current["icon"], "partly-cloudy-night")      # 06:30, before sunrise
        self.assertEqual(current["feels"], "14°")
        labels = {d["key"]: d["value"] for d in current["details"]}
        self.assertEqual(labels, {"air_quality": "30", "wind": "6 km/sa", "humidity": "%90", "visibility": "24 km",
                                  "pressure": "1015 mb", "dew_point": "12°"})
        self.assertFalse(backend.offline)

    def test_days_chart_and_details(self):
        backend = self.make("en", "F", settings={"home": {"name": "Istanbul", "region": "", "country": "Türkiye",
                                                          "lat": 41.01384, "lon": 28.94966}})
        backend.start()
        days = backend.days
        self.assertEqual(len(days), 10)
        self.assertEqual(days[0]["name"], "Today")
        self.assertEqual(days[1]["name"], "Mon")
        self.assertTrue(days[0]["selected"])
        chart = backend.chart
        self.assertEqual(len(chart["values"]), 24)
        self.assertEqual(chart["labels"][0], "Now")
        self.assertEqual(chart["labels"][1], "7 AM")
        self.assertTrue(chart["texts"][0].endswith("°"))
        backend.selectDay(2)
        self.assertEqual(backend.chart["labels"][0], "12 AM")
        backend.setChartKind("precipitation")
        self.assertEqual((backend.chart["min"], backend.chart["max"]), (0, 100))
        backend.setChartKind("wind")
        self.assertTrue(backend.chart["arrows"])
        self.assertEqual(backend.chart["unit"], "mph")
        details = backend.details
        self.assertEqual(details["sunrise"], "7:26 AM")
        self.assertEqual(details["sunPosition"], -1.0)               # before sunrise
        self.assertEqual(details["aqiBand"], "Fair")
        self.assertIn(details["moonName"], [strings.text("en", k) for k in conditions.MOON_PHASES])
        self.assertEqual(details["windFrom"], "From N")                 # 22°
        self.assertEqual(details["pressure"], "29.97 in")

    def test_search_favorites_and_units(self):
        backend = self.make("en", "C")
        backend.search("ist")
        self.assertEqual(backend.searchResults[0]["name"], "İstanbul")
        backend.choosePlace(0)
        self.assertEqual(backend.placeName, "İstanbul")
        self.assertEqual(backend.searchResults, [])
        backend.toggleFavorite()
        self.assertTrue(backend.isFavorite)
        backend.loadFavorites()
        favorite = backend.favorites[0]
        self.assertEqual((favorite["name"], favorite["temperature"]), ("İstanbul", "14°"))
        from veltos_weather import app
        self.assertEqual(app.default_unit({"LANG": "en_US.UTF-8"}), "C")   # °C until chosen otherwise
        backend.setUnit("F")
        self.assertEqual(backend.favorites[0]["temperature"], "57°")
        saved = json.loads(backend._settings_file.read_text(encoding="utf-8"))
        self.assertEqual(saved["unit"], "F")
        self.assertEqual(len(saved["favorites"]), 1)
        backend.removeFavorite(0)
        self.assertFalse(backend.isFavorite)

    def test_history(self):
        backend = self.make("tr", "C")
        backend.start()
        backend.setPage("history")
        months = backend.months
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0]["name"], "Oca")
        self.assertTrue(months[9]["current"])                        # October
        self.assertTrue(any("archive-api" in url for url in self.net.urls))

    def test_offline(self):
        backend = self.make("en", "C", online=False)
        backend.start()
        self.assertTrue(backend.offline)
        self.assertFalse(backend.hasPlace)
        self.assertEqual(backend.current, {})


if __name__ == "__main__":
    unittest.main()
