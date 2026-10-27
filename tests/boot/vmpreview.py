#!/usr/bin/env python3
"""Preview VeltOS package changes in a live VM without rebuilding the ISO.

    vmpreview.py --iso veltos.iso --debs /out/packages --results /out/preview \
        --actions "key:meta_l sleep:2 shot:start-menu type:fire sleep:2 shot:search"

Boots the ISO, installs the given .deb files in the live system (missing
dependencies come from the network), resets the live user's configuration
so first-login defaults apply again, restarts the session, then plays the
actions and saves screenshots plus the session's QML/Plasma log.

Development aid only: what ships is the ISO from `build/run.sh iso`, which
is verified by vmtest.py.

Actions (space separated):
  key:NAME[+NAME]   press keys together (QEMU qcodes: meta_l, esc, ret, tab, a...)
  type:TEXT         type text (letters, digits, space as "_")
  typeraw:TEXT      type text literally (US layout symbols allowed), space as "~"
  click:X,Y         left click at screen coordinates (1920x1080)
  rclick:X,Y        right click
  drag:X1,Y1,X2,Y2  drag with the left button
  sleep:SECONDS     wait
  shot:NAME         save screenshot NAME.png
  frames:SECONDS,STEP,NAME
                    a screenshot every STEP seconds for SECONDS
                    (NAME-000.png, ...), e.g. to see every screen of a boot
"""

import argparse
import datetime as dt
import shutil
import sys
import tempfile
import time
from pathlib import Path

from vmlib import LIVE_USER, start_qemu, wait_for

# Coordinates assume the default VeltOS layout at 1920x1080 (Start menu
# centred above the taskbar).
DEFAULT_ACTIONS = ("sleep:3 shot:01-desktop key:meta_l sleep:3 shot:02-start-menu "
                   "rclick:555,450 sleep:2 shot:03-context-menu key:esc sleep:1 "
                   "click:1062,397 sleep:2 shot:04-all-apps key:esc sleep:1 "
                   "type:fire sleep:3 shot:05-search key:esc sleep:1 "
                   "click:1084,1004 sleep:2 shot:06-power-menu key:esc sleep:1 key:esc sleep:2 "
                   "shot:07-closed")


