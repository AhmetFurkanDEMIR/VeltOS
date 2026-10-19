"""A stand-in for the command-line tools devices.py runs (test data only).

Outputs are in the formats of the tools in Debian 13 (nmcli 1.52,
bluetoothctl 5.82, pactl 17, kscreen-doctor 6.3, timedatectl 257). Every
command is recorded in `commands`.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_settings import devices  # noqa: E402

# A Bluetooth adapter as the kernel shows it (/sys/class/bluetooth/hci0).
devices.BLUETOOTH_SYSFS = Path(tempfile.mkdtemp()) / "bluetooth"
(devices.BLUETOOTH_SYSFS / "hci0").mkdir(parents=True)

SINKS = [{
    "index": 50, "name": "alsa_output.pci-0000_00_1f.3.analog-stereo",
    "description": "Speakers (Built-in Audio)", "mute": False,
    "volume": {"front-left": {"value": 42597, "value_percent": "65%"},
               "front-right": {"value": 42597, "value_percent": "65%"}},
}, {
    "index": 51, "name": "bluez_output.AA_BB_CC_DD_EE_FF.1",
    "description": "WH-1000XM4", "mute": True,
    "volume": {"mono": {"value": 32768, "value_percent": "50%"}},
}]
SOURCES = [{
    "index": 60, "name": "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor",
    "description": "Monitor of Speakers", "mute": False,
    "volume": {"mono": {"value": 65536, "value_percent": "100%"}},
}, {
    "index": 61, "name": "alsa_input.pci-0000_00_1f.3.analog-stereo",
    "description": "Microphone (Built-in Audio)", "mute": False,
    "volume": {"front-left": {"value": 26214, "value_percent": "40%"}},
}]
SCREENS = {"outputs": [{
    "id": 1, "name": "eDP-1", "connected": True, "enabled": True, "scale": 1.25,
    "currentModeId": "3", "preferredModes": ["1"],
    "modes": [
        {"id": "1", "name": "1920x1080@60", "refreshRate": 60.0, "size": {"width": 1920, "height": 1080}},
        {"id": "2", "name": "1920x1080@48", "refreshRate": 48.0, "size": {"width": 1920, "height": 1080}},
        {"id": "3", "name": "1280x720@60", "refreshRate": 60.0, "size": {"width": 1280, "height": 720}},
    ],
}, {
    "id": 2, "name": "HDMI-A-1", "connected": False, "enabled": False, "modes": [],
}]}

OUTPUTS = {
    ("nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"):
        "wlp2s0:wifi:connected:Home Net\nenp1s0:ethernet:unavailable:\nlo:loopback:connected (externally):lo\n",
    ("nmcli", "-t", "-f", "WIFI", "radio"): "enabled\n",
    ("nmcli", "-t", "-f", "UUID,TYPE", "connection", "show"):
        "1111-aaaa:802-11-wireless\n2222-bbbb:802-3-ethernet\n3333-cccc:802-11-wireless\n",
    ("nmcli", "-t", "-g", "802-11-wireless.ssid", "connection", "show", "uuid", "1111-aaaa"): "Home Net\n",
    ("nmcli", "-t", "-g", "802-11-wireless.ssid", "connection", "show", "uuid", "3333-cccc"): "Cafe\\:Free\n",
    ("nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "auto"):
        "*:Home Net:82:WPA2\n :Home Net:40:WPA2\n :Cafe\\:Free:60:\n ::30:WPA2\n"
        " :Office:55:WPA2 802.1X\n :New Net:70:WPA3\n",
    ("bluetoothctl", "list"): "Controller 00:1A:7D:DA:71:13 velt [default]\n",
    ("bluetoothctl", "show"): "Controller 00:1A:7D:DA:71:13 (public)\n\tName: velt\n\tPowered: yes\n",
    ("bluetoothctl", "devices", "Paired"):
        "Device AA:BB:CC:DD:EE:FF WH-1000XM4\nDevice 11:22:33:44:55:66 MX Master 3\n",
    ("bluetoothctl", "info", "AA:BB:CC:DD:EE:FF"):
        "Device AA:BB:CC:DD:EE:FF (public)\n\tIcon: audio-headset\n\tConnected: yes\n"
        "\tBattery Percentage: 0x50 (80)\n",
    ("bluetoothctl", "info", "11:22:33:44:55:66"):
        "Device 11:22:33:44:55:66 (random)\n\tIcon: input-mouse\n\tConnected: no\n",
    ("pactl", "--format=json", "list", "sinks"): json.dumps(SINKS),
    ("pactl", "--format=json", "list", "sources"): json.dumps(SOURCES),
    ("pactl", "get-default-sink"): "alsa_output.pci-0000_00_1f.3.analog-stereo\n",
    ("pactl", "get-default-source"): "alsa_input.pci-0000_00_1f.3.analog-stereo\n",
    ("kscreen-doctor", "--json"): json.dumps(SCREENS),
    ("timedatectl", "show", "-p", "Timezone", "-p", "NTP", "-p", "CanNTP"):
        "Timezone=Europe/Istanbul\nNTP=yes\nCanNTP=yes\n",
    ("timedatectl", "list-timezones"): "America/New_York\nEurope/Istanbul\nEurope/London\nUTC\n",
}


class FakeSystem:
    def __init__(self, outputs=None, fail=()):
        self.outputs = dict(OUTPUTS)
        self.outputs.update(outputs or {})
        self.fail = set(fail)          # command names (first words) that fail
        self.commands = []

    def __call__(self, command, timeout=20):
        self.commands.append(list(command))
        key = tuple(command)
        if command[0] in self.fail or " ".join(command[:3]) in self.fail:
            return 1, ""
        if command[:3] == ["nmcli", "radio", "wifi"]:
            self.outputs[("nmcli", "-t", "-f", "WIFI", "radio")] = \
                "enabled\n" if command[3] == "on" else "disabled\n"
        if key in self.outputs:
            return 0, self.outputs[key]
        return 0, ""
