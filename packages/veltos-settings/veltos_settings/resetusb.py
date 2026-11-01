"""Accounts > Sign-in options: the password hint and the password reset USB
(product owner, 2026-11-01: a forgotten password set again on the sign-in
screen with a USB drive; a hint as in Windows 11).

The drive itself is made by veltos-auth's password-recovery command (the
key on the drive, only its hash on the PC; see veltos_auth/recovery.py):
Settings lists the USB drives with it and runs `create`/`remove` through
pkexec (an administrator approves, as for Windows' password reset disk).
Without veltos-auth the row is not shown.

The hint is AccountsService's own PasswordHint, which a user may set for
their account without a password (org.freedesktop.accounts.change-own-
user-data); the sign-in screen shows it after a wrong password.
"""

import json
import os
import re
import socket

try:
    from veltos_settings.devices import run
except ImportError:  # pragma: no cover - run from the source tree
    from devices import run

COMMAND = "/usr/libexec/veltos/password-recovery"
# pkexec waits for the administrator's password, then the drive is written.
TIMEOUT = 300 + 120


def user_path(uid=None):
    return f"/org/freedesktop/Accounts/User{os.getuid() if uid is None else uid}"


class ResetUsb:
    def __init__(self, runner=run, command=COMMAND, user=None, uid=None, host=None):
        self.run = runner
        self.command = command
        self.user = user or os.environ.get("USER") or ""
        self.path = user_path(uid)
        self.host = host or socket.gethostname()

    def available(self):
        return os.path.exists(self.command)

    def _json(self, args, timeout=30):
        code, out = self.run(args, timeout=timeout)
        starts = [i for i in (out.find("{"), out.find("[")) if i >= 0]
        try:
            return code, json.loads(out[min(starts):]) if starts else None
        except ValueError:
            return code, None

    def status(self):
        """{"available", "configured", "hint"}."""
        if not self.available():
            return {"available": False, "configured": False, "hint": self.hint()}
        _code, data = self._json([self.command, "status", self.user])
        return {"available": True, "configured": bool(isinstance(data, dict) and data.get("configured")),
                "hint": self.hint()}

    def drives(self):
        """The USB drives a key can go on: [{"path", "label", "size", ...}]."""
        if not self.available():
            return []
        _code, data = self._json([self.command, "drives"])
        return data if isinstance(data, list) else []

    def create(self, partition):
        """"" or an error key (password-recovery's, or "not-allowed" when
        the administrator's permission was not given)."""
        code, data = self._json(["pkexec", self.command, "create", self.user, partition, "--host", self.host],
                                timeout=TIMEOUT)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        if code in (126, 127):           # pkexec: dismissed or not authorised
            return "not-allowed"
        return "" if code == 0 else "failed"

    def remove(self):
        code, data = self._json(["pkexec", self.command, "remove", self.user], timeout=TIMEOUT)
        if code in (126, 127):
            return "not-allowed"
        return "" if code == 0 else "failed"

    def hint(self):
        code, out = self.run(["busctl", "--system", "get-property", "org.freedesktop.Accounts", self.path,
                              "org.freedesktop.Accounts.User", "PasswordHint"])
        match = re.match(r'\s*s\s+"(.*)"\s*$', out, re.S) if code == 0 else None
        if not match:
            return ""
        # busctl writes the string C-escaped.
        return bytes(match.group(1), "utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8", "replace")

    def set_hint(self, hint):
        hint = re.sub(r"[\r\n]", " ", hint).strip()[:100]
        return self.run(["busctl", "--system", "call", "org.freedesktop.Accounts", self.path,
                         "org.freedesktop.Accounts.User", "SetPasswordHint", "s", hint])[0] == 0
