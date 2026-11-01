"""Password reset USB (veltos_auth/recovery.py) against a stand-in for
lsblk, findmnt, mount, chpasswd and busctl, with folders standing in for
the drives and the target system."""

import json
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_auth import recovery  # noqa: E402

# lsblk -J -b -o NAME,PATH,TYPE,RM,HOTPLUG,TRAN,SIZE,MODEL,VENDOR,LABEL,FSTYPE,MOUNTPOINTS,PKNAME
# (util-linux 2.41, Debian 13): the PC's disk, the live USB the installer
# runs from, a USB stick with FAT and one without a file system.
LSBLK = {"blockdevices": [
    {"name": "nvme0n1", "path": "/dev/nvme0n1", "type": "disk", "rm": False, "hotplug": False, "tran": "nvme",
     "size": 512110190592, "model": "Samsung SSD", "vendor": None, "label": None, "fstype": None,
     "mountpoints": [None], "children": [
         {"name": "nvme0n1p2", "path": "/dev/nvme0n1p2", "type": "part", "rm": False, "hotplug": False,
          "tran": None, "size": 511000000000, "model": None, "vendor": None, "label": None, "fstype": "ext4",
          "mountpoints": ["/"]}]},
    {"name": "sda", "path": "/dev/sda", "type": "disk", "rm": True, "hotplug": True, "tran": "usb",
     "size": 15500000000, "model": "Flash Disk", "vendor": "SanDisk ", "label": None, "fstype": "iso9660",
     "mountpoints": [None], "children": [
         {"name": "sda1", "path": "/dev/sda1", "type": "part", "rm": True, "hotplug": True, "tran": None,
          "size": 2100000000, "model": None, "vendor": None, "label": "VeltOS", "fstype": "iso9660",
          "mountpoints": ["/run/live/medium"]}]},
    {"name": "sdb", "path": "/dev/sdb", "type": "disk", "rm": True, "hotplug": True, "tran": "usb",
     "size": 8000000000, "model": "DataTraveler", "vendor": "Kingston", "label": None, "fstype": None,
     "mountpoints": [None], "children": [
         {"name": "sdb1", "path": "/dev/sdb1", "type": "part", "rm": True, "hotplug": True, "tran": None,
          "size": 7990000000, "model": None, "vendor": None, "label": "KEYS", "fstype": "vfat",
          "mountpoints": [None]}]},
    {"name": "sdc", "path": "/dev/sdc", "type": "disk", "rm": True, "hotplug": True, "tran": "usb",
     "size": 4000000000, "model": "Empty", "vendor": None, "label": None, "fstype": None,
     "mountpoints": [None]},
]}


class FakeSystem:
    def __init__(self):
        self.commands = []
        self.inputs = []
        self.lsblk = LSBLK
        self.medium = "/dev/sda1"
        self.chpasswd_code = 0

    def __call__(self, command, input=None, timeout=60):
        self.commands.append(list(command))
        if command[0] == "lsblk":
            return 0, json.dumps(self.lsblk)
        if command[0] == "findmnt":
            return (0, self.medium + "\n") if self.medium else (1, "")
        if command[0] == "chpasswd":
            self.inputs.append(input)
            return self.chpasswd_code, ""
        if command[:2] == ["busctl", "call"] and "FindUserByName" in command:
            return 0, 'o "/org/freedesktop/Accounts/User1000"\n'
        return 0, ""


