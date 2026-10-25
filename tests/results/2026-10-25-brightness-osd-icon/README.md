# Brightness flyout: the quick settings' sun icon (2026-10-25, dev VM)

Item 25 of the product owner's 2026-10-23 list. QEMU dev VM with this
change's `veltos-desktop`; the brightness flyout was called through
plasmashell's OSD service (`qdbus6 org.kde.plasmashell /org/kde/osdService
org.kde.osdService.brightnessChanged 60`, what PowerDevil does on a
brightness key), the volume flyout with the volume key.

| Picture | What it shows |
|---|---|
| `brightness-flyout.png` | The brightness flyout with the sun (`brightness-high-symbolic`) |
| `quick-settings.png` | Quick settings: the brightness slider's sun is the same icon, the volume slider's speaker the same outline as the volume flyout |
| `volume-flyout.png` | The volume flyout with the outline speaker (`audio-volume-high-symbolic`) |

plasmashell asks for `video-display-brightness` (a monitor picture) for
the screen brightness and `input-keyboard-brightness` for the keyboard
light (both found with `strings -el /usr/bin/plasmashell`, Plasma 6.3);
the flyout (`OsdItem.qml`, `shownIcon`) shows the quick settings' icons
instead. Not seen with a real brightness key on a laptop.
