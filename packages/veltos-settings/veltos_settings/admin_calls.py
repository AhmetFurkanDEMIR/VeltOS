"""Several AccountsService calls in one process, so that polkit asks for
the administrator password once, as Windows does.

AccountsService's "user-administration" action is auth_admin_keep: polkit
remembers the password for a few minutes, but only for the process that
made the call. Every `gdbus call` was a new process, so adding a user (create
it, then set its password) asked twice (VM, 2026-10-23).

    python3 -m veltos_settings.admin_calls < calls.json

The JSON list on standard input (never in the command line, where `ps`
would show the password hash) holds the calls, in order:

    [{"path": "/org/freedesktop/Accounts", "interface": "org.freedesktop.Accounts",
      "method": "CreateUser", "signature": "(ssi)", "args": ["ayse", "Ayşe", 0]},
     {"path": "@created", "interface": "org.freedesktop.Accounts.User",
      "method": "SetPassword", "signature": "(ss)", "args": ["$6$...", ""]}]

"@created" is the object path the previous call returned. Exit status 0
when every call worked, otherwise the number of the call that failed (its
error on standard error); the calls after it are not made.
"""

import json
import sys

BUS = "org.freedesktop.Accounts"
# The person types the password into the VeltOS prompt meanwhile.
TIMEOUT_MS = 300 * 1000


def system_bus():
    from gi.repository import Gio
    return Gio.bus_get_sync(Gio.BusType.SYSTEM, None)


def main(stdin=None, bus=None):
    from gi.repository import Gio, GLib
    calls = json.load(stdin or sys.stdin)
    bus = bus or system_bus()
    created = ""
    for number, call in enumerate(calls, 1):
        path = created if call["path"] == "@created" else call["path"]
        try:
            reply = bus.call_sync(BUS, path, call["interface"], call["method"],
                                  GLib.Variant(call["signature"], tuple(call["args"])), None,
                                  Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, TIMEOUT_MS, None)
        except GLib.Error as error:
            print(error.message, file=sys.stderr)
            return number
        if reply is not None and reply.n_children() and reply.get_child_value(0).get_type_string() == "o":
            created = reply.get_child_value(0).get_string()
    return 0


if __name__ == "__main__":
    sys.exit(main())