def play(actions, qmp, outdir):
    for action in actions.split():
        kind, _, arg = action.partition(":")
        print(f"  action {action}", flush=True)
        if kind == "key":
            qmp.key(*arg.split("+"))
        elif kind == "type":
            qmp.type_text(arg.replace("_", " "))
        elif kind == "typeraw":
            qmp.type_text(arg.replace("~", " "))
        elif kind == "move":  # hover, e.g. to see a button's hover state
            x, y = (int(v) for v in arg.split(","))
            qmp._move(x, y)
        elif kind in ("click", "rclick"):
            x, y = (int(v) for v in arg.split(","))
            qmp.click(x, y, "left" if kind == "click" else "right")
        elif kind in ("wheeldown", "wheelup"):  # wheeldown:x,y,clicks
            x, y, clicks = (int(v) for v in arg.split(","))
            qmp._move(x, y)
            button = "wheel-down" if kind == "wheeldown" else "wheel-up"
            for _ in range(clicks):
                for down in (True, False):
                    qmp.execute("input-send-event", events=[
                        {"type": "btn", "data": {"down": down, "button": button}}])
                time.sleep(0.05)
        elif kind == "dblclick":
            x, y = (int(v) for v in arg.split(","))
            qmp.click(x, y)
            qmp.click(x, y)
        elif kind == "drag":  # drag:x1,y1,x2,y2 with the left button, in steps
            x1, y1, x2, y2 = (int(v) for v in arg.split(","))
            qmp._move(x1, y1)
            time.sleep(0.15)
            qmp.execute("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}])
            for step in range(1, 11):
                qmp._move(x1 + (x2 - x1) * step // 10, y1 + (y2 - y1) * step // 10)
                time.sleep(0.04)
            qmp.execute("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}])
        elif kind == "powerbutton":  # ACPI power button (VirtualBox: "ACPI Shutdown")
            qmp.execute("system_powerdown")
        elif kind == "reset":  # the reset button: keys sent right after reach the firmware and GRUB
            qmp.execute("system_reset")
        elif kind == "sleep":
            time.sleep(float(arg))
        elif kind == "shot":
            qmp.screenshot(outdir / f"{arg}.png")
        elif kind == "shot2":  # the second monitor (vmctl start --outputs 2)
            qmp.screenshot(outdir / f"{arg}.png", head=1)
        elif kind == "wakeup":  # wake a guest that went to sleep (systemctl suspend)
            qmp.execute("system_wakeup")
        elif kind == "frames":
            seconds, step, name = arg.split(",")
            end = time.monotonic() + float(seconds)
            frame = 0
            while time.monotonic() < end:
                try:
                    qmp.screenshot(outdir / f"{name}-{frame:03d}.png")
                except (OSError, RuntimeError) as error:   # display switching modes
                    print(f"  frame {frame}: {error}", flush=True)
                frame += 1
                time.sleep(float(step))
        else:
            raise SystemExit(f"unknown action {action!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--debs", type=Path, required=True, help="directory with .deb files")
    parser.add_argument("--results", type=Path, default=Path("/out/preview"))
    parser.add_argument("--actions", default=DEFAULT_ACTIONS)
    parser.add_argument("--firmware", default="uefi")
    args = parser.parse_args()

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    outdir = args.results / stamp
    outdir.mkdir(parents=True)
    debs = sorted(args.debs.glob("*.deb"))
    if not debs:
        raise SystemExit(f"no .deb files in {args.debs}")

    workdir = Path(tempfile.mkdtemp(prefix="vmpreview-"))
    proc = None
    log = []
    try:
        proc, qmp, agent = start_qemu(args.iso, args.firmware, outdir, workdir)
        time.sleep(8)
        qmp.key("ret")
        if not agent.connect(time.monotonic() + 300):
            raise SystemExit("guest agent did not come up")
        print("guest up; installing packages", flush=True)

        agent.run("mkdir -p /tmp/veltos-debs")
        for deb in debs:
            agent.upload(deb, f"/tmp/veltos-debs/{deb.name}")
        code, out, err = agent.run(
            "export DEBIAN_FRONTEND=noninteractive; apt-get update -qq && "
            "apt-get install -y -q /tmp/veltos-debs/*.deb", timeout=900)
        log.append(f"## apt install (exit {code})\n{out[-4000:]}\n{err[-4000:]}")
        if code != 0:
            raise SystemExit(f"package install failed:\n{err[-2000:]}")

        # Fresh first login: drop the live user's config and restart SDDM,
        # which autologins again (Relogin=true; by default SDDM autologins only
        # once per boot) and runs the Plasma layout script.
        agent.run("grep -q '^Relogin=' /etc/sddm.conf || "
                  "sed -i '/^\\[Autologin\\]/a Relogin=true' /etc/sddm.conf")
        agent.run("systemctl stop sddm; sleep 2; "
                  f"rm -rf /home/{LIVE_USER}/.config /home/{LIVE_USER}/.local/share "
                  f"/home/{LIVE_USER}/.cache; systemctl start sddm", timeout=120)
        time.sleep(5)
        if wait_for(agent, f"pgrep -u {LIVE_USER} -x plasmashell", 180) is None:
            qmp.screenshot(outdir / "99-no-plasmashell.png")
            raise SystemExit("plasmashell did not start after the session reset")
        time.sleep(15)
        print("session restarted; playing actions", flush=True)
        play(args.actions, qmp, outdir)

        _, out, _ = agent.run(
            f"journalctl -b --no-pager -o cat _UID=$(id -u {LIVE_USER}) | "
            "grep -i -E 'qml|veltos|startmenu|plasmashell.*(error|warning)' | tail -n 80")
        log.append(f"## session log (QML/Plasma)\n{out}")
        _, out, _ = agent.run("coredumpctl list --no-pager 2>&1 | tail -n 10; "
                              "coredumpctl info --no-pager 2>/dev/null | "
                              "sed -n '/Stack trace of thread/,/^$/p' | head -n 70", timeout=120)
        log.append(f"## crashes (coredumpctl)\n{out}")
        _, out, _ = agent.run(f"cat /home/{LIVE_USER}/.config/plasma-org.kde.plasma.desktop-appletsrc")
        (outdir / "plasma-appletsrc.txt").write_text(out)
    finally:
        if proc and proc.poll() is None:
            proc.kill()
        shutil.rmtree(workdir, ignore_errors=True)
        (outdir / "preview.log").write_text("\n\n".join(log) + "\n")
    print(f"Preview: {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
