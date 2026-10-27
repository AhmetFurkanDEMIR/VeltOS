"""VeltOS file chooser portal backend: the file dialogs of every program.

Programs that ask the desktop portal for a file dialog (GTK programs such
as Firefox and Mail with GTK_USE_PORTAL=1, Qt and KDE programs through
Qt's portal platform theme, LibreOffice) reach xdg-desktop-portal, which
hands the request to the backend named for the FileChooser interface in
/etc/xdg/xdg-desktop-portal/kde-portals.conf: this one. Each request opens
`veltos-explorer --pick` (the Windows 11 style dialog, picker.py) and
answers with the files chosen.

It is also the AppChooser backend: when a program asks the portal to open
a file and the portal wants the user to choose the app ("Open with"), the
request opens `veltos-explorer --open-with --choose` (Windows 11's "Select
an app to open this file", openwith.py) and answers with the app chosen;
the portal then opens the file with it.

    veltos-explorer --portal      (D-Bus activation of
                                   org.freedesktop.impl.portal.desktop.veltos)

Only the GLib main loop and GDBus are used here (python3-gi), no Qt: the
dialog runs in its own process. The service ends after a while without
requests; D-Bus starts it again for the next one.
"""

import json
import os
import subprocess
import sys
import time

BUS_NAME = "org.freedesktop.impl.portal.desktop.veltos"
OBJECT_PATH = "/org/freedesktop/portal/desktop"
IFACE = "org.freedesktop.impl.portal.FileChooser"
APP_IFACE = "org.freedesktop.impl.portal.AppChooser"
REQUEST_IFACE = "org.freedesktop.impl.portal.Request"
VERSION = 4
# Portal response codes.
SUCCESS, CANCELLED, OTHER = 0, 1, 2
IDLE_SECONDS = 300

NODE_XML = f"""
<node>
  <interface name="{IFACE}">
    <property name="version" type="u" access="read"/>
    <method name="OpenFile">
      <arg type="o" name="handle" direction="in"/>
      <arg type="s" name="app_id" direction="in"/>
      <arg type="s" name="parent_window" direction="in"/>
      <arg type="s" name="title" direction="in"/>
      <arg type="a{{sv}}" name="options" direction="in"/>
      <arg type="u" name="response" direction="out"/>
      <arg type="a{{sv}}" name="results" direction="out"/>
    </method>
    <method name="SaveFile">
      <arg type="o" name="handle" direction="in"/>
      <arg type="s" name="app_id" direction="in"/>
      <arg type="s" name="parent_window" direction="in"/>
      <arg type="s" name="title" direction="in"/>
      <arg type="a{{sv}}" name="options" direction="in"/>
      <arg type="u" name="response" direction="out"/>
      <arg type="a{{sv}}" name="results" direction="out"/>
    </method>
    <method name="SaveFiles">
      <arg type="o" name="handle" direction="in"/>
      <arg type="s" name="app_id" direction="in"/>
      <arg type="s" name="parent_window" direction="in"/>
      <arg type="s" name="title" direction="in"/>
      <arg type="a{{sv}}" name="options" direction="in"/>
      <arg type="u" name="response" direction="out"/>
      <arg type="a{{sv}}" name="results" direction="out"/>
    </method>
  </interface>
  <interface name="{APP_IFACE}">
    <property name="version" type="u" access="read"/>
    <method name="ChooseApplication">
      <arg type="o" name="handle" direction="in"/>
      <arg type="s" name="app_id" direction="in"/>
      <arg type="s" name="parent_window" direction="in"/>
      <arg type="as" name="choices" direction="in"/>
      <arg type="a{{sv}}" name="options" direction="in"/>
      <arg type="u" name="response" direction="out"/>
      <arg type="a{{sv}}" name="results" direction="out"/>
    </method>
    <method name="UpdateChoices">
      <arg type="o" name="handle" direction="in"/>
      <arg type="as" name="choices" direction="in"/>
    </method>
  </interface>
</node>
"""
APP_VERSION = 2
REQUEST_XML = f"""
<node>
  <interface name="{REQUEST_IFACE}">
    <method name="Close"/>
  </interface>
</node>
"""


