"""What the numbers mean: WMO weather codes as Windows 11's Weather words
and pictures, air quality and UV bands, the moon's phase, wind
directions and the units Windows uses (°C with km/h, km and mb; °F with
mph, mi and in). Pure functions, tested without a network."""

import datetime
import math

from . import strings

# WMO weather interpretation code -> (text key by day, text key by night, picture).
# Pictures with "*" have a day and a night drawing (icons/<name>-day.svg).
WMO = {
    0: ("sunny", "clear", "clear*"),
    1: ("mostly_sunny", "mostly_clear", "mostly-clear*"),
    2: ("partly_cloudy", "partly_cloudy", "partly-cloudy*"),
    3: ("cloudy", "cloudy", "cloudy"),
    45: ("fog", "fog", "fog"),
    48: ("fog", "fog", "fog"),
    51: ("light_drizzle", "light_drizzle", "drizzle"),
    53: ("drizzle", "drizzle", "drizzle"),
    55: ("drizzle", "drizzle", "drizzle"),
    56: ("freezing_drizzle", "freezing_drizzle", "freezing-rain"),
    57: ("freezing_drizzle", "freezing_drizzle", "freezing-rain"),
    61: ("light_rain", "light_rain", "rain"),
    63: ("rain", "rain", "rain"),
    65: ("heavy_rain", "heavy_rain", "heavy-rain"),
    66: ("freezing_rain", "freezing_rain", "freezing-rain"),
    67: ("freezing_rain", "freezing_rain", "freezing-rain"),
    71: ("light_snow", "light_snow", "snow"),
    73: ("snow", "snow", "snow"),
    75: ("heavy_snow", "heavy_snow", "snow"),
    77: ("snow_grains", "snow_grains", "snow"),
    80: ("rain_showers", "rain_showers", "showers*"),
    81: ("rain_showers", "rain_showers", "showers*"),
    82: ("heavy_showers", "heavy_showers", "heavy-rain"),
    85: ("snow_showers", "snow_showers", "snow-showers"),
    86: ("snow_showers", "snow_showers", "snow-showers"),
    95: ("thunderstorm", "thunderstorm", "thunderstorm"),
    96: ("thunderstorm_hail", "thunderstorm_hail", "thunderstorm"),
    97: ("thunderstorm", "thunderstorm", "thunderstorm"),
    99: ("thunderstorm_hail", "thunderstorm_hail", "thunderstorm"),
}

ICONS = ("clear-day", "clear-night", "mostly-clear-day", "mostly-clear-night", "partly-cloudy-day",
         "partly-cloudy-night", "cloudy", "fog", "drizzle", "rain", "heavy-rain", "freezing-rain", "snow",
         "showers-day", "showers-night", "snow-showers", "thunderstorm")

# The sky behind the current weather: (top, bottom) colours.
SKIES = {
    "clear-day": ("#2F6FD6", "#7DB7F5"), "clear-night": ("#0B1736", "#2A3D73"),
    "mostly-clear-day": ("#3474D8", "#86BCF2"), "mostly-clear-night": ("#0D1A3A", "#2E4177"),
    "partly-cloudy-day": ("#4A7FC8", "#9DBFE6"), "partly-cloudy-night": ("#141E3C", "#36476F"),
    "cloudy": ("#5C6B82", "#9AA8BC"), "fog": ("#6E7684", "#AEB5C0"),
    "drizzle": ("#4F607A", "#8797AE"), "rain": ("#3E4E68", "#76869F"), "heavy-rain": ("#2F3A50", "#5E6C85"),
    "freezing-rain": ("#4E6585", "#93A8C4"), "snow": ("#7F93AE", "#C5D3E4"),
    "showers-day": ("#47648F", "#8AA6CB"), "showers-night": ("#18233F", "#3A4B72"),
    "snow-showers": ("#71869F", "#B9C8DB"), "thunderstorm": ("#2A2741", "#57557A"),
}


def condition(code, is_day=True):
    """(text key, picture name) for a WMO code."""
    day_key, night_key, picture = WMO.get(int(code) if code is not None else 3, WMO[3])
    if picture.endswith("*"):
        picture = picture[:-1] + ("-day" if is_day else "-night")
    return (day_key if is_day else night_key), picture


# --- units ----------------------------------------------------------------------------------------

def temperature(celsius, unit="C"):
    """A whole number in the chosen unit, or None."""
    if celsius is None:
        return None
    value = celsius * 9 / 5 + 32 if unit == "F" else celsius
    return int(math.floor(value + 0.5))


def degrees(celsius, unit="C"):
    value = temperature(celsius, unit)
    return "--" if value is None else f"{value}°"


def speed(kmh, unit="C", lang="en"):
    if kmh is None:
        return "--"
    if unit == "F":
        return f"{round(kmh / 1.609344)} mph"
    return f"{round(kmh)} km/h" if lang != "tr" else f"{round(kmh)} km/sa"


def distance(metres, unit="C", lang="en"):
    if metres is None:
        return "--"
    if unit == "F":
        miles = metres / 1609.344
        return f"{miles:.0f} mi" if miles >= 10 else number(miles, 1, lang) + " mi"
    km = metres / 1000
    return f"{km:.0f} km" if km >= 10 else number(km, 1, lang) + " km"


