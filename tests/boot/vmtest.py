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
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from vmlib import FIRMWARE, LIVE_USER, start_qemu, wait_for

# QEMU's PNG of an all-black 800x600 or 640x480 screen is about 1.5 KB; the
# boot menu is about 85 KB.
BLACK_PNG_MAX = 4000


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


def run_checks(args, report, qmp, agent):
    shots = args.outdir

    # The boot menu is hidden (like Windows): F4 during GRUB's 2 s wait shows
    # it. Firmware and GRUB take a varying time to start, so F4 is repeated
    # until something is drawn (a black screen gives a tiny PNG). With the
    # menu open GRUB waits, so Enter is repeated until the menu is gone.
    # A menu that never appears is reported (GRUB's PNG reader once left it
    # black, ISO 20261020-083729).
    time.sleep(args.menu_delay)
    menu = shots / "01-boot-menu.png"
    deadline = time.monotonic() + 20
    while True:
        qmp.key("f4")
        time.sleep(1.0)
        qmp.screenshot(menu)
        if menu.stat().st_size > BLACK_PNG_MAX or time.monotonic() > deadline:
            break
    report.artifacts["boot menu"] = "01-boot-menu.png"
    report.check("boot menu drawn", menu.stat().st_size > BLACK_PNG_MAX,
                 f"screenshot {menu.stat().st_size} bytes")
    probe = shots / "01a-after-enter.png"
    for _ in range(5):
        qmp.key("ret")
        time.sleep(1.5)
        qmp.screenshot(probe)
        if probe.read_bytes() != menu.read_bytes():
            break
    probe.unlink(missing_ok=True)
    time.sleep(args.splash_delay)
    qmp.screenshot(shots / "01b-boot-splash.png")
    report.artifacts["boot splash"] = "01b-boot-splash.png"

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
                             "veltos-base veltos-desktop veltos-auth veltos-clock veltos-explorer "
                             "plasma-workspace linux-image-amd64")
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
    report.artifacts["desktop (with the live welcome window)"] = "02-desktop.png"

    _, out, _ = agent.run("systemctl is-system-running; systemctl --failed --no-legend --plain")
    state = out.splitlines()[0] if out else "unknown"
    report.check("no failed systemd units", state == "running", out, required=False)

    home = f"/home/{LIVE_USER}"
    _, appletsrc, _ = agent.run(f"cat {home}/.config/plasma-org.kde.plasma.desktop-appletsrc")
    report.check("VeltOS taskbar layout applied",
                 appletsrc.count("plugin=org.kde.plasma.panelspacer") == 2
                 and "plugin=org.kde.plasma.icontasks" in appletsrc
                 and "plugin=org.veltos.startmenu" in appletsrc,
                 "2 panel spacers, icon tasks, VeltOS Start menu")
    report.check("VeltOS wallpaper set", "/usr/share/wallpapers/VeltOS" in appletsrc)
    (args.outdir / "plasma-appletsrc.txt").write_text(appletsrc)

    _, out, _ = agent.run("for f in veltos-explorer firefox-esr org.kde.konsole veltos-settings; do "
                          "test -f /usr/share/applications/$f.desktop && echo \"ok $f\" || echo \"missing $f\"; done")
    report.check("taskbar launcher .desktop files exist", "missing" not in out, out)

    # Live system experience and Windows 11 look (veltos-desktop, -boot,
    # calamares-settings-veltos).
    _, out, _ = agent.run("lsinitramfs /run/live/medium/live/initrd.img* 2>/dev/null | "
                          "grep -c 'plymouth/themes/veltos/veltos.plymouth$'")
    report.check("boot splash (VeltOS Plymouth theme) is in the live initramfs",
                 out.strip() not in ("", "0"), out.strip())
    _, out, _ = agent.run(f"pgrep -u {LIVE_USER} -f 'veltos-installer/veltos-live-welcome' || true")
    report.check("live welcome window started", out.strip() != "", out.strip() or "not running")
    _, out, _ = agent.run(f"tr '\\0' '\\n' < /proc/$(pgrep -u {LIVE_USER} -x plasmashell | head -n1)/environ "
                          "| grep '^XDG_DATA_DIRS='")
    report.check("session uses VeltOS application names (XDG_DATA_DIRS)",
                 "/var/lib/veltos/xdg:" in out, out.strip())
    _, out, _ = agent.run("grep -h '^Name=' /usr/share/applications/veltos-explorer.desktop; "
                          "grep -c '^NoDisplay=true' /var/lib/veltos/xdg/applications/systemsettings.desktop; "
                          "dpkg-query -W -f='${db:Status-Abbrev}' dolphin 2>/dev/null || echo no-dolphin")
    report.check("VeltOS File Explorer only (no Dolphin); KDE System Settings hidden",
                 "Name=File Explorer" in out and "\n1\n" in out + "\n" and "ii" not in out,
                 out.replace("\n", "; "))
    _, out, _ = agent.run(f"cat {home}/.config/Kvantum/kvantum.kvconfig; "
                          f"grep -c 'GroupState-Remote-IsHidden>true' {home}/.local/share/user-places.xbel; "
                          f"grep -h 'Autolock' {home}/.config/kscreenlockerrc")
    report.check("per-user defaults: VeltOS style, File Explorer side bar, no live screen lock",
                 "theme=VeltOS" in out and "\n1\n" in out and "Autolock=false" in out,
                 out.replace("\n", "; "))
    # The session's helpers: VeltOS' password prompt (not KDE's agent),
    # Clock's alarm agent, and the VeltOS file dialogs for every program.
    _, out, _ = agent.run(f"pgrep -u {LIVE_USER} -f veltos-auth-agent >/dev/null && echo veltos-agent; "
                          f"pgrep -u {LIVE_USER} -f polkit-kde-authentication-agent-1 >/dev/null && echo kde-agent; "
                          f"pgrep -u {LIVE_USER} -f veltos-clock-agent >/dev/null && echo clock-agent; "
                          "grep -h FileChooser /etc/xdg/xdg-desktop-portal/kde-portals.conf; "
                          # plasmashell's environment is what programs started from Start
                          # inherit: the portal theme must be there (a drop-in giving
                          # plasmashell KDE's theme took the Windows 11 file dialogs away
                          # from every program, 2026-10-22).
                          f"grep -c xdgdesktopportal /proc/$(pgrep -u {LIVE_USER} -x plasmashell | head -1)/environ")
    report.check("VeltOS password prompt and Clock alarms run with the session; portal file dialogs",
                 "veltos-agent" in out and "kde-agent" not in out and "clock-agent" in out
                 and "FileChooser=veltos" in out and "\n1" in out,
                 out.replace("\n", "; "))

    # The welcome window covers the desktop: close it and show the desktop
    # and the Start menu for review.
    agent.run(f"pkill -u {LIVE_USER} -f 'veltos-installer/veltos-live-welcome' || true")
    time.sleep(3)
    qmp.screenshot(shots / "03-desktop-clean.png")
    report.artifacts["desktop without welcome window"] = "03-desktop-clean.png"
    qmp.key("meta_l")
    time.sleep(3)
    qmp.screenshot(shots / "04-start-menu.png")
    report.artifacts["start menu"] = "04-start-menu.png"
    qmp.key("esc")
    time.sleep(1)

    if args.firmware != "bios":
        _, out, _ = agent.run("test -d /sys/firmware/efi && echo efi || echo bios")
        report.check("booted via UEFI", out.strip() == "efi", out)
    if args.firmware == "secureboot":
        _, out, _ = agent.run("mokutil --sb-state")
        report.check("Secure Boot enabled in guest", "SecureBoot enabled" in out, out)

    # Any crash (core dump) during boot, login or idle is a failure.
    _, out, _ = agent.run("coredumpctl list --no-legend --no-pager 2>/dev/null")
    report.check("no crashed processes", out.strip() == "", out or "none")
    if out.strip():
        _, trace, _ = agent.run("coredumpctl info --no-pager 2>/dev/null | "
                                "sed -n '/Stack trace of thread/,/^$/p' | head -n 40", timeout=120)
        report.measurements["crash_stack_trace"] = trace

    _, out, _ = agent.run("journalctl -b -p err --no-pager -o short-monotonic | tail -n 40")
    report.measurements["journal_errors_tail"] = out or "(none)"

    # Measurements (live session; see docs/dev/testing.md for caveats).
    _, out, _ = agent.run("systemd-analyze 2>&1 | head -n1")
    report.measurements["systemd_analyze"] = out.strip()
    _, out, _ = agent.run("systemd-analyze blame --no-pager 2>/dev/null | head -n 10")
    report.measurements["systemd_analyze_blame_top10"] = out
    # The image carries AppArmor's profile cache for its kernel
    # (8500-veltos-apparmor-cache); compiling at boot took 11 s.
    _, out, _ = agent.run("systemctl show -p ExecMainStartTimestampMonotonic,ExecMainExitTimestampMonotonic "
                          "apparmor.service")
    stamps = dict(line.split("=", 1) for line in out.split() if "=" in line)
    try:
        took = (int(stamps["ExecMainExitTimestampMonotonic"]) -
                int(stamps["ExecMainStartTimestampMonotonic"])) / 1e6
    except (KeyError, ValueError):
        took = None
    report.check("AppArmor profiles loaded from the build-time cache",
                 took is not None and 0 <= took < 3, f"apparmor.service took {took} s")
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
    parser.add_argument("--menu-delay", type=float, default=3)
    parser.add_argument("--splash-delay", type=float, default=5,
                        help="seconds after leaving the boot menu to capture the splash")
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
        proc, qmp, agent = start_qemu(args.iso, args.firmware, args.outdir, workdir,
                                       args.cpus, args.memory)
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
