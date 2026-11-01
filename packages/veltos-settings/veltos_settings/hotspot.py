"""Network & internet > Mobile hotspot: share this PC's internet connection
over Wi-Fi, as Windows 11's Mobile hotspot does.

NetworkManager does the work. The hotspot is one Wi-Fi profile in access
point mode with IPv4 "shared": NetworkManager starts dnsmasq for DHCP and
DNS and adds nftables rules that masquerade the devices' traffic. The
profile belongs to the user (`connection.permissions user:NAME`), so polkit
lets a standard user change and start it without an administrator password
(settings.modify.own and network-control are "yes" for active sessions).
Its UUID is derived from the user name, so every user has one hotspot
profile that is found again without a search.

"Share my internet connection from": NetworkManager masquerades towards
whatever the default route is. Choosing another connection makes it the
PC's preferred one while the hotspot runs (`nmcli device modify` with a
lower route metric, runtime only); stopping the hotspot gives the device
its own settings back (`nmcli device reapply`).

Over the same Wi-Fi card: most laptops reach the internet through their
only Wi-Fi card, and Windows 11 shares that connection over the same
adapter. Many cards can be connected to a network and host one at the same
time (iw's "valid interface combinations": a station and an access point,
often on one channel). Then a privileged helper adds a second interface on
the card (`/usr/libexec/veltos/hotspot-interface`, pkexec, no password for
the active session's user), the hotspot runs there on the channel of the
card's own connection, and stopping it removes the interface again. Before
2026-10-31 VeltOS said such a PC could not share its connection
(product owner: "it works in Windows 11").

Which band: the band chosen in Edit where the card may start a network
on it (iw marks the channels where it may not "no IR", "radar detection"
or "disabled"), then 2.4 GHz; a card that shares its own connection uses
the channel of that connection where it may (no time-sharing between two
channels). The owner's laptop could not start a 5 GHz hotspot beside its
5 GHz connection (2026-11-01); VeltOS then falls back to 2.4 GHz, and
Settings says so. Every failed start is written to
`~/.cache/veltos-settings/hotspot.log` with what the card reported, so a
report from a PC we cannot test on says why.

The network key never goes on a command line: the profile is written
through NetworkManager's D-Bus API (`write_profile`), and Settings hands
the key to the command-line helper on standard input.

Connected devices: the stations the Wi-Fi card reports (`iw station
dump`, readable by users), their addresses from the neighbour table and
their names from the hotspot's own DNS server (dnsmasq answers reverse
lookups for its DHCP leases; its lease file is root-only).

Run as `/usr/libexec/veltos/hotspot status|start|stop|configure|source
UUID` (Quick Settings), it prints the state as JSON; `configure` reads
{"ssid", "password", "band"} as JSON from standard input.
"""

import json
import os
import re
import secrets
import socket
import string
import sys
import time
import uuid as uuid_module
from pathlib import Path

try:
    from veltos_settings.devices import run, split_terse, terse_lines
except ImportError:  # pragma: no cover - run from the source tree
    from devices import run, split_terse, terse_lines

PROFILE_ID = "VeltOS Hotspot"
# Namespace of the per-user profile UUIDs (uuid5 of "veltos-hotspot:USER").
UUID_NAMESPACE = uuid_module.UUID("5b3fe04f-7cff-4a8f-a8f0-2fa8f00e1846")
IW = "/usr/sbin/iw"
# The hotspot's own interface on a card that stays connected (the helper's NAME).
VIRTUAL = "veltos-ap"
INTERFACE_HELPER = "/usr/libexec/veltos/hotspot-interface"
# How much of the start log is kept (characters).
LOG_LIMIT = 32768
BANDS = ("", "bg", "a")          # Any available, 2.4 GHz, 5 GHz (NetworkManager's names)
# Connection types whose default route can be shared (nmcli's type names).
SOURCE_TYPES = {"802-3-ethernet": "ethernet", "802-11-wireless": "wifi", "gsm": "cellular",
                "cdma": "cellular", "bluetooth": "bluetooth", "vpn": "vpn", "wireguard": "vpn",
                "pppoe": "ethernet", "infiniband": "ethernet"}