def bytes_path(value):
    """A path the portal sends as a NUL-terminated byte array."""
    if isinstance(value, (bytes, bytearray)):
        data = bytes(value)
    elif isinstance(value, (list, tuple)):
        data = bytes(v for v in value)
    else:
        data = str(value or "").encode("utf-8")
    return data.rstrip(b"\0").decode("utf-8", "replace")


def portal_filter(entry):
    """A portal filter (name, [(0, "*.png") | (1, "image/jpeg")]) as the
    dialog's {"name", "patterns", "mimes"}."""
    name, rules = entry
    patterns = [str(value) for kind, value in rules if kind == 0]
    mimes = [str(value) for kind, value in rules if kind == 1]
    return {"name": str(name), "patterns": patterns, "mimes": mimes}


def to_request(method, title, options):
    """The dialog request (picker.py) for a portal method and its options
    (already plain Python values)."""
    request = {"title": str(title or "")}
    filters = [portal_filter(f) for f in options.get("filters", []) if isinstance(f, (list, tuple)) and len(f) == 2]
    request["filters"] = filters
    current = options.get("current_filter")
    if current is not None:
        wanted = portal_filter(current)
        request["current_filter"] = next((i for i, f in enumerate(filters) if f == wanted), 0)
        if wanted not in filters:
            filters.insert(0, wanted)
            request["current_filter"] = 0
    label = str(options.get("accept_label") or "")
    if label:
        request["accept_label"] = label
    if "current_folder" in options:
        request["current_folder"] = bytes_path(options["current_folder"])
    if method == "OpenFile":
        request["mode"] = "folder" if options.get("directory") else "open"
        request["multiple"] = bool(options.get("multiple"))
    elif method == "SaveFile":
        request["mode"] = "save"
        request["current_name"] = str(options.get("current_name") or "")
        if "current_file" in options:
            request["current_file"] = bytes_path(options["current_file"])
    else:                                       # SaveFiles: a folder for the given names
        request["mode"] = "folder"
        request["files"] = [bytes_path(f) for f in options.get("files", [])]
    return request


def to_uri(path):
    from urllib.parse import quote
    return "file://" + quote(path, safe="/:@+,=~!$&'()*;")


def to_results(method, request, answer):
    """(response code, {results}) for the dialog's answer ({"paths", "filter"})."""
    paths = [p for p in (answer or {}).get("paths", []) if isinstance(p, str)]
    if not paths:
        return CANCELLED, {}
    if method == "SaveFiles":
        folder = paths[0]
        uris = [to_uri(os.path.join(folder, os.path.basename(name))) for name in request.get("files", [])]
    else:
        uris = [to_uri(p) for p in paths]
    results = {"uris": uris}
    filters = request.get("filters") or []
    index = (answer or {}).get("filter")
    if isinstance(index, int) and 0 <= index < len(filters):
        chosen = filters[index]
        results["current_filter"] = (chosen["name"], [(0, p) for p in chosen["patterns"]]
                                     + [(1, m) for m in chosen["mimes"]])
    return SUCCESS, results


def picker_command():
    return [sys.executable, "-m", "veltos_explorer", "--pick"]


def chooser_command(choices, options):
    """The "open with" window for an AppChooser request: the portal's
    candidates (app ids without ".desktop") and the file's type and name."""
    command = [sys.executable, "-m", "veltos_explorer", "--open-with", "--choose"]
    content_type = str(options.get("content_type") or "")
    if content_type:
        command += ["--type", content_type]
    if choices:
        command += ["--choices", ",".join(str(c) for c in choices)]
    name = str(options.get("uri") or options.get("filename") or "")
    if name:
        command.append(name)
    return command