def pressure(hpa, unit="C", lang="en"):
    if hpa is None:
        return "--"
    if unit == "F":
        return number(hpa * 0.0295299830714, 2, lang) + " in"
    return f"{round(hpa)} mb"


def precipitation_amount(mm, unit="C", lang="en"):
    if mm is None:
        return "--"
    if unit == "F":
        return number(mm / 25.4, 2, lang) + " in"
    return number(mm, 1, lang) + " mm"


def number(value, places, lang="en"):
    text = f"{value:.{places}f}"
    return text.replace(".", ",") if lang == "tr" else text


def percent(value, lang="en"):
    if value is None:
        return "--"
    return f"%{round(value)}" if lang == "tr" else f"{round(value)}%"


def wind_direction(degrees_from, lang="en"):
    if degrees_from is None:
        return ""
    names = strings.WIND_DIRECTIONS["tr" if lang == "tr" else "en"]
    return names[int((degrees_from % 360) / 45 + 0.5) % 8]


# --- bands ----------------------------------------------------------------------------------------

def aqi_band(european_aqi):
    """(key, colour, fraction of the scale) of the European air quality index."""
    if european_aqi is None:
        return "", "#8A90A2", 0.0
    bands = ((20, "good", "#3FB950"), (40, "fair", "#9ACD32"), (60, "moderate", "#F2C200"),
             (80, "poor", "#F08C1A"), (100, "very_poor", "#E5484D"))
    for limit, key, colour in bands:
        if european_aqi <= limit:
            return key, colour, min(1.0, european_aqi / 120)
    return "extremely_poor", "#8E3BB8", min(1.0, european_aqi / 120)


def uv_band(index):
    if index is None:
        return "", "#8A90A2"
    for limit, key, colour in ((2.5, "low", "#3FB950"), (5.5, "moderate", "#F2C200"), (7.5, "high", "#F08C1A"),
                               (10.5, "very_high", "#E5484D")):
        if index < limit:
            return key, colour
    return "extreme", "#8E3BB8"


def humidity_key(relative):
    if relative is None:
        return "humidity_comfortable"
    if relative < 30:
        return "humidity_dry"
    return "humidity_humid" if relative > 65 else "humidity_comfortable"


def visibility_key(metres):
    if metres is None or metres >= 10000:
        return "visibility_good"
    return "visibility_moderate" if metres >= 4000 else "visibility_poor"


def feels_key(actual, feels):
    if actual is None or feels is None or abs(feels - actual) < 1.5:
        return "feels_same"
    return "feels_colder" if feels < actual else "feels_warmer"


def pressure_trend(values):
    """Rising, falling or steady over the next three hours."""
    values = [v for v in values if v is not None]
    if len(values) < 2:
        return "pressure_steady"
    change = values[-1] - values[0]
    if change > 0.8:
        return "pressure_rising"
    return "pressure_falling" if change < -0.8 else "pressure_steady"


# --- the moon ---------------------------------------------------------------------------------------

SYNODIC_MONTH = 29.530588853
NEW_MOON = datetime.datetime(2000, 1, 6, 18, 14, tzinfo=datetime.timezone.utc)
MOON_PHASES = ("moon_new", "moon_waxing_crescent", "moon_first_quarter", "moon_waxing_gibbous", "moon_full",
               "moon_waning_gibbous", "moon_last_quarter", "moon_waning_crescent")


def moon(when):
    """(phase 0..1 from new moon, illuminated fraction, phase text key) at
    a moment (an aware datetime): the mean synodic month from a known new
    moon, accurate to about a day, as a weather app shows it."""
    days = (when - NEW_MOON).total_seconds() / 86400
    phase = (days / SYNODIC_MONTH) % 1.0
    illuminated = (1 - math.cos(2 * math.pi * phase)) / 2
    return phase, illuminated, MOON_PHASES[int(phase * 8 + 0.5) % 8]


# --- words --------------------------------------------------------------------------------------------

def summary(lang, condition_key, high, low, chance, is_day=True):
    """Windows' sentence under the temperature."""
    if not is_day:
        text = strings.text(lang, "summary_night", condition=strings.text(lang, condition_key), low=low)
    else:
        text = strings.text(lang, "summary", condition=strings.text(lang, condition_key), high=high, low=low)
    if chance is not None and chance >= 40:
        text += strings.text(lang, "summary_rain", chance=percent(chance, lang))
    return text


def day_name(date, lang, today):
    if date == today:
        return strings.text(lang, "today")
    return strings.DAYS["tr" if lang == "tr" else "en"][date.weekday()]


def hour_text(moment, lang):
    """"14:00" in Turkish, "2 PM" in English."""
    if lang == "tr":
        return f"{moment.hour:02d}:00"
    hour = moment.hour % 12 or 12
    return f"{hour} {'AM' if moment.hour < 12 else 'PM'}"


def clock_text(moment, lang):
    if lang == "tr":
        return moment.strftime("%H:%M")
    hour = moment.hour % 12 or 12
    return f"{hour}:{moment.minute:02d} {'AM' if moment.hour < 12 else 'PM'}"