PASSWORD_CHARS = "".join(c for c in string.ascii_letters + string.digits if c not in "0OolI1")
LIVE_NEIGHBOURS = ("REACHABLE", "DELAY", "PROBE")


def user_name():
    try:
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name
    except (ImportError, KeyError):
        return os.environ.get("USER", "user")


def profile_uuid(user):
    return str(uuid_module.uuid5(UUID_NAMESPACE, "veltos-hotspot:" + user))


def config_path():
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "veltos" / "hotspot.json"


def log_path():
    cache = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return Path(cache) / "veltos-settings" / "hotspot.log"


def valid_ssid(ssid):
    return isinstance(ssid, str) and ssid.strip() == ssid and 0 < len(ssid.encode("utf-8")) <= 32


def valid_password(password):
    """WPA2-Personal: 8 to 63 printable ASCII characters (as Windows asks)."""
    return (isinstance(password, str) and 8 <= len(password) <= 63
            and all(" " <= c <= "~" for c in password))


def default_ssid():
    """"<PC name> 1234", the pattern of Windows' default hotspot name."""
    host = socket.gethostname().split(".")[0] or "VeltOS"
    name = f"{host} {secrets.randbelow(9000) + 1000}"
    return name if valid_ssid(name) else f"VeltOS {secrets.randbelow(9000) + 1000}"


def default_password():
    return "".join(secrets.choice(PASSWORD_CHARS) for _ in range(8))


def profile_settings(user, ssid, password, band, device, channel=0):
    """The whole hotspot profile as plain Python values (write_profile
    turns them into D-Bus types)."""
    wireless = {"ssid": ssid.encode("utf-8"), "mode": "ap"}
    if band:
        wireless["band"] = band
        if channel:
            wireless["channel"] = channel
    return {
        "connection": {"id": PROFILE_ID, "uuid": profile_uuid(user), "type": "802-11-wireless",
                       "autoconnect": False, "permissions": [f"user:{user}:"],
                       "interface-name": device},
        "802-11-wireless": wireless,
        "802-11-wireless-security": {"key-mgmt": "wpa-psk", "proto": ["rsn"], "pairwise": ["ccmp"],
                                     "group": ["ccmp"], "psk": password},
        "ipv4": {"method": "shared"},
        "ipv6": {"method": "ignore"},
    }


VARIANT_TYPES = {"ssid": "ay", "autoconnect": "b", "permissions": "as", "proto": "as",
                 "pairwise": "as", "group": "as", "channel": "u"}


def shared_channels(phy_info):
    """How many channels a card may use while it is connected to a network
    and hosts one (the best of iw's "valid interface combinations" with a
    station and an access point); 0 if it cannot do both at once."""
    block = re.search(r"valid interface combinations:\n(.*?)(?=\n\t\S|\Z)", phy_info, re.S)
    best = 0
    for entry in re.split(r"^\s*\* ", block.group(1), flags=re.M) if block else []:
        groups = [([name.strip() for name in names.split(",")], int(limit))
                  for names, limit in re.findall(r"#\{\s*([^}]*)\}\s*<=\s*(\d+)", entry)]
        total = re.search(r"total <= (\d+)", entry)
        channels = re.search(r"#channels <= (\d+)", entry)
        if not total or int(total.group(1)) < 2:
            continue
        if not any("managed" in names for names, _ in groups) or not any("AP" in names for names, _ in groups):
            continue
        if any("managed" in names and "AP" in names and limit < 2 for names, limit in groups):
            continue
        best = max(best, int(channels.group(1)) if channels else 1)
    return best


