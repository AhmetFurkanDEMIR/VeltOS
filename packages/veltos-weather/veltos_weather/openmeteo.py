"""Open-Meteo (https://open-meteo.com): forecasts, air quality, place
search and weather records without an account or a key.

The free service is for non-commercial use (VeltOS: no ads, no
subscriptions), allows 10,000 calls a day per IP address and gives its
data under CC BY 4.0, which the app credits. Answers are kept in
~/.cache/veltos-weather: a forecast is asked for again after 15 minutes,
air quality after an hour, the records after 30 days; offline the last
saved answer is shown. Coordinates are rounded to four decimals.
"""

import datetime
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
USER_AGENT = "VeltOS-Weather/1.0 (+https://veltos.ahmetfurkandemir.com)"

CURRENT = ("temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day", "precipitation",
           "weather_code", "cloud_cover", "pressure_msl", "wind_speed_10m", "wind_direction_10m",
           "wind_gusts_10m", "visibility", "uv_index", "dew_point_2m")
HOURLY = ("temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
          "precipitation_probability", "precipitation", "weather_code", "pressure_msl", "cloud_cover",
          "visibility", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "uv_index", "is_day")
DAILY = ("weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max",
         "apparent_temperature_min", "sunrise", "sunset", "daylight_duration", "uv_index_max", "precipitation_sum",
         "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max", "wind_direction_10m_dominant")
AIR = ("european_aqi", "us_aqi", "pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "ozone",
       "sulphur_dioxide")
ARCHIVE_DAILY = ("temperature_2m_max", "temperature_2m_min", "precipitation_sum")
FORECAST_DAYS = 10
HISTORY_YEARS = 5

MAX_AGE = {"forecast": 15 * 60, "air": 60 * 60, "history": 30 * 86400}


def coordinate(value):
    return f"{round(float(value), 4):.4f}"


def forecast_url(lat, lon):
    return FORECAST_URL + "?" + urllib.parse.urlencode({
        "latitude": coordinate(lat), "longitude": coordinate(lon), "timezone": "auto",
        "forecast_days": FORECAST_DAYS, "current": ",".join(CURRENT), "hourly": ",".join(HOURLY),
        "daily": ",".join(DAILY)})


def air_url(lat, lon):
    return AIR_URL + "?" + urllib.parse.urlencode({
        "latitude": coordinate(lat), "longitude": coordinate(lon), "timezone": "auto", "current": ",".join(AIR)})


def geocode_url(name, lang="en", count=8):
    return GEOCODE_URL + "?" + urllib.parse.urlencode({
        "name": name.strip(), "count": count, "language": lang, "format": "json"})


def archive_range(today):
    """The last HISTORY_YEARS whole years of records up to the month before
    this one (the records arrive with a delay of about five days)."""
    first_of_month = today.replace(day=1)
    end = first_of_month - datetime.timedelta(days=1)
    start = first_of_month.replace(year=first_of_month.year - HISTORY_YEARS)
    return start, end


def archive_url(lat, lon, today):
    start, end = archive_range(today)
    return ARCHIVE_URL + "?" + urllib.parse.urlencode({
        "latitude": coordinate(lat), "longitude": coordinate(lon), "timezone": "auto",
        "start_date": start.isoformat(), "end_date": end.isoformat(), "daily": ",".join(ARCHIVE_DAILY)})


def get_json(url, opener=None, timeout=15):
    """The answer as JSON; raises OSError when there is none (offline,
    refused, not JSON)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, TimeoutError) as error:
        raise OSError(str(error)) from error
    if isinstance(data, dict) and data.get("error"):
        raise OSError(str(data.get("reason") or "error"))
    return data


class Cache:
    """Answers kept on disk, by kind and place."""

    def __init__(self, folder=None, clock=time.time):
        self.folder = Path(folder or (Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
                                      / "veltos-weather"))
        self.clock = clock

    def path(self, kind, lat, lon):
        key = hashlib.sha1(f"{kind}:{coordinate(lat)}:{coordinate(lon)}".encode()).hexdigest()[:16]
        return self.folder / f"{kind}-{key}.json"

    def load(self, kind, lat, lon):
        """(data, age in seconds) or (None, None)."""
        try:
            saved = json.loads(self.path(kind, lat, lon).read_text(encoding="utf-8"))
            return saved["data"], max(0.0, self.clock() - float(saved["time"]))
        except (OSError, ValueError, KeyError, TypeError):
            return None, None

    def save(self, kind, lat, lon, data):
        path = self.path(kind, lat, lon)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"time": self.clock(), "data": data}), encoding="utf-8")
            tmp.replace(path)
        except OSError:
            pass


def fetch(kind, lat, lon, url, cache, opener=None, force=False):
    """(data, fresh, failed): the saved answer while it is young enough,
    otherwise a new one; the saved one again when the network fails."""
    saved, age = cache.load(kind, lat, lon)
    if saved is not None and not force and age < MAX_AGE[kind]:
        return saved, True, False
    try:
        data = get_json(url, opener)
    except OSError:
        return saved, False, True
    cache.save(kind, lat, lon, data)
    return data, True, False


def places(data):
    """Places from a geocoding answer: [{id, name, region, country, lat, lon, timezone}]."""
    found = []
    for item in (data or {}).get("results") or []:
        try:
            lat, lon = float(item["latitude"]), float(item["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        region = item.get("admin1") or ""
        found.append({"id": int(item.get("id") or 0), "name": item.get("name") or "",
                      "region": region if region != item.get("name") else (item.get("admin2") or ""),
                      "country": item.get("country") or "", "countryCode": item.get("country_code") or "",
                      "lat": lat, "lon": lon, "timezone": item.get("timezone") or ""})
    return found


def monthly_averages(data):
    """Twelve months of averages from daily records: [{month 1..12, high,
    low, precip (a month's total), rainyDays, highest, lowest}] (None where
    there are no records)."""
    daily = (data or {}).get("daily") or {}
    months = {m: {"highs": [], "lows": [], "precip": [], "years": set()} for m in range(1, 13)}
    for index, day in enumerate(daily.get("time") or []):
        try:
            month = int(day[5:7])
        except (TypeError, ValueError):
            continue
        entry = months[month]
        entry["years"].add(day[:4])
        for key, values in (("highs", "temperature_2m_max"), ("lows", "temperature_2m_min"),
                            ("precip", "precipitation_sum")):
            series = daily.get(values) or []
            value = series[index] if index < len(series) else None
            if value is not None:
                entry[key].append(value)
    result = []
    for month in range(1, 13):
        entry = months[month]
        years = max(1, len(entry["years"]))
        highs, lows, precip = entry["highs"], entry["lows"], entry["precip"]
        result.append({
            "month": month,
            "high": sum(highs) / len(highs) if highs else None,
            "low": sum(lows) / len(lows) if lows else None,
            "precip": sum(precip) / years if precip else None,
            "rainyDays": sum(1 for p in precip if p >= 1.0) / years if precip else None,
            "highest": max(highs) if highs else None,
            "lowest": min(lows) if lows else None,
        })
    return result
