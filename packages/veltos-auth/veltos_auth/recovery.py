"""Password reset USB: a forgotten password can be set again on the sign-in
screen with a USB drive made for the account (product owner, 2026-11-01:
"Forgot password" at sign-in, the drive made in the installer, optional;
without one a forgotten password cannot be reset, and VeltOS says so).

What is where:

  * The USB drive holds the key: a file in the folder "VeltOS Password
    Reset" (`<pc>-<user>.veltoskey`, JSON with the user, the PC's name and
    256 random bits written as 52 letters and digits) and a short note
    saying what the drive does. Nothing on the drive is formatted or
    removed.
  * The PC keeps only a hash of the key: /var/lib/veltos/recovery/<user>.json
    (scrypt with a random salt, readable by root only). The folder is
    readable, so Settings and the sign-in screen can tell whether an
    account has a reset drive without learning anything else.
  * Whoever holds the drive can set a new password for that account, as
    with Windows' password reset disk: VeltOS tells the user to keep it
    safe. Disk encryption keeps its own password; KDE Wallet keeps the old
    one until it is opened with it.

Making a drive (`create`) and removing it (`remove`) need root: the
installer's job runs it in the new system, Settings through pkexec. The
sign-in screen (SDDM, user "sddm") cannot run programs: it talks to
`serve`, a socket-activated service on 127.0.0.1 that answers only
connections of the sddm user (the peer's socket owner in /proc/net/tcp)
and resets a password only after finding a drive whose key matches the
account's hash.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import pwd
except ImportError:  # pragma: no cover - unit tests on a Windows host
    pwd = None

FOLDER = "VeltOS Password Reset"
SUFFIX = ".veltoskey"
# Below the system root ("/" or the installer's target).
RECORDS = "var/lib/veltos/recovery"
ACCOUNTS = Path("/var/lib/AccountsService/users")
PORT = 47824
GREETER_USER = "sddm"
# File systems a reset drive can carry (what Windows and VeltOS can write).
FILESYSTEMS = ("vfat", "exfat", "ntfs", "ntfs3", "ext4", "ext3", "ext2", "btrfs", "f2fs")
# scrypt's cost: the key is random (256 bits), the hash only has to keep it
# from being read back.
SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1}
USER_RE = re.compile(r"[a-z_][a-z0-9_-]{0,31}\$?")
NOTE = {
    "en": "This USB drive can set a new password for the account \"{user}\" on the PC \"{host}\" "
          "(VeltOS, made {date}).\nKeep it safe: anyone who has it can reset that password.\n"
          "On the sign-in screen, choose \"Reset password\" and insert this drive.\n",
}
PATH = "/usr/sbin:/usr/bin:/sbin:/bin"


def run(command, input=None, timeout=60):
    try:
        result = subprocess.run(command, input=input, capture_output=True, text=True, timeout=timeout,
                                env=dict(os.environ, PATH=PATH, LC_ALL="C.UTF-8"))
        return result.returncode, result.stdout + result.stderr
    except (OSError, subprocess.SubprocessError) as error:
        return 127, str(error)


# --- keys and records ------------------------------------------------------------------


def new_key():
    """256 random bits as 52 letters and digits in groups of four
    (base32: no letters that look alike in lower and upper case)."""
    text = base64.b32encode(secrets.token_bytes(32)).decode().rstrip("=")
    return "-".join(text[i:i + 4] for i in range(0, len(text), 4))


def normal(key):
    return re.sub(r"[^A-Z2-7]", "", str(key).upper())


def key_hash(key, salt):
    return hashlib.scrypt(normal(key).encode(), salt=salt, dklen=32, **SCRYPT).hex()


def make_record(key):
    salt = secrets.token_bytes(16)
    return {"format": 1, "salt": salt.hex(), "hash": key_hash(key, salt), "created": int(time.time())}


def matches(record, key):
    try:
        expected = record["hash"]
        actual = key_hash(key, bytes.fromhex(record["salt"]))
    except (KeyError, TypeError, ValueError):
        return False
    return hmac.compare_digest(expected, actual)


def valid_user(user):
    return bool(USER_RE.fullmatch(user or ""))


def record_path(user, root="/"):
    return Path(root) / RECORDS / f"{user}.json"


def configured(user, root="/"):
    """Whether the account has a reset drive (the record exists)."""
    return valid_user(user) and record_path(user, root).is_file()


def read_record(user, root="/"):
    try:
        data = json.loads(record_path(user, root).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def write_record(user, record, root="/"):
    path = record_path(user, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # The folder is readable (whether an account has a drive); the records are not.
    os.chmod(path.parent, 0o755)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle)
    os.chmod(path, 0o600)


def remove_record(user, root="/"):
    try:
        record_path(user, root).unlink()
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


def user_exists(user, root="/"):
    if root in ("/", ""):
        try:
            pwd.getpwnam(user)
            return True
        except KeyError:
            return False
    try:
        lines = (Path(root) / "etc/passwd").read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    return any(line.split(":", 1)[0] == user for line in lines)


def key_file_name(user, host):
    host = re.sub(r"[^A-Za-z0-9_.-]", "", host or "") or "PC"
    return f"{host}-{user}{SUFFIX}"


# --- drives -----------------------------------------------------------------------------


def live_medium(runner=run):
    """The disk the live system runs from (the installer's USB), if any."""
    code, out = runner(["findmnt", "-n", "-o", "SOURCE", "/run/live/medium"])
    return out.strip().splitlines()[0] if code == 0 and out.strip() else ""


def drives(runner=run, exclude=()):
    """The partitions of USB and removable drives that can hold a key:
    [{"path", "disk", "label", "size", "model", "fstype", "mountpoint"}].
    The live medium and disks in `exclude` (the installation's target) are
    left out, and so is any drive with a mounted system folder."""
    code, out = runner(["lsblk", "-J", "-b", "-o",
                        "NAME,PATH,TYPE,RM,HOTPLUG,TRAN,SIZE,MODEL,VENDOR,LABEL,FSTYPE,MOUNTPOINTS,PKNAME"])
    if code != 0:
        return []
    try:
        devices = json.loads(out[out.index("{"):]).get("blockdevices", [])
    except ValueError:
        return []
    medium = live_medium(runner)
    excluded = set(exclude)
    result = []
    for disk in devices:
        if disk.get("type") != "disk":
            continue
        removable = disk.get("rm") in (True, "1", 1) or disk.get("hotplug") in (True, "1", 1) or disk.get("tran") == "usb"
        if not removable or disk.get("path") in excluded:
            continue
        parts = disk.get("children") or [disk]
        paths = {p.get("path") for p in parts} | {disk.get("path")}
        if medium and (medium in paths or any(medium.startswith(p or "\0") for p in paths)):
            continue
        mounted = [m for p in parts for m in (p.get("mountpoints") or []) if m]
        # A system's own disk, the live medium, and the disk being installed
        # onto (Calamares mounts it under /tmp/calamares-root-*).
        if any(m in ("/", "/boot", "/boot/efi", "/home", "/usr", "/var") or m.startswith("/run/live")
               or m.startswith("/tmp/calamares-root") for m in mounted):
            continue
        model = " ".join(x.strip() for x in (disk.get("vendor") or "", disk.get("model") or "") if x and x.strip())
        for part in parts:
            if (part.get("fstype") or "") not in FILESYSTEMS:
                continue
            points = [m for m in (part.get("mountpoints") or []) if m]
            result.append({"path": part.get("path"), "disk": disk.get("path"), "label": part.get("label") or "",
                           "size": int(part.get("size") or disk.get("size") or 0), "model": model,
                           "fstype": part.get("fstype"), "mountpoint": points[0] if points else ""})
    return result


class Mounted:
    """A partition's folder: where it is mounted already, or a private
    mount of our own for the time of the `with` block."""

    def __init__(self, drive, write=False, runner=run):
        self.drive, self.write, self.runner = drive, write, runner
        self.folder, self.ours = None, None

    def __enter__(self):
        if self.drive.get("mountpoint"):
            self.folder = Path(self.drive["mountpoint"])
            return self.folder
        self.ours = tempfile.mkdtemp(prefix="veltos-reset-")
        options = ("rw" if self.write else "ro") + ",nosuid,nodev,noexec"
        code, _ = self.runner(["mount", "-o", options, self.drive["path"], self.ours])
        if code != 0:
            os.rmdir(self.ours)
            self.ours = None
            return None
        self.folder = Path(self.ours)
        return self.folder

    def __exit__(self, *_exc):
        if self.ours:
            self.runner(["sync"])
            self.runner(["umount", self.ours])
            try:
                os.rmdir(self.ours)
            except OSError:
                pass
        return False


def read_keys(folder):
    """The key files in a drive's reset folder: [{"user", "host", "key"}]."""
    found = []
    base = Path(folder) / FOLDER
    for path in sorted(base.glob(f"*{SUFFIX}")) if base.is_dir() else []:
        try:
            if path.stat().st_size > 4096:
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and valid_user(data.get("user")) and data.get("key"):
            found.append({"user": data["user"], "host": str(data.get("host", "")), "key": str(data["key"])})
    return found


def find_key(user, root="/", runner=run, mount=Mounted):
    """("", key) when an inserted drive has a key matching the account's
    hash, else (error, ""): "not-set-up", "no-drive", "no-key"."""
    record = read_record(user, root)
    if record is None:
        return "not-set-up", ""
    candidates = drives(runner)
    if not candidates:
        return "no-drive", ""
    for drive in candidates:
        with mount(drive, write=False, runner=runner) as folder:
            if folder is None:
                continue
            for entry in read_keys(folder):
                if entry["user"] == user and matches(record, entry["key"]):
                    return "", entry["key"]
    return "no-key", ""


# --- the root actions -------------------------------------------------------------------


def create(user, partition, root="/", host=None, runner=run, mount=Mounted, exclude=()):
    """Make a reset drive for the account on a USB partition; "" or an
    error key: "bad-user", "bad-drive", "write-failed"."""
    if not valid_user(user) or not user_exists(user, root):
        return "bad-user"
    drive = next((d for d in drives(runner, exclude) if d["path"] == partition), None)
    if drive is None:
        return "bad-drive"
    host = host or socket.gethostname()
    key = new_key()
    content = json.dumps({"format": 1, "user": user, "host": host, "key": key}, indent=1) + "\n"
    with mount(drive, write=True, runner=runner) as folder:
        if folder is None:
            return "write-failed"
        try:
            target = folder / FOLDER
            target.mkdir(exist_ok=True)
            (target / key_file_name(user, host)).write_bytes(content.encode("utf-8"))
            note = NOTE["en"].format(user=user, host=host, date=time.strftime("%Y-%m-%d"))
            (target / "README.txt").write_bytes(note.encode("utf-8"))
        except OSError:
            return "write-failed"
    try:
        write_record(user, make_record(key), root)
    except OSError:
        return "write-failed"
    return ""


def set_hint(user, hint, runner=run):
    """The account's password hint through AccountsService (as root)."""
    code, out = runner(["busctl", "call", "org.freedesktop.Accounts", "/org/freedesktop/Accounts",
                        "org.freedesktop.Accounts", "FindUserByName", "s", user])
    match = re.search(r'"(/org/freedesktop/Accounts/User\d+)"', out) if code == 0 else None
    if not match:
        return False
    return runner(["busctl", "call", "org.freedesktop.Accounts", match.group(1),
                   "org.freedesktop.Accounts.User", "SetPasswordHint", "s", hint])[0] == 0


def hint_of(user, accounts=ACCOUNTS):
    """The account's password hint (AccountsService keeps it as
    PasswordHint in its root-only file of the user)."""
    try:
        text = (Path(accounts) / user).read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(r"^PasswordHint=(.*)$", text, re.M)
    return match.group(1).strip() if match else ""


def valid_password(password):
    return bool(password) and len(password) <= 512 and not re.search(r"[\r\n\0]", password)


def reset(user, password, hint=None, root="/", runner=run, mount=Mounted):
    """Set a new password after finding the account's drive; "" or an
    error key ("not-set-up", "no-drive", "no-key", "bad-password",
    "failed")."""
    if not valid_user(user) or not user_exists(user, root):
        return "not-set-up"
    if not valid_password(password):
        return "bad-password"
    error, _key = find_key(user, root, runner, mount)
    if error:
        return error
    code, _ = runner(["chpasswd"], input=f"{user}:{password}\n")
    if code != 0:
        return "failed"
    if hint is not None:
        set_hint(user, hint, runner)
    return ""


# --- the sign-in screen's service --------------------------------------------------------


def peer_uid(sock, tables=("/proc/net/tcp",)):
    """The owner of the socket at the other end of a 127.0.0.1 connection."""
    try:
        host, port = sock.getpeername()[:2]
    except OSError:
        return None
    if host != "127.0.0.1":
        return None
    wanted = f"0100007F:{port:04X}"
    for table in tables:
        try:
            lines = Path(table).read_text(encoding="ascii").splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) > 7 and fields[1] == wanted:
                return int(fields[7])
    return None