def channel_of(frequency):
    """(band, channel) of a frequency in MHz: ("bg", 6) for 2437."""
    if frequency == 2484:
        return "bg", 14
    if 2412 <= frequency < 2484:
        return "bg", (frequency - 2407) // 5
    if 5000 < frequency < 5925:
        return "a", (frequency - 5000) // 5
    return "", 0


def frequency_of(band, channel):
    """The frequency (MHz) of a channel: 2437 for ("bg", 6)."""
    if band == "bg":
        return 2484 if channel == 14 else 2407 + 5 * channel
    if band == "a":
        return 5000 + 5 * channel
    return 0


def ap_allowed(phy_info, frequency):
    """Whether the card may start a network on a frequency: iw marks the
    channels where it may not "no IR" (no initiating radiation: a station may
    use them, an access point may not), "radar detection" (DFS) or
    "disabled". Without iw's word a frequency counts as allowed."""
    for mhz, flags in re.findall(r"^\s*\* (\d{4})(?:\.\d+)? MHz \[\d+\](.*)$", phy_info, re.M):
        if int(mhz) == frequency:
            return not re.search(r"no IR|disabled|radar", flags)
    return True


def write_profile(settings):
    """Create or replace the profile through NetworkManager's D-Bus API
    (Settings.AddConnection / Settings.Connection.Update). True on success."""
    try:
        from gi.repository import Gio, GLib
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    except Exception:  # no GLib bindings or no system bus
        return False
    value = {group: {key: GLib.Variant(VARIANT_TYPES.get(key, "s"), item) for key, item in values.items()}
             for group, values in settings.items()}

    def call(path, interface, method, args, reply):
        return bus.call_sync("org.freedesktop.NetworkManager", path, interface, method, args,
                             GLib.VariantType(reply), Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION,
                             30000, None).unpack()

    try:
        path = call("/org/freedesktop/NetworkManager/Settings", "org.freedesktop.NetworkManager.Settings",
                    "GetConnectionByUuid", GLib.Variant("(s)", (settings["connection"]["uuid"],)), "(o)")[0]
    except GLib.Error:
        path = None
    try:
        if path:
            call(path, "org.freedesktop.NetworkManager.Settings.Connection", "Update",
                 GLib.Variant("(a{sa{sv}})", (value,)), "()")
        else:
            call("/org/freedesktop/NetworkManager/Settings", "org.freedesktop.NetworkManager.Settings",
                 "AddConnection", GLib.Variant("(a{sa{sv}})", (value,)), "(o)")
        return True
    except GLib.Error:
        return False


def reverse_name(address, server, timeout=0.6):
    """A device's name from the hotspot's DNS server (dnsmasq names its
    DHCP clients): a PTR query over UDP, standard library only."""
    try:
        parts = [int(p) for p in address.split(".")]
        if len(parts) != 4:
            return ""
    except ValueError:
        return ""
    ident = secrets.randbelow(65536)
    question = b"".join(bytes([len(label)]) + label.encode()
                        for label in [str(p) for p in reversed(parts)] + ["in-addr", "arpa"]) + b"\0"
    query = ident.to_bytes(2, "big") + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00" + question + b"\x00\x0c\x00\x01"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(query, (server, 53))
            reply = sock.recv(512)
    except OSError:
        return ""
    return parse_ptr_reply(reply, ident)


def _read_name(data, offset):
    labels, jumps = [], 0
    while offset < len(data) and jumps < 20:
        length = data[offset]
        if length == 0:
            return ".".join(labels), offset + 1
        if length & 0xC0 == 0xC0:
            pointer = ((length & 0x3F) << 8) | data[offset + 1]
            name, _ = _read_name(data, pointer) if pointer < offset else ("", 0)
            return ".".join(labels + ([name] if name else [])), offset + 2
        labels.append(data[offset + 1:offset + 1 + length].decode("utf-8", "replace"))
        offset += 1 + length
        jumps += 1
    return ".".join(labels), offset


