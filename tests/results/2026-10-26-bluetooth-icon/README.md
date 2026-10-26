# Quick Settings Bluetooth icon

Item 41 of the product owner's list.

## Verified

- Quick Settings' paired and nearby device rows now use the monochrome
  `bluetooth-symbolic` glyph. The active Bluetooth tile retains its accent
  colour, and Wi-Fi rows are unchanged.
- `veltos-desktop` built successfully; 8 repository checks and 132 package
  tests passed.
- The rebuilt package was installed in the QEMU development VM. Plasma's
  QML cache was cleared and the shell restarted before the screenshot.
- A nearby-device row was provided by the repository's `btvirt` test aid
  using Debian's `bluez-test-tools` 5.82-1.1 in the VM. No physical
  Bluetooth device was used.

## Screenshot

- `bluetooth-device-icons.png` — the nearby device row with the plain
  Bluetooth glyph.
- The earlier blue device artwork is visible in
  `../2026-10-24-quick-settings-wifi-bluetooth/bluetooth-paired-connected.png`.
