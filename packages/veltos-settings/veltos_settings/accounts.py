"""Accounts > Your info, Sign-in options and Other users.

Users come from AccountsService (the system's account service, which
Plasma and SDDM also use) through `gdbus`: name, picture and account type.
Changing one's own name or picture needs no password; adding, removing or
promoting a user asks for the administrator password through polkit.
Changing one's own password runs `passwd` in a pseudo terminal, like
Windows asks for the current password first.
"""

import os
import pwd
import re
import select
import shutil
import subprocess
import time

from .devices import run

BUS = "org.freedesktop.Accounts"
ROOT = "/org/freedesktop/Accounts"
USER_IFACE = "org.freedesktop.Accounts.User"
USERNAME_RE = re.compile(r"[a-z_][a-z0-9_-]{0,30}")
ADMIN_GROUPS = ("sudo",)


def gdbus(*args):
    return ["gdbus", "call", "--system", "--dest", BUS, *args]


def gvariant_string(text):
    return "'" + str(text).replace("\\", "\\\\").replace("'", "\\'") + "'"


def gvariant_value(text, key):
    """One value of a GetAll reply: strings, numbers and booleans."""
    match = re.search(r"'" + re.escape(key) + r"': <(?:(?:u?int\d+|byte) )?"
                      r"('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|-?\d+|true|false)>", text)
    if not match:
        return None
    value = match.group(1)
    if value[0] in "'\"":
        return re.sub(r"\\(.)", r"\1", value[1:-1])
    if value in ("true", "false"):
        return value == "true"
    return int(value)


def local_users(passwd_text):
    """People's accounts from `getent passwd`: uid 1000-59999 with a login shell."""
    users = []
    for line in passwd_text.splitlines():
        fields = line.split(":")
        if len(fields) < 7 or not fields[2].isdigit():
            continue
        uid = int(fields[2])
        if 1000 <= uid < 60000 and not fields[6].endswith(("nologin", "false")):
            users.append({"name": fields[0], "uid": uid, "gecos": fields[4].split(",")[0]})
    return sorted(users, key=lambda u: u["uid"])


def group_members(group_text):
    fields = group_text.strip().split(":")
    return [m for m in fields[3].split(",") if m] if len(fields) >= 4 else []