def chooser_results(output):
    """(response, {"choice": app id}) for the window's answer (a desktop
    file name, or an empty line when cancelled)."""
    lines = [line.strip() for line in (output or "").splitlines() if line.strip()]
    if not lines:
        return CANCELLED, {}
    return SUCCESS, {"choice": lines[-1].removesuffix(".desktop")}


LANGUAGE_VARIABLES = ("LANGUAGE", "LANG", "LC_ALL", "LC_MESSAGES")


def session_environment(runner=subprocess.run, environ=None):
    """The environment for a dialog: this service's, with the language of
    the session as it is now. D-Bus may have started the service before
    Plasma passed the session's language on, and the dialog then spoke
    English in a Turkish session ("File name", "Save as type"; product
    owner, 2026-10-22). systemd's user manager has the session's values
    (Plasma updates it at sign-in)."""
    env = dict(os.environ if environ is None else environ)
    try:
        out = runner(["systemctl", "--user", "show-environment"], capture_output=True, text=True,
                     timeout=3).stdout
    except Exception:  # no systemd, no session: the service's own environment
        return env
    for line in out.splitlines():
        name, _, value = line.partition("=")
        if name in LANGUAGE_VARIABLES and value:
            env[name] = value
    return env


# A second, identical request from the same window within this time joins
# the first dialog instead of opening another (LibreOffice's Qt file
# picker asks twice for one Ctrl+O: two dialogs appeared, VM 2026-10-21).
DUPLICATE_SECONDS = 3.0


def request_key(method, parent_window, title, request):
    return (method, parent_window, title, json.dumps(request, sort_keys=True))


class Dialog:
    """One dialog process and the portal requests it answers."""

    def __init__(self, key, process, method, request):
        self.key = key
        self.process = process
        self.method = method
        self.request = request
        self.started = time.monotonic()
        self.invocations = []         # (handle, invocation, registration id)


