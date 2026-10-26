# veltos-weather — VeltOS Weather

The Weather app in the layout of Windows 11's Weather app (PySide6/QML),
on Open-Meteo's open data: no account, no key.

- **Navigation rail**: Forecast, Historical weather, Favorites, Settings.
- **Header**: "Search for location" (Open-Meteo's place search, GeoNames
  names in the app's language; arrows and Enter pick a result), Refresh,
  °F / °C. Under it the place, with the star (favorites) and home.
- **Forecast**: the current weather over a sky of its condition and the
  time of day (temperature, picture, condition, feels like, a sentence
  about the day, air quality, wind with its direction, humidity,
  visibility, pressure, dew point); the 10-day forecast (pictures, high
  and low, chance of precipitation; a click picks the day); the hourly
  chart of the chosen day (from now for today) with Overview (pictures,
  temperature, chance of precipitation), Precipitation, Wind (arrows),
  Humidity, UV index, Feels like, Cloud cover, Pressure, Visibility;
  weather details: Sun (sunrise and sunset, the sun on its path,
  daylight), Moon (phase drawn and named, illuminated share), Wind
  (compass), Humidity (dew point), UV index and air quality (coloured
  scales and advice, pollutants), Visibility, Pressure (trend), Feels
  like, Precipitation. The source and the time of the data at the bottom.
- **Historical weather**: average high and low of every month from five
  years of records (Open-Meteo's ERA5 archive), the chosen month's
  averages, highest and lowest, precipitation and days with precipitation.
- **Favorites**: cards with the weather now; a click opens the place, the
  bin removes it.
- **Settings**: temperature unit (°C by default, °F on request; product
  owner, 2026-10-26), launch location (home), about and the data's
  licence.
- First start: the home place is the city of the computer's time zone
  (`/etc/localtime`, "Europe/Istanbul" → İstanbul); without a network the
  app asks for a place and offers "Try again".
- English and Turkish; light and dark follow the system; the accent
  colour is the system's.

## Data

`openmeteo.py` asks `api.open-meteo.com` (forecast, 10 days, current
conditions every 15 minutes), `air-quality-api.open-meteo.com` (European
AQI and pollutants), `geocoding-api.open-meteo.com` (places) and
`archive-api.open-meteo.com` (records). Terms checked on 2026-10-25
(open-meteo.com/en/terms): the free API is for non-commercial use (no
ads, no subscriptions), 10,000 calls a day per IP address, data under
CC BY 4.0 (credited in the app). The app identifies itself
(`VeltOS-Weather/1.0`), rounds coordinates to four decimals and keeps
answers in `~/.cache/veltos-weather` (forecast 15 minutes, air quality an
hour, records 30 days); offline it shows the last saved answer.
MET Norway's API was the other candidate; its terms ask apps with many
users to go through their own caching proxy.

Settings (unit, home, last place, favorites): `~/.config/veltos/weather.json`.

## Files

| File | What |
|---|---|
| `veltos_weather/app.py` | Backend for the QML window: place, background loading, texts in the chosen units, chart and details, history, favorites, settings |
| `veltos_weather/openmeteo.py` | URLs, requests, cache, places, monthly averages |
| `veltos_weather/conditions.py` | WMO codes → words and pictures, skies, units, wind directions, AQI/UV bands, moon phase, sentences |
| `veltos_weather/strings.py` | English and Turkish texts |
| `veltos_weather/qml/` | `Main.qml` (window, rail, search, place), `ForecastPage.qml`, `HourlyChart.qml`, `HistoryPage.qml`, `FavoritesPage.qml`, `SettingsPage.qml`, `Drawings.qml` (sun path, moon, compass, scale), small parts |
| `veltos_weather/qml/icons/` | Weather pictures and glyphs drawn by `tools/weather-icons.py` (original VeltOS drawings) |

## Tests

`tests/test_weather.py`: every WMO code has words, a picture and a sky;
units and their Turkish forms; bands; the moon at two eclipses; the
texts in both languages; Open-Meteo's URLs (four decimals, no key), the
User-Agent, the cache (young, old, offline); places and monthly averages;
the backend on real answers kept in `tests/data` (first start from the
time zone, current weather, days, chart kinds, details, search,
favorites, °F, history, offline). `tests/test_ui.py`: the window offscreen
in English and Turkish, every page and chart kind, a narrow window, an
offline first start; any QML warning fails.

## Not done

- Windows 11 Weather's Maps (radar and temperature maps): there is no
  map and radar tile service that may be used by an app like this
  without a key or an agreement (OpenStreetMap's tile policy forbids it).
- Device location is offered by VeltOS Maps and its Location privacy
  setting. Weather itself still chooses its home place from the time zone
  or a search.