class Accounts:
    def __init__(self, runner=run, me=None):
        self.run = runner
        self.me = me or pwd.getpwuid(os.getuid()).pw_name

    def _path(self, name):
        code, out = self.run(gdbus("--object-path", ROOT, "--method", f"{BUS}.FindUserByName", name))
        match = re.search(r"objectpath '([^']+)'", out) if code == 0 else None
        return match.group(1) if match else ""

    def _admins(self):
        members = set()
        for group in ADMIN_GROUPS:
            code, out = self.run(["getent", "group", group])
            if code == 0:
                members.update(group_members(out))
        return members

    def users(self):
        code, out = self.run(["getent", "passwd"])
        admins = self._admins()
        result = []
        for user in local_users(out if code == 0 else ""):
            path = self._path(user["name"])
            props = ""
            if path:
                code, props = self.run(gdbus("--object-path", path, "--method",
                                             "org.freedesktop.DBus.Properties.GetAll", USER_IFACE))
                props = props if code == 0 else ""
            real = gvariant_value(props, "RealName") or user["gecos"] or user["name"]
            icon = gvariant_value(props, "IconFile") or ""
            account_type = gvariant_value(props, "AccountType")
            admin = user["name"] in admins if account_type is None else account_type == 1
            result.append({"name": user["name"], "realName": real, "uid": user["uid"],
                           "icon": icon if icon and os.path.isfile(icon) else "",
                           "admin": bool(admin), "me": user["name"] == self.me, "path": path})
        return result

    def state(self):
        users = self.users()
        me = next((u for u in users if u["me"]), {"name": self.me, "realName": self.me, "icon": "",
                                                 "admin": False, "uid": os.getuid(), "path": ""})
        return {"me": me, "others": [u for u in users if not u["me"]]}

    def set_real_name(self, name):
        name = name.strip()
        path = self._path(self.me)
        if not name or not path or len(name) > 100:
            return False
        return self.run(gdbus("--object-path", path, "--method", f"{USER_IFACE}.SetRealName",
                              gvariant_string(name)))[0] == 0

    def set_picture(self, image):
        """AccountsService copies the picture; Plasma and the sign-in screen
        read it from there."""
        path = self._path(self.me)
        if not path or not os.path.isfile(image):
            return False
        return self.run(gdbus("--object-path", path, "--method", f"{USER_IFACE}.SetIconFile",
                              gvariant_string(image)))[0] == 0

    def add_user(self, username, real_name, password, admin):
        """Creates the account (polkit asks for the administrator password)
        and sets its password. Returns "" or an error key."""
        if not USERNAME_RE.fullmatch(username):
            return "bad_username"
        if len(password) < 1:
            return "password_missing"
        code, _ = self.run(gdbus("--object-path", ROOT, "--method", f"{BUS}.CreateUser",
                                 username, gvariant_string(real_name.strip() or username),
                                 "1" if admin else "0"), timeout=300)
        if code != 0:
            return "add_failed"
        hashed = hash_password(password)
        path = self._path(username)
        if not hashed or not path:
            return "add_failed"
        code, _ = self.run(gdbus("--object-path", path, "--method", f"{USER_IFACE}.SetPassword",
                                 gvariant_string(hashed), "''"), timeout=300)
        return "" if code == 0 else "add_failed"

    def remove_user(self, username, remove_files=True):
        users = {u["name"]: u for u in self.users()}
        user = users.get(username)
        if user is None or user["me"]:
            return False
        return self.run(gdbus("--object-path", ROOT, "--method", f"{BUS}.DeleteUser",
                              str(user["uid"]), "true" if remove_files else "false"), timeout=300)[0] == 0

    def set_admin(self, username, admin):
        users = {u["name"]: u for u in self.users()}
        user = users.get(username)
        if user is None or user["me"] or not user["path"]:
            return False
        return self.run(gdbus("--object-path", user["path"], "--method", f"{USER_IFACE}.SetAccountType",
                              "1" if admin else "0"), timeout=300)[0] == 0


def hash_password(password):
    """SHA-512 crypt hash (what Debian uses) through openssl."""
    try:
        out = subprocess.run(["openssl", "passwd", "-6", "-stdin"], input=password + "\n",
                             capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out if out.startswith("$6$") else ""


def change_password(current, new, passwd_command=None, timeout=30):
    """Change the own password with `passwd` (PAM checks the current one and
    the quality of the new one). Returns "" or an error key: "wrong_password",
    "weak_password", "password_failed"."""
    import pty

    command = passwd_command or [shutil.which("passwd") or "/usr/bin/passwd"]
    pid, fd = pty.fork()
    if pid == 0:                                    # child: passwd in English
        os.environ["LC_ALL"] = "C"
        os.environ["LANGUAGE"] = "C"
        try:
            os.execv(command[0], command)
        finally:
            os._exit(127)
    answers = [current, new, new]
    output = b""
    status = None
    deadline = time.monotonic() + timeout
    try:
        while status is None and time.monotonic() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.2)
            if fd in ready:
                try:
                    chunk = os.read(fd, 1024)
                except OSError:          # the terminal closed: passwd ended
                    chunk = b""
                output += chunk
                if output.decode("utf-8", "replace").lower().rstrip().endswith("password:"):
                    if not answers:      # asked again (new password refused)
                        break
                    os.write(fd, (answers.pop(0) + "\n").encode())
                    output += b"\n"
            finished, code = os.waitpid(pid, os.WNOHANG)
            if finished:
                status = code
        if status is None:
            os.kill(pid, 9)
            status = os.waitpid(pid, 0)[1]
    finally:
        os.close(fd)
    text = output.decode("utf-8", "replace").lower()
    if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
        return ""
    if "authentication token manipulation error" in text or "authentication failure" in text:
        return "wrong_password"
    if "bad password" in text or "too short" in text or "too simple" in text or "dictionary" in text:
        return "weak_password"
    return "password_failed"