class Service:
    """The D-Bus object; one dialog process per request (or per burst of
    identical requests)."""

    def __init__(self, loop, connection, gio, glib):
        self.loop = loop
        self.connection = connection
        self.Gio, self.GLib = gio, glib
        self.dialogs = {}             # handle -> Dialog
        self.last_activity = time.monotonic()
        node = gio.DBusNodeInfo.new_for_xml(NODE_XML)
        self.request_node = gio.DBusNodeInfo.new_for_xml(REQUEST_XML)
        for interface in node.interfaces:
            connection.register_object(OBJECT_PATH, interface, self.handle_call, self.get_property, None)
        self.choosers = {}            # handle -> (process, invocation, registration)

    def get_property(self, _connection, _sender, _path, iface, name):
        if name == "version":
            return self.GLib.Variant("u", APP_VERSION if iface == APP_IFACE else VERSION)
        return None

    def handle_call(self, connection, sender, path, iface, method, parameters, invocation):
        if iface == APP_IFACE:
            return self.handle_app_call(method, parameters, invocation)
        self.last_activity = time.monotonic()
        handle, _app_id, parent_window, title, options = parameters.unpack()
        request = to_request(method, title, options)
        key = request_key(method, parent_window, title, request)
        dialog = next((d for d in self.dialogs.values()
                       if d.key == key and time.monotonic() - d.started < DUPLICATE_SECONDS), None)
        if dialog is None:
            try:
                process = subprocess.Popen(picker_command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.DEVNULL, text=True, env=session_environment())
            except OSError:
                invocation.return_value(self.GLib.Variant("(ua{sv})", (OTHER, {})))
                return
            dialog = Dialog(key, process, method, request)
            process.stdin.write(json.dumps(request))
            process.stdin.close()
            self.GLib.child_watch_add(self.GLib.PRIORITY_DEFAULT, process.pid,
                                      lambda _pid, _status, d=dialog: self.finished(d))
        registration = self.connection.register_object(
            handle, self.request_node.interfaces[0],
            lambda *args: self.close_request(handle, *args), None, None)
        dialog.invocations.append((handle, invocation, registration))
        self.dialogs[handle] = dialog

    def finished(self, dialog):
        """The dialog ended: every request that joined it gets the answer."""
        try:
            answer = json.loads(dialog.process.stdout.read() or "{}")
        except ValueError:
            answer = {}
        dialog.process.wait()
        code, results = to_results(dialog.method, dialog.request, answer)
        variant_results = {}
        if "uris" in results:
            variant_results["uris"] = self.GLib.Variant("as", results["uris"])
        if "current_filter" in results:
            variant_results["current_filter"] = self.GLib.Variant("(sa(us))", results["current_filter"])
        for handle, invocation, registration in dialog.invocations:
            invocation.return_value(self.GLib.Variant("(ua{sv})", (code, variant_results)))
            if registration:
                self.connection.unregister_object(registration)
            self.dialogs.pop(handle, None)
        dialog.invocations = []
        self.last_activity = time.monotonic()

    def close_request(self, handle, _connection, _sender, _path, _iface, _method, _parameters, invocation):
        """The program withdrew its request: the dialog goes away once no
        request of that window is waiting for it any more."""
        dialog = self.dialogs.pop(handle, None)
        if dialog is not None:
            kept = []
            for item in dialog.invocations:
                if item[0] == handle:
                    item[1].return_value(self.GLib.Variant("(ua{sv})", (CANCELLED, {})))
                    if item[2]:
                        self.connection.unregister_object(item[2])
                else:
                    kept.append(item)
            dialog.invocations = kept
            if not kept and dialog.process.poll() is None:
                dialog.process.terminate()
        invocation.return_value(None)

    # --- AppChooser ----------------------------------------------------------------------

    def handle_app_call(self, method, parameters, invocation):
        self.last_activity = time.monotonic()
        if method == "UpdateChoices":
            # The window lists every app for the type anyway.
            invocation.return_value(None)
            return
        handle, _app_id, _parent_window, choices, options = parameters.unpack()
        try:
            process = subprocess.Popen(chooser_command(choices, options), stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                       env=session_environment())
        except OSError:
            invocation.return_value(self.GLib.Variant("(ua{sv})", (OTHER, {})))
            return
        registration = self.connection.register_object(
            handle, self.request_node.interfaces[0],
            lambda *args: self.close_chooser(handle, *args), None, None)
        self.choosers[handle] = (process, invocation, registration)
        self.GLib.child_watch_add(self.GLib.PRIORITY_DEFAULT, process.pid,
                                  lambda _pid, _status: self.chooser_finished(handle))

    def chooser_finished(self, handle):
        item = self.choosers.pop(handle, None)
        if item is None:
            return
        process, invocation, registration = item
        output = process.stdout.read()
        process.wait()
        code, results = chooser_results(output)
        variants = {key: self.GLib.Variant("s", value) for key, value in results.items()}
        invocation.return_value(self.GLib.Variant("(ua{sv})", (code, variants)))
        if registration:
            self.connection.unregister_object(registration)
        self.last_activity = time.monotonic()

    def close_chooser(self, handle, _connection, _sender, _path, _iface, _method, _parameters, invocation):
        item = self.choosers.pop(handle, None)
        if item is not None:
            process, request, registration = item
            request.return_value(self.GLib.Variant("(ua{sv})", (CANCELLED, {})))
            if registration:
                self.connection.unregister_object(registration)
            if process.poll() is None:
                process.terminate()
        invocation.return_value(None)

    def idle_check(self):
        if not self.dialogs and not self.choosers and time.monotonic() - self.last_activity > IDLE_SECONDS:
            self.loop.quit()
            return False
        return True


def serve(_argv=None):
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    loop = GLib.MainLoop()
    service = {}

    def on_bus(connection, _name):
        service["object"] = Service(loop, connection, Gio, GLib)
        GLib.timeout_add_seconds(60, lambda: service["object"].idle_check())

    def on_lost(_connection, _name):
        loop.quit()

    Gio.bus_own_name(Gio.BusType.SESSION, BUS_NAME, Gio.BusNameOwnerFlags.NONE, on_bus, None, on_lost)
    loop.run()
    return 0
