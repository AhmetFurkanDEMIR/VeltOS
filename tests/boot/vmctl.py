#!/usr/bin/env python3
"""Keep a VeltOS VM running and drive it step by step (install tests, demos).

Run inside the builder container (`build/run.sh vm ...` wraps these):

    vmctl.py start --iso X.iso [--disk /vm/disk.qcow2 --disk-size 40G] [--boot cdrom|disk]
    vmctl.py do "click:960,540 sleep:2 shot:step1"     # actions as in vmpreview.py
    vmctl.py exec "systemctl is-system-running"        # command in the guest (root)
    vmctl.py exec-user "veltos-run x.exe &"             # in the live user's session
    vmctl.py upload /tmp /out/packages/*.deb             # copy files into the guest
    vmctl.py stop

`start` keeps running (it is the container's main process) until the VM is
shut down; the other commands connect to its QMP and guest-agent sockets
one at a time. Screenshots go to --shots (default /out/vm).
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

from vmlib import FIRMWARE, OVMF, SCREEN, GuestAgent, Qmp
from vmpreview import play

RUN = Path("/tmp/vmctl")


def start(args):
    RUN.mkdir(parents=True, exist_ok=True)
    args.shots.mkdir(parents=True, exist_ok=True)
    cmd = [
        "qemu-system-x86_64", "-machine", "q35,accel=kvm", "-cpu", "host",
        "-smp", "4", "-m", str(args.memory), "-display", "none",
        "-vga", "none",
        # --outputs 2: a second monitor, off until the guest connects it
        # (docs/dev/testing.md, "Several monitors"); "shot2:" takes its picture.
        "-device", f"virtio-vga,id=video0,max_outputs={args.outputs},xres={SCREEN[0]},yres={SCREEN[1]}",
        "-device", "virtio-tablet-pci",
        "-nic", "user,model=virtio-net-pci",
        "-qmp", f"unix:{RUN / 'qmp.sock'},server=on,wait=off",
        "-chardev", f"socket,path={RUN / 'qga.sock'},server=on,wait=off,id=qga0",
        "-device", "virtio-serial",
        "-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
        "-serial", f"file:{args.shots / 'serial.log'}",
    ]
    if args.disk:
        if not args.disk.exists():
            args.disk.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["qemu-img", "create", "-f", "qcow2", str(args.disk), args.disk_size], check=True)
        cmd += ["-drive", f"file={args.disk},if=virtio,format=qcow2,cache=unsafe"]
    if args.iso:
        cmd += ["-cdrom", str(args.iso)]
    cmd += ["-boot", "d" if args.boot == "cdrom" else "c"]
    code, vars_template = FIRMWARE[args.firmware] or (None, None)
    if code:
        # Persistent NVRAM next to the disk, so boot entries written by the
        # installer survive a reboot into the installed system.
        nvram = (args.disk.parent if args.disk else RUN) / f"OVMF_VARS-{args.firmware}.fd"
        if not nvram.exists():
            shutil.copy(OVMF / vars_template, nvram)
        if args.firmware == "secureboot":
            cmd[cmd.index("q35,accel=kvm")] = "q35,accel=kvm,smm=on"
            cmd += ["-global", "driver=cfi.pflash01,property=secure,value=on"]
        cmd += ["-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={OVMF / code}",
                "-drive", f"if=pflash,format=raw,unit=1,file={nvram}"]
    print(" ".join(cmd), flush=True)
    return subprocess.call(cmd)


def do(args):
    qmp = Qmp(RUN / "qmp.sock")
    play(args.actions, qmp, args.shots)
    return 0


def exec_(args):
    agent = GuestAgent(RUN / "qga.sock")
    if not agent.connect(time.monotonic() + args.timeout):
        print("guest agent not reachable", file=sys.stderr)
        return 1
    code, out, err = agent.run(args.command, timeout=args.timeout)
    sys.stdout.write(out)
    sys.stderr.write(err)
    return code


def upload(args):
    agent = GuestAgent(RUN / "qga.sock")
    if not agent.connect(time.monotonic() + 60):
        return 1
    for src in args.files:
        agent.upload(src, f"{args.dest.rstrip('/')}/{Path(src).name}")
    return 0


def exec_user(args):
    agent = GuestAgent(RUN / "qga.sock")
    if not agent.connect(time.monotonic() + 60):
        return 1
    code, out, err = agent.run_as_user(args.command, timeout=args.timeout)
    sys.stdout.write(out)
    sys.stderr.write(err)
    return code


def stop(_args):
    try:
        Qmp(RUN / "qmp.sock").execute("quit")
    except (OSError, ConnectionError, RuntimeError):
        pass
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--shots", type=Path, default=Path("/out/vm"))
    sub = parser.add_subparsers(dest="command_name", required=True)
    p = sub.add_parser("start")
    p.add_argument("--iso", type=Path)
    p.add_argument("--disk", type=Path)
    p.add_argument("--disk-size", default="40G")
    p.add_argument("--boot", choices=["cdrom", "disk"], default="cdrom")
    p.add_argument("--firmware", choices=sorted(FIRMWARE), default="uefi")
    p.add_argument("--memory", type=int, default=4096)
    p.add_argument("--outputs", type=int, default=1, help="display outputs (a second monitor: 2)")
    p.set_defaults(func=start)
    p = sub.add_parser("do")
    p.add_argument("actions")
    p.set_defaults(func=do)
    p = sub.add_parser("exec")
    p.add_argument("command")
    p.add_argument("--timeout", type=float, default=120)
    p.set_defaults(func=exec_)
    p = sub.add_parser("upload")
    p.add_argument("dest")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=upload)
    p = sub.add_parser("exec-user")
    p.add_argument("command")
    p.add_argument("--timeout", type=float, default=120)
    p.set_defaults(func=exec_user)
    p = sub.add_parser("stop")
    p.set_defaults(func=stop)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