def greeter_uid():
    try:
        return pwd.getpwnam(GREETER_USER).pw_uid
    except KeyError:
        return None


def read_request(stream, limit=8192):
    """(method, path, body dict) of one HTTP request, or None."""
    data = b""
    while b"\r\n\r\n" not in data and len(data) < limit:
        chunk = stream.recv(1024)
        if not chunk:
            break
        data += chunk
    head, _, body = data.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n")
    parts = lines[0].split(" ") if lines and lines[0] else []
    if len(parts) < 2:
        return None
    length = 0
    for line in lines[1:]:
        name, _, value = line.partition(":")
        if name.strip().lower() == "content-length" and value.strip().isdigit():
            length = min(int(value.strip()), limit)
    while len(body) < length:
        chunk = stream.recv(1024)
        if not chunk:
            break
        body += chunk
    try:
        payload = json.loads(body[:length].decode("utf-8")) if length else {}
    except ValueError:
        payload = {}
    return parts[0], parts[1], payload if isinstance(payload, dict) else {}


def respond(stream, status, payload):
    body = json.dumps(payload).encode("utf-8")
    reason = {200: "OK", 400: "Bad Request", 403: "Forbidden", 404: "Not Found"}.get(status, "OK")
    stream.sendall((f"HTTP/1.0 {status} {reason}\r\nContent-Type: application/json\r\n"
                    f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode("latin-1") + body)


def answer(method, path, body, root="/", runner=run, mount=Mounted, accounts=ACCOUNTS):
    """(status, payload) for the sign-in screen's requests:
    POST /status {"user"}            -> {"configured", "hint"}
    POST /find {"user"}              -> {"error"} ("" when the drive is in)
    POST /reset {"user", "password", "hint"} -> {"error"}"""
    user = str(body.get("user", ""))
    if method != "POST" or not valid_user(user) or not user_exists(user, root):
        return 400, {"error": "bad-request"}
    if path == "/status":
        return 200, {"configured": configured(user, root), "hint": hint_of(user, accounts)}
    if path == "/find":
        return 200, {"error": find_key(user, root, runner, mount)[0]}
    if path == "/reset":
        hint = body.get("hint")
        return 200, {"error": reset(user, str(body.get("password", "")),
                                    str(hint)[:200] if hint is not None else None, root, runner, mount)}
    return 404, {"error": "bad-request"}


def serve(sock, allowed_uid=None, uid_of=peer_uid, **kwargs):
    """Answer one connection (systemd's socket, Accept=yes)."""
    allowed = greeter_uid() if allowed_uid is None else allowed_uid
    request = read_request(sock)
    if request is None:
        return 1
    if allowed is None or uid_of(sock) != allowed:
        respond(sock, 403, {"error": "forbidden"})
        return 1
    if request[0] == "OPTIONS":
        respond(sock, 200, {})
        return 0
    status, payload = answer(*request, **kwargs)
    respond(sock, status, payload)
    return 0


def main(args):
    if args[:1] == ["drives"]:
        exclude = args[1:]
        print(json.dumps(drives(exclude=exclude)))
        return 0
    if len(args) == 2 and args[0] == "status":
        print(json.dumps({"configured": configured(args[1])}))
        return 0
    if args[:1] == ["serve"]:
        sock = socket.socket(fileno=0)
        try:
            return serve(sock)
        finally:
            sock.close()
    if os.geteuid() != 0:
        print(json.dumps({"error": "not-root"}))
        return 2
    if args[:1] == ["create"] and len(args) >= 3:
        options = dict(zip(args[3::2], args[4::2]))
        exclude = [d for d in options.get("--exclude", "").split(",") if d]
        error = create(args[1], args[2], root=options.get("--root", "/"), host=options.get("--host"),
                       exclude=exclude)
        print(json.dumps({"error": error}))
        return 1 if error else 0
    if len(args) == 2 and args[0] == "remove":
        ok = valid_user(args[1]) and remove_record(args[1])
        print(json.dumps({"error": "" if ok else "failed"}))
        return 0 if ok else 1
    print("usage: password-recovery drives [DISK...] | status USER | create USER PARTITION "
          "[--root DIR] [--host NAME] [--exclude DISK,...] | remove USER | serve", file=sys.stderr)
    return 2
