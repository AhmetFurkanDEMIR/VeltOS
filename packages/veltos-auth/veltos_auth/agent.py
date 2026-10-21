"""VeltOS authentication agent: answers polkit's requests for the
administrator password with the Windows 11 style prompt (dialog.py)
instead of KDE's window.

    veltos-auth-agent          (started with the Plasma session)

polkit (the system's permission service) asks the session's registered
agent whenever a program needs an administrator's say-so: installing
apps, adding users, changing the time zone. The agent is a D-Bus object
on the system bus; polkit calls BeginAuthentication with a cookie and
the accounts that may answer. The agent opens the prompt in its own
process, which checks the password through polkit's setuid helper
(polkit-agent-helper-1) and tells polkit the result; the agent then
answers the call. Only GLib and GDBus are used here (python3-gi); the
window is Qt (PySide6) in the other process.
"""

import json
import os
import signal
import subprocess
import sys

from . import users

AUTHORITY = "org.freedesktop.PolicyKit1"
AUTHORITY_PATH = "/org/freedesktop/PolicyKit1/Authority"
AUTHORITY_IFACE = "org.freedesktop.PolicyKit1.Authority"
AGENT_PATH = "/org/veltos/PolicyKit1/AuthenticationAgent"
AGENT_IFACE = "org.freedesktop.PolicyKit1.AuthenticationAgent"
ERROR_CANCELLED = "org.freedesktop.PolicyKit1.Error.Cancelled"
ERROR_FAILED = "org.freedesktop.PolicyKit1.Error.Failed"
# KDE's agent, which VeltOS replaces: its unit is masked by the package;
# an old session may still run it.
KDE_AGENT = "polkit-kde-authentication-agent-1"

AGENT_XML = f"""
<node>
  <interface name="{AGENT_IFACE}">
    <method name="BeginAuthentication">
      <arg type="s" name="action_id" direction="in"/>
      <arg type="s" name="message" direction="in"/>
      <arg type="s" name="icon_name" direction="in"/>
      <arg type="a{{ss}}" name="details" direction="in"/>
      <arg type="s" name="cookie" direction="in"/>
      <arg type="a(sa{{sv}})" name="identities" direction="in"/>
    </method>
    <method name="CancelAuthentication">
      <arg type="s" name="cookie" direction="in"/>
    </method>
  </interface>
</node>
"""


def process_start_time(pid="self"):
    """The start time polkit expects for a unix-process subject (field 22
    of /proc/PID/stat, clock ticks since boot)."""
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8", errors="replace") as fh:
            stat = fh.read()
    except OSError:
        return 0
    fields = stat.rsplit(")", 1)[1].split()
    try:
        return int(fields[19])
    except (IndexError, ValueError):
        return 0


def subject(environ=None, glib=None):
    """The session this agent answers for: the login session named by
    XDG_SESSION_ID, else this process (polkit finds its session)."""
    environ = os.environ if environ is None else environ
    session = environ.get("XDG_SESSION_ID", "")
    if session:
        return ("unix-session", {"session-id": glib.Variant("s", session)})
    return ("unix-process", {"pid": glib.Variant("u", os.getpid()),
                             "start-time": glib.Variant("t", process_start_time())})


def prompt_request(action_id, message, icon_name, details, cookie, identities, lang="en"):
    """What the prompt is told (JSON on its standard input)."""
    return {
        "cookie": cookie,
        "action": action_id,
        "message": message,
        "icon": icon_name,
        "details": dict(details),
        "program": users.program_name(dict(details)),
        "description": users.action_description(action_id, lang=lang),
        "users": users.users_for(identities),
    }


def dialog_command():
    return [sys.executable, "-m", "veltos_auth.dialog"]