def mounter(folders):
    """A Mounted stand-in: each partition is a folder."""
    class FakeMounted(recovery.Mounted):
        def __enter__(self):
            folder = folders.get(self.drive["path"])
            if folder is None:
                return None
            folder.mkdir(parents=True, exist_ok=True)
            return folder

        def __exit__(self, *_exc):
            return False
    return FakeMounted


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "target"
        (self.root / "etc").mkdir(parents=True)
        (self.root / "etc/passwd").write_bytes("root:x:0:0:root:/root:/bin/bash\n"
                                               "ayse:x:1000:1000:Ayşe:/home/ayse:/bin/bash\n".encode("utf-8"))
        self.stick = self.tmp / "stick"
        self.system = FakeSystem()
        self.mount = mounter({"/dev/sdb1": self.stick})

    def create(self, user="ayse", partition="/dev/sdb1"):
        return recovery.create(user, partition, root=str(self.root), host="ayse-pc", runner=self.system,
                               mount=self.mount)

    def test_keys_are_long_random_and_compared_by_hash(self):
        key = recovery.new_key()
        self.assertEqual(len(recovery.normal(key)), 52)          # 256 bits in base32
        self.assertNotEqual(key, recovery.new_key())
        record = recovery.make_record(key)
        self.assertNotIn(recovery.normal(key), json.dumps(record))
        self.assertTrue(recovery.matches(record, key))
        self.assertTrue(recovery.matches(record, key.lower().replace("-", " ")))
        self.assertFalse(recovery.matches(record, recovery.new_key()))
        self.assertFalse(recovery.matches({"salt": "zz"}, key))

    def test_only_usb_drives_with_a_file_system_and_never_the_live_medium(self):
        found = recovery.drives(self.system)
        self.assertEqual([d["path"] for d in found], ["/dev/sdb1"])
        self.assertEqual((found[0]["label"], found[0]["model"], found[0]["fstype"]),
                         ("KEYS", "Kingston DataTraveler", "vfat"))
        # The installation's target disk is left out too, named or mounted
        # by the installer.
        self.assertEqual(recovery.drives(self.system, exclude=["/dev/sdb"]), [])
        target = json.loads(json.dumps(LSBLK))
        target["blockdevices"][2]["children"][0]["mountpoints"] = ["/tmp/calamares-root-x2"]
        self.system.lsblk = target
        self.assertEqual(recovery.drives(self.system), [])

    def test_create_writes_the_key_to_the_drive_and_only_a_hash_to_the_pc(self):
        self.assertEqual(self.create(), "")
        key_file = self.stick / recovery.FOLDER / "ayse-pc-ayse.veltoskey"
        data = json.loads(key_file.read_text())
        self.assertEqual((data["user"], data["host"]), ("ayse", "ayse-pc"))
        self.assertIn("Keep it safe", (self.stick / recovery.FOLDER / "README.txt").read_text())
        record_file = self.root / "var/lib/veltos/recovery/ayse.json"
        record = json.loads(record_file.read_text())
        self.assertTrue(recovery.matches(record, data["key"]))
        self.assertNotIn(recovery.normal(data["key"]), record_file.read_text())
        self.assertTrue(recovery.configured("ayse", str(self.root)))
        if hasattr(record_file, "stat") and sys.platform != "win32":
            self.assertEqual(record_file.stat().st_mode & 0o777, 0o600)

    def test_create_refuses_unknown_users_and_other_disks(self):
        self.assertEqual(self.create(user="nobody"), "bad-user")
        self.assertEqual(self.create(user="../etc"), "bad-user")
        self.assertEqual(self.create(partition="/dev/nvme0n1p2"), "bad-drive")
        self.assertEqual(self.create(partition="/dev/sda1"), "bad-drive")     # the live USB
        self.assertFalse(recovery.configured("ayse", str(self.root)))

    def test_reset_needs_the_drive_with_the_matching_key(self):
        self.assertEqual(recovery.reset("ayse", "new pass", root=str(self.root), runner=self.system,
                                        mount=self.mount), "not-set-up")
        self.assertEqual(self.create(), "")
        # Another PC's key for an account of the same name does not count.
        other = self.stick / recovery.FOLDER / "ayse-pc-ayse.veltoskey"
        good = other.read_text()
        other.write_text(json.dumps({"user": "ayse", "host": "ayse-pc", "key": recovery.new_key()}))
        self.assertEqual(recovery.reset("ayse", "new pass", root=str(self.root), runner=self.system,
                                        mount=self.mount), "no-key")
        self.assertEqual(self.system.inputs, [])
        other.write_text(good)
        self.assertEqual(recovery.reset("ayse", "line\nbreak", root=str(self.root), runner=self.system,
                                        mount=self.mount), "bad-password")
        self.assertEqual(recovery.reset("ayse", "new pass", hint="cat", root=str(self.root), runner=self.system,
                                        mount=self.mount), "")
        self.assertEqual(self.system.inputs, ["ayse:new pass\n"])
        self.assertIn(["busctl", "call", "org.freedesktop.Accounts", "/org/freedesktop/Accounts/User1000",
                       "org.freedesktop.Accounts.User", "SetPasswordHint", "s", "cat"], self.system.commands)
        # Without a drive in.
        self.system.lsblk = {"blockdevices": LSBLK["blockdevices"][:1]}
        self.assertEqual(recovery.reset("ayse", "x", root=str(self.root), runner=self.system,
                                        mount=self.mount), "no-drive")

    def test_hint_comes_from_accountsservice(self):
        accounts = self.tmp / "accounts"
        accounts.mkdir()
        (accounts / "ayse").write_text("[User]\nSession=\nPasswordHint=my first cat\nIcon=/home/ayse/.face\n")
        self.assertEqual(recovery.hint_of("ayse", accounts), "my first cat")
        self.assertEqual(recovery.hint_of("ali", accounts), "")

    def test_sign_in_screen_requests(self):
        self.assertEqual(self.create(), "")
        accounts = self.tmp / "accounts"
        accounts.mkdir()
        (accounts / "ayse").write_text("[User]\nPasswordHint=tea\n")
        kwargs = {"root": str(self.root), "runner": self.system, "mount": self.mount, "accounts": accounts,
                  "wants": self.tmp / "wants"}
        self.assertEqual(recovery.answer("POST", "/status", {"user": "ayse"}, **kwargs),
                         (200, {"configured": True, "hint": "tea", "resetRequested": False}))
        self.assertEqual(recovery.answer("POST", "/find", {"user": "ayse"}, **kwargs), (200, {"error": ""}))
        self.assertEqual(recovery.answer("POST", "/reset", {"user": "ayse", "password": "p"}, **kwargs),
                         (200, {"error": ""}))
        self.assertEqual(recovery.answer("GET", "/status", {"user": "ayse"}, **kwargs)[0], 400)
        self.assertEqual(recovery.answer("POST", "/status", {"user": "root;x"}, **kwargs)[0], 400)
        self.assertEqual(recovery.answer("POST", "/status", {"user": "nobody"}, **kwargs)[0], 400)

    def serve_once(self, request, uid):
        server, client = socket.socketpair()
        client.settimeout(10)
        result = {}
        accounts = {1000: "ayse", 1001: "ali"}
        thread = threading.Thread(target=lambda: result.update(code=recovery.serve(
            server, allowed_uid=117, uid_of=lambda _sock: uid, account_of=lambda peer: accounts.get(peer, ""),
            wants=self.tmp / "wants", root=str(self.root), runner=self.system, mount=self.mount,
            accounts=self.tmp)))
        thread.start()
        client.sendall(request)
        data = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\r\n\r\n" in data:
                head, _, body = data.partition(b"\r\n\r\n")
                length = int(head.decode().split("Content-Length: ")[1].split("\r\n")[0])
                if len(body) >= length:
                    break
        thread.join(5)
        server.close()
        client.close()
        return data

    def test_only_the_sign_in_screen_is_answered(self):
        body = json.dumps({"user": "ayse"}).encode()
        request = (b"POST /status HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
                   b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
        answer = self.serve_once(request, uid=117)
        self.assertTrue(answer.startswith(b"HTTP/1.0 200 OK"), answer)
        self.assertEqual(json.loads(answer.partition(b"\r\n\r\n")[2]),
                         {"configured": False, "hint": "", "resetRequested": False})
        refused = self.serve_once(request, uid=1000)
        self.assertTrue(refused.startswith(b"HTTP/1.0 403"), refused)

    @staticmethod
    def post(path, user):
        body = json.dumps({"user": user}).encode()
        return (f"POST {path} HTTP/1.0\r\nContent-Length: {len(body)}\r\n\r\n").encode() + body

    def test_lock_screen_asks_for_the_reset_panel(self):
        # The lock screen (the user's own process) may ask the sign-in
        # screen to open its reset panel, for its own account only; the
        # sign-in screen sees the wish once.
        self.assertTrue(self.serve_once(self.post("/want-reset", "ayse"), uid=1000).startswith(b"HTTP/1.0 200"))
        for uid, user, path in ((1001, "ayse", "/want-reset"), (1000, "ayse", "/status"),
                                (1000, "ayse", "/reset"), (0, "root", "/want-reset")):
            self.assertTrue(self.serve_once(self.post(path, user), uid=uid).startswith(b"HTTP/1.0 403"), path)
        first = self.serve_once(self.post("/status", "ayse"), uid=117)
        self.assertTrue(json.loads(first.partition(b"\r\n\r\n")[2])["resetRequested"])
        again = self.serve_once(self.post("/status", "ayse"), uid=117)
        self.assertFalse(json.loads(again.partition(b"\r\n\r\n")[2])["resetRequested"])
        # An old wish is not used.
        recovery.want_reset("ayse", self.tmp / "wants", now=1000)
        self.assertFalse(recovery.take_reset_wish("ayse", self.tmp / "wants", now=1000 + 301))

    def test_own_hint_through_accountsservice(self):
        def runner(command, input=None, timeout=60):
            if "FindUserByName" in command:
                return 0, '{"type":"o","data":["/org/freedesktop/Accounts/User1000"]}'
            if command[-1] == "PasswordHint" and command[-3] == "/org/freedesktop/Accounts/User1000":
                return 0, '{"type":"s","data":"tea with \\"milk\\""}'
            return 1, ""
        self.assertEqual(recovery.own_hint("ayse", runner), 'tea with "milk"')
        self.assertEqual(recovery.own_hint("ayse", lambda *a, **k: (1, "")), "")

    def test_peer_uid_from_the_tcp_table(self):
        table = self.tmp / "tcp"
        table.write_text(
            "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
            "   0: 0100007F:BA9F 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 1 1\n"
            "   1: 0100007F:D431 0100007F:BA9F 01 00000000:00000000 00:00000000 00000000   117        0 2 1\n"
            "   2: 0100007F:BA9F 0100007F:D431 01 00000000:00000000 00:00000000 00000000     0        0 3 1\n")

        class Peer:
            def getpeername(self):
                return ("127.0.0.1", 0xD431)
        self.assertEqual(recovery.peer_uid(Peer(), tables=(str(table),)), 117)

        class Remote:
            def getpeername(self):
                return ("192.168.1.5", 0xD431)
        self.assertIsNone(recovery.peer_uid(Remote(), tables=(str(table),)))


if __name__ == "__main__":
    unittest.main()
