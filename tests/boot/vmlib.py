"""Shared QEMU/KVM helpers for VeltOS VM tests (standard library only).

A VM is driven through two Unix sockets:
  * QMP (QEMU monitor): screenshots, keyboard and absolute-pointer input;
  * the QEMU guest agent (qemu-guest-agent ships in the image): commands and
    file transfer inside the guest.
"""

import base64
import json
import random
import shutil
import socket
import subprocess
import time
from pathlib import Path

OVMF = Path("/usr/share/OVMF")
FIRMWARE = {
    "bios": None,
    "uefi": ("OVMF_CODE_4M.fd", "OVMF_VARS_4M.fd"),
    # Microsoft keys enrolled: exercises the signed shim -> GRUB -> kernel path.
    "secureboot": ("OVMF_CODE_4M.secboot.fd", "OVMF_VARS_4M.ms.fd"),
}
LIVE_USER = "velt"
SCREEN = (1920, 1080)


class JsonLineSocket:
    """Newline-delimited JSON over a Unix socket (QMP and QGA both use it)."""

    def __init__(self, path, timeout):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect(str(path))
        self.buf = b""

    def send(self, obj):
        self.sock.sendall(json.dumps(obj).encode() + b"\n")

    def recv(self):
        while b"\n" not in self.buf:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("socket closed")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        line = line.strip(b"\xff \r")  # guest-sync-delimited sentinel
        return json.loads(line) if line else self.recv()

    def close(self):
        self.sock.close()


class Qmp:
    def __init__(self, path):
        self.conn = JsonLineSocket(path, timeout=30)
        self.conn.recv()  # greeting
        self.execute("qmp_capabilities")

    def execute(self, command, **arguments):
        msg = {"execute": command}
        if arguments:
            msg["arguments"] = arguments
        self.conn.send(msg)
        while True:
            reply = self.conn.recv()
            if "event" in reply:
                continue
            if "error" in reply:
                raise RuntimeError(f"QMP {command}: {reply['error']}")
            return reply.get("return")

    def screenshot(self, path, head=None):
        """The screen as PNG; `head` picks another output of the display
        device (vmctl --outputs; QEMU wants the device id with it)."""
        if head:
            self.execute("screendump", filename=str(path), format="png", device="video0", head=int(head))
        else:
            self.execute("screendump", filename=str(path), format="png")

    def key(self, *names):
        """Press keys together (e.g. key("ctrl", "a")) and release them."""
        self.execute("send-key", keys=[{"type": "qcode", "data": n} for n in names])

    # US keyboard layout: character -> QEMU qcode(s).
    KEYS = {" ": ["spc"], ".": ["dot"], "-": ["minus"], "/": ["slash"], "=": ["equal"],
            ",": ["comma"], ";": ["semicolon"], "'": ["apostrophe"], "\\": ["backslash"],
            "_": ["shift", "minus"], "$": ["shift", "4"], ":": ["shift", "semicolon"],
            '"': ["shift", "apostrophe"], "|": ["shift", "backslash"], ">": ["shift", "dot"],
            "<": ["shift", "comma"], "*": ["shift", "8"], "&": ["shift", "7"],
            "(": ["shift", "9"], ")": ["shift", "0"], "{": ["shift", "bracket_left"],
            "}": ["shift", "bracket_right"], "[": ["bracket_left"], "]": ["bracket_right"]}

    def type_text(self, text, delay=0.05):
        for ch in text:
            if ch.isupper():
                self.key("shift", ch.lower())
            else:
                self.key(*self.KEYS.get(ch, [ch]))
            time.sleep(delay)

    def _move(self, x, y):
        # The virtio tablet uses absolute coordinates scaled to 0..0x7fff.
        sx = int(x * 0x7FFF / (SCREEN[0] - 1))
        sy = int(y * 0x7FFF / (SCREEN[1] - 1))
        self.execute("input-send-event", events=[
            {"type": "abs", "data": {"axis": "x", "value": sx}},
            {"type": "abs", "data": {"axis": "y", "value": sy}},
        ])

    def click(self, x, y, button="left"):
        self._move(x, y)
        time.sleep(0.15)
        for down in (True, False):
            self.execute("input-send-event", events=[
                {"type": "btn", "data": {"down": down, "button": button}}])
            time.sleep(0.08)