class Agent:
    """The D-Bus object polkit talks to; one prompt process per cookie."""

    def __init__(self, loop, connection, gio, glib, lang="en"):
        self.loop = loop
        self.connection = connection
        self.Gio, self.GLib = gio, glib
        self.lang = lang
        self.pending = {}          # cookie -> (process, invocation)
        node = gio.DBusNodeInfo.new_for_xml(AGENT_XML)
        self.registration = connection.register_object(AGENT_PATH, node.interfaces[0], self.handle_call, None, None)

    def register(self):
        """Tell polkit this agent answers for the session."""
        self.connection.call_sync(
            AUTHORITY, AUTHORITY_PATH, AUTHORITY_IFACE, "RegisterAuthenticationAgent",
            self.GLib.Variant("((sa{sv})ss)", (subject(glib=self.GLib), self.lang, AGENT_PATH)),
            None, self.Gio.DBusCallFlags.NONE, -1, None)

    def unregister(self):
        try:
            self.connection.call_sync(
                AUTHORITY, AUTHORITY_PATH, AUTHORITY_IFACE, "UnregisterAuthenticationAgent",
                self.GLib.Variant("((sa{sv})s)", (subject(glib=self.GLib), AGENT_PATH)),
                None, self.Gio.DBusCallFlags.NONE, -1, None)
        except Exception:        # polkit gone: nothing to undo
            pass

    def handle_call(self, _connection, _sender, _path, _iface, method, parameters, invocation):
        if method == "BeginAuthentication":
            self.begin(parameters.unpack(), invocation)
        elif method == "CancelAuthentication":
            (cookie,) = parameters.unpack()
            self.cancel(cookie)
            invocation.return_value(None)

    def begin(self, arguments, invocation):
        action_id, message, icon_name, details, cookie, identities = arguments
        request = prompt_request(action_id, message, icon_name, details, cookie, identities, self.lang)
        if not request["users"]:
            invocation.return_dbus_error(ERROR_FAILED, "No account can answer this request")
            return
        try:
            process = subprocess.Popen(dialog_command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL, text=True)
        except OSError as error:
            invocation.return_dbus_error(ERROR_FAILED, f"The prompt could not be started: {error}")
            return
        self.pending[cookie] = (process, invocation)
        process.stdin.write(json.dumps(request))
        process.stdin.close()
        self.GLib.child_watch_add(self.GLib.PRIORITY_DEFAULT, process.pid,
                                  lambda _pid, _status: self.finished(cookie))

    def finished(self, cookie):
        process, invocation = self.pending.pop(cookie, (None, None))
        if process is None:
            return
        result = (process.stdout.read() or "").strip().splitlines()
        process.wait()
        verdict = result[-1] if result else "FAILURE"
        if verdict == "SUCCESS":
            invocation.return_value(None)
        elif verdict == "CANCELLED":
            invocation.return_dbus_error(ERROR_CANCELLED, "Authentication cancelled")
        else:
            invocation.return_dbus_error(ERROR_FAILED, "Authentication failed")

    def cancel(self, cookie):
        """polkit withdrew the request (the program gave up): the prompt
        goes away and the call is answered as cancelled."""
        process, invocation = self.pending.pop(cookie, (None, None))
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
        invocation.return_dbus_error(ERROR_CANCELLED, "Authentication cancelled")


def stop_kde_agent():
    """An older session may still run KDE's agent, and polkit allows one
    agent per session."""
    subprocess.run(["pkill", "-x", "-f", f".*/{KDE_AGENT}$"], capture_output=True)
    subprocess.run(["pkill", "-f", f"[/]{KDE_AGENT}"], capture_output=True)


def serve(_argv=None):
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
    from .strings import language

    stop_kde_agent()
    loop = GLib.MainLoop()
    connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    agent = Agent(loop, connection, Gio, GLib, language())
    last_error = None
    for attempt in range(10):
        try:
            agent.register()
            break
        except Exception as error:         # polkit not up yet, or KDE's agent still registered
            last_error = error
            stop_kde_agent()
            GLib.usleep(500_000)
    else:
        print(f"veltos-auth-agent: cannot register with polkit: {last_error}", file=sys.stderr)
        return 1

    def quit_(*_args):
        agent.unregister()
        loop.quit()
        return True
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, quit_)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, quit_)
    loop.run()
    return 0


if __name__ == "__main__":
    sys.exit(serve(sys.argv))
