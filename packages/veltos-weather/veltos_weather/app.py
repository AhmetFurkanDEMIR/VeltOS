"""VeltOS Weather: Python backend for the QML window (Windows 11 Weather
layout).

    veltos-weather [forecast|history|favorites|settings]

The place shown first is the home place (Settings), else the last one,
else the city of the computer's time zone. Forecasts come from
Open-Meteo (openmeteo.py) in a background thread; what the numbers mean
is in conditions.py. Settings (unit, home, favorites) live in
~/.config/veltos/weather.json.
"""

import configparser
import datetime
import json
import os
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import conditions, openmeteo, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
ICON_DIR = QML_DIR / "icons"
PAGES = ("forecast", "history", "favorites", "settings")
CHART_KINDS = ("overview", "precipitation", "wind", "humidity", "uv_index", "feels_like", "cloud_cover",
               "pressure", "visibility")
REFRESH_SECONDS = 15 * 60


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
    parts = kde_value("General", "font").split(",")
    try:
        return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
    except ValueError:
        return 1.0


def accent_colour():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def config_path():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "veltos" / "weather.json"


def default_unit(environ=None):
    """°F where the United States' measures are used (as Windows does), °C elsewhere."""
    environ = os.environ if environ is None else environ
    for variable in ("LC_ALL", "LC_MEASUREMENT", "LANG"):
        value = environ.get(variable, "")
        if value:
            return "F" if value.split(".")[0] in ("en_US", "en_LR", "my_MM") else "C"
    return "C"


def system_zone(localtime="/etc/localtime", timezone_file="/etc/timezone"):
    """The computer's time zone name ("Europe/Istanbul") or ""."""
    try:
        target = os.path.realpath(localtime)
        if "zoneinfo/" in target:
            return target.split("zoneinfo/", 1)[1]
    except OSError:
        pass
    try:
        return Path(timezone_file).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def zone_city(zone):
    if "/" not in zone:
        return ""
    return zone.rsplit("/", 1)[1].replace("_", " ")


def parse_time(text):
    try:
        return datetime.datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def pick(series, index):
    return series[index] if series and index < len(series) else None


def place_label(place):
    parts = [p for p in (place.get("region"), place.get("country")) if p]
    return ", ".join(parts)


