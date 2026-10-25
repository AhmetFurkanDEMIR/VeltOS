# VeltOS Weather (2026-10-25, dev VM, live data)

Item 21 of the product owner's 2026-10-23 list: a Weather app like
Windows 11's, without an API key. Turkish session, data from Open-Meteo
over the VM's network at 07:00-07:05 local time.

| Picture | What it shows |
|---|---|
| `first-start-istanbul.png` | First start with no settings: the home place is the city of the time zone (Europe/Istanbul → İstanbul); current weather at 07:00 (before sunrise: the night picture), 14 °C, partly cloudy, feels like, the sentence, air quality 32 (fair), wind with its direction, humidity, visibility, pressure, dew point; the 10-day forecast |
| `forecast-dark.png` | Maximised: the 10 days and the hourly chart (Overview: pictures, temperatures, chance of precipitation, hours from "Şimdi") |
| `details-dark.png` | Weather details: sun (sunrise 07:26, sunset 18:09, daylight), moon (full moon, 99 % lit), wind compass, humidity and dew point, UV index and air quality scales with advice and pollutants, visibility, pressure (steady), feels like, precipitation |
| `forecast-light.png`, `details-light.png` | The same in the light theme |
| `search.png` | "ankara" typed: Open-Meteo's place search in Turkish (GeoNames) |
| `history-ankara.png` | Ankara chosen, Historical weather: average high/low of every month from five years of records, October's averages, highest and lowest, precipitation and days with precipitation |
| `favorites.png` | Ankara starred: its card with the weather now |
| `condition-pictures.png` | The 17 weather pictures (tools/weather-icons.py) on a light card, a dark card and a sky |
| `app-icon.png` | The app icon (sun behind a cloud) next to Calendar, Clock and Mail |

Package tests: 22 (16 without a window on real answers kept in
`packages/veltos-weather/tests/data`, 6 window tests in English and
Turkish).

Not done: Windows 11 Weather's Maps page (no map/radar tile service that
may be used without a key or an agreement) and the device's location
(item 40).
