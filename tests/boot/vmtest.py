#!/usr/bin/env python3
"""Boot a VeltOS ISO in QEMU/KVM and verify that the live desktop comes up.

    vmtest.py --iso veltos.iso --firmware uefi --results out/test-results

The VM is driven through two sockets:
  * QMP (QEMU monitor): screenshots, key presses, shutdown;
  * the QEMU guest agent (qemu-guest-agent is part of the image): commands
    inside the guest to check services, the Plasma session and measurements.

Writes report.json, report.md, screenshots and the QEMU log to a new
directory under --results. Exits non-zero if any required check fails.
Standard library only; meant to run inside the veltos-builder container.
"""

import argparse
import base64
import datetime as dt
import json
import os
import random
import shutil
import socket
import subprocess
import sys
import tempfile
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

    def screenshot(self, path):
        self.execute("screendump", filename=str(path), format="png")

    def key(self, name):
        self.execute("send-key", keys=[{"type": "qcode", "data": name}])


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
                        self.conn.sock.settimeout(60)
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
                decode = lambda key: base64.b64decode(status.get(key, "")).decode(
                    "utf-8", errors="replace")
                return status.get("exitcode", -1), decode("out-data"), decode("err-data")
            time.sleep(0.5)
        return -1, "", f"timed out after {timeout}s"


class Report:
    def __init__(self, directory, meta):
        self.dir = directory
        self.meta = meta
        self.checks = []
        self.measurements = {}
        self.artifacts = {}
        self.t0 = time.monotonic()

    def elapsed(self):
        return round(time.monotonic() - self.t0, 1)

    def check(self, name, passed, detail="", required=True):
        status = "PASS" if passed else ("FAIL" if required else "WARN")
        self.checks.append({"name": name, "status": status, "detail": detail.strip()})
        print(f"[{self.elapsed():7.1f}s] {status:4} {name}" + (f" — {detail.strip()[:200]}" if detail else ""),
              flush=True)
        return passed

    def failed(self):
        return any(c["status"] == "FAIL" for c in self.checks)

    def write(self):
        data = {"meta": self.meta, "checks": self.checks,
                "measurements": self.measurements, "artifacts": self.artifacts,
                "result": "FAIL" if self.failed() else "PASS"}
        (self.dir / "report.json").write_text(json.dumps(data, indent=2) + "\n")
        lines = [f"# VeltOS boot test — {self.meta['firmware']} — {data['result']}", ""]
        for key, value in self.meta.items():
            lines.append(f"- **{key}**: {value}")
        lines += ["", "## Checks", "", "| Status | Check | Detail |", "|---|---|---|"]
        for c in self.checks:
            detail = c["detail"].replace("\n", " ").replace("|", "\\|")[:300]
            lines.append(f"| {c['status']} | {c['name']} | {detail} |")
        lines += ["", "## Measurements", ""]
        for key, value in self.measurements.items():
            if isinstance(value, str) and "\n" in value:
                lines += [f"### {key}", "", "```", value.rstrip(), "```", ""]
            else:
                lines.append(f"- **{key}**: {value}")
        lines += ["", "## Screenshots", ""]
        for name, path in self.artifacts.items():
            lines.append(f"- {name}: `{path}`")
        (self.dir / "report.md").write_text("\n".join(lines) + "\n")


