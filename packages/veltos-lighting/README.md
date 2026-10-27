# veltos-lighting — VeltOS Keyboard Lighting

A laptop keyboard's lights in the layout of Windows 11's Dynamic Lighting
(product owner, 2026-10-27: "laptop keyboards light up; write an app that
turns them on and off and sets their colours, and add it to Settings").
Start: "Keyboard Lighting" / "Klavye Aydınlatması"; Settings >
Personalization > Keyboard lighting opens it.

- **Lighting** on/off and **Brightness** for every keyboard light Linux
  shows (`/sys/class/leds/*kbd_backlight*`: ThinkPad, Dell, HP, Lenovo
  IdeaPad, ASUS, MSI, System76, Apple and others).
- **Colour** (twelve swatches, a custom colour by hue, "Match my accent
  colour") where the driver has one: the kernel's multicolour LEDs
  (`multi_intensity`), ASUS (`asus-wmi` `kbd_rgb_mode`, also the
  **Breathing** and **Colour cycle** effects with their speed) and
  System76 (`color`). Formats checked against the kernel's documentation
  (Debian 13, 6.12) on 2026-10-27.
- The choices are kept per light (`~/.config/veltos/lighting.json`) and
  applied again at sign-in (`/etc/xdg/autostart/veltos-lighting-restore.desktop`
  runs `veltos-lighting --restore`: Python without Qt, ends at once on a
  PC without keyboard lights).
- Writing the light's files needs root: `/usr/libexec/veltos/keyboard-light`
  (`helper.py`) runs through pkexec; the polkit action
  `org.veltos.lighting.set` lets the signed-in user of the active session
  do it without a password, as Windows does. The helper accepts only a
  keyboard light of this PC and checked values.
- Not covered: keyboards with their own USB controller (gaming keyboards)
  need their maker's tools (OpenRGB is not in Debian 13); laptop drivers
  that are not in Debian's kernel (TUXEDO/Clevo, Lenovo Legion RGB) show
  no colour.

## Tests

`tests/test_lighting.py`: a made-up `/sys/class/leds` with a ThinkPad
(brightness only), ASUS, System76 and a multicolour LED; the helper's
checks and writes, the sign-in restore, the window offscreen in English
and Turkish. Not tried on a real backlit keyboard yet.