class GuestAgent:
    def __init__(self, path):
        self.path = path
        self.conn = None

    def connect(self, deadline):
        """Wait until the agent inside the guest answers guest-sync."""
        while time.monotonic() < deadline:
            try:
                self.conn = JsonLineSocket(self.path, timeout=5)
                sync_id = random.randint(1, 2**31)
                self.conn.send({"execute": "guest-sync-delimited",
                                "arguments": {"id": sync_id}})
                while True:  # discard stale replies from earlier attempts
                    reply = self.conn.recv()
                    if reply.get("return") == sync_id:
                        self.conn.sock.settimeout(120)
                        return True
            except (OSError, ConnectionError, json.JSONDecodeError):
                if self.conn:
                    self.conn.close()
                    self.conn = None
                time.sleep(3)
        return False

    def call(self, command, **arguments):
        self.conn.send({"execute": command, "arguments": arguments})
        reply = self.conn.recv()
        if "error" in reply:
            raise RuntimeError(f"QGA {command}: {reply['error']}")
        return reply["return"]

    def run(self, shell_cmd, timeout=60):
        """Run a shell command in the guest as root -> (exitcode, stdout, stderr)."""
        pid = self.call("guest-exec", path="/bin/sh", arg=["-c", shell_cmd],
                        **{"capture-output": True})["pid"]
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.call("guest-exec-status", pid=pid)
            if status["exited"]:
                def decode(key):
                    return base64.b64decode(status.get(key, "")).decode("utf-8", errors="replace")
                return status.get("exitcode", -1), decode("out-data"), decode("err-data")
            time.sleep(0.5)
        return -1, "", f"timed out after {timeout}s"

    def run_as_user(self, shell_cmd, timeout=60, user=LIVE_USER, uid=1000):
        """Run inside the user's graphical session environment."""
        env = (f"XDG_RUNTIME_DIR=/run/user/{uid} "
               f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus "
               "WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland")
        quoted = shell_cmd.replace("'", "'\\''")
        return self.run(f"runuser -u {user} -- env {env} sh -c '{quoted}'", timeout)

    def upload(self, local_path, guest_path, chunk=1 << 20):
        handle = self.call("guest-file-open", path=str(guest_path), mode="w")
        try:
            with open(local_path, "rb") as fh:
                while True:
                    data = fh.read(chunk)
                    if not data:
                        break
                    self.call("guest-file-write", handle=handle,
                              **{"buf-b64": base64.b64encode(data).decode()})
        finally:
            self.call("guest-file-close", handle=handle)


def start_qemu(iso, firmware, outdir, workdir, cpus=4, memory=4096):
    """Start QEMU; returns (process, Qmp, GuestAgent)."""
    qmp_sock = workdir / "qmp.sock"
    qga_sock = workdir / "qga.sock"
    cmd = [
        "qemu-system-x86_64",
        "-machine", "q35,accel=kvm" + (",smm=on" if firmware == "secureboot" else ""),
        "-cpu", "host", "-smp", str(cpus), "-m", str(memory),
        "-display", "none",
        "-vga", "none", "-device", f"virtio-vga,xres={SCREEN[0]},yres={SCREEN[1]}",
        "-device", "virtio-tablet-pci",
        "-cdrom", str(iso), "-boot", "d",
        "-nic", "user,model=virtio-net-pci",
        "-qmp", f"unix:{qmp_sock},server=on,wait=off",
        "-chardev", f"socket,path={qga_sock},server=on,wait=off,id=qga0",
        "-device", "virtio-serial",
        "-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
        "-serial", f"file:{outdir / 'serial.log'}",
    ]
    fw = FIRMWARE[firmware]
    if fw:
        code, vars_template = fw
        vars_copy = workdir / "OVMF_VARS.fd"
        shutil.copy(OVMF / vars_template, vars_copy)
        if firmware == "secureboot":
            cmd += ["-global", "driver=cfi.pflash01,property=secure,value=on"]
        cmd += ["-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={OVMF / code}",
                "-drive", f"if=pflash,format=raw,unit=1,file={vars_copy}"]
    log = open(outdir / "qemu.log", "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(100):
        if qmp_sock.exists():
            break
        if proc.poll() is not None:
            raise SystemExit(f"QEMU exited early; see {outdir / 'qemu.log'}")
        time.sleep(0.1)
    return proc, Qmp(qmp_sock), GuestAgent(qga_sock)


def wait_for(agent, shell_cmd, timeout, interval=3):
    """Poll a guest command until it succeeds; returns its stdout or None."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        code, out, _ = agent.run(shell_cmd)
        if code == 0:
            return out
        time.sleep(interval)
    return None
