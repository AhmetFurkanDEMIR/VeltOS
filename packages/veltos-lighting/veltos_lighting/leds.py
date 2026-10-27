"""Keyboard lights as Linux shows them (/sys/class/leds), checked against
Debian 13's kernel 6.12 on 2026-10-27:

- Every laptop driver that lights its keyboard registers an LED named
  "<driver>::kbd_backlight" (thinkpad_acpi "tpacpi::kbd_backlight",
  dell-laptop, ideapad-laptop, hp-wmi, msi-ec, asus-wmi, system76_acpi,
  apple, ...): `brightness` from 0 to `max_brightness`. UPower offers the
  first one to every user (org.freedesktop.UPower.KbdBacklight).
- Colours depend on the driver:
  * the kernel's multicolor LED class (leds-class-multicolor):
    `multi_index` ("red green blue") and `multi_intensity` ("255 0 128");
  * ASUS (asus-wmi): `kbd_rgb_mode` takes "cmd mode red green blue speed"
    (cmd 1 keeps it after a restart; mode 0 static, 1 breathing, 2 colour
    cycle; speed 0 slow, 1 medium, 2 fast; Documentation/ABI/testing/
    sysfs-platform-asus-wmi);
  * System76 (system76_acpi): `color` takes "RRGGBB".
  Other drivers light the keyboard in one colour: brightness only.
- Keyboards with their own USB controller (gaming keyboards) need their
  maker's tools; OpenRGB is not in Debian 13.

Writing to these files needs root: the VeltOS helper (helper.py, through
pkexec with an action that lets the signed-in user do it without a
password, as Windows changes keyboard lights) writes them. This module
only reads; `root` is a parameter for the tests.
"""

import re
from pathlib import Path

LEDS = Path("/sys/class/leds")
EFFECTS = ("static", "breathing", "cycle")
ASUS_MODES = {"static": 0, "breathing": 1, "cycle": 2}

# Display names by driver prefix (the part before "::").
MAKERS = {"tpacpi": "Lenovo ThinkPad", "dell": "Dell", "asus": "ASUS", "system76_acpi": "System76",
          "system76": "System76", "ideapad": "Lenovo IdeaPad", "hp": "HP", "msiacpi": "MSI", "msi": "MSI",
          "smc": "Apple", "apple": "Apple", "chromeos": "Chromebook", "platform": "", "acer": "Acer",
          "samsung": "Samsung", "toshiba": "Toshiba", "fujitsu": "Fujitsu", "sony": "Sony",
          "huawei": "Huawei", "lg": "LG", "framework_laptop": "Framework", "cros_ec": "Chromebook"}


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def is_keyboard(name):
    return "kbd_backlight" in name and "::" in name or name.endswith(":kbd_backlight")


def color_kind(folder):
    if (folder / "kbd_rgb_mode").exists():
        return "asus"
    if (folder / "color").exists():
        return "system76"
    index = read(folder / "multi_index").split()
    if (folder / "multi_intensity").exists() and {"red", "green", "blue"} <= set(index):
        return "multicolor"
    return ""


def current_color(folder, kind):
    """"#RRGGBB" the keyboard shows now, or "" when it cannot tell."""
    if kind == "system76":
        value = read(folder / "color")
        return "#" + value.upper() if re.fullmatch(r"[0-9A-Fa-f]{6}", value) else ""
    if kind == "multicolor":
        index = read(folder / "multi_index").split()
        values = read(folder / "multi_intensity").split()
        if len(index) == len(values):
            channels = dict(zip(index, values))
            try:
                return "#%02X%02X%02X" % tuple(min(255, int(channels[c])) for c in ("red", "green", "blue"))
            except (KeyError, ValueError):
                return ""
    return ""        # asus-wmi cannot be read back


def maker(name):
    prefix = name.split(":", 1)[0]
    return MAKERS.get(prefix, prefix.replace("_", " ").title() if prefix else "")


def keyboards(root=LEDS):
    """The keyboard lights: [{"id", "maker", "brightness", "max", "colorKind",
    "color", "effects"}], by name."""
    found = []
    folder_root = Path(root)
    if not folder_root.is_dir():
        return found
    for folder in sorted(folder_root.iterdir()):
        if not is_keyboard(folder.name):
            continue
        try:
            maximum = int(read(folder / "max_brightness") or 0)
            brightness = int(read(folder / "brightness") or 0)
        except ValueError:
            continue
        if maximum <= 0:
            continue
        kind = color_kind(folder)
        found.append({"id": folder.name, "maker": maker(folder.name), "brightness": brightness, "max": maximum,
                      "colorKind": kind, "color": current_color(folder, kind),
                      "effects": list(EFFECTS) if kind == "asus" else (["static"] if kind else [])})
    return found


def valid_id(name, root=LEDS):
    """The LED's folder when `name` is a keyboard light of this PC, else None."""
    if not name or "/" in name or name.startswith(".") or not is_keyboard(name):
        return None
    folder = Path(root) / name
    return folder if folder.is_dir() else None


def parse_color(value):
    """(r, g, b) of "#RRGGBB", or None."""
    match = re.fullmatch(r"#?([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})", value or "")
    return tuple(int(part, 16) for part in match.groups()) if match else None


def writes(folder, kind, brightness=None, color=None, effect="static", speed=1):
    """[(file, text)] that set the light: what the helper writes, in order."""
    out = []
    rgb = parse_color(color) if color else None
    if rgb is not None:
        if kind == "asus":
            out.append((folder / "kbd_rgb_mode", f"1 {ASUS_MODES.get(effect, 0)} {rgb[0]} {rgb[1]} {rgb[2]} "
                                                f"{max(0, min(2, speed))}"))
        elif kind == "system76":
            out.append((folder / "color", "%02X%02X%02X" % rgb))
        elif kind == "multicolor":
            index = read(folder / "multi_index").split()
            channel = {"red": rgb[0], "green": rgb[1], "blue": rgb[2]}
            out.append((folder / "multi_intensity", " ".join(str(channel.get(c, 0)) for c in index)))
    if brightness is not None:
        maximum = int(read(folder / "max_brightness") or 0)
        out.append((folder / "brightness", str(max(0, min(maximum, int(brightness))))))
    return out
