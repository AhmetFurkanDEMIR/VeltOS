"""The VeltOS network agent: NetworkManager's questions for a network's key,
asked in VeltOS' Windows 11 window (wifikey.py) instead of KDE's.

NetworkManager asks the session's secret agent (org.freedesktop.
NetworkManager.SecretAgent) for a key it does not have, and for a new one
after a wrong key. Plasma's agent (kded's networkmanagement module) asked in
KDE's "Wi-Fi password dialog" window and reported "No secrets were
provided" in a KDE notification (VM, 2026-10-31; product owner: no old
system windows). VeltOS turns that kded module off (veltos-desktop,
/etc/xdg/kded6rc) and this agent, started with the session, takes its
place: Wi-Fi keys (WPA/WPA2/WPA3 personal, WEP) and the user name and
password of WPA2/WPA3-Enterprise networks; other requests (VPN, mobile
broadband PINs) get "no secrets" so NetworkManager ends them at once.
Keys are not stored here: VeltOS' connections keep them in NetworkManager
(secret flags 0), so it asks only for new or wrong ones. Only GLib while
idle; the window is a program of its own that runs only while it asks.
"""

import os
import sys

AGENT_PATH = "/org/freedesktop/NetworkManager/SecretAgent"
AGENT_ID = "org.veltos.networkagent"
INTERFACE = """<node>
  <interface name="org.freedesktop.NetworkManager.SecretAgent">
    <method name="GetSecrets">
      <arg type="a{sa{sv}}" direction="in"/><arg type="o" direction="in"/><arg type="s" direction="in"/>
      <arg type="as" direction="in"/><arg type="u" direction="in"/>
      <arg type="a{sa{sv}}" direction="out"/>
    </method>
    <method name="CancelGetSecrets"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
    <method name="SaveSecrets"><arg type="a{sa{sv}}" direction="in"/><arg type="o" direction="in"/></method>
    <method name="DeleteSecrets"><arg type="a{sa{sv}}" direction="in"/><arg type="o" direction="in"/></method>
  </interface>
</node>"""
ERROR = "org.freedesktop.NetworkManager.SecretAgent."
ALLOW_INTERACTION = 0x1
REQUEST_NEW = 0x2
USER_REQUESTED = 0x4


def plain(value):
    """A GLib-unpacked value: byte arrays come as bytes or lists of ints."""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, list) and all(isinstance(v, int) for v in value):
        return bytes(value)
    return value


def network_name(connection):
    """The network's name: the SSID, else the connection's name."""
    ssid = plain(connection.get("802-11-wireless", {}).get("ssid", b""))
    if isinstance(ssid, bytes) and ssid:
        return ssid.decode("utf-8", errors="replace")
    return str(connection.get("connection", {}).get("id", "")) or "Wi-Fi"


def question(connection, setting, flags):
    """(kind, retry) for a request the window can ask: kind "psk", "wep" or
    "eap" (user name and password); None for anything else."""
    if not flags & ALLOW_INTERACTION:
        return None
    retry = bool(flags & REQUEST_NEW)
    if setting == "802-11-wireless-security":
        key_mgmt = str(connection.get(setting, {}).get("key-mgmt", ""))
        if key_mgmt in ("wpa-psk", "sae"):
            return "psk", retry
        if key_mgmt == "none":              # static WEP
            return "wep", retry
        return None                           # enterprise networks ask for "802-1x"
    if setting == "802-1x":
        eap = [str(e) for e in connection.get(setting, {}).get("eap", [])]
        if any(e in ("peap", "ttls", "pwd", "fast", "leap", "md5") for e in eap):
            return "eap", retry
    return None


def secrets(kind, answer):
    """The reply's settings for what the window printed."""
    if kind == "psk":
        return {"802-11-wireless-security": {"psk": ("s", answer)}}
    if kind == "wep":
        return {"802-11-wireless-security": {"wep-key0": ("s", answer)}}
    identity, _sep, password = answer.partition("\n")
    return {"802-1x": {"identity": ("s", identity), "password": ("s", password)}}


def main():
    from gi.repository import Gio, GLib

    node = Gio.DBusNodeInfo.new_for_xml(INTERFACE)
    state = {"bus": None, "asking": None}
    loop = GLib.MainLoop()

    def variant(settings):
        return GLib.Variant("(a{sa{sv}})", ({name: {key: GLib.Variant(sig, value)
                                                    for key, (sig, value) in values.items()}
                                             for name, values in settings.items()},))

    def close_window(path=None, setting=None):
        asking = state["asking"]
        if asking is None or (path is not None and (asking["path"], asking["setting"]) != (path, setting)):
            return
        state["asking"] = None
        asking["process"].force_exit()
        asking["invocation"].return_dbus_error(ERROR + "AgentCanceled", "Canceled")

    def ask(connection, path, setting, flags, invocation):
        found = question(connection, setting, flags)
        if found is None:
            invocation.return_dbus_error(ERROR + "NoSecrets", "No secrets")
            return
        kind, retry = found
        close_window()
        command = ["veltos-settings", "--wifi-key", kind, network_name(connection)]
        if retry:
            command.append("retry")
        try:
            process = Gio.Subprocess.new(command, Gio.SubprocessFlags.STDOUT_PIPE)
        except GLib.Error as error:
            invocation.return_dbus_error(ERROR + "InternalError", error.message)
            return
        asking = {"process": process, "invocation": invocation, "path": path, "setting": setting}
        state["asking"] = asking

        def done(proc, result):
            if state["asking"] is not asking:
                return                        # cancelled or replaced
            state["asking"] = None
            try:
                _, out, _ = proc.communicate_utf8_finish(result)
            except GLib.Error:
                out = ""
            if proc.get_if_exited() and proc.get_exit_status() == 0 and out:
                invocation.return_value(variant(secrets(kind, out.rstrip("\n"))))
            else:
                invocation.return_dbus_error(ERROR + "UserCanceled", "The user canceled")
        process.communicate_utf8_async(None, None, done)

    def on_call(connection, sender, path, interface, method, parameters, invocation):
        args = parameters.unpack()
        if method == "GetSecrets":
            ask(args[0], args[1], args[2], args[4], invocation)
        elif method == "CancelGetSecrets":
            close_window(args[0], args[1])
            invocation.return_value(None)
        else:                                 # SaveSecrets, DeleteSecrets: NetworkManager keeps them
            invocation.return_value(None)

    def register(*_args):
        try:
            state["bus"].call_sync("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/AgentManager",
                                   "org.freedesktop.NetworkManager.AgentManager", "RegisterWithCapabilities",
                                   GLib.Variant("(su)", (AGENT_ID, 0)), None, Gio.DBusCallFlags.NONE, 5000, None)
        except GLib.Error as error:
            print(f"veltos-network-agent: {error.message}", file=sys.stderr)
        return False

    state["bus"] = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    state["bus"].register_object(AGENT_PATH, node.interfaces[0], on_call, None, None)
    # Registered again whenever NetworkManager (re)starts.
    Gio.bus_watch_name_on_connection(state["bus"], "org.freedesktop.NetworkManager",
                                     Gio.BusNameWatcherFlags.NONE, register, None)
    loop.run()
    return 0


if __name__ == "__main__":
    sys.exit(main() if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY") else 0)
