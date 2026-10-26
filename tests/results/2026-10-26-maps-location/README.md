# VeltOS Maps and location settings

Item 40 of the product owner's list.

## Verified

- The rebuilt Maps package opened Google Maps in its VeltOS window in the
  QEMU development VM.
- The **My location** action is disabled when location access is off and
  enabled after opting in. A deterministic test provider verified that a
  fix updates the map URL.
- The Settings Location page opened from Maps, displayed the GeoClue and
  Mozilla Location Service privacy disclosure, and shared the same setting.
- On the installed package, GeoClue was activated when **My location** was
  requested. With location enabled, the request timed out after 25 seconds;
  the VM has no physical GPS or nearby Wi-Fi scan source. Turning location
  off afterward disabled **My location** again.
- The Maps package and its GeoClue D-Bus/introspection dependencies installed
  in the VM.

## Not verified

No real location fix or accuracy was demonstrated. The QEMU timeout is not
evidence that location acquisition works on physical hardware; test a real
GPS or supported Wi-Fi location source before making that claim.

## Screenshots

- `maps-final-installed.png` — Google Maps rendered in the rebuilt app.
- `maps-final-location-enabled.png` — location opt-in enabled.
- `maps-final-location-result.png` — the VM's 25-second no-fix timeout.
- `maps-final-location-off.png` — access off and **My location** disabled.
- `maps-location-settings-latest.png` — Settings Location page and privacy
  disclosure.

Package validation in the Debian builder: 8 repository checks, 10 Maps tests,
and 116 Settings tests passed.
