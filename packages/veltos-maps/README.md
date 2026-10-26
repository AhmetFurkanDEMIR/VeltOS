# veltos-maps — VeltOS Maps

VeltOS Maps opens the public Google Maps website in a VeltOS window. Search
uses Google Maps URLs, so no Google Maps Platform API key is needed. Maps
needs an internet connection; its map content and search queries come from
Google and are subject to Google's terms and privacy policy.

The app uses an off-the-record Qt WebEngine profile: cookies, cache and site
permissions are kept in memory and are not retained after the app closes.
Only HTTPS Google domains are kept inside the map view; links to other sites
open in the user's browser. JavaScript is enabled for the maps website,
while plugins, persistent cookies and non-geolocation site permissions are
disabled or denied.

Location access is off by default. The switch in VeltOS Maps and Settings >
Privacy & security > Location writes the same `kdeglobals` preference. The
Maps toolbar's **My location** action requests a one-time fix from GeoClue 2
only while access is enabled, then opens that position in Google Maps.
GeoClue's default Wi-Fi provider may send nearby Wi-Fi information to Mozilla
Location Service to estimate a position; Google receives the coordinates
when the user chooses **My location**. Turning access off cancels a pending
request and revokes the web profile's in-memory geolocation permission. The
QEMU VM has no physical GPS or nearby Wi-Fi scan source, so a real-device
location fix and accuracy have not been verified.

## Files

| File | What |
|---|---|
| `veltos_maps/app.py` | Window backend, Maps URL search, GeoClue one-shot location requests, shared preference, and external-link handling |
| `veltos_maps/qml/Main.qml` | VeltOS toolbar and the Google Maps WebEngine view with guarded permissions |
| `veltos_maps/strings.py` | English and Turkish interface text |
| `data/90-veltos-maps.conf` | GeoClue authorization for the opt-in location request |
| `data/veltos-maps.desktop` | Application launcher and GeoClue desktop ID |

## Tests

`tests/test_maps.py` checks key-free search URLs, HTTPS origin checks, the
default-off shared preference, opt-in gating, and English/Turkish text.
`tests/test_ui.py` loads the real QML window offscreen in English without
network requests and verifies the My location action with a deterministic
test provider; this does not certify real hardware location acquisition.
