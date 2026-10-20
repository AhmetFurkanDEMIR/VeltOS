"""Bluetooth & devices > Mouse and Touchpad, through KWin.

KWin (Wayland) owns the input devices: their settings are D-Bus properties
of /org/kde/KWin/InputDevice/<eventN> (org.kde.KWin.InputDevice), changed
at once, and KWin reads them back at the next start from kcminputrc,
group [Libinput][<vendor>][<product>][<name>] (KWin 6.3, as KDE's mouse
settings module writes them).
"""

import re

from .devices import run

DEVICE_ROOT = "/org/kde/KWin/InputDevice"
IFACE = "org.kde.KWin.InputDevice"
# D-Bus property -> kcminputrc key
CONFIG_KEYS = {"leftHanded": "LeftHanded", "pointerAcceleration": "PointerAcceleration",
               "naturalScroll": "NaturalScroll", "tapToClick": "TapToClick",
               "scrollFactor": "ScrollFactor", "enabled": "Enabled"}
BOOLEAN = ("leftHanded", "naturalScroll", "tapToClick", "enabled")


def session_gdbus(*args):
    return ["gdbus", "call", "--session", "--dest", "org.kde.KWin", *args]


def parse_properties(text):
    """{name: value} from a gdbus GetAll reply (strings, numbers, booleans)."""
    values = {}
    for match in re.finditer(r"'(\w+)': <(?:(?:u?int\d+|double|byte) )?"
                             r"('(?:[^'\\]|\\.)*'|true|false|-?\d+(?:\.\d+)?(?:e-?\d+)?)>", text):
        key, raw = match.groups()
        if raw.startswith("'"):
            values[key] = re.sub(r"\\(.)", r"\1", raw[1:-1])
        elif raw in ("true", "false"):
            values[key] = raw == "true"
        elif re.fullmatch(r"-?\d+", raw):
            values[key] = int(raw)
        else:
            values[key] = float(raw)
    return values


class Inputs:
    def __init__(self, runner=run):
        self.run = runner

    def devices(self):
        code, out = self.run(session_gdbus("--object-path", DEVICE_ROOT, "--method",
                                           "org.freedesktop.DBus.Properties.Get",
                                           "org.kde.KWin.InputDeviceManager", "devicesSysNames"))
        names = re.findall(r"'(event\d+)'", out) if code == 0 else []
        devices = []
        for name in names:
            code, out = self.run(session_gdbus("--object-path", f"{DEVICE_ROOT}/{name}", "--method",
                                               "org.freedesktop.DBus.Properties.GetAll", IFACE))
            if code != 0:
                continue
            props = parse_properties(out)
            if props.get("pointer") and not props.get("keyboard"):
                devices.append(dict(props, sysName=name))
        return devices

    def state(self):
        devices = self.devices()
        mice = [d for d in devices if not d.get("touchpad")]
        pads = [d for d in devices if d.get("touchpad")]

        def first(items, key, default):
            return items[0].get(key, default) if items else default
        return {
            "hasMouse": bool(mice), "hasTouchpad": bool(pads),
            "leftHanded": first(mice or pads, "leftHanded", False),
            "speed": first(mice, "pointerAcceleration", 0.0),
            "scrollFactor": first(mice, "scrollFactor", 1.0),
            "mouseNaturalScroll": first(mice, "naturalScroll", False),
            "touchpadOn": first(pads, "enabled", True),
            "tapToClick": first(pads, "tapToClick", False),
            "touchpadNaturalScroll": first(pads, "naturalScroll", True),
            "touchpadSpeed": first(pads, "pointerAcceleration", 0.0),
        }

    def set(self, prop, value, touchpad=None):
        """Set a property on all mice (touchpad=False), all touchpads (True)
        or every pointing device (None), now and for the next start."""
        if prop not in CONFIG_KEYS:
            return False
        if prop in BOOLEAN:
            value = bool(value)
            variant = "<true>" if value else "<false>"
        else:
            value = float(value)
            if prop == "pointerAcceleration":
                value = max(-1.0, min(1.0, value))
            variant = f"<{value:.3f}>"
        ok = True
        for device in self.devices():
            if touchpad is not None and bool(device.get("touchpad")) != touchpad:
                continue
            if prop == "leftHanded" and not device.get("supportsLeftHanded", True):
                continue
            ok &= self.run(session_gdbus("--object-path", f"{DEVICE_ROOT}/{device['sysName']}", "--method",
                                         "org.freedesktop.DBus.Properties.Set", IFACE, prop, variant))[0] == 0
            text = ("true" if value else "false") if prop in BOOLEAN else f"{value:.3f}"
            self.run(["kwriteconfig6", "--file", "kcminputrc", "--group", "Libinput",
                      "--group", str(device.get("vendor", 0)), "--group", str(device.get("product", 0)),
                      "--group", device.get("name", ""), "--key", CONFIG_KEYS[prop], text])
        return ok
