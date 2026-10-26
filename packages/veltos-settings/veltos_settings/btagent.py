"""The VeltOS Bluetooth agent: BlueZ's questions while pairing, asked in
Windows 11's "Add a device" window (btpair.py).

BlueZ asks the default agent of the system (org.bluez.Agent1) to confirm a
PIN, show one to type on a keyboard, take a PIN, or allow a device. Plasma's
agent (kded's bluedevil) asked in notifications with KDE's wording; this
agent registers as the default one when the session starts (and again when
bluetoothd restarts) and opens `veltos-settings --bt-pair` for each
question, answering BlueZ with what the user chose (product owner,
2026-10-27). Only GLib: a few megabytes while idle; the window is a
program of its own that runs only while it asks.
"""

import os
import sys

AGENT_PATH = "/org/veltos/bluetooth/agent"
CAPABILITY = "KeyboardDisplay"
INTERFACE = """<node>
  <interface name="org.bluez.Agent1">
    <method name="Release"/>
    <method name="RequestPinCode"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
    <method name="DisplayPinCode"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
    <method name="RequestPasskey"><arg type="o" direction="in"/><arg type="u" direction="out"/></method>
    <method name="DisplayPasskey">
      <arg type="o" direction="in"/><arg type="u" direction="in"/><arg type="q" direction="in"/>
    </method>
    <method name="RequestConfirmation"><arg type="o" direction="in"/><arg type="u" direction="in"/></method>
    <method name="RequestAuthorization"><arg type="o" direction="in"/></method>
    <method name="AuthorizeService"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
    <method name="Cancel"/>
  </interface>
</node>"""
REJECTED = "org.bluez.Error.Rejected"
CANCELED = "org.bluez.Error.Canceled"


def question(method, args):
    """The --bt-pair kind and value for an Agent1 call; None when BlueZ
    expects no question (Release, Cancel)."""
    if method == "RequestConfirmation":
        return "confirm", f"{int(args[1]):06d}"
    if method == "DisplayPasskey":
        return "display", f"{int(args[1]):06d}"
    if method == "DisplayPinCode":
        return "display", str(args[1])
    if method == "RequestPinCode":
        return "pin", ""
    if method == "RequestPasskey":
        return "passkey", ""
    if method == "RequestAuthorization":
        return "authorize", ""
    if method == "AuthorizeService":
        return "service", ""
    return None


def reply_value(method, typed):
    """BlueZ's reply for a "yes": the typed PIN (s), a passkey (u) or nothing."""
    if method == "RequestPinCode":
        return ("(s)", (typed,))
    if method == "RequestPasskey":
        return ("(u)", (int(typed),))
    return (None, None)


def main():
    from gi.repository import Gio, GLib

    node = Gio.DBusNodeInfo.new_for_xml(INTERFACE)
    state = {"bus": None, "registration": None, "asking": None}
    loop = GLib.MainLoop()

    def device_property(path, name):
        try:
            value = state["bus"].call_sync("org.bluez", path, "org.freedesktop.DBus.Properties", "Get",
                                           GLib.Variant("(ss)", ("org.bluez.Device1", name)),
                                           GLib.VariantType("(v)"), Gio.DBusCallFlags.NONE, 2000, None)
            return value.unpack()[0]
        except GLib.Error:
            return None

    def close_window():
        asking = state["asking"]
        state["asking"] = None
        if asking is not None:
            asking["process"].force_exit()
            if asking["invocation"] is not None:
                asking["invocation"].return_dbus_error(CANCELED, "Canceled")

    def ask(method, args, invocation):
        kind, value = question(method, args)
        name = device_property(args[0], "Alias") or device_property(args[0], "Name") or ""
        close_window()
        try:
            process = Gio.Subprocess.new(["veltos-settings", "--bt-pair", kind, name, value],
                                         Gio.SubprocessFlags.STDOUT_PIPE)
        except GLib.Error as error:
            if invocation is not None:
                invocation.return_dbus_error(REJECTED, error.message)
            return
        asking = {"process": process, "invocation": invocation}
        state["asking"] = asking

        def done(proc, result):
            if state["asking"] is not asking:
                return                        # cancelled or replaced
            state["asking"] = None
            if invocation is None:
                return                        # Display*: nothing to answer
            try:
                _, out, _ = proc.communicate_utf8_finish(result)
            except GLib.Error:
                out = ""
            if proc.get_if_exited() and proc.get_exit_status() == 0:
                signature, values = reply_value(method, (out or "").strip())
                invocation.return_value(GLib.Variant(signature, values) if signature else None)
            else:
                invocation.return_dbus_error(REJECTED, "Rejected")
        process.communicate_utf8_async(None, None, done)

    def on_call(connection, sender, path, interface, method, parameters, invocation):
        args = parameters.unpack()
        if method == "Release":
            invocation.return_value(None)
        elif method == "Cancel":
            close_window()
            invocation.return_value(None)
        elif method in ("DisplayPinCode", "DisplayPasskey"):
            invocation.return_value(None)    # shown until BlueZ cancels or the user does
            if state["asking"] is None or method != "DisplayPasskey" or args[2] == 0:
                ask(method, args, None)
        elif method == "AuthorizeService" and (device_property(args[0], "Trusted")
                                               or device_property(args[0], "Paired")):
            # A device paired with this PC (also one being set up right now,
            # before VeltOS marks it trusted): no question, as on Windows.
            invocation.return_value(None)
        else:
            ask(method, args, invocation)

    def register():
        try:
            manager = Gio.DBusProxy.new_sync(state["bus"], Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES, None,
                                             "org.bluez", "/org/bluez", "org.bluez.AgentManager1", None)
            manager.call_sync("RegisterAgent", GLib.Variant("(os)", (AGENT_PATH, CAPABILITY)),
                              Gio.DBusCallFlags.NONE, 5000, None)
        except GLib.Error as error:
            if "AlreadyExists" not in str(error):
                print(f"veltos-bt-agent: {error.message}", file=sys.stderr)
                return False
        try:
            manager.call_sync("RequestDefaultAgent", GLib.Variant("(o)", (AGENT_PATH,)),
                              Gio.DBusCallFlags.NONE, 5000, None)
        except GLib.Error as error:
            print(f"veltos-bt-agent: {error.message}", file=sys.stderr)
        return False

    def bluez_appeared(connection, name, owner):
        # Plasma's agent asks to be the default one when kded starts; asking
        # again a little later keeps VeltOS' window in front.
        register()
        GLib.timeout_add_seconds(10, register)
        GLib.timeout_add_seconds(30, register)

    state["bus"] = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    state["registration"] = state["bus"].register_object(AGENT_PATH, node.interfaces[0], on_call, None, None)
    Gio.bus_watch_name_on_connection(state["bus"], "org.bluez", Gio.BusNameWatcherFlags.NONE,
                                     bluez_appeared, None)
    loop.run()
    return 0


if __name__ == "__main__":
    sys.exit(main() if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY") else 0)
