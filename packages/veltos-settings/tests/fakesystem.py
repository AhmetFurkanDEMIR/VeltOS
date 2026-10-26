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
        self.inputs = []               # (command, standard input) when there was one
        # veltos-desktop's power-mode helper (its own tests cover the policy).
        self.power = {"profiles": ["power-saver", "balanced", "performance"], "active": "balanced",
                      "source": "ac", "hasBattery": True,
                      "modes": {"ac": "performance", "battery": "power-saver"}}

    def power_mode(self, args):
        state = self.power
        if args[:1] == ["prefer"] and len(args) == 3:
            source, profile = args[1:]
            if profile not in state["profiles"]:
                return 1, json.dumps(dict(state, success=False, error="not supported"))
            state["modes"][source] = profile
            if source == state["source"]:
                state["active"] = profile
        return 0, json.dumps(dict(state, success=True, error=""))

    def __call__(self, command, timeout=20, input=None):
        self.commands.append(list(command))
        if input is not None:
            self.inputs.append((list(command), input))
        key = tuple(command)
        if command[0] in self.fail or " ".join(command[:3]) in self.fail:
            return 1, ""
        if command[0] == "/usr/libexec/veltos/power-mode":
            return self.power_mode(command[1:])
        if command[:3] == ["nmcli", "radio", "wifi"]:
            self.outputs[("nmcli", "-t", "-f", "WIFI", "radio")] = \
                "enabled\n" if command[3] == "on" else "disabled\n"
        if key in self.outputs:
            return 0, self.outputs[key]
        return 0, ""