def parse_ptr_reply(reply, ident):
    if len(reply) < 12 or int.from_bytes(reply[:2], "big") != ident or reply[3] & 0x0F:
        return ""
    questions, answers = int.from_bytes(reply[4:6], "big"), int.from_bytes(reply[6:8], "big")
    offset = 12
    try:
        for _ in range(questions):
            _, offset = _read_name(reply, offset)
            offset += 4
        for _ in range(answers):
            _, offset = _read_name(reply, offset)
            kind = int.from_bytes(reply[offset:offset + 2], "big")
            length = int.from_bytes(reply[offset + 8:offset + 10], "big")
            offset += 10
            if kind == 12:
                return _read_name(reply, offset)[0].rstrip(".")
            offset += length
    except IndexError:
        pass
    return ""


class Hotspot:
    def __init__(self, runner=run, writer=write_profile, resolver=reverse_name, user=None, config=None,
                 sleep=time.sleep, helper=INTERFACE_HELPER, log=None):
        self.run = runner
        self.write = writer
        self.resolve = resolver
        self.sleep = sleep
        self.helper = helper
        self.user = user or user_name()
        self.uuid = profile_uuid(self.user)
        self.config_file = Path(config) if config else config_path()
        self.log_file = Path(log) if log else (self.config_file.parent / "hotspot.log" if config else log_path())

    # --- the user's choices that are not in the profile -------------------------------

    def load_config(self):
        try:
            data = json.loads(self.config_file.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_config(self, data):
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self.config_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(data, handle)
            os.chmod(self.config_file, 0o600)
        except OSError:
            pass

    def note(self, text):
        """Add to the start log (the newest LOG_LIMIT characters are kept)."""
        try:
            old = self.log_file.read_text(encoding="utf-8") if self.log_file.exists() else ""
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w", encoding="utf-8", newline="\n") as handle:
                handle.write((old + time.strftime("%Y-%m-%d %H:%M:%S ") + text.rstrip() + "\n")[-LOG_LIMIT:])
        except OSError:
            pass

    def card_facts(self, state):
        """What the card says about itself, for the start log."""
        card = state.get("parent") or state.get("device") or ""
        real = card and card != VIRTUAL
        info = self.phy_info(card) if real else ""
        lines = [f"card {card or '-'}, hotspot on {state.get('device') or '-'}, shared {state.get('shared')}, "
                 f"bands {state.get('bands')}, chosen {state.get('band')!r}",
                 f"link frequency {self.link_frequency(card) if real else 0} MHz"]
        combos = re.search(r"valid interface combinations:\n(.*?)(?=\n\t\S|\Z)", info, re.S)
        if combos:
            lines.append("combinations: " + " ".join(combos.group(1).split()))
        lines += ["  " + line.strip() for line in re.findall(r"^\s*(\* \d{4}(?:\.\d+)? MHz.*)$", info, re.M)]
        code, out = self.run([IW, "reg", "get"])
        if code == 0 and out.strip():
            lines += ["  " + line.rstrip() for line in out.strip().splitlines()[:12]]
        return "\n".join(lines)

    # --- what NetworkManager knows ------------------------------------------------

    def wifi_devices(self):
        code, out = self.run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"])
        result = []
        for device, kind, state, connection, *_ in terse_lines(code, out, 4):
            if kind != "wifi":
                continue
            code, props = self.run(["nmcli", "-t", "-f", "WIFI-PROPERTIES", "device", "show", device])
            caps = {}
            for line in props.splitlines() if code == 0 else []:
                key, _, value = line.partition(":")
                caps[key.rsplit(".", 1)[-1]] = value.strip() == "yes"
            result.append({"device": device, "state": state, "connection": connection,
                           "ap": caps.get("AP", False),
                           "5ghz": caps.get("5GHZ", False) and self.may_send_5ghz(device)})
        return result

    def phy_info(self, device):
        """`iw phy ... info` of a Wi-Fi device's card ("" without iw)."""
        code, out = self.run([IW, "dev", device, "info"])
        match = re.search(r"^\s*wiphy (\d+)", out, re.M) if code == 0 else None
        if not match:
            return ""
        code, out = self.run([IW, "phy", "phy" + match.group(1), "info"])
        return out if code == 0 else ""

    def may_send_5ghz(self, device):
        """Whether the card may start a network on 5 GHz where it is: the
        regulatory domain marks channels "no IR" (no initiating radiation)
        until a country is known, and an access point then fails to start
        (NetworkManager: supplicant-timeout; dev VM, 2026-10-26). Without iw
        NetworkManager's word is all there is."""
        out = self.phy_info(device)
        if not out:
            return True
        channels = re.findall(r"^\s*\* 5\d{3}(?:\.\d+)? MHz \[\d+\](.*)$", out, re.M)
        return any(not re.search(r"no IR|disabled|radar", flags) for flags in channels)

    def link_frequency(self, device):
        """The frequency (MHz) of the network the device is connected to; 0
        if unknown."""
        code, out = self.run([IW, "dev", device, "link"])
        match = re.search(r"^\s*freq: (\d+)", out, re.M) if code == 0 else None
        return int(match.group(1)) if match else 0

    def same_card(self, device):
        """How the hotspot can run beside the device's own connection:
        {"channels": N, "band": "bg"|"a", "channel": C, "allowed": bool} or
        None."""
        if not os.path.exists(self.helper):
            return None
        channels = shared_channels(self.phy_info(device))
        if not channels:
            return None
        frequency = self.link_frequency(device)
        band, channel = channel_of(frequency)
        if not channel:
            return None
        # Whether the hotspot may run on the connection's own channel.
        return {"channels": channels, "band": band, "channel": channel,
                "allowed": ap_allowed(self.phy_info(device), frequency)}

    def active_connections(self):
        code, out = self.run(["nmcli", "-t", "-f", "NAME,UUID,TYPE,DEVICE", "connection", "show", "--active"])
        return [{"name": f[0], "uuid": f[1], "type": f[2], "device": f[3]} for f in terse_lines(code, out, 4)]

    def default_routes(self):
        """{device: lowest metric} of the IPv4 default routes."""
        code, out = self.run(["ip", "-4", "route", "show", "default"])
        routes = {}
        for line in out.splitlines() if code == 0 else []:
            device = re.search(r"\bdev (\S+)", line)
            metric = re.search(r"\bmetric (\d+)", line)
            if device:
                value = int(metric.group(1)) if metric else 0
                routes[device.group(1)] = min(value, routes.get(device.group(1), value))
        return routes

    def profile(self):
        """{"ssid", "password", "band", "device"} of the saved profile, or None."""
        code, out = self.run(["nmcli", "-s", "-t", "-g",
                              "802-11-wireless.ssid,802-11-wireless.band,802-11-wireless-security.psk,"
                              "connection.interface-name", "connection", "show", "uuid", self.uuid])
        if code != 0:
            return None
        lines = (out.split("\n") + ["", "", "", ""])[:4]
        ssid, band, password, device = (split_terse(line)[0] if line else "" for line in lines)
        return {"ssid": ssid, "band": band if band in BANDS else "", "password": password, "device": device}

    def clients(self, device, server):
        """Devices connected to the hotspot: [{"name", "ip", "mac"}]."""
        code, out = self.run(["ip", "neigh", "show", "dev", device])
        addresses, live = {}, set()
        for line in out.splitlines() if code == 0 else []:
            match = re.match(r"(\d+\.\d+\.\d+\.\d+) lladdr ([0-9a-f:]{17})\s*(\S*)", line.strip())
            if match:
                addresses[match.group(2)] = match.group(1)
                if match.group(3) in LIVE_NEIGHBOURS:
                    live.add(match.group(2))
        code, out = self.run([IW, "dev", device, "station", "dump"])
        if code == 0:
            stations = re.findall(r"^Station ([0-9a-f:]{17})", out, re.M)
        else:  # no iw: the neighbours that answer now
            stations = sorted(live)
        result = []
        for mac in stations:
            ip = addresses.get(mac, "")
            name = self.resolve(ip, server) if ip and server else ""
            result.append({"name": name, "ip": ip, "mac": mac.upper()})
        return result

    def hotspot_address(self, device):
        code, out = self.run(["ip", "-4", "-o", "addr", "show", "dev", device])
        match = re.search(r"\binet (\d+\.\d+\.\d+\.\d+)/", out) if code == 0 else None
        return match.group(1) if match else ""

    # --- the state Settings and Quick Settings show -------------------------------

    def status(self):
        devices = self.wifi_devices()
        active = self.active_connections()
        mine = next((c for c in active if c["uuid"] == self.uuid), None)
        routes = self.default_routes()
        config = self.load_config()
        saved = self.profile()
        if saved is None:
            # Windows' first values, kept until the profile is first written.
            if not valid_ssid(config.get("ssid", "")) or not valid_password(config.get("password", "")):
                config.update(ssid=default_ssid(), password=default_password(), band="")
                self.save_config(config)
            saved = {"ssid": config["ssid"], "password": config["password"],
                     "band": config.get("band", "") if config.get("band", "") in BANDS else "", "device": ""}

        # The band chosen in Edit; the profile may carry the band a start
        # fell back to.
        choice = config["band"] if config.get("band") in BANDS else saved["band"]

        hotspot_device = mine["device"] if mine else ""
        sources = []
        for connection in active:
            if connection["uuid"] == self.uuid or connection["device"] not in routes:
                continue
            sources.append({"uuid": connection["uuid"], "name": connection["name"],
                            "kind": SOURCE_TYPES.get(connection["type"], "ethernet"),
                            "device": connection["device"], "metric": routes[connection["device"]]})
        sources.sort(key=lambda s: (s["metric"], s["name"].lower()))

        # A card that hosts the hotspot on its own interface leaves its Wi-Fi
        # network, so another card or connection is preferred; a card that
        # can do both at once shares its own connection (same_card).
        capable = [d for d in devices if d["ap"] and d["device"] != VIRTUAL]
        parent, shared = "", None
        if hotspot_device:
            device = next((d for d in devices if d["device"] == hotspot_device), None)
            if hotspot_device == VIRTUAL:
                parent = config.get("parent", "")
                shared = self.same_card(parent) if parent else None
        else:
            free = [d for d in capable if any(s["device"] != d["device"] for s in sources)]
            device = (next((d for d in free if d["device"] == saved["device"]), None)
                      or next((d for d in free if d["state"] != "connected"), None)
                      or (free[0] if free else None))
            if device is None and sources:
                for card in capable:
                    if card["state"] == "connected" and any(s["device"] == card["device"] for s in sources):
                        shared = self.same_card(card["device"])
                        if shared:
                            parent = card["device"]
                            device = {"device": VIRTUAL, "state": "disconnected", "connection": "", "ap": True,
                                      "5ghz": card["5ghz"]}
                            break
        if device and device["device"] != VIRTUAL:
            sources = [s for s in sources if s["device"] != device["device"]]
        if not devices:
            reason = "no-wifi"
        elif not capable:
            reason = "no-ap"
        elif device is None:
            # Every card that could host it carries the only internet.
            reason = "same-adapter" if sources else "no-internet"
        elif not sources:
            reason = "no-internet"
        elif shared and shared["channels"] < 2 and not shared["allowed"] and mine is None:
            # One channel for both, and the card may not start a network on
            # its connection's (a DFS or restricted 5 GHz channel).
            reason = "channel"
        else:
            reason = ""

        bands = ["", "bg"] + (["a"] if device and device["5ghz"] else [])
        if shared and shared["channels"] < 2:
            # One channel for both: the hotspot is on the connection's band.
            bands = ["", shared["band"]]
        chosen = config.get("source", "")
        current = sources[0]["uuid"] if sources else ""
        state = {
            "available": bool(capable), "reason": reason, "active": mine is not None,
            "device": device["device"] if device else "",
            # The card whose own connection the hotspot shares beside it.
            "parent": parent, "shared": shared,
            # A 5 GHz choice the card cannot use here starts on any band.
            "ssid": saved["ssid"], "password": saved["password"],
            "band": choice if choice in bands else "",
            "bands": bands,
            # The band it runs on when the chosen one could not be used.
            "fallback": config.get("fallback", "") if mine else "",
            "security": "WPA2-Personal",
            # The Wi-Fi network the card leaves when the hotspot starts.
            "disconnects": device["connection"] if device and not mine and device["state"] == "connected" else "",
            "sources": sources,
            "source": chosen if any(s["uuid"] == chosen for s in sources) else current,
            "clients": [], "error": "",
        }
        if mine:
            state["clients"] = self.clients(hotspot_device, self.hotspot_address(hotspot_device))
        return state

    # --- changes --------------------------------------------------------------------

    def plans(self, state, band):
        """The (band, channel) pairs to try, best first (channel 0:
        NetworkManager picks one)."""
        band = band if band in state.get("bands", BANDS) else ""
        shared = state.get("shared")
        if shared and shared["channels"] < 2:
            # The card serves both on one channel: its connection's.
            return [(shared["band"], shared["channel"])]
        plans = []
        if shared and shared["allowed"] and band in ("", shared["band"]):
            # The connection's channel: no time-sharing between two.
            plans.append((shared["band"], shared["channel"]))
        if band == "a":
            plans.append(("a", 0))
        if shared or band:
            # 2.4 GHz after 5 GHz could not start (and beside a connection,
            # where 5 GHz hotspots are often not allowed).
            plans.append(("bg", 0))
        else:
            plans.append(("", 0))
        return list(dict.fromkeys(plans))

    def _write(self, state, ssid, password, band):
        plan_band, channel = self.plans(state, band)[0]
        return self.write(profile_settings(self.user, ssid, password, plan_band, state["device"], channel))

    def _bring_up(self, state, ssid, password, band):
        """Start the hotspot with the first plan that works ("" or the
        error); the band it fell back to is kept for Settings."""
        config = self.load_config()
        if config.pop("fallback", None) is not None:
            self.save_config(config)
        facts = ""
        for plan_band, channel in self.plans(state, band):
            if not self.write(profile_settings(self.user, ssid, password, plan_band, state["device"], channel)):
                return "save-failed"
            code, out = self.run(["nmcli", "--wait", "60", "connection", "up", "uuid", self.uuid,
                                  "ifname", state["device"]], timeout=75, merge=True)
            if code == 0:
                if band and plan_band != band:
                    config = self.load_config()
                    config["fallback"] = plan_band or "bg"
                    self.save_config(config)
                return ""
            facts = facts or self.card_facts(state)
            self.note(f"start on band {plan_band or 'any'} channel {channel or 'any'} failed ({code}): "
                      f"{' '.join(out.split())[:400]}\n{facts}")
        return "start-failed"

    def start(self):
        state = self.status()
        if state["active"]:
            return state
        if state["reason"]:
            return dict(state, error=state["reason"])
        self.run(["nmcli", "radio", "wifi", "on"])
        if state.get("parent") and not self.add_interface(state["parent"]):
            self.note(f"the hotspot interface could not be added on {state['parent']}\n{self.card_facts(state)}")
            return dict(state, error="start-failed")
        error = self._bring_up(state, state["ssid"], state["password"], state["band"])
        if error:
            self.remove_interface()
            return dict(self.status(), error=error)
        self.prefer_source(self.load_config().get("source", ""))
        return self.status()

    def stop(self):
        self.run(["nmcli", "connection", "down", "uuid", self.uuid], timeout=30)
        self.restore_source()
        self.remove_interface()
        config = self.load_config()
        if config.pop("fallback", None) is not None:
            self.save_config(config)
        return self.status()

    def add_interface(self, parent):
        """The hotspot's interface on the parent's card, once NetworkManager
        knows it (it would otherwise join a known network on it first)."""
        if self.run(["pkexec", self.helper, "add", parent], timeout=60)[0] != 0:
            return False
        for _ in range(20):
            code, out = self.run(["nmcli", "-t", "-f", "DEVICE", "device", "status"])
            if code == 0 and VIRTUAL in out.split():
                self.run(["nmcli", "device", "set", VIRTUAL, "autoconnect", "no"])
                config = self.load_config()
                config["parent"] = parent
                self.save_config(config)
                return True
            self.sleep(0.5)
        self.remove_interface()
        return False

    def remove_interface(self):
        config = self.load_config()
        if not config.pop("parent", "") and self.run(["ip", "-o", "link", "show", "dev", VIRTUAL])[0] != 0:
            return
        self.run(["pkexec", self.helper, "remove"], timeout=60)
        self.save_config(config)

    def configure(self, ssid, password, band):
        """Save the network name, key and band; a running hotspot starts
        again with them (Windows restarts it too)."""
        if not valid_ssid(ssid):
            return dict(self.status(), error="invalid-name")
        if not valid_password(password):
            return dict(self.status(), error="invalid-password")
        band = band if band in BANDS else ""
        state = self.status()
        config = self.load_config()
        # The choice is kept apart from the profile, which may carry the
        # band a start fell back to.
        config["band"] = band
        if self.profile() is None:
            config.update(ssid=ssid, password=password)
            self.save_config(config)
            if not state["device"]:
                return self.status()
        self.save_config(config)
        if state["active"]:
            error = self._bring_up(state, ssid, password, band)
            if error:
                return dict(self.status(), error=error)
        elif not self._write(state, ssid, password, band):
            return dict(state, error="save-failed")
        return self.status()

    def set_source(self, source_uuid):
        config = self.load_config()
        config["source"] = source_uuid
        self.save_config(config)
        state = self.status()
        if state["active"]:
            self.restore_source()
            self.prefer_source(source_uuid)
            state = self.status()
        return state

    def prefer_source(self, source_uuid):
        """Make the chosen connection the default route while the hotspot
        runs (runtime only: NetworkManager's `device modify`)."""
        routes = self.default_routes()
        active = {c["uuid"]: c for c in self.active_connections()}
        chosen = active.get(source_uuid)
        if not chosen or chosen["device"] not in routes:
            return False
        others = [m for d, m in routes.items() if d != chosen["device"]]
        if not others or routes[chosen["device"]] < min(others):
            return True
        metric = max(0, min(others) - 1)
        if self.run(["nmcli", "device", "modify", chosen["device"], "ipv4.route-metric", str(metric)])[0] != 0:
            return False
        config = self.load_config()
        config["modified"] = chosen["device"]
        self.save_config(config)
        return True

    def restore_source(self):
        config = self.load_config()
        device = config.pop("modified", "")
        if device:
            self.run(["nmcli", "device", "reapply", device])
            self.save_config(config)


def main(args=None, hotspot=None, stdin=None):
    args = sys.argv[1:] if args is None else args
    hotspot = hotspot or Hotspot()
    command = args[0] if args else "status"
    if command == "status":
        result = hotspot.status()
    elif command == "start":
        result = hotspot.start()
    elif command == "stop":
        result = hotspot.stop()
    elif command == "source" and len(args) == 2:
        result = hotspot.set_source(args[1])
    elif command == "configure":
        try:
            data = json.loads((stdin or sys.stdin).read() or "{}")
        except ValueError:
            data = {}
        result = hotspot.configure(str(data.get("ssid", "")), str(data.get("password", "")),
                                   str(data.get("band", "")))
    else:
        print("usage: hotspot status|start|stop|configure|source UUID", file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