class Backend(QObject):
    changed = Signal()          # place, forecast, unit
    pageChanged = Signal()
    searchChanged = Signal()
    historyChanged = Signal()
    favoritesChanged = Signal()
    statusChanged = Signal()
    _loaded = Signal(str, object, int)

    def __init__(self, lang=None, start_page="forecast", opener=None, cache=None, settings_file=None,
                 zone=None, threaded=True, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self._page = start_page if start_page in PAGES else "forecast"
        self._opener = opener
        self._cache = cache or openmeteo.Cache()
        self._settings_file = Path(settings_file) if settings_file else config_path()
        self._threaded = threaded
        self._zone = system_zone() if zone is None else zone
        self.settings = self._read_settings()
        self.unit = self.settings.get("unit") or default_unit()
        self.place = self.settings.get("home") or self.settings.get("last") or None
        self.forecast = None
        self.air = None
        self.history = None
        self.selected_day = 0
        self.chart_kind = "overview"
        self.results = []
        self.searching = False
        self.loading = False
        self.offline = False
        self.updated_at = None
        self.favorite_weather = {}
        self._generation = 0
        self._search_generation = 0
        self._loaded.connect(self._on_loaded)
        self._timer = QTimer(self)
        self._timer.setInterval(REFRESH_SECONDS * 1000)
        self._timer.timeout.connect(lambda: self.load(False))
        self._timer.start()

    # --- settings -------------------------------------------------------------------------------------

    def _read_settings(self):
        try:
            data = json.loads(self._settings_file.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save_settings(self):
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._settings_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            tmp.replace(self._settings_file)
        except OSError:
            pass

    # --- background work ----------------------------------------------------------------------------

    def _run(self, kind, work, generation):
        def job():
            try:
                result = work()
            except Exception as error:   # a bad answer must not end the app
                print(f"veltos-weather: {kind}: {error}", file=sys.stderr)
                result = None
            self._loaded.emit(kind, result, generation)
        if self._threaded:
            threading.Thread(target=job, daemon=True).start()
        else:
            job()

    def start(self):
        """First load: the saved place, or the city of the time zone."""
        if self.place:
            self.load(False)
            return
        city = zone_city(self._zone)
        if not city:
            return
        self.loading = True
        self.statusChanged.emit()
        url = openmeteo.geocode_url(city, self.lang, 5)
        zone = self._zone

        def work():
            found = openmeteo.places(openmeteo.get_json(url, self._opener))
            return next((p for p in found if p["timezone"] == zone), found[0] if found else None)
        self._run("guess", work, self._generation)

    def load(self, force):
        if not self.place:
            return
        self._generation += 1
        generation, place = self._generation, dict(self.place)
        self.loading = True
        self.statusChanged.emit()
        lat, lon = place["lat"], place["lon"]

        def work():
            forecast, fresh, failed = openmeteo.fetch("forecast", lat, lon, openmeteo.forecast_url(lat, lon),
                                                      self._cache, self._opener, force)
            air, _fresh, _failed = openmeteo.fetch("air", lat, lon, openmeteo.air_url(lat, lon), self._cache,
                                                   self._opener, force)
            _data, age = self._cache.load("forecast", lat, lon)
            return {"forecast": forecast, "air": air, "failed": failed, "age": age}
        self._run("forecast", work, generation)

    @Slot(str, object, int)
    def _on_loaded(self, kind, result, generation):
        if kind == "guess":
            self.loading = False
            if result:
                self.place = result
                self.settings["home"] = result
                self._save_settings()
                self.changed.emit()
                self.load(False)
            else:
                self.offline = True
            self.statusChanged.emit()
            return
        if kind == "search":
            if generation == self._search_generation:
                self.results = result or []
                self.searching = False
                self.searchChanged.emit()
            return
        if kind == "history":
            if generation == self._generation:
                self.history = result
                self.historyChanged.emit()
            return
        if kind == "favorites":
            self.favorite_weather.update(result or {})
            self.favoritesChanged.emit()
            return
        if generation != self._generation:
            return
        result = result or {"failed": True}
        self.loading = False
        self.offline = bool(result.get("failed"))
        if result.get("forecast"):
            self.forecast = result["forecast"]
            self.air = result.get("air")
            age = result.get("age")
            self.updated_at = time.time() - (age or 0)
            if self.selected_day >= len(self.days_raw()):
                self.selected_day = 0
        self.changed.emit()
        self.statusChanged.emit()

    # --- texts and look -------------------------------------------------------------------------------

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Property(bool, constant=True)
    def darkMode(self):
        return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")

    @Property(str, constant=True)
    def accent(self):
        return accent_colour()

    @Property(float, constant=True)
    def textScale(self):
        return text_scale()

    @Property("QVariantList", constant=True)
    def compassNames(self):
        names = strings.WIND_DIRECTIONS["tr" if self.lang == "tr" else "en"]
        return [names[0], names[2], names[4], names[6]]

    @Property(str, constant=True)
    def iconDir(self):
        return QUrl.fromLocalFile(str(ICON_DIR)).toString() + "/"

    @Property(str, notify=pageChanged)
    def page(self):
        return self._page

    @Slot(str)
    def setPage(self, page):
        if page in PAGES and page != self._page:
            self._page = page
            self.pageChanged.emit()
            if page == "history":
                self.loadHistory()
            elif page == "favorites":
                self.loadFavorites()

    # --- status ---------------------------------------------------------------------------------------

    @Property(bool, notify=statusChanged)
    def loading(self):
        return self._loading

    @loading.setter
    def loading(self, value):
        self._loading = value

    @Property(bool, notify=statusChanged)
    def offline(self):
        return self._offline

    @offline.setter
    def offline(self, value):
        self._offline = value

    @Property(str, notify=statusChanged)
    def updatedText(self):
        if not self.updated_at:
            return ""
        moment = datetime.datetime.fromtimestamp(self.updated_at)
        return strings.text(self.lang, "updated", time=conditions.clock_text(moment, self.lang))

    @Slot()
    def refresh(self):
        if self.place:
            self.load(True)
        else:
            self.start()

    # --- place ----------------------------------------------------------------------------------------

    @Property(bool, notify=changed)
    def hasPlace(self):
        return bool(self.place)

    @Property(bool, notify=changed)
    def hasForecast(self):
        return bool(self.forecast)

    @Property(str, notify=changed)
    def placeName(self):
        return (self.place or {}).get("name", "")

    @Property(str, notify=changed)
    def placeRegion(self):
        return place_label(self.place or {})

    @Property(str, notify=changed)
    def homeName(self):
        home = self.settings.get("home") or {}
        return ", ".join(p for p in (home.get("name"), place_label(home)) if p)

    @Property(bool, notify=changed)
    def isFavorite(self):
        return any(self._same(f, self.place) for f in self.settings.get("favorites", []))

    @Property(bool, notify=changed)
    def isHome(self):
        return self._same(self.settings.get("home"), self.place)

    @staticmethod
    def _same(a, b):
        if not a or not b:
            return False
        return abs(a["lat"] - b["lat"]) < 1e-3 and abs(a["lon"] - b["lon"]) < 1e-3

    def show_place(self, place):
        self.place = place
        self.settings["last"] = place
        self._save_settings()
        self.forecast = None
        self.air = None
        self.history = None
        self.selected_day = 0
        self.changed.emit()
        self.historyChanged.emit()
        self.load(False)
        if self._page in ("favorites", "settings"):
            self.setPage("forecast")
        elif self._page == "history":
            self.loadHistory()

    @Slot()
    def toggleFavorite(self):
        if not self.place:
            return
        favorites = [f for f in self.settings.get("favorites", []) if not self._same(f, self.place)]
        if len(favorites) == len(self.settings.get("favorites", [])):
            favorites.append(self.place)
        self.settings["favorites"] = favorites
        self._save_settings()
        self.changed.emit()
        self.favoritesChanged.emit()

    @Slot()
    def setHome(self):
        if self.place:
            self.settings["home"] = self.place
            self._save_settings()
            self.changed.emit()

    # --- search ---------------------------------------------------------------------------------------

    @Property("QVariantList", notify=searchChanged)
    def searchResults(self):
        return [{"name": p["name"], "detail": place_label(p)} for p in self.results]

    @Property(bool, notify=searchChanged)
    def searchBusy(self):
        return self.searching

    @Slot(str)
    def search(self, text):
        self._search_generation += 1
        text = text.strip()
        if len(text) < 2:
            self.results = []
            self.searching = False
            self.searchChanged.emit()
            return
        self.searching = True
        self.searchChanged.emit()
        url = openmeteo.geocode_url(text, self.lang)
        self._run("search", lambda: openmeteo.places(openmeteo.get_json(url, self._opener)), self._search_generation)

    @Slot(int)
    def choosePlace(self, index):
        if 0 <= index < len(self.results):
            place = self.results[index]
            self.results = []
            self.searchChanged.emit()
            self.show_place(place)

    # --- units ------------------------------------------------------------------------------------------

    @Property(str, notify=changed)
    def unitName(self):
        return self.unit

    @Slot(str)
    def setUnit(self, unit):
        if unit in ("C", "F") and unit != self.unit:
            self.unit = unit
            self.settings["unit"] = unit
            self._save_settings()
            self.changed.emit()
            self.historyChanged.emit()
            self.favoritesChanged.emit()

    def deg(self, value):
        return conditions.degrees(value, self.unit)

    # --- the forecast -------------------------------------------------------------------------------------

    def now(self):
        """The place's local time of the forecast ("current.time")."""
        current = (self.forecast or {}).get("current") or {}
        return parse_time(current.get("time")) or datetime.datetime.now()

    def days_raw(self):
        daily = (self.forecast or {}).get("daily") or {}
        return [{key: pick(daily.get(key), index) for key in openmeteo.DAILY} | {"time": day}
                for index, day in enumerate(daily.get("time") or [])]

    @Property("QVariantMap", notify=changed)
    def current(self):
        current = (self.forecast or {}).get("current") or {}
        if not current:
            return {}
        is_day = bool(current.get("is_day", 1))
        key, icon = conditions.condition(current.get("weather_code"), is_day)
        days = self.days_raw()
        today = days[0] if days else {}
        top, bottom = conditions.SKIES.get(icon, conditions.SKIES["cloudy"])
        summary = conditions.summary(self.lang, key, self.deg(today.get("temperature_2m_max")),
                                     self.deg(today.get("temperature_2m_min")),
                                     today.get("precipitation_probability_max"), is_day)
        air = ((self.air or {}).get("current") or {}).get("european_aqi")
        band, colour, _fraction = conditions.aqi_band(air)
        lang, unit = self.lang, self.unit
        details = [
            {"key": "air_quality", "label": self.text("air_quality"), "value": "--" if air is None else str(round(air)),
             "colour": colour, "hint": self.text("aqi_" + band) if band else ""},
            {"key": "wind", "label": self.text("wind"), "value": conditions.speed(current.get("wind_speed_10m"), unit, lang),
             "angle": float(current.get("wind_direction_10m") or 0), "colour": ""},
            {"key": "humidity", "label": self.text("humidity"),
             "value": conditions.percent(current.get("relative_humidity_2m"), lang), "colour": ""},
            {"key": "visibility", "label": self.text("visibility"),
             "value": conditions.distance(current.get("visibility"), unit, lang), "colour": ""},
            {"key": "pressure", "label": self.text("pressure"),
             "value": conditions.pressure(current.get("pressure_msl"), unit, lang), "colour": ""},
            {"key": "dew_point", "label": self.text("dew_point"), "value": self.deg(current.get("dew_point_2m")),
             "colour": ""},
        ]
        return {
            "temperature": "--" if current.get("temperature_2m") is None
            else str(conditions.temperature(current.get("temperature_2m"), unit)),
            "unit": "°" + unit,
            "condition": self.text(key),
            "icon": icon,
            "isDay": is_day,
            "feels": self.deg(current.get("apparent_temperature")),
            "summary": summary,
            "time": conditions.clock_text(self.now(), self.lang),
            "skyTop": top,
            "skyBottom": bottom,
            "details": details,
        }

    @Property("QVariantList", notify=changed)
    def days(self):
        today = self.now().date()
        result = []
        for index, day in enumerate(self.days_raw()):
            date = datetime.date.fromisoformat(day["time"])
            key, icon = conditions.condition(day.get("weather_code"), True)
            chance = day.get("precipitation_probability_max")
            result.append({
                "name": conditions.day_name(date, self.lang, today),
                "date": str(date.day),
                "icon": icon,
                "condition": self.text(key),
                "high": self.deg(day.get("temperature_2m_max")),
                "low": self.deg(day.get("temperature_2m_min")),
                "chance": "" if chance is None else conditions.percent(chance, self.lang),
                "selected": index == self.selected_day,
            })
        return result

    @Property(int, notify=changed)
    def selectedDay(self):
        return self.selected_day

    @Slot(int)
    def selectDay(self, index):
        if 0 <= index < len(self.days_raw()) and index != self.selected_day:
            self.selected_day = index
            self.changed.emit()

    @Property("QVariantList", constant=True)
    def chartKinds(self):
        labels = {"overview": "overview", "precipitation": "precipitation", "wind": "wind",
                  "humidity": "humidity", "uv_index": "uv_index", "feels_like": "feels_like",
                  "cloud_cover": "cloud_cover", "pressure": "pressure", "visibility": "visibility"}
        return [{"key": k, "label": self.text(labels[k])} for k in CHART_KINDS]

    @Property(str, notify=changed)
    def chartKind(self):
        return self.chart_kind

    @Slot(str)
    def setChartKind(self, kind):
        if kind in CHART_KINDS and kind != self.chart_kind:
            self.chart_kind = kind
            self.changed.emit()

    def hours_raw(self, day=None):
        """24 hours: from now for today (day 0), else the whole day."""
        day = self.selected_day if day is None else day
        hourly = (self.forecast or {}).get("hourly") or {}
        times = hourly.get("time") or []
        days = self.days_raw()
        if not days or day >= len(days):
            return []
        if day == 0:
            now = self.now().replace(minute=0, second=0, microsecond=0)
            start = next((i for i, t in enumerate(times) if parse_time(t) and parse_time(t) >= now), 0)
        else:
            date = days[day]["time"]
            start = next((i for i, t in enumerate(times) if t.startswith(date)), 0)
        return [{key: pick(hourly.get(key), index) for key in openmeteo.HOURLY} | {"time": times[index]}
                for index in range(start, min(start + 24, len(times)))]

    @Property("QVariantMap", notify=changed)
    def chart(self):
        rows = self.hours_raw()
        kind, unit, lang = self.chart_kind, self.unit, self.lang
        values, texts, icons, labels, extras = [], [], [], [], []
        for index, row in enumerate(rows):
            moment = parse_time(row["time"]) or self.now()
            labels.append(self.text("now") if index == 0 and self.selected_day == 0
                          else conditions.hour_text(moment, lang))
            _key, icon = conditions.condition(row.get("weather_code"), bool(row.get("is_day", 1)))
            icons.append(icon)
            if kind in ("overview", "feels_like"):
                raw = row.get("temperature_2m" if kind == "overview" else "apparent_temperature")
                value = conditions.temperature(raw, unit)
                text = self.deg(raw)
            elif kind == "precipitation":
                value = row.get("precipitation_probability")
                text = conditions.percent(value, lang)
            elif kind == "wind":
                raw = row.get("wind_speed_10m")
                value = None if raw is None else (raw / 1.609344 if unit == "F" else raw)
                text = "--" if value is None else str(round(value))
            elif kind in ("humidity", "cloud_cover"):
                value = row.get("relative_humidity_2m" if kind == "humidity" else "cloud_cover")
                text = conditions.percent(value, lang)
            elif kind == "uv_index":
                value = row.get("uv_index")
                text = "--" if value is None else str(round(value))
            elif kind == "pressure":
                raw = row.get("pressure_msl")
                value = None if raw is None else (raw * 0.0295299830714 if unit == "F" else raw)
                text = "--" if value is None else (conditions.number(value, 2, lang) if unit == "F" else str(round(value)))
            else:   # visibility
                raw = row.get("visibility")
                value = None if raw is None else raw / (1609.344 if unit == "F" else 1000)
                text = "--" if value is None else conditions.number(value, 0 if value >= 10 else 1, lang)
            values.append(value)
            texts.append(text)
            chance = row.get("precipitation_probability")
            extras.append({"chance": "" if chance is None else conditions.percent(chance, lang),
                           "angle": float(row.get("wind_direction_10m") or 0)})
        present = [v for v in values if v is not None]
        low, high = (min(present), max(present)) if present else (0, 1)
        if kind in ("precipitation", "humidity", "cloud_cover"):
            low, high = 0, 100
        elif kind == "uv_index":
            low, high = 0, max(11, high)
        elif kind == "wind":
            low = 0
        units = {"overview": "°" + unit, "feels_like": "°" + unit, "precipitation": "%", "humidity": "%",
                 "cloud_cover": "%", "uv_index": "", "wind": "mph" if unit == "F" else ("km/sa" if lang == "tr" else "km/h"),
                 "pressure": "in" if unit == "F" else "mb", "visibility": "mi" if unit == "F" else "km"}
        return {"kind": kind, "values": [0 if v is None else v for v in values], "texts": texts, "icons": icons,
                "labels": labels, "extras": extras, "min": low, "max": high if high > low else low + 1,
                "unit": units[kind], "showIcons": kind == "overview", "arrows": kind == "wind"}

    # --- weather details --------------------------------------------------------------------------------

    @Property("QVariantMap", notify=changed)
    def details(self):
        current = (self.forecast or {}).get("current") or {}
        days = self.days_raw()
        if not current or not days:
            return {}
        lang, unit = self.lang, self.unit
        today = days[0]
        now = self.now()
        sunrise, sunset = parse_time(today.get("sunrise")), parse_time(today.get("sunset"))
        position = -1.0
        if sunrise and sunset and sunrise <= now <= sunset:
            position = (now - sunrise).total_seconds() / max(1.0, (sunset - sunrise).total_seconds())
        daylight = int(today.get("daylight_duration") or 0)
        offset = datetime.timedelta(seconds=int((self.forecast or {}).get("utc_offset_seconds") or 0))
        moment = (now - offset).replace(tzinfo=datetime.timezone.utc)
        phase, illuminated, phase_key = conditions.moon(moment)
        uv = current.get("uv_index")
        uv_key, uv_colour = conditions.uv_band(uv)
        air = (self.air or {}).get("current") or {}
        aqi = air.get("european_aqi")
        aqi_key, aqi_colour, aqi_fraction = conditions.aqi_band(aqi)
        hourly_pressure = [row.get("pressure_msl") for row in self.hours_raw(0)[:4]]
        precip = today.get("precipitation_sum")
        pollutants = []
        for key, label in (("pm2_5", "PM2.5"), ("pm10", "PM10"), ("ozone", "O₃"), ("nitrogen_dioxide", "NO₂"),
                           ("sulphur_dioxide", "SO₂"), ("carbon_monoxide", "CO")):
            if air.get(key) is not None:
                pollutants.append({"label": label, "value": conditions.number(air[key], 1, lang) + " µg/m³"})
        return {
            "sunrise": conditions.clock_text(sunrise, lang) if sunrise else "--",
            "sunset": conditions.clock_text(sunset, lang) if sunset else "--",
            "sunPosition": position,
            "daylight": strings.text(lang, "daylight", h=daylight // 3600, m=daylight % 3600 // 60),
            "moonPhase": phase,
            "moonName": self.text(phase_key),
            "moonLight": strings.text(lang, "illumination", percent=conditions.percent(illuminated * 100, lang)),
            "windSpeed": conditions.speed(current.get("wind_speed_10m"), unit, lang),
            "windGusts": strings.text(lang, "gusts", speed=conditions.speed(current.get("wind_gusts_10m"), unit, lang)),
            "windAngle": float(current.get("wind_direction_10m") or 0),
            "windFrom": strings.text(lang, "from_direction",
                                     direction=conditions.wind_direction(current.get("wind_direction_10m"), lang)),
            "humidity": conditions.percent(current.get("relative_humidity_2m"), lang),
            "humidityValue": float(current.get("relative_humidity_2m") or 0),
            "humidityText": self.text(conditions.humidity_key(current.get("relative_humidity_2m"))),
            "dewPoint": self.deg(current.get("dew_point_2m")),
            "uv": "--" if uv is None else str(round(uv)),
            "uvValue": float(uv or 0),
            "uvBand": self.text("uv_" + uv_key) if uv_key else "",
            "uvColour": uv_colour,
            "uvText": self.text("uv_text_" + uv_key) if uv_key else "",
            "visibility": conditions.distance(current.get("visibility"), unit, lang),
            "visibilityText": self.text(conditions.visibility_key(current.get("visibility"))),
            "pressure": conditions.pressure(current.get("pressure_msl"), unit, lang),
            "pressureValue": float(current.get("pressure_msl") or 1013),
            "pressureTrend": self.text(conditions.pressure_trend(hourly_pressure)),
            "aqi": "--" if aqi is None else str(round(aqi)),
            "aqiBand": self.text("aqi_" + aqi_key) if aqi_key else "",
            "aqiColour": aqi_colour,
            "aqiFraction": aqi_fraction,
            "aqiText": self.text("aqi_text_" + aqi_key) if aqi_key else "",
            "pollutants": pollutants,
            "feels": self.deg(current.get("apparent_temperature")),
            "feelsText": self.text(conditions.feels_key(current.get("temperature_2m"),
                                                        current.get("apparent_temperature"))),
            "precip": conditions.precipitation_amount(precip, unit, lang),
            "precipText": strings.text(lang, "precip_today", amount=conditions.precipitation_amount(precip, unit, lang))
            if precip else self.text("precip_none"),
        }

    # --- history ----------------------------------------------------------------------------------------

    @Slot()
    def loadHistory(self):
        if not self.place or self.history is not None:
            return
        lat, lon = self.place["lat"], self.place["lon"]
        url = openmeteo.archive_url(lat, lon, datetime.date.today())

        def work():
            data, _fresh, _failed = openmeteo.fetch("history", lat, lon, url, self._cache, self._opener)
            return openmeteo.monthly_averages(data) if data else None
        self._run("history", work, self._generation)

    @Property("QVariantList", notify=historyChanged)
    def months(self):
        if not self.history:
            return []
        names = strings.MONTHS["tr" if self.lang == "tr" else "en"]
        current = self.now().month
        result = []
        for entry in self.history:
            precip = entry["precip"]
            result.append({
                "name": names[entry["month"] - 1],
                "high": conditions.temperature(entry["high"], self.unit),
                "low": conditions.temperature(entry["low"], self.unit),
                "highText": self.deg(entry["high"]),
                "lowText": self.deg(entry["low"]),
                "highest": self.deg(entry["highest"]),
                "lowest": self.deg(entry["lowest"]),
                "precip": conditions.precipitation_amount(precip, self.unit, self.lang),
                "precipValue": float(precip or 0),
                "rainyDays": strings.text(self.lang, "days_value", n=round(entry["rainyDays"] or 0)),
                "current": entry["month"] == current,
            })
        return result

    # --- favorites ----------------------------------------------------------------------------------------

    @Property("QVariantList", notify=favoritesChanged)
    def favorites(self):
        result = []
        for place in self.settings.get("favorites", []):
            key = f"{place['lat']:.3f},{place['lon']:.3f}"
            forecast = self.favorite_weather.get(key) or {}
            current = forecast.get("current") or {}
            daily = forecast.get("daily") or {}
            condition_key, icon = conditions.condition(current.get("weather_code"), bool(current.get("is_day", 1)))
            result.append({
                "name": place.get("name", ""), "detail": place_label(place),
                "temperature": self.deg(current.get("temperature_2m")) if current else "",
                "condition": self.text(condition_key) if current else "",
                "icon": icon if current else "",
                "high": self.deg((daily.get("temperature_2m_max") or [None])[0]) if daily else "",
                "low": self.deg((daily.get("temperature_2m_min") or [None])[0]) if daily else "",
                "home": self._same(place, self.settings.get("home")),
            })
        return result

    @Slot()
    def loadFavorites(self):
        favorites = list(self.settings.get("favorites", []))
        if not favorites:
            return

        def work():
            found = {}
            for place in favorites:
                lat, lon = place["lat"], place["lon"]
                data, _fresh, _failed = openmeteo.fetch("forecast", lat, lon, openmeteo.forecast_url(lat, lon),
                                                        self._cache, self._opener)
                if data:
                    found[f"{lat:.3f},{lon:.3f}"] = data
            return found
        self._run("favorites", work, self._generation)

    @Slot(int)
    def openFavorite(self, index):
        favorites = self.settings.get("favorites", [])
        if 0 <= index < len(favorites):
            self.show_place(favorites[index])

    @Slot(int)
    def removeFavorite(self, index):
        favorites = self.settings.get("favorites", [])
        if 0 <= index < len(favorites):
            del favorites[index]
            self._save_settings()
            self.changed.emit()
            self.favoritesChanged.emit()


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
    app.setApplicationName("veltos-weather")
    app.setApplicationDisplayName(strings.text(strings.language(), "app_title"))
    app.setDesktopFileName("veltos-weather")
    app.setWindowIcon(QIcon.fromTheme("veltos-weather"))
    page = next((a for a in argv[1:] if a in PAGES), "forecast")
    backend = Backend(start_page=page)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    backend.start()
    if page == "history":
        backend.loadHistory()
    elif page == "favorites":
        backend.loadFavorites()
    code = app.exec()
    del engine
    return code