def start_qemu(args, workdir):
    qmp_sock = workdir / "qmp.sock"
    qga_sock = workdir / "qga.sock"
    cmd = [
        "qemu-system-x86_64",
        "-machine", "q35,accel=kvm" + (",smm=on" if args.firmware == "secureboot" else ""),
        "-cpu", "host", "-smp", str(args.cpus), "-m", str(args.memory),
        "-display", "none",
        "-vga", "none", "-device", "virtio-vga,xres=1920,yres=1080",
        "-cdrom", str(args.iso), "-boot", "d",
        "-nic", "user,model=virtio-net-pci",
        "-qmp", f"unix:{qmp_sock},server=on,wait=off",
        "-chardev", f"socket,path={qga_sock},server=on,wait=off,id=qga0",
        "-device", "virtio-serial",
        "-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
        "-serial", f"file:{args.outdir / 'serial.log'}",
    ]
    fw = FIRMWARE[args.firmware]
    if fw:
        code, vars_template = fw
        vars_copy = workdir / "OVMF_VARS.fd"
        shutil.copy(OVMF / vars_template, vars_copy)
        if args.firmware == "secureboot":
            cmd += ["-global", "driver=cfi.pflash01,property=secure,value=on"]
        cmd += ["-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={OVMF / code}",
                "-drive", f"if=pflash,format=raw,unit=1,file={vars_copy}"]
    log = open(args.outdir / "qemu.log", "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(100):
        if qmp_sock.exists():
            break
        if proc.poll() is not None:
            raise SystemExit(f"QEMU exited early; see {args.outdir / 'qemu.log'}")
        time.sleep(0.1)
    return proc, Qmp(qmp_sock), GuestAgent(qga_sock)


def wait_for(agent, shell_cmd, timeout, interval=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        code, out, _ = agent.run(shell_cmd)
        if code == 0:
            return out
        time.sleep(interval)
    return None


def run_checks(args, report, qmp, agent):
    shots = args.outdir

    # Boot menu: give the firmware and GRUB a moment, capture, then boot the
    # default entry right away instead of waiting for the countdown.
    time.sleep(args.menu_delay)
    qmp.screenshot(shots / "01-boot-menu.png")
    report.artifacts["boot menu"] = "01-boot-menu.png"
    qmp.key("ret")

    agent_up = agent.connect(time.monotonic() + args.boot_timeout)
    report.measurements["guest_agent_ready_s"] = report.elapsed()
    if not report.check("guest agent reachable (system booted)", agent_up,
                        f"after {report.elapsed()}s"):
        qmp.screenshot(shots / "99-failure.png")
        report.artifacts["failure"] = "99-failure.png"
        return

    _, os_release, _ = agent.run("cat /etc/os-release")
    report.check("os-release identifies VeltOS", "ID=veltos" in os_release,
                 os_release.replace("\n", "; "))
    report.measurements["os-release"] = os_release

    code, out, _ = agent.run("dpkg-query -W -f='${Package} ${Version}\\n' "
                             "veltos-base veltos-desktop plasma-workspace linux-image-amd64")
    report.check("VeltOS packages installed", code == 0, out)
    report.measurements["key_packages"] = out

    session = wait_for(agent, f"pgrep -u {LIVE_USER} -x plasmashell", args.desktop_timeout)
    report.measurements["plasmashell_running_s"] = report.elapsed()
    if not report.check("plasmashell running for live user", session is not None,
                        f"after {report.elapsed()}s"):
        qmp.screenshot(shots / "99-failure.png")
        report.artifacts["failure"] = "99-failure.png"

    _, out, _ = agent.run("loginctl list-sessions --no-legend | awk '{print $1}' | "
                          "while read s; do loginctl show-session $s -p Name -p Type -p State; done")
    report.check("graphical session is Wayland", "Type=wayland" in out,
                 out.replace("\n", "; "), required=False)
    report.measurements["sessions"] = out

    # Let the desktop settle before judging it and measuring idle state.
    time.sleep(args.settle)
    qmp.screenshot(shots / "02-desktop.png")
    report.artifacts["desktop"] = "02-desktop.png"

    _, out, _ = agent.run("systemctl is-system-running; systemctl --failed --no-legend --plain")
    state = out.splitlines()[0] if out else "unknown"
    report.check("no failed systemd units", state == "running", out, required=False)

    home = f"/home/{LIVE_USER}"
    _, appletsrc, _ = agent.run(f"cat {home}/.config/plasma-org.kde.plasma.desktop-appletsrc")
    report.check("VeltOS taskbar layout applied",
                 appletsrc.count("plugin=org.kde.plasma.panelspacer") == 2
                 and "plugin=org.kde.plasma.icontasks" in appletsrc
                 and "veltos-logo" in appletsrc,
                 "2 panel spacers, icon tasks, VeltOS launcher icon")
    report.check("VeltOS wallpaper set", "/usr/share/wallpapers/VeltOS" in appletsrc)
    (args.outdir / "plasma-appletsrc.txt").write_text(appletsrc)

    _, out, _ = agent.run("for f in org.kde.dolphin firefox-esr org.kde.konsole systemsettings; do "
                          "test -f /usr/share/applications/$f.desktop && echo \"ok $f\" || echo \"missing $f\"; done")
    report.check("taskbar launcher .desktop files exist", "missing" not in out, out)

    if args.firmware != "bios":
        _, out, _ = agent.run("test -d /sys/firmware/efi && echo efi || echo bios")
        report.check("booted via UEFI", out.strip() == "efi", out)
    if args.firmware == "secureboot":
        _, out, _ = agent.run("mokutil --sb-state")
        report.check("Secure Boot enabled in guest", "SecureBoot enabled" in out, out)

    _, out, _ = agent.run("journalctl -b -p err --no-pager -o short-monotonic | tail -n 40")
    report.measurements["journal_errors_tail"] = out or "(none)"

    # Measurements (live session; see docs/testing.md for caveats).
    _, out, _ = agent.run("systemd-analyze 2>&1 | head -n1")
    report.measurements["systemd_analyze"] = out.strip()
    _, out, _ = agent.run("free -m")
    report.measurements["free_m"] = out
    _, meminfo, _ = agent.run("grep -E '^(MemTotal|MemAvailable|Shmem|Cached):' /proc/meminfo")
    fields = {l.split(":")[0]: int(l.split()[1]) for l in meminfo.splitlines() if l}
    if "MemTotal" in fields and "MemAvailable" in fields:
        used = (fields["MemTotal"] - fields["MemAvailable"]) // 1024
        report.measurements["idle_used_mib(MemTotal-MemAvailable)"] = used
        report.measurements["shmem_mib(live overlay tmpfs etc.)"] = fields.get("Shmem", 0) // 1024
    _, out, _ = agent.run("ps -eo rss=,comm= --sort=-rss | head -n 15 | "
                          "awk '{printf \"%7.1f MiB  %s\\n\", $1/1024, $2}'")
    report.measurements["top_processes_by_rss"] = out
    _, out, _ = agent.run("ps -e --no-headers | wc -l")
    report.measurements["process_count"] = out.strip()
    _, out, _ = agent.run("uname -r; lspci -k 2>/dev/null | grep -A2 -i vga")
    report.measurements["kernel_and_gpu"] = out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--firmware", choices=sorted(FIRMWARE), default="uefi")
    parser.add_argument("--results", type=Path, default=Path("out/test-results"))
    parser.add_argument("--memory", type=int, default=4096, help="guest RAM in MiB")
    parser.add_argument("--cpus", type=int, default=4)
    parser.add_argument("--menu-delay", type=float, default=8)
    parser.add_argument("--boot-timeout", type=float, default=300)
    parser.add_argument("--desktop-timeout", type=float, default=240)
    parser.add_argument("--settle", type=float, default=60,
                        help="seconds to idle after login before measuring")
    args = parser.parse_args()

    if not Path("/dev/kvm").exists():
        raise SystemExit("/dev/kvm missing: run the container with --device /dev/kvm")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    args.outdir = args.results / f"{stamp}-{args.firmware}"
    args.outdir.mkdir(parents=True)

    meta = {
        "iso": args.iso.name,
        "iso_sha256": subprocess.run(["sha256sum", str(args.iso)], capture_output=True,
                                     text=True).stdout.split()[0],
        "firmware": args.firmware,
        "vm": f"QEMU/KVM q35, {args.cpus} vCPU (host CPU model), {args.memory} MiB RAM, "
              "virtio-vga 1920x1080 (no 3D acceleration), virtio-net",
        "qemu": subprocess.run(["qemu-system-x86_64", "--version"], capture_output=True,
                               text=True).stdout.splitlines()[0],
        "started_utc": stamp,
    }
    report = Report(args.outdir, meta)
    workdir = Path(tempfile.mkdtemp(prefix="vmtest-"))
    proc = None
    try:
        proc, qmp, agent = start_qemu(args, workdir)
        run_checks(args, report, qmp, agent)
        try:
            qmp.execute("quit")
        except (OSError, ConnectionError, RuntimeError):
            pass
    finally:
        if proc and proc.poll() is None:
            proc.kill()
        shutil.rmtree(workdir, ignore_errors=True)
        report.meta["duration_s"] = report.elapsed()
        report.write()
    print(f"Report: {args.outdir / 'report.md'}")
    return 1 if report.failed() else 0


if __name__ == "__main__":
    sys.exit(main())