class HotspotRunner:
    """NetworkManager, iw and ip for the mobile hotspot, in the formats of
    nmcli 1.52, iw 6.9 and iproute2 6.15 (Debian 13), as seen in the dev VM
    with a mac80211_hwsim radio (2026-10-26). `wifi_client` puts the Wi-Fi
    card on a network as well; `ethernet=False` leaves only Wi-Fi."""

    def __init__(self, ethernet=True, wifi_client=False, ap=True, second_card=False):
        self.ethernet = ethernet
        self.wifi_client = wifi_client
        self.ap = ap
        self.second_card = second_card
        self.profile = None          # {"ssid", "password", "band", "device"}
        self.up_on = ""              # device the hotspot runs on
        self.fail_up = False
        self.no_ir_5ghz = False      # the regulatory domain forbids starting a 5 GHz network
        self.metrics = {"enp1s0": 100, "wlp2s0": 600, "wlp3s0": 600}
        self.stations = []           # (mac, ip, name)
        self.commands = []
        self.written = []

    def write(self, settings):
        self.written.append(settings)
        self.profile = {"ssid": settings["802-11-wireless"]["ssid"].decode(),
                        "password": settings["802-11-wireless-security"]["psk"],
                        "band": settings["802-11-wireless"].get("band", ""),
                        "device": settings["connection"]["interface-name"],
                        "uuid": settings["connection"]["uuid"]}
        return True

    def resolve(self, ip, server):
        return next((name for _mac, address, name in self.stations if address == ip), "")

    def __call__(self, command, timeout=20, input=None):
        self.commands.append(list(command))
        c = command
        if c[:3] == ["nmcli", "-t", "-f"] and c[3] == "DEVICE,TYPE,STATE,CONNECTION":
            lines = []
            if self.ethernet:
                lines.append("enp1s0:ethernet:connected:Wired connection 1")
            if self.up_on == "wlp2s0":
                lines.append("wlp2s0:wifi:connected:VeltOS Hotspot")
            elif self.wifi_client:
                lines.append("wlp2s0:wifi:connected:Home Net")
            else:
                lines.append("wlp2s0:wifi:disconnected:")
            if self.second_card:
                lines.append("wlp3s0:wifi:connected:VeltOS Hotspot" if self.up_on == "wlp3s0"
                             else "wlp3s0:wifi:disconnected:")
            lines += ["lo:loopback:connected (externally):lo", "p2p-dev-wlp2s0:wifi-p2p:disconnected:"]
            return 0, "\n".join(lines) + "\n"
        if c[:4] == ["nmcli", "-t", "-f", "WIFI-PROPERTIES"]:
            ap = "yes" if self.ap else "no"
            return 0, (f"WIFI-PROPERTIES.WEP:yes\nWIFI-PROPERTIES.WPA2:yes\nWIFI-PROPERTIES.AP:{ap}\n"
                       "WIFI-PROPERTIES.ADHOC:yes\nWIFI-PROPERTIES.2GHZ:yes\nWIFI-PROPERTIES.5GHZ:yes\n")
        if c[:6] == ["nmcli", "-t", "-f", "NAME,UUID,TYPE,DEVICE", "connection", "show"]:
            lines = []
            if self.up_on and self.profile:
                lines.append(f"VeltOS Hotspot:{self.profile['uuid']}:802-11-wireless:{self.up_on}")
            if self.ethernet:
                lines.append("Wired connection 1:2222-bbbb:802-3-ethernet:enp1s0")
            if self.wifi_client and self.up_on != "wlp2s0":
                lines.append("Home Net:1111-aaaa:802-11-wireless:wlp2s0")
            lines.append("lo:84d5-lo:loopback:lo")
            return 0, "\n".join(lines) + "\n"
        if c[:4] == ["ip", "-4", "route", "show"]:
            lines = []
            if self.ethernet:
                lines.append(f"default via 192.168.1.1 dev enp1s0 proto dhcp src 192.168.1.20 "
                             f"metric {self.metrics['enp1s0']}")
            if self.wifi_client and self.up_on != "wlp2s0":
                lines.append(f"default via 192.168.0.1 dev wlp2s0 proto dhcp src 192.168.0.5 "
                             f"metric {self.metrics['wlp2s0']}")
            return 0, "\n".join(lines) + ("\n" if lines else "")
        if c[:3] == ["nmcli", "-s", "-t"]:
            if not self.profile:
                return 10, ""
            p = self.profile
            return 0, f"{p['ssid'].replace(':', chr(92) + ':')}\n{p['band']}\n{p['password']}\n{p['device']}\n"
        if c[:4] == ["nmcli", "--wait", "60", "connection"] and c[4] == "up":
            if self.fail_up or not self.profile:
                return 4, ""
            self.up_on = c[-1]
            return 0, ""
        if c[:3] == ["nmcli", "connection", "down"]:
            self.up_on = ""
            return 0, ""
        if c[:3] == ["nmcli", "device", "modify"]:
            self.metrics[c[3]] = int(c[5])
            return 0, ""
        if c[:3] == ["nmcli", "device", "reapply"]:
            self.metrics[c[3]] = 100 if c[3] == "enp1s0" else 600
            return 0, ""
        if c[:3] == ["ip", "neigh", "show"]:
            return 0, "".join(f"{ip} lladdr {mac} STALE \n" for mac, ip, _ in self.stations)
        if c[0].endswith("iw") and c[1] == "dev" and c[3:] == ["info"]:
            return 0, f"Interface {c[2]}\n\tifindex 3\n\twiphy {1 if c[2] == 'wlp3s0' else 0}\n\ttype managed\n"
        if c[0].endswith("iw") and c[1] == "phy" and c[3:] == ["info"]:
            flag = " (no IR)" if self.no_ir_5ghz else ""
            return 0, ("Wiphy " + c[2] + "\n\tBand 1:\n\t\tFrequencies:\n\t\t\t* 2412.0 MHz [1] (20.0 dBm)\n"
                       "\t\t\t* 2484.0 MHz [14] (20.0 dBm) (no IR)\n\tBand 2:\n\t\tFrequencies:\n"
                       f"\t\t\t* 5180.0 MHz [36] (20.0 dBm){flag}\n"
                       "\t\t\t* 5260.0 MHz [52] (20.0 dBm) (no IR, radar detection)\n")
        if c[0].endswith("iw") and c[3:] == ["station", "dump"]:
            return 0, "".join(f"Station {mac} (on {c[2]})\n\tinactive time:\t12 ms\n" for mac, _, _ in self.stations)
        if c[:5] == ["ip", "-4", "-o", "addr", "show"]:
            return 0, (f"5: {c[-1]}    inet 10.42.0.1/24 brd 10.42.0.255 scope global noprefixroute "
                       f"{c[-1]}\\       valid_lft forever preferred_lft forever\n")
        return 0, ""
